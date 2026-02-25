# Resumen de cambios en scripts de migración V14 → V19

## Contexto

Se migra una instancia de Odoo de **V14 a V19**. En V14, el repositorio OCA/commission
contenía un único módulo `sale_commission` con toda la funcionalidad. En V19 se divide
en tres módulos con nombres diferentes:

| V14 | V19 |
|-----|-----|
| `sale_commission` | `commission_oca` + `account_commission_oca` + `sale_commission_oca` |

Además, Odoo 19 Enterprise introduce un módulo oficial `sale_commission` con modelos
diferentes (`sale.commission.plan`, `sale.commission.achievement`), por lo que los
módulos OCA llevan el sufijo `_oca` para evitar conflictos.

---

## Problema original

Los scripts de migración ubicados en `migrations/` **solo se ejecutan durante UPGRADES**
(cuando el módulo ya estaba instalado y se actualiza a una versión mayor). Al pasar de
V14 a V19, los tres módulos V19 son **instalaciones nuevas** (no existían en V14), por
lo que Odoo los trata como `install`, no `upgrade`, y **los scripts de migración nunca
se ejecutaban**.

## Solución implementada

Se crearon `pre_init_hook` en cada módulo. Los hooks se ejecutan **siempre** (tanto en
instalación como en upgrade) y son el punto de entrada correcto para migraciones
cross-version.

---

## Cambios por módulo

### 1. `commission_oca`

#### Archivos nuevos
- **`hooks.py`** — `pre_init_hook` principal que maneja:
  - **Migración V14:** Detecta `sale_commission` instalado y ejecuta:
    - Renombrado de 6 modelos concretos (con tabla) y 4 abstractos/transitorios
    - Renombrado de tablas correspondientes
    - Renombrado de campo `res.partner.agent_ids` → `commission_agent_ids`
    - Limpieza del módulo viejo `sale_commission` en `ir_module_module`
  - **Migración V16-V18:** Detecta `commission` instalado y mueve XML IDs a `commission_oca`
  - Usa `odoo-upgrade-util` cuando está disponible, con fallback a SQL directo

#### Archivos modificados
- **`__manifest__.py`** — Se agregó `"pre_init_hook": "pre_init_hook"`
- **`__init__.py`** — Se agregó `from .hooks import pre_init_hook`

#### Scripts de migración (intra-V19)
Estos scripts manejan upgrades **dentro** de V19 (ej: `19.0.1.x.x` → `19.0.2.0.0`):

| Archivo anterior | Archivo nuevo | Cambio |
|---|---|---|
| `pre-migrate.py` (con lógica de rename_module) | `pre-migrate.py` | Simplificado: solo rename de campo `agent_ids` → `commission_agent_ids` |
| `post-migration.py` | `post-migrate.py` | Renombrado (nombre correcto Odoo) y simplificado |
| `end-cleanup.py` | `end-migrate.py` | Renombrado (nombre correcto Odoo) y simplificado |

---

### 2. `account_commission_oca`

#### Archivos nuevos
- **`hooks.py`** — `pre_init_hook` que detecta `account_commission` instalado (V16-V18)
  y mueve XML IDs y dependencias a `account_commission_oca`

#### Archivos modificados
- **`__manifest__.py`** — Se agregó `"pre_init_hook": "pre_init_hook"`
- **`__init__.py`** — Se agregó `from .hooks import pre_init_hook`

#### Scripts de migración
| Archivo anterior | Archivo nuevo |
|---|---|
| `pre-migration.py` | `pre-migrate.py` |
| `post-migration.py` | `post-migrate.py` |

---

### 3. `sale_commission_oca`

#### Archivos nuevos
- **`hooks.py`** — `pre_init_hook` que:
  - Detecta `sale_commission` OCA instalado (V16-V18) y renombra a `sale_commission_oca`
  - Verifica posibles conflictos con el módulo Enterprise `sale_commission`

