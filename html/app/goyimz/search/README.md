# Gooyims Search Engine — Motor de búsqueda sobre SpiderBot DB

## Estructura de archivos

```
/tu-web/
├── index.php           ← portada Gooyims (tu archivo original)
├── search.php          ← página de resultados (ESTE PROYECTO)
├── search.db           ← copia aquí la BD de SpiderBot (rename de spiderbot.db)
├── lib/
│   ├── Database.php    ← capa de acceso a SQLite
│   ├── SearchModel.php ← toda la lógica de queries
│   └── ViewHelpers.php ← funciones de renderizado HTML
├── views/
│   └── detail.php      ← vista de detalle de un escaneo
└── api/
    └── search.php      ← endpoint JSON (para AJAX / integraciones)
```

## Instalación

1. **Copia** todos estos archivos a tu directorio web.
2. **Copia** tu `spiderbot.db` como `search.db` en la raíz del directorio.
3. **Verifica** permisos de lectura sobre `search.db` (PHP necesita leerlo).
4. Listo — abre `search.php?q=google.com` en el navegador.

## Requisitos

- PHP 8.1+ con extensión `pdo_sqlite` habilitada
- SQLite 3
- `search.db` generado por SpiderBot v2.0

## Uso del API JSON

```bash
# Búsqueda
GET /api/search.php?q=apache&tab=web&page=1&per_page=10

# Estadísticas del índice
GET /api/search.php?action=stats

# Detalle de un scan
GET /api/search.php?action=detail&id=42
```

### Tabs disponibles

| Tab     | Descripción                          |
|---------|--------------------------------------|
| `web`   | Scans + contenido HTTP (por defecto) |
| `ports` | Puertos abiertos                     |
| `links` | URLs descubiertas por el bot         |
| `live`  | Más recientes, en tiempo real        |

### Filtros

- `only_http=1` → solo resultados con HTTP activo
- `port=80`     → filtrar por puerto específico

## Esquema DB (SpiderBot v2.0)

```sql
scans  (id, ip, domain, thread_id, scan_time)
ports  (id, scan_id, port, protocol, service, is_http, html_content)
links  (id, scan_id, port_id, url, link_type)
```

## Escalado / multi-diseño

- Para añadir un nuevo tema visual: duplica la sección de estilos en `search.php`
  y actívalo con un parámetro `?theme=dark` (lógica de router ya prevista).
- Para añadir nuevas fuentes de datos: crea un método en `SearchModel.php`
  y un nuevo `case` en `SearchModel::search()`.
- El endpoint `/api/search.php` es agnóstico al frontend: puedes conectar
  React, Vue o cualquier SPA sin tocar el backend.
