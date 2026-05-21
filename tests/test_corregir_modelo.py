from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCorregirModelo(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.modelo = cls.env["product.attribute"].create(
            {"name": "Modelo", "create_variant": "always"})
        cls.marca = cls.env["product.attribute"].create(
            {"name": "Marca", "create_variant": "always"})
        AV = cls.env["product.attribute.value"]
        cls.v_sin = AV.create({"name": "SIN", "attribute_id": cls.modelo.id})
        cls.v_all = AV.create({"name": "All", "attribute_id": cls.modelo.id})
        cls.v_mich = AV.create({"name": "MICHELIN", "attribute_id": cls.marca.id})
        cls.v_bkt = AV.create({"name": "BKT", "attribute_id": cls.marca.id})
        cls.partner = cls.env["res.partner"].create({"name": "Cliente test"})

    def _tmpl(self, name, marca_val, modelo_val):
        return self.env["product.template"].create({
            "name": name, "type": "consu",
            "attribute_line_ids": [
                (0, 0, {"attribute_id": self.marca.id,
                        "value_ids": [(6, 0, [marca_val.id])]}),
                (0, 0, {"attribute_id": self.modelo.id,
                        "value_ids": [(6, 0, [modelo_val.id])]}),
            ],
        })

    def _so_line(self, variant, price=1000.0, qty=3):
        so = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": variant.id,
                "product_uom_qty": qty,
                "price_unit": price,
            })],
        })
        return so.order_line

    def _modelo_name(self, variant):
        ptav = variant.product_template_variant_value_ids.filtered(
            lambda v: v.attribute_id == self.modelo)
        return ptav.product_attribute_value_id.name

    # ── Camino 1: valor único -> renombrar (sin regenerar) ───────────────
    def test_rename_unique(self):
        tmpl = self._tmpl("11.00 R16", self.v_mich, self.v_sin)
        variant = tmpl.product_variant_ids
        line = self._so_line(variant)
        self.assertTrue(line.can_fix_model)

        wiz = self.env["camiletti.corregir.modelo"].create({
            "line_id": line.id, "product_id": variant.id,
            "modelo_actual": "SIN", "modelo_nuevo": "XZL"})
        wiz.action_confirmar()

        # mismo registro de valor, renombrado en el lugar
        self.assertEqual(self.v_sin.name, "XZL")
        # misma variante (no se regeneró)
        self.assertEqual(line.product_id, variant)
        self.assertEqual(self._modelo_name(variant), "XZL")
        self.assertFalse(line.can_fix_model)

    # ── Camino 2: valor compartido -> reasignar solo este template ───────
    def test_reassign_shared_preserva_otros_y_precio(self):
        tmpl_a = self._tmpl("225/50 R17", self.v_mich, self.v_all)
        tmpl_b = self._tmpl("195/60 R15", self.v_bkt, self.v_all)  # comparte "All"
        var_a = tmpl_a.product_variant_ids
        line = self._so_line(var_a, price=1234.0, qty=5)

        wiz = self.env["camiletti.corregir.modelo"].create({
            "line_id": line.id, "product_id": var_a.id,
            "modelo_actual": "All", "modelo_nuevo": "PRIMACY 4"})
        wiz.action_confirmar()

        # "All" NO se renombró (sigue para el template B)
        self.assertEqual(self.v_all.name, "All")
        b_model = tmpl_b.product_variant_ids.product_template_variant_value_ids.filtered(
            lambda v: v.attribute_id == self.modelo).product_attribute_value_id.name
        self.assertEqual(b_model, "All")
        # la línea quedó reapuntada a la nueva variante con el modelo correcto
        self.assertNotEqual(line.product_id, var_a)
        self.assertEqual(self._modelo_name(line.product_id), "PRIMACY 4")
        # precio y cantidad preservados
        self.assertEqual(line.price_unit, 1234.0)
        self.assertEqual(line.product_uom_qty, 5)

    # ── Camino 3: el modelo destino ya existe -> reusar, sin duplicar ────
    def test_reassign_reusa_valor_existente(self):
        existente = self.env["product.attribute.value"].create(
            {"name": "PRIMACY 4", "attribute_id": self.modelo.id})
        tmpl_a = self._tmpl("205/55 R16", self.v_mich, self.v_all)
        tmpl_b = self._tmpl("215/55 R17", self.v_bkt, self.v_all)
        var_a = tmpl_a.product_variant_ids
        line = self._so_line(var_a)

        wiz = self.env["camiletti.corregir.modelo"].create({
            "line_id": line.id, "product_id": var_a.id,
            "modelo_actual": "All", "modelo_nuevo": "PRIMACY 4"})
        wiz.action_confirmar()

        # no se creó un valor duplicado "PRIMACY 4"
        n = self.env["product.attribute.value"].search_count(
            [("attribute_id", "=", self.modelo.id), ("name", "=", "PRIMACY 4")])
        self.assertEqual(n, 1)
        self.assertEqual(self._modelo_name(line.product_id), "PRIMACY 4")
