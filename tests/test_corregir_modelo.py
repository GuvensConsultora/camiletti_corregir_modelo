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

    def _wizard(self, product, nuevo):
        return self.env["camiletti.corregir.modelo"].create({
            "product_id": product.id,
            "modelo_actual": product._get_modelo_ptav().name,
            "modelo_nuevo": nuevo,
        })

    def _modelo_name(self, variant):
        return variant.product_template_variant_value_ids.filtered(
            lambda v: v.attribute_id == self.modelo
        ).product_attribute_value_id.name

    # ── flag de visibilidad ──────────────────────────────────────────────
    def test_can_fix_model_flag(self):
        placeholder = self._tmpl("11.00 R16", self.v_mich, self.v_sin)
        self.assertTrue(placeholder.product_variant_ids.can_fix_model)

    # ── Camino 1: valor único -> renombrar (sin regenerar) ───────────────
    def test_rename_unique(self):
        tmpl = self._tmpl("11.00 R16", self.v_mich, self.v_sin)
        variant = tmpl.product_variant_ids
        self.assertTrue(variant.can_fix_model)

        self._wizard(variant, "XZL").action_confirmar()

        # mismo registro de valor, renombrado en el lugar (no regenera)
        self.assertEqual(self.v_sin.name, "XZL")
        self.assertEqual(self._modelo_name(variant), "XZL")
        self.assertFalse(variant.can_fix_model)

    # ── Camino 2: valor compartido -> reasignar solo este template ───────
    def test_reassign_shared_no_afecta_otros(self):
        tmpl_a = self._tmpl("225/50 R17", self.v_mich, self.v_all)
        tmpl_b = self._tmpl("195/60 R15", self.v_bkt, self.v_all)  # comparte "All"
        var_a = tmpl_a.product_variant_ids

        self._wizard(var_a, "PRIMACY 4").action_confirmar()

        # "All" NO se renombró: el template B lo conserva
        self.assertEqual(self.v_all.name, "All")
        self.assertEqual(
            self._modelo_name(tmpl_b.product_variant_ids), "All")
        # el template A quedó con el modelo correcto
        self.assertEqual(
            self._modelo_name(tmpl_a.product_variant_ids), "PRIMACY 4")

    # ── Camino 3: el modelo destino ya existe -> reusar, sin duplicar ────
    def test_reassign_reusa_valor_existente(self):
        self.env["product.attribute.value"].create(
            {"name": "PRIMACY 4", "attribute_id": self.modelo.id})
        tmpl_a = self._tmpl("205/55 R16", self.v_mich, self.v_all)
        self._tmpl("215/55 R17", self.v_bkt, self.v_all)
        var_a = tmpl_a.product_variant_ids

        self._wizard(var_a, "PRIMACY 4").action_confirmar()

        n = self.env["product.attribute.value"].search_count(
            [("attribute_id", "=", self.modelo.id), ("name", "=", "PRIMACY 4")])
        self.assertEqual(n, 1)
        self.assertEqual(
            self._modelo_name(tmpl_a.product_variant_ids), "PRIMACY 4")