#### Archivos modificados
- **`__manifest__.py`** — Se agregó `"pre_init_hook": "pre_init_hook"`
- **`__init__.py`** — Se agregó `from .hooks import pre_init_hook`

#### Scripts de migración
| Archivo anterior | Archivo nuevo |
|---|---|
| `pre-migration.py` | `pre-migrate.py` |
| `post-migration.py` | `post-migrate.py` |

---

## Mapeo completo de modelos V14 → V19

| Modelo V14 | Modelo V19 | Tabla V14 | Tabla V19 | Módulo V19 |
|---|---|---|---|---|
| `sale.commission` | `commission` | `sale_commission` | `commission` | `commission_oca` |
| `sale.commission.section` | `commission.section` | `sale_commission_section` | `commission_section` | `commission_oca` |
| `sale.commission.settlement` | `commission.settlement` | `sale_commission_settlement` | `commission_settlement` | `commission_oca` |
| `sale.commission.settlement.line` | `commission.settlement.line` | `sale_commission_settlement_line` | `commission_settlement_line` | `commission_oca` |
| `sale.commission.mixin` | `commission.mixin` | *(abstracto)* | *(abstracto)* | `commission_oca` |
| `sale.commission.line.mixin` | `commission.line.mixin` | *(abstracto)* | *(abstracto)* | `commission_oca` |
| `sale.commission.make.settle` | `commission.make.settle` | *(transient)* | *(transient)* | `commission_oca` |
| `sale.commission.make.invoice` | `commission.make.invoice` | *(transient)* | *(transient)* | `account_commission_oca` |
| `account.invoice.line.agent` | `account.invoice.line.agent` | *(sin cambio)* | *(sin cambio)* | `account_commission_oca` |
| `sale.order.line.agent` | `sale.order.line.agent` | *(sin cambio)* | *(sin cambio)* | `sale_commission_oca` |

## Campo renombrado

| Modelo | Campo V14 | Campo V19 |
|---|---|---|
| `res.partner` | `agent_ids` | `commission_agent_ids` |

---

## Corrección de nombres de archivos

Odoo reconoce **exclusivamente** estos nombres para scripts de migración:
- `pre-migrate.py` (antes de cargar el módulo)
- `post-migrate.py` (después de cargar el módulo y sus dependencias)
- `end-migrate.py` (después de cargar **todos** los módulos)

Los nombres anteriores (`pre-migration.py`, `post-migration.py`, `end-cleanup.py`)
**no son reconocidos** por el framework de upgrade de Odoo y por lo tanto nunca se
ejecutaban.

---

## Orden de ejecución en la migración

```
1. commission_oca pre_init_hook
   ├── Detecta sale_commission (V14) → renombra modelos, tablas, campos
   └── Detecta commission (V16-V18) → mueve XML IDs
2. commission_oca se instala (ORM crea/verifica tablas)
3. account_commission_oca pre_init_hook
   └── Detecta account_commission (V16-V18) → mueve XML IDs
4. account_commission_oca se instala
5. sale_commission_oca pre_init_hook
   └── Detecta sale_commission (V16-V18) → mueve XML IDs, verifica Enterprise
6. sale_commission_oca se instala
```

## Comando de instalación recomendado

```bash
# Con upgrade-util (recomendado para migración robusta)
pip install odoo_upgrade@git+https://github.com/odoo/upgrade-util@master

# Instalar los módulos
odoo-bin -d DATABASE \
  -i commission_oca,account_commission_oca,sale_commission_oca \
  --upgrade-path=/path/to/upgrade-util/src \
  --stop-after-init
```

## Referencias

- [Odoo Upgrade Scripts](https://www.odoo.com/documentation/19.0/developer/reference/upgrades/upgrade_scripts.html)
- [Odoo Upgrade Utils](https://www.odoo.com/documentation/19.0/developer/reference/upgrades/upgrade_utils.html)
- [OCA/commission V14](https://github.com/OCA/commission/tree/14.0)
- [OCA/commission V19](https://github.com/OCA/commission/tree/19.0)
