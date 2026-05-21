{
    "name": "Corregir Modelo desde Presupuesto",
    "version": "19.0.2.0.0",
    "summary": "Ítem 'Corregir modelo' en la tarjeta del catálogo del "
               "presupuesto para corregir el valor de Modelo de una cubierta, "
               "sin romper variantes.",
    "description": """
Corregir Modelo desde el Catálogo del Presupuesto
=================================================

Agrega un ítem "Corregir modelo" en el menú de la tarjeta del catálogo del
presupuesto (vista kanban de product.product) para completar/corregir el valor
del atributo *Modelo* de una cubierta que quedó con un placeholder
('SIN', 'S/M', 'All') desde la migración.

El wizard decide solo el camino que no rompe nada:
- Si el valor de Modelo lo usa SOLO ese producto -> renombra el
  product.attribute.value (no regenera variantes).
- Si el valor está compartido -> crea/usa un valor propio, reapunta la línea de
  atributo de ese template y reapunta la línea del presupuesto a la variante
  resultante.

Solo opera sobre el atributo Modelo; no toca Marca ni Medida.
""",
    "author": "Yagüven C.G.",
    "website": "https://yaguven.com",
    "category": "Sales",
    "license": "LGPL-3",
    "depends": ["sale_management"],
    "data": [
        "wizards/corregir_modelo_views.xml",
        "views/product_catalog_views.xml",
    ],
    "installable": True,
    "application": False,
}
