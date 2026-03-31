
```
          ██████   ██████  ██       █████  ██████
         ██    ██ ██    ██ ██      ██   ██ ██   ██
         ██    ██ ██    ██ ██      ███████ ██████
         ██    ██ ██    ██ ██      ██   ██ ██   ██
          ██████   ██████  ███████ ██   ██ ██████
```

# odoo-lab (`oolab`)

**CLI scaffolder para crear y gestionar workspaces de desarrollo Odoo con soporte multi-proyecto.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Odoo 16-19](https://img.shields.io/badge/odoo-16%20|%2017%20|%2018%20|%2019-blueviolet.svg)](https://www.odoo.com/)
[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-green.svg)](https://www.gnu.org/licenses/lgpl-3.0)

> Desarrollado por **[IKU Solutions SAS](https://www.iku.solutions)** | Autor: **Yan Chirino** \<yan.chirino@iku.solutions\>

---

## Que es oolab?

`oolab` es una herramienta de linea de comandos que automatiza la creacion y gestion de entornos de desarrollo Odoo. Permite trabajar con multiples proyectos de clientes simultaneamente, compartiendo un solo framework Odoo (Community + Enterprise opcional), con configuraciones de debug individuales por proyecto.

### Caracteristicas principales

- **Multi-proyecto**: gestiona multiples clientes/tenants en un solo workspace
- **Multi-version**: soporte para Odoo 16, 17, 18 y 19
- **Enterprise ready**: integra Odoo Enterprise via git o copia local (requiere licencia propia)
- **VSCode integrado**: genera `launch.json` con configs de debug por proyecto (run, shell, install, update)
- **Entornos aislados**: venvs por version de Odoo (`.venv-v19`, `.venv-v18`)
- **Scaffold OCA**: crea proyectos vacios con estructura de calidad (pre-commit, ruff, pylint)
- **Dependencias robustas**: instalacion con uv + fallbacks automaticos
- **Interactivo**: wizard paso a paso con spinners y feedback visual
- **Multi-plataforma**: compatible con macOS, Linux y Windows

---

## Sobre Odoo Enterprise

`oolab` permite configurar proyectos que usan Odoo Enterprise, pero **no incluye ni distribuye los modulos Enterprise**. Para usarlos necesitas:

- **Tener una suscripcion activa** de [Odoo Enterprise](https://www.odoo.com/pricing) o ser partner autorizado de Odoo.
- **Acceso al repositorio privado** `github.com/odoo/enterprise` (Odoo otorga acceso con la suscripcion), **o bien** tener una copia local de los modulos Enterprise en tu maquina.

Al agregar un proyecto Enterprise con `oolab add`, el CLI te preguntara si quieres clonar desde un repositorio git (necesitas acceso SSH/HTTPS al repo de Enterprise) o indicar un directorio local donde ya tengas los modulos.

> **Importante:** Los modulos Enterprise estan protegidos por la licencia Odoo Enterprise Edition. Consulta los [terminos de licencia de Odoo](https://www.odoo.com/legal) antes de usarlos.

---

## Instalacion

### Requisitos previos

- **Python** >= 3.10
- **git**
- **Docker** + Docker Compose v2
- **[uv](https://github.com/astral-sh/uv)** (se instala automaticamente si no existe)

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

### Agregar al PATH (si es necesario)

**macOS / Linux (zsh):**

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**macOS / Linux (bash):**

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):** uv agrega automaticamente al PATH. Si no, agrega `%USERPROFILE%\.local\bin` a las variables de entorno del sistema.

### Instalar desde el codigo fuente (para desarrollo)

Si quieres contribuir o modificar oolab:

```bash
git clone https://github.com/ikusolutions/odoo-lab.git
cd odoo-lab
uv tool install -e . --python 3.11
```

### Verificar

```bash
oolab -v
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

# 5. Abre en VSCode y presiona F5
code .
```

---

## Comandos

| Comando | Descripcion |
|---------|-------------|
| `oolab init` | Crea un nuevo workspace `odoo-launchpad/` con wizard interactivo |
| `oolab add` | Agrega un proyecto de cliente (clona repo o crea con scaffold OCA) |
| `oolab remove <nombre>` | Elimina un proyecto del workspace |
| `oolab list` | Lista todos los proyectos configurados con su estado |
| `oolab generate` | Regenera todos los archivos de configuracion desde `oolab.yaml` |
| `oolab doctor` | Verifica dependencias del sistema (git, docker, uv, python) |
| `oolab -v` | Muestra version e informacion del CLI |
| `oolab -h` | Muestra la ayuda |

---

## Estructura del workspace

```
odoo-launchpad/
├── odoo/                 # Odoo Community (compartido entre proyectos)
├── enterprise/           # Enterprise addons (opcional, compartido)
├── tenants/
│   ├── cliente-a/        # Proyecto de cliente A (repo independiente)
│   └── cliente-b/        # Proyecto de cliente B (repo independiente)
├── config/
│   └── odoo/odoo.conf    # Configuracion central de Odoo
├── docker/
│   └── docker-compose.yaml
├── .vscode/
│   ├── launch.json       # Configs de debug: Community, Shell, Update, Install + tenants
│   ├── settings.json     # Python paths, venv
│   └── tasks.json        # docker-compose-up
├── .venv-v19/            # Entorno virtual (uno por version de Odoo)
├── .env
└── oolab.yaml            # Fuente de verdad del workspace
```

---

## Ejemplo de uso

### Crear workspace con Enterprise y un cliente

```bash
$ cd ~/Projects
$ oolab init

  Odoo Lab v0.1.0  |  IKU Solutions SAS  |  https://www.iku.solutions

  Version de Odoo [16 / 17 / 18 / 19] (19): 19
  Incluir Enterprise? [y/n]: y
  URL del repositorio Enterprise: git@github.com:odoo/enterprise.git
  Agregar un proyecto de cliente ahora? [y/n]: y
  Nombre del proyecto: Mi Cliente ERP
  Clonar desde un repositorio existente? [y/n]: y
  URL del repositorio: git@github.com:org/mi-cliente-erp.git

  ...spinners y progreso...

  Workspace listo!
```

### Agregar otro proyecto despues

```bash
$ cd odoo-launchpad
$ oolab add

  Nombre del proyecto: Otro Cliente
  Version de Odoo [16 / 17 / 18 / 19] (19): 18
  Clonar desde un repositorio existente? [y/n]: n

  Proyecto 'Otro Cliente' agregado correctamente.
```

---

## Contribuir

Las contribuciones son bienvenidas! Este es un proyecto open source mantenido por [IKU Solutions SAS](https://www.iku.solutions).

### Como contribuir

1. **Fork** el repositorio
2. Crea tu **branch** (`git checkout -b feature/mi-feature`)
3. **Commit** tus cambios (`git commit -m 'feat: descripcion'`)
4. **Push** al branch (`git push origin feature/mi-feature`)
5. Abre un **Pull Request**

### Reportar issues

Si encuentras un bug o tienes una sugerencia, abre un [issue](https://github.com/ikusolutions/odoo-lab/issues).

### Guias de desarrollo

- Usa [Conventional Commits](https://www.conventionalcommits.org/) para mensajes de commit
- El codigo sigue las convenciones de [Ruff](https://docs.astral.sh/ruff/) con line-length=88
- Pre-commit hooks recomendados para calidad de codigo

---

## Roadmap

- [ ] Soporte para multiples versiones de Odoo en un mismo workspace
- [ ] Comando `oolab upgrade` para actualizar el framework
- [ ] Comando `oolab db` para gestionar bases de datos
- [ ] Soporte para PyCharm/IntelliJ
- [ ] Publicacion en PyPI

---

## Licencia

Este proyecto esta licenciado bajo [LGPL-3.0-or-later](https://www.gnu.org/licenses/lgpl-3.0.html).

```
Copyright (c) 2026 IKU Solutions SAS
Autor: Yan Chirino <yan.chirino@iku.solutions>
Website: https://www.iku.solutions
```

---

<p align="center">
  Hecho con <b>Python</b> + <b>Typer</b> + <b>Rich</b> por <a href="https://www.iku.solutions"><b>IKU Solutions</b></a>
</p>
