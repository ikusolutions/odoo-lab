# odoo-lab (oolab)

CLI scaffolder para crear y gestionar workspaces de desarrollo Odoo con soporte multi-proyecto.

Desarrollado por **[IKU Solutions SAS](https://www.iku.solutions)** | Autor: **Yan Chirino** <yan.chirino@iku.solutions>

---

## Contenido

- [[Instalacion]]
- [[Quick Start]]
- [[Comandos]]
- [[Estructura del Workspace]]
- [[Enterprise]]
- [[FAQ]]
- [[Contribuir]]

---

## Que es oolab?

`oolab` es una herramienta de linea de comandos que automatiza la creacion y gestion de entornos de desarrollo Odoo. Permite trabajar con multiples proyectos de clientes simultaneamente, compartiendo un solo framework Odoo (Community + Enterprise opcional), con configuraciones de debug individuales por proyecto.

### Caracteristicas

- **Multi-proyecto** — multiples clientes/tenants en un solo workspace
- **Multi-version** — Odoo 15, 16, 17, 18 y 19 con venvs separados
- **Enterprise ready** — integra Odoo Enterprise (requiere licencia propia)
- **VSCode integrado** — `launch.json` con una entrada de debug por proyecto (F5)
- **Gestion de modulos por CLI** — `module-install`, `module-update` y `open-shell` con barra de progreso parseando logs de `odoo-bin` en vivo
- **Auto-deteccion de addons** — encuentra modulos en `src/`, `vendor/OCA/`, `vendor/Cybrosys/`, etc., sin configuracion manual
- **Entornos aislados** — venvs por version (`.venv-v19`, `.venv-v18`, ...)
- **Scaffold OCA** — estructura de calidad para proyectos nuevos (pre-commit, ruff, pylint)
- **Servicios Docker** — `start`, `stop`, `status`, `logs` con coloreo por nivel
- **Comando repair** — reinstala paquetes core sin reinicializar el workspace
- **Multi-plataforma** — macOS, Linux, Windows
