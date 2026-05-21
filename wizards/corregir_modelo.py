from odoo import fields, models, _
from odoo.exceptions import UserError

from ..models.product_product import MODELO_ATTR, PLACEHOLDERS


class CorregirModelo(models.TransientModel):
    _name = "camiletti.corregir.modelo"
    _description = "Corregir el valor de Modelo de una cubierta"

    # Opcional: si se invoca desde una línea de presupuesto se reapunta; desde
    # el catálogo no hay línea y solo se corrige el producto.
    line_id = fields.Many2one(
        "sale.order.line", string="Línea", ondelete="cascade",
    )
    product_id = fields.Many2one(
        "product.product", string="Producto", required=True, readonly=True,
    )
    modelo_actual = fields.Char(string="Modelo actual", readonly=True)
    modelo_nuevo = fields.Char(string="Modelo correcto", required=True)

    # ── helpers ──────────────────────────────────────────────────────────
    def _modelo_attribute(self):
        attr = self.env["product.attribute"].search(
            [("name", "=", MODELO_ATTR)], limit=1)
        if not attr:
            raise UserError(_("No existe el atributo '%s'.") % MODELO_ATTR)
        return attr

    def _current_value(self):
        ptav = self.product_id.product_template_variant_value_ids.filtered(
            lambda v: v.attribute_id.name == MODELO_ATTR
        )[:1]
        return ptav.product_attribute_value_id if ptav else False

    # ── acción principal ─────────────────────────────────────────────────
    def action_confirmar(self):
        self.ensure_one()
        nuevo = (self.modelo_nuevo or "").strip()
        if not nuevo:
            raise UserError(_("Ingresá el modelo correcto."))
        if nuevo.upper() in PLACEHOLDERS:
            raise UserError(_("'%s' no es un modelo válido.") % nuevo)

        attr = self._modelo_attribute()
        current_value = self._current_value()
        if not current_value:
            raise UserError(_(
                "El producto no tiene Modelo como atributo de variante."))

        template = self.product_id.product_tmpl_id
        attr_line = template.attribute_line_ids.filtered(
            lambda l: l.attribute_id == attr)[:1]
        if not attr_line:
            raise UserError(_("El producto no tiene línea de atributo Modelo."))

        target = self.env["product.attribute.value"].search([
            ("attribute_id", "=", attr.id), ("name", "=ilike", nuevo),
        ], limit=1)
        n_uses = self.env["product.template.attribute.value"].search_count(
            [("product_attribute_value_id", "=", current_value.id)])

        if (not target or target == current_value) and n_uses == 1:
            # Valor único de este producto -> renombrar (sin regenerar)
            current_value.name = nuevo
            if self.line_id:
                self._refresh_line_name(self.product_id)
            mensaje = _("Modelo renombrado a '%s' (sin regenerar variantes).") % nuevo
        else:
            # Valor compartido o ya existe -> reasignar solo este template
            if not target or target == current_value:
                target = self.env["product.attribute.value"].create({
                    "name": nuevo, "attribute_id": attr.id,
                })
            self._reassign(template, attr_line, current_value, target)
            mensaje = _("Modelo corregido a '%s'.") % nuevo

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success", "title": _("Modelo corregido"),
                "message": mensaje, "next": {"type": "ir.actions.act_window_close"},
            },
        }

    # ── reasignación (regenera la variante y, si hay línea, la reapunta) ──
    def _reassign(self, template, attr_line, old_value, target_value):
        otros = self.product_id.product_template_variant_value_ids.filtered(
            lambda v: v.attribute_id.name != MODELO_ATTR
        ).mapped("product_attribute_value_id")

        nuevos_valores = (attr_line.value_ids - old_value) | target_value
        attr_line.value_ids = [(6, 0, nuevos_valores.ids)]
        template.invalidate_recordset()

        objetivo_ids = set(otros.ids) | {target_value.id}
        nueva_variante = template.product_variant_ids.filtered(
            lambda p: set(
                p.product_template_variant_value_ids
                .mapped("product_attribute_value_id").ids
            ) == objetivo_ids
        )[:1]
        if not nueva_variante:
            raise UserError(_(
                "No se pudo ubicar la variante con el modelo nuevo. "
                "Revisá el producto manualmente."))

        if self.line_id:
            # Reapuntar la línea preservando precio y cantidad (write directo).
            price = self.line_id.price_unit
            qty = self.line_id.product_uom_qty
            self.line_id.write({"product_id": nueva_variante.id})
            self._refresh_line_name(nueva_variante)
            self.line_id.write({"price_unit": price, "product_uom_qty": qty})

    def _refresh_line_name(self, variant):
        desc = variant.get_product_multiline_description_sale() or variant.display_name
        self.line_id.write({"name": desc})
