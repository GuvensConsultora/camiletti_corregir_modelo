from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Nombre del atributo que representa el modelo de la cubierta.
MODELO_ATTR = "Modelo"

# Valores que consideramos "modelo no cargado" (placeholders de migración).
PLACEHOLDERS = {"SIN", "S/M", "ALL", "SIN MODELO", "S/MODELO", "N/A", "-", ""}


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Campo computado NO almacenado: solo controla la visibilidad del botón,
    # no agrega columna real en la tabla nativa (C.2).
    can_fix_model = fields.Boolean(
        string="Modelo corregible",
        compute="_compute_can_fix_model",
    )

    def _get_modelo_ptav(self):
        """product.template.attribute.value de Modelo de la variante de la
        línea (o recordset vacío si el producto no tiene Modelo como variante)."""
        self.ensure_one()
        if not self.product_id:
            return self.env["product.template.attribute.value"]
        return self.product_id.product_template_variant_value_ids.filtered(
            lambda v: v.attribute_id.name == MODELO_ATTR
        )[:1]

    @api.depends("product_id")
    def _compute_can_fix_model(self):
        for line in self:
            ptav = line._get_modelo_ptav()
            name = (ptav.name or "").strip().upper() if ptav else ""
            line.can_fix_model = bool(ptav) and name in PLACEHOLDERS

    def action_corregir_modelo(self):
        """Abre el wizard para corregir el valor de Modelo de esta línea."""
        self.ensure_one()
        ptav = self._get_modelo_ptav()
        if not ptav:
            raise UserError(_(
                "Este producto no usa 'Modelo' como atributo de variante; "
                "no se puede corregir el modelo desde la línea."
            ))
        return {
            "type": "ir.actions.act_window",
            "name": _("Corregir modelo"),
            "res_model": "camiletti.corregir.modelo",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_line_id": self.id,
                "default_product_id": self.product_id.id,
                "default_modelo_actual": ptav.name,
            },
        }
