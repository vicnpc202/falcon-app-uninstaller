# Recursos gráficos

`recursos.zip` contiene imágenes públicas de familias/productos, iconos genéricos y
los SVG originales de Papirus. La aplicación los extrae localmente al iniciar.
No se descargan iconos desde los equipos ni se incluye un inventario precargado.

- **selfh.st icons**: CC-BY-4.0. Atribución, revisión y enlaces en `FUENTES.json` y `LICENCIA-selfhst.txt`.
- **Simple Icons 13.21.0**: colección CC0-1.0; condiciones de cada marca en `FUENTES-simple-icons.json` y `LICENCIA-simple-icons.txt`.
- **Papirus**: GPL-3.0. Procedencia en `FUENTES-papirus.json` y `FUENTES-categorias.json`; fuentes en `recursos.zip` → `fuentes-papirus/`; licencia y autores en `PAPIRUS-*`.
- **Sitios oficiales**: fuentes en `FUENTES-sitios-*.json`; los archivos no declaran necesariamente una licencia de redistribución. Son marcas de sus titulares y no se relicencian bajo la GPL del código.
- **Fabricantes**: atribuciones en `FUENTES-fabricantes.json`; un icono del fabricante o categoría no es un logo propio del programa.

Las imágenes se han ajustado y centrado a 128, 20 y 42 píxeles (PNG RGBA).
Los nombres, logos y marcas pertenecen a sus respectivos titulares.

`reglas.json` contiene alias genéricos de productos; `fabricantes.json` y
`categorias.json` ofrecen alternativas. Las asociaciones de cada instalación se
generan en `catalogo.json`, que es local y está excluido de Git.
Para un logo propio, coloca un PNG en `personalizados/` con el nombre indicado
por el campo `personalizado` del catálogo local.
