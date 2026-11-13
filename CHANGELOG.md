# Cambios

## 1.1.0 — 2026-11-13

- Añade **Usar archivo previo (put)** por aplicación y un selector con búsqueda de los archivos ya subidos a Falcon.
- Comprueba el archivo existente o realiza la transferencia; valida SHA256 antes de ejecutar el desinstalador.
- Conserva las etapas y la selección de cada envío al reiniciar, sin modificar órdenes antiguas.
- Recupera sesiones RTR caducadas y vuelve a preparar el destino cuando corresponde.
- Bloquea archivos cambiados, transferencias fallidas y envíos de resultado incierto; mantiene el flujo sin put para scripts que no lo necesitan.
- Documenta el uso y sus límites e incluye la captura de la nueva función.
- Añade pruebas de cola, migración, errores de transferencia y selector de interfaz.

## 1.0.3 — 2026-11-11

- Elimina **Guardar y volver a equipos** del editor para evitar confundir el guardado local con la publicación en Falcon.
- Destaca **Publicar en Falcon** en azul como acción principal y conserva **Elegir script de Falcon…** para reutilizar scripts publicados.
- Aclara que los scripts nuevos o modificados deben publicarse antes de enviarlos desde Equipos.

## 1.0.2 — 2026-11-11

- Corrige el selector de scripts: los botones **Vincular seleccionado**,
  **Cancelar** y **Actualizar lista** permanecen visibles al redimensionar.
- La tabla ocupa solo el espacio disponible; los textos se ajustan al ancho.
- Permite vincular el script seleccionado con doble clic o la tecla Enter.
- Añade una prueba de interfaz que comprueba visibilidad y vínculo con distintas
  escalas de texto y tamaños de ventana, sin ejecutar órdenes remotas.

## 1.0.1 — 2026-11-11

- Reemplaza **Exportar para Falcon…** por **Elegir script de Falcon…**.
- Permite buscar y vincular custom scripts existentes a varias fichas de aplicación,
  conservando el vínculo tras reiniciar y verificando plataforma y contenido.
- Elimina vínculos guardados obsoletos al editar el contenido local.

## 1.0.0 — 2026-11-10

Primera distribución pública: inventario por organización, publicación de scripts
RTR, campañas con cola para equipos desconectados, seguimiento persistente,
verificación por inventario, historial CSV y temas claro/oscuro.

Incluye los estados online/offline/unknown, Last seen en hora local, recursos
gráficos genéricos y un modo de ejemplo sin conexión a Falcon. No incluye datos
de ninguna organización.
