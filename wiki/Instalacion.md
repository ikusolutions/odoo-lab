# Instalacion

## Requisitos previos

- **Python** >= 3.10
- **git**
- **Docker** + Docker Compose v2
- **[uv](https://github.com/astral-sh/uv)** (se instala automaticamente si no existe)

## 1. Instalar uv

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 2. Instalar oolab

```bash
uv tool install odoo-lab --python 3.11
```

O con pipx:

```bash
pipx install odoo-lab
```

## 3. Agregar al PATH (si es necesario)

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

**Windows:** uv agrega automaticamente al PATH. Si no funciona, agrega `%USERPROFILE%\.local\bin` a las variables de entorno del sistema.

## 4. Verificar

```bash
oolab -v
```

Deberia mostrar el banner con la version y la info de IKU Solutions.

## Actualizar

```bash
uv tool upgrade odoo-lab
```

## Instalar desde codigo fuente (desarrollo)

```bash
git clone https://github.com/ikusolutions/odoo-lab.git
cd odoo-lab
uv tool install -e . --python 3.11
```
