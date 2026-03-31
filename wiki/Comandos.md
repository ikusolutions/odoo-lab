# Comandos

## oolab init

Crea un nuevo workspace `odoo-launchpad/` en el directorio actual.

```bash
oolab init
```

- Wizard interactivo paso a paso
- Clona Odoo Community
- Configura Enterprise si se elige
- Crea el primer proyecto (opcional)
- Genera todas las configuraciones (VSCode, Docker, Odoo)
- Crea el entorno virtual e instala dependencias
- Valida que no estes dentro de un workspace existente

## oolab add

Agrega un nuevo proyecto/tenant al workspace.

```bash
oolab add                          # Modo interactivo
oolab add --url git@... --new      # Modo directo
```

Flujo interactivo:
1. Nombre del proyecto → genera slug automaticamente
2. Version de Odoo (puede ser diferente al workspace)
3. Enterprise si/no
4. Clonar repo existente o crear vacio (con scaffold OCA)

Si la version elegida es diferente:
- Hace checkout del branch correcto en `odoo/`
- Hace checkout en `enterprise/` si es git
- Crea nuevo venv (`.venv-vXX`) si no existe
- Instala requirements del branch correcto

## oolab remove

Elimina un proyecto del workspace.

```bash
oolab remove mi-cliente
```

- Pregunta si quieres borrar los archivos del directorio
- Actualiza `oolab.yaml`
- Regenera configuraciones

## oolab list

Lista todos los proyectos configurados.

```bash
oolab list
```

Muestra: nombre, display name, branch, db-filter, estado (clonado/faltante).

## oolab generate

Regenera todos los archivos de configuracion desde `oolab.yaml`.

```bash
oolab generate
```

Util despues de editar `oolab.yaml` manualmente. Regenera:
- `.vscode/launch.json`, `settings.json`, `tasks.json`, `extensions.json`
- `config/odoo/odoo.conf`
- `docker/docker-compose.yaml`
- `config/nginx/nginx.conf`
- `.env`
- `README.md`

## oolab doctor

Verifica dependencias del sistema.

```bash
oolab doctor
```

Comprueba: git, docker, docker compose v2, uv, python3.
Si uv no esta instalado, ofrece instalarlo automaticamente.

## Opciones globales

```bash
oolab -v       # Version con banner
oolab -h       # Ayuda
```
