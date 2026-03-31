# Contribuir

Las contribuciones son bienvenidas! `odoo-lab` es un proyecto open source mantenido por [IKU Solutions SAS](https://www.iku.solutions).

## Como contribuir

1. **Fork** el repositorio en GitHub
2. Clona tu fork:
   ```bash
   git clone https://github.com/TU-USUARIO/odoo-lab.git
   cd odoo-lab
   ```
3. Instala en modo desarrollo:
   ```bash
   uv tool install -e . --python 3.11
   ```
4. Crea un branch:
   ```bash
   git checkout -b feature/mi-feature
   ```
5. Haz tus cambios y commitea:
   ```bash
   git commit -m "feat: descripcion del cambio"
   ```
6. Push y abre un Pull Request:
   ```bash
   git push origin feature/mi-feature
   ```

## Convenciones

- **Commits**: usa [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.)
- **Python**: Ruff con line-length=88
- **Idioma**: codigo y nombres de variables en ingles, mensajes al usuario en espanol

## Estructura del proyecto

```
odoo-lab/
├── src/oolab/
│   ├── cli.py              # Typer app principal
│   ├── config.py           # Dataclass WorkspaceConfig
│   ├── versions.py         # Mapeo Odoo → Python
│   ├── scaffold.py         # Scaffold OCA para tenants vacios
│   ├── commands/
│   │   ├── init.py         # oolab init
│   │   ├── add.py          # oolab add
│   │   ├── remove.py       # oolab remove
│   │   ├── list.py         # oolab list
│   │   ├── generate.py     # oolab generate
│   │   └── doctor.py       # oolab doctor
│   └── templates/          # Jinja2 templates para archivos generados
├── wiki/                   # Contenido del wiki de GitHub
├── .github/workflows/      # GitHub Actions (CI/CD, PyPI publish)
├── pyproject.toml
├── README.md
└── LICENSE
```

## Reportar issues

Abre un [issue en GitHub](https://github.com/ikusolutions/odoo-lab/issues) con:
- Descripcion del problema o sugerencia
- Pasos para reproducir (si es un bug)
- Version de oolab (`oolab -v`)
- Sistema operativo

## Licencia

Al contribuir, aceptas que tus contribuciones se licencien bajo [LGPL-3.0-or-later](https://www.gnu.org/licenses/lgpl-3.0.html).
