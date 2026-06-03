# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # True si el usuario actual es gerente de ventas. Solo gerencia puede editar
    # la "Fecha de la orden" (date_order) en borrador para backdatear el
    # presupuesto; al vendedor le aparece readonly. El candado de confirmación
    # con fecha pasada vive además en action_confirm().
    is_sale_manager = fields.Boolean(
        compute="_compute_is_sale_manager", string="Es gerente de ventas")

    @api.depends_context("uid")
    def _compute_is_sale_manager(self):
        is_manager = self.env.user.has_group("sale.group_sale_manager")
        for order in self:
            order.is_sale_manager = is_manager

    def action_confirm(self):
        """Permite confirmar con fecha anterior a hoy SOLO a gerentes y conserva
        esa fecha. El nativo, al confirmar, pisa ``date_order`` con la fecha del
        día (``_prepare_confirmation_values``); por eso, tras el ``super()``, le
        restauramos la fecha original que el gerente cargó en el borrador.
        """
        today = fields.Date.today()
        is_manager = self.env.user.has_group("sale.group_sale_manager")
        for order in self:
            if order.date_order and order.date_order.date() < today:
                if not is_manager:
                    raise UserError(_(
                        "Solo los gerentes pueden confirmar cotizaciones con "
                        "fecha anterior a hoy. Comunicate con la gerencia para "
                        "autorizar."
                    ))
        past_dates = {
            o.id: o.date_order
            for o in self
            if o.date_order and o.date_order.date() < today
        }
        result = super().action_confirm()
        if past_dates and is_manager:
            for order in self.filtered(lambda o: o.id in past_dates):
                if order.date_order != past_dates[order.id]:
                    order.write({"date_order": past_dates[order.id]})
        return result
