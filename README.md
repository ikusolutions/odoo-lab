
```
          ██████   ██████  ██       █████  ██████
         ██    ██ ██    ██ ██      ██   ██ ██   ██
         ██    ██ ██    ██ ██      ███████ ██████
         ██    ██ ██    ██ ██      ██   ██ ██   ██
          ██████   ██████  ███████ ██   ██ ██████
```

# odoo-lab (`oolab`)

**CLI para crear y gestionar workspaces de desarrollo Odoo multi-proyecto y multi-versión.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Odoo 15-19](https://img.shields.io/badge/odoo-15%20|%2016%20|%2017%20|%2018%20|%2019-blueviolet.svg)](https://www.odoo.com/)
[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-green.svg)](https://www.gnu.org/licenses/lgpl-3.0)

> Desarrollado por **[IKU Solutions SAS](https://www.iku.solutions)** | Autor: **Yan Chirino** \<yan.chirino@iku.solutions\>

---

## ¿Qué es oolab?

`oolab` automatiza la creación y gestión de entornos de desarrollo Odoo. Permite trabajar con múltiples proyectos de clientes en un solo workspace, compartiendo el framework Odoo (Community + Enterprise opcional), con configuraciones de debug individuales por proyecto en VSCode.

Resuelve problemas reales del día a día:
- Múltiples clientes con distintas versiones de Odoo (15, 16, 17, 18, 19)
- Proyectos con estructuras de addons no estándar (`vendor/OCA/`, `vendor/Cybrosys/`, `src/`, etc.)
- Incompatibilidades de paquetes Python en macOS arm64 (psycopg2, cryptography, lxml, gevent)
- Configuración manual repetitiva de `launch.json`, `odoo.conf` y `docker-compose`

### Características principales

- **Multi-proyecto**: gestiona múltiples clientes/tenants en un solo workspace
- **Multi-versión**: soporte para Odoo 15, 16, 17, 18 y 19 con venvs separados por versión
- **Enterprise ready**: integra Odoo Enterprise via git o copia local (requiere licencia propia)
- **VSCode integrado**: genera `launch.json` con configs de debug por proyecto (run, shell, install, update)
- **Auto-detección de addons**: escanea la estructura del proyecto y detecta todos los directorios con módulos Odoo automáticamente, sin importar si están en `src/`, `vendor/OCA/`, `vendor/Cybrosys/` u otra estructura
- **Entornos aislados**: venvs por versión de Odoo (`.venv-v15`, `.venv-v19`)
- **Dependencias robustas**: instalación con `uv` + compatibilidad automática con macOS arm64 + fallback paquete por paquete
- **Comando repair**: repara workspaces con paquetes Python rotos sin tener que reinicializar
- **Docker integrado**: comandos `start`, `stop`, `logs` y `status` para gestionar los servicios del workspace
- **Interactivo**: wizard paso a paso con spinners y feedback visual en tiempo real
- **Multi-plataforma**: compatible con macOS, Linux y Windows

---

## Sobre Odoo Enterprise

`oolab` permite configurar proyectos que usan Odoo Enterprise, pero **no incluye ni distribuye los módulos Enterprise**. Para usarlos necesitas:

- **Tener una suscripción activa** de [Odoo Enterprise](https://www.odoo.com/pricing) o ser partner autorizado de Odoo.
- **Acceso al repositorio privado** `github.com/odoo/enterprise` (Odoo otorga acceso con la suscripción), **o bien** tener una copia local de los módulos Enterprise en tu máquina.

> **Importante:** Los módulos Enterprise están protegidos por la licencia Odoo Enterprise Edition. Consulta los [términos de licencia de Odoo](https://www.odoo.com/legal) antes de usarlos.

---

## Instalación

### Requisitos previos

- **Python** >= 3.10
- **git**
- **Docker** + Docker Compose v2
- **[uv](https://github.com/astral-sh/uv)** (se instala automáticamente si no existe)

### Instalar uv (si no lo tienes)

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Instalar oolab

```bash
uv tool install odoo-lab --python 3.11
```

O con pipx:
```bash
pipx install odoo-lab
```

### Instalar desde el código fuente

```bash
git clone https://github.com/ikusolutions/odoo-lab.git
cd odoo-lab
uv tool install -e . --python 3.11
```

### Verificar

```bash
oolab --version
```

---

## Quick Start

```bash
# 1. Navega a donde quieres crear el workspace
cd ~/Projects

# 2. Crea el workspace (wizard interactivo)
oolab init

# 3. Entra al workspace creado
cd odoo-launchpad

# 4. Agrega proyectos de clientes
oolab add

# 5. Levanta los servicios y abre en VSCode
oolab start
code .
# Presiona F5 para debuguear
```

---

## Comandos

### Workspace

| Comando | Descripción |
|---------|-------------|
| `oolab init` | Crea un workspace `odoo-launchpad/` con wizard interactivo: clona Odoo, Enterprise (opcional) y configura el entorno |
| `oolab add [nombre]` | Agrega un proyecto de cliente: clona un repo existente o crea uno nuevo con scaffold OCA |
| `oolab remove <nombre>` | Elimina un proyecto del workspace y lo quita de `oolab.yaml` |
| `oolab list` | Lista los proyectos con su versión de Odoo, branch y estado |
| `oolab generate` | Regenera `odoo.conf`, `docker-compose`, `launch.json` y demás configs desde `oolab.yaml` |
| `oolab repair` | Repara el workspace reinstalando paquetes core (psycopg2, lxml, Pillow) |
| `oolab repair --full` | Repara reinstalando también todos los `requirements.txt` |

### Servicios Docker

| Comando | Descripción |
|---------|-------------|
| `oolab start` | Levanta PostgreSQL y Nginx vía Docker Compose |
| `oolab start --build` | Levanta reconstruyendo imágenes Docker |
| `oolab stop` | Detiene los servicios Docker |
| `oolab status` | Muestra el estado: servicios activos, branches y tenants |
| `oolab logs [servicio]` | Muestra logs de los servicios (`db`, `nginx`) |
| `oolab logs -f` | Sigue los logs en tiempo real |

### Base de datos

| Comando | Descripción |
|---------|-------------|
| `oolab reset-pwd <db> <password>` | Resetea la contraseña del usuario admin en una base de datos local |
| `oolab reset-pwd <db> <password> --login <login>` | Resetea la contraseña del usuario especificado |

### Diagnóstico

| Comando | Descripción |
|---------|-------------|
| `oolab doctor` | Verifica dependencias del sistema (git, Docker, uv, Python) |
| `oolab --version` | Muestra la versión del CLI |
| `oolab --help` | Muestra la ayuda general |
| `oolab <comando> --help` | Muestra la ayuda de un comando específico |

---

## Estructura del workspace

```
odoo-launchpad/
├── odoo/                   # Odoo Community (compartido entre proyectos)
├── enterprise/             # Enterprise addons (opcional, compartido)
├── tenants/
│   ├── cliente-a/          # Proyecto estándar
│   │   └── addons/
│   └── cliente-b/          # Proyecto con estructura vendor
│       ├── src/
│       └── vendor/
│           ├── OCA/
│           └── Cybrosys/
├── config/
│   └── odoo/odoo.conf      # Configuración central de Odoo
├── docker/
│   └── docker-compose.yaml
├── .vscode/
│   ├── launch.json         # Configs de debug: por tenant + Shell + Update + Install
│   ├── settings.json
│   └── tasks.json
├── .venv-v15/              # Venv para Odoo 15 (Python 3.10)
├── .venv-v19/              # Venv para Odoo 19 (Python 3.11)
├── .env
└── oolab.yaml              # Fuente de verdad del workspace
```

### Auto-detección de addons

`oolab` escanea automáticamente la estructura del proyecto para encontrar todos los directorios con módulos Odoo (identificados por `__manifest__.py` o `__openerp__.py`), hasta 3 niveles de profundidad. Esto cubre estructuras como:

```
tenants/proyecto/src/               → detectado
tenants/proyecto/vendor/OCA/        → detectado
tenants/proyecto/vendor/Cybrosys/   → detectado
tenants/proyecto/addons/            → detectado
```

El `launch.json` generado incluye todos los paths detectados automáticamente. Sin configuración manual.

---

## oolab.yaml

Archivo central de configuración del workspace. Se genera en `oolab init` y se actualiza con `oolab add` / `oolab remove`.

```yaml
name: odoo-launchpad
python_version: "3.11"
postgres_version: "16"
postgres_port: 5432
postgres_user: odoo
postgres_password: odoo
enterprise_enabled: false
nginx_enabled: true
nginx_http_port: 80

tenants:
  - name: cliente-a
    display_name: "Cliente A"
    url: git@github.com:org/cliente-a.git
    branch: "19.0"
    db_filter: cliente-a

  - name: assenza
    display_name: "Assenza"
    url: git@github.com:org/assenza.git
    branch: "15.0"
    db_filter: assenza
    enterprise: false
```

---

## Versiones soportadas

| Versión Odoo | Python | PostgreSQL mínimo |
|---|---|---|
| 15 | 3.10 | 14 |
| 16 | 3.10 | 16 |
| 17 | 3.10 | 16 |
| 18 | 3.11 | 16 |
| 19 | 3.11 | 16 |

Cada versión usa un venv separado (`.venv-v15`, `.venv-v16`, etc.). Los proyectos con la misma versión comparten el venv.

---

## Contribuir

Las contribuciones son bienvenidas. Este es un proyecto open source mantenido por [IKU Solutions SAS](https://www.iku.solutions).

1. **Fork** el repositorio
2. Crea tu **branch** (`git checkout -b feature/mi-feature`)
3. **Commit** tus cambios siguiendo [Conventional Commits](https://www.conventionalcommits.org/)
4. Abre un **Pull Request**

Reporta bugs en [issues](https://github.com/ikusolutions/odoo-lab/issues).

---

## Licencia

Este proyecto está licenciado bajo [LGPL-3.0-or-later](https://www.gnu.org/licenses/lgpl-3.0.html).

```
Copyright (c) 2026 IKU Solutions SAS
Autor: Yan Chirino <yan.chirino@iku.solutions>
Website: https://www.iku.solutions
```

---

<p align="center">
  Hecho con <b>Python</b> + <b>Typer</b> + <b>Rich</b> por <a href="https://www.iku.solutions"><b>IKU Solutions</b></a>
</p>
