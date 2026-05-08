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

## oolab module-install

Instala uno o mas modulos en una base de datos.

```bash
oolab module-install acme-testdb sale,purchase,stock
oolab module-install -d acme-testdb -m sale
oolab module-install -d acme-testdb -m sale -t 3600
```

Opciones: `-d/--db`, `-m/--modules`, `-t/--timeout` (default 1800s).

- Resuelve venv, addons-path y odoo.conf automaticamente desde `oolab.yaml`
- Matchea el tenant por `db_filter` o `name` para elegir el venv correcto
- Valida que los modulos existan en el addons-path antes de invocar Odoo
- Usa `--stop-after-init` y `--no-http` (no levanta servidor web)
- Stream de logs en tiempo real

## oolab module-update

Actualiza uno o mas modulos. Acepta `all` para actualizar todos.

```bash
oolab module-update acme-testdb sale
oolab module-update -d acme-testdb -m sale,purchase
oolab module-update acme-testdb all
```

Opciones: `-d/--db`, `-m/--modules`, `-t/--timeout`. Mismo flujo que
`module-install` pero con `-u` en odoo-bin. `all` omite la validacion previa
de modulos.

## oolab open-shell

Abre una shell ORM interactiva contra una base de datos.

```bash
oolab open-shell acme-testdb
oolab open-shell -d acme-testdb
```

Opciones: `-d/--db`.

- Sesion interactiva con `env`, `self.env`, etc.
- Misma resolucion de venv y addons-path que el resto de comandos
- `Ctrl+D` o `exit()` para salir

## oolab reset-pwd

Resetea la contrasena del usuario admin (`base.user_admin`).

```bash
oolab reset-pwd acme-testdb nuevoPass
oolab reset-pwd -d acme-testdb -p nuevoPass
oolab reset-pwd -d acme-testdb -p nuevoPass -l nuevo_login
```

Opciones: `-d/--db`, `-p/--password`, `-l/--login` (default `admin`).

- Conecta via Odoo shell y ejecuta `user.write({...})`
- Soporta cambiar tambien el login

## Opciones globales

```bash
oolab -v       # Version con banner
oolab -h       # Ayuda
```
