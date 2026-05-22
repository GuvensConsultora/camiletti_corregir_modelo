from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Nombre del atributo que representa el modelo de la cubierta.
MODELO_ATTR = "Modelo"

# Valores que consideramos "modelo no cargado" (placeholders de migración).
PLACEHOLDERS = {"SIN", "S/M", "ALL", "SIN MODELO", "S/MODELO", "N/A", "-", ""}


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Almacenado: la tarjeta del catálogo del presupuesto no trae campos
    # computados no almacenados, así que lo guardamos para que el t-if del
    # ítem "Corregir modelo" pueda evaluarlo.
    can_fix_model = fields.Boolean(
        string="Modelo corregible",
        compute="_compute_can_fix_model",
        store=True,
    )

    def _get_modelo_ptav(self):
        """product.template.attribute.value de Modelo de esta variante
        (recordset vacío si el producto no usa Modelo como variante)."""
        self.ensure_one()
        return self.product_template_variant_value_ids.filtered(
            lambda v: v.attribute_id.name == MODELO_ATTR
        )[:1]

    @api.depends("product_template_variant_value_ids",
                 "product_template_variant_value_ids.name")
    def _compute_can_fix_model(self):
        for product in self:
            ptav = product._get_modelo_ptav()
            name = (ptav.name or "").strip().upper() if ptav else ""
            product.can_fix_model = bool(ptav) and name in PLACEHOLDERS

    def action_corregir_modelo(self):
        """Abre el wizard para corregir el valor de Modelo de este producto
        (desde la tarjeta del catálogo del presupuesto)."""
        self.ensure_one()
        ptav = self._get_modelo_ptav()
        if not ptav:
            raise UserError(_(
                "Este producto no usa 'Modelo' como atributo de variante; "
                "no se puede corregir el modelo desde acá."
            ))
        return {
            "type": "ir.actions.act_window",
            "name": _("Corregir modelo"),
            "res_model": "camiletti.corregir.modelo",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_product_id": self.id,
                "default_modelo_actual": ptav.name,
            },
        }
