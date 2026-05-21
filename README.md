# Corregir Modelo desde Presupuesto

Módulo Odoo 19 (Yagüven C.G.) para **Camilleti Neumáticos**.

Agrega un ítem **"Corregir modelo"** en el menú de la tarjeta del **catálogo del
presupuesto** (vista kanban de `product.product`) que permite completar/corregir
el valor del atributo **Modelo** de una cubierta que quedó con un placeholder
(`SIN`, `S/M`, `All`) desde la migración, sin salir del flujo de venta.

## Cómo funciona

El ítem aparece solo cuando la cubierta tiene el Modelo en placeholder. El
operador escribe el modelo correcto y el wizard elige solo el camino que no
rompe nada:

- Si el valor de Modelo lo usa **solo ese producto** → **renombra** el
  `product.attribute.value` (no regenera variantes).
- Si el valor está **compartido** (caso `All`) → crea/reusa un valor propio,
  reapunta la línea de atributo de ese template y reapunta la línea del
  presupuesto a la variante resultante, **preservando precio y cantidad**.

Solo opera sobre el atributo *Modelo*; no toca *Marca* ni *Medida*.

## Dependencias

`sale_management`.

## Licencia

LGPL-3.
