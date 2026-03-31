# FAQ

## Puedo tener proyectos de diferentes versiones de Odoo?

Si. Cada proyecto puede ser de una version diferente. Al hacer `oolab add`, se te pregunta la version. Si es diferente a la actual:
- `odoo/` se cambia al branch correcto
- Se crea un venv nuevo (`.venv-vXX`) si no existe
- Se instalan los requirements de esa version

## Que es el db-filter?

Es el nombre de la base de datos que Odoo filtra al arrancar. Cada proyecto tiene su propio `db-filter` (por defecto, el slug del nombre). Cuando Odoo arranca con `--db-filter=mi-proyecto`, solo muestra/usa bases de datos que coincidan con ese filtro.

Crea la base de datos desde: `http://localhost:8069/web/database/manager`

## Puedo editar oolab.yaml manualmente?

Si, pero despues ejecuta `oolab generate` para regenerar todos los archivos de configuracion.

## Que pasa si borro un archivo generado?

Ejecuta `oolab generate` y se regenera todo desde `oolab.yaml`.

## Como actualizo Odoo a una nueva version?

Cambia la version en `oolab.yaml` y ejecuta `oolab generate`. Luego haz `git checkout XX.0` en `odoo/` y `enterprise/` manualmente, o agrega un nuevo proyecto con la version deseada usando `oolab add`.

## Funciona en Windows?

Si. Todos los comandos funcionan en macOS, Linux y Windows. Las instrucciones de activar el venv varian:
- **macOS/Linux**: `source .venv-v19/bin/activate`
- **Windows PowerShell**: `.venv-v19\Scripts\Activate.ps1`
- **Windows CMD**: `.venv-v19\Scripts\activate.bat`

## El venv se crea con conda?

No. Se usa venv estandar de Python + uv como gestor de paquetes. No se requiere conda.

## Necesito Docker?

Si, para PostgreSQL y Nginx. Docker Compose v2 se usa para levantar los servicios. Se inician automaticamente al hacer debug en VSCode (preLaunchTask).

## Puedo usar otro IDE que no sea VSCode?

Actualmente solo se generan configuraciones para VSCode. Soporte para PyCharm/IntelliJ esta en el roadmap.

## Donde se guardan los datos de Odoo?

En `odoo-data/` dentro del workspace. Este directorio no se versiona.
