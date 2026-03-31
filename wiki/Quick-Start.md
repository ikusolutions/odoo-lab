# Quick Start

## Crear un workspace

```bash
# Navega a donde quieres crear el workspace
cd ~/Projects

# Ejecuta el wizard interactivo
oolab init
```

El wizard te preguntara:
1. **Version de Odoo** (16, 17, 18, 19)
2. **Enterprise** (si/no — necesitas licencia propia)
3. **Primer proyecto** (nombre, clonar repo o crear vacio)

Al finalizar, crea la carpeta `odoo-launchpad/` con todo configurado.

## Abrir en VSCode

```bash
cd odoo-launchpad
code .
```

## Ejecutar Odoo

1. Presiona **F5** en VSCode (o Run > Start Debugging)
2. Selecciona la configuracion de tu proyecto
3. Odoo estara disponible en `http://localhost:8069`
4. La primera vez, crea una base de datos desde el Database Manager

## Agregar mas proyectos

```bash
oolab add
```

El CLI te pedira nombre, version de Odoo, si es Enterprise, y si quieres clonar un repo o crear un proyecto vacio.

## Ejemplo completo

```
$ oolab init
  Version de Odoo: 19
  Incluir Enterprise? n
  Agregar proyecto? y
  Nombre: Mi Cliente
  → Slug: mi-cliente
  Enterprise? n
  Clonar repo? n
  
  ✓ Workspace creado!

$ cd odoo-launchpad
$ oolab add
  Nombre: Otro Cliente
  Version: 18
  Enterprise? y
  → Enterprise no configurado, clonando...
  Clonar repo? y
  URL: git@github.com:org/otro-cliente.git
  
  ✓ Proyecto agregado!

$ oolab list
  ┌────────────┬─────────┬───────────┐
  │ Nombre     │ Branch  │ Estado    │
  ├────────────┼─────────┼───────────┤
  │ mi-cliente │ 19.0    │ ✓ clonado │
  │ otro-cli.. │ 18.0    │ ✓ clonado │
  └────────────┴─────────┴───────────┘
```
