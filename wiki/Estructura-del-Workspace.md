# Estructura del Workspace

## Directorios

```
odoo-launchpad/
├── odoo/                  # Framework Odoo Community (compartido)
├── enterprise/            # Addons Enterprise (opcional, compartido)
├── tenants/               # Proyectos de clientes
│   ├── cliente-a/         # Cada tenant es un repo git independiente
│   └── cliente-b/
├── config/
│   └── odoo/odoo.conf     # Configuracion central de Odoo
├── docker/
│   └── docker-compose.yaml # PostgreSQL + Nginx
├── .vscode/
│   ├── launch.json         # Configs de debug (una por proyecto + utilidades)
│   ├── settings.json       # Python paths, venv
│   ├── tasks.json          # docker-compose-up (preLaunchTask)
│   └── extensions.json     # Extensiones recomendadas
├── .venv-v19/             # Entorno virtual para Odoo 19 (Python 3.11)
├── .venv-v18/             # Entorno virtual para Odoo 18 (si se usa)
├── .env                    # Variables de entorno
├── oolab.yaml              # Fuente de verdad del workspace
└── README.md               # Documentacion generada
```

## odoo/

Framework Odoo Community. Se clona una sola vez y se comparte entre todos los proyectos. Cuando agregas un proyecto de una version diferente, `oolab` hace checkout al branch correcto.

## enterprise/

Addons Enterprise de Odoo. Solo se crea si algun proyecto lo necesita. Puede venir de:
- **Git**: clonado del repo privado de Odoo (necesitas acceso)
- **Local**: copiado desde un directorio en tu maquina

## tenants/

Cada subdirectorio es un proyecto de cliente. Puede ser:
- Un **repo git clonado** con los addons del cliente
- Un **proyecto nuevo** con scaffold OCA (pre-commit, ruff, pylint, etc.)

Cada tenant tiene su propia config de debug en `launch.json` con su `db-filter` y `addons-path`.

## oolab.yaml

Fuente de verdad del workspace. Contiene:
- Version de Odoo y Python
- Configuracion de Enterprise (enabled, source, url)
- Lista de tenants con nombre, branch, db-filter, y si es enterprise
- Configuracion de Docker (PostgreSQL, Nginx)

**Nunca edites los archivos generados directamente.** Edita `oolab.yaml` y ejecuta `oolab generate`.

## .venv-vXX/

Entornos virtuales por version de Odoo. Se crean automaticamente:
- `.venv-v19` para Odoo 19 (Python 3.11)
- `.venv-v18` para Odoo 18 (Python 3.11)
- `.venv-v17` para Odoo 17 (Python 3.10)
- `.venv-v16` para Odoo 16 (Python 3.10)

## launch.json

Configuraciones de debug generadas automaticamente:

| Config | Descripcion |
|--------|-------------|
| **Odoo - Community** | Arranca Odoo base sin tenants |
| **{Nombre Proyecto}** | Arranca con addons del proyecto (+ Enterprise si aplica) |
| **Odoo - Shell** | Consola interactiva |
| **Odoo - Update module** | Actualiza un modulo (`-u module_name`) |
| **Odoo - Install module** | Instala un modulo (`-i module_name`) |

Cada config incluye `"python"` apuntando al venv correcto, `preLaunchTask` que levanta Docker, y `--dev=reload` para hot-reload.
