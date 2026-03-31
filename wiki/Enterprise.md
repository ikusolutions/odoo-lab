# Odoo Enterprise

## Importante

`oolab` **no incluye ni distribuye los modulos Enterprise de Odoo**. Para usarlos necesitas:

- **Suscripcion activa** de [Odoo Enterprise](https://www.odoo.com/pricing) o ser partner autorizado
- **Acceso al repositorio privado** `github.com/odoo/enterprise` (Odoo otorga acceso con la suscripcion)
- **O una copia local** de los modulos Enterprise en tu maquina

Los modulos Enterprise estan protegidos por la licencia Odoo Enterprise Edition. Consulta los [terminos de licencia de Odoo](https://www.odoo.com/legal).

## Como funciona en oolab

Enterprise es **por proyecto**, no global. Un workspace puede tener mezcla de proyectos Community y Enterprise.

### Al crear el workspace (oolab init)

Si eliges "Incluir Enterprise", se te pedira:
- **git**: URL del repo (ej. `git@github.com:odoo/enterprise.git`)
- **local**: path de un directorio donde ya tengas los modulos

### Al agregar un proyecto (oolab add)

Si marcas el proyecto como Enterprise:
1. Si `enterprise/` ya existe, se reutiliza
2. Si no, se te pide configurarlo (git o local)
3. Si es git, se hace checkout al branch correcto para la version del proyecto

### En el launch.json

Los proyectos Enterprise incluyen `enterprise/` en su `--addons-path`. Los proyectos Community no.

```json
// Proyecto Enterprise
"--addons-path=${workspaceFolder}/odoo/addons,${workspaceFolder}/enterprise,${workspaceFolder}/tenants/mi-proyecto"

// Proyecto Community
"--addons-path=${workspaceFolder}/odoo/addons,${workspaceFolder}/tenants/mi-proyecto"
```

## Obtener acceso al repo Enterprise

1. Compra una suscripcion en [odoo.com/pricing](https://www.odoo.com/pricing)
2. Contacta a Odoo para que te den acceso al repo `github.com/odoo/enterprise`
3. Configura tu clave SSH en GitHub para poder clonar

Si eres partner de Odoo, ya deberias tener acceso.
