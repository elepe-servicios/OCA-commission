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

Se implementó una **estrategia de dos piezas**:

1. **Módulo puente `sale_commission/`**: Un módulo "bridge" con el nombre viejo que Odoo
   V19 puede encontrar en el addons path. Cuando se ejecuta `-u all`, Odoo ve que
   `sale_commission` está instalado en la BD (V14) y existe en el addons path (bridge,
   versión 19.0.14.99.0), así que lo marca para upgrade. Sus dependencias (`commission_oca`,
   `account_commission_oca`, `sale_commission_oca`) causan la **instalación** de los tres
   módulos V19.

2. **`pre_init_hook` en cada módulo V19**: Los hooks se ejecutan ANTES de que el ORM cargue
   las tablas, renombrando tablas, modelos y campos para que el ORM encuentre los datos
   existentes.

### Flujo de `-u all` (V14 → V19)

```
1. Odoo detecta sale_commission instalado (V14) → bridge en addons → marca to upgrade
2. Resuelve dependencias: commission_oca, account_commission_oca, sale_commission_oca
3. commission_oca se INSTALA:
   ├── pre_init_hook detecta sale_commission + tabla sale_commission existe → V14!
   ├── Renombra tablas: sale_commission → commission, etc.
   ├── Renombra modelos en metadatos
   ├── Renombra campo agent_ids → commission_agent_ids
   ├── Limpia XML IDs técnicos, mueve datos a commission_oca
   └── NO marca sale_commission como uninstalled (bridge aún procesando)
4. account_commission_oca se INSTALA:
   └── pre_init_hook → no detecta account_commission en V14 → no-op
5. sale_commission_oca se INSTALA:
   ├── pre_init_hook detecta sale_commission en 'to upgrade' (bridge)
   └── Solo mueve XML IDs residuales, no marca como uninstalled
6. sale_commission (bridge) se ACTUALIZA:
   └── post-migrate.py → limpieza final de XML IDs huérfanos
```

---

## Cambios por módulo

### 0. `sale_commission` (módulo puente/bridge)

#### Archivos nuevos
- **`__manifest__.py`** — Versión `19.0.14.99.0`, depende de los 3 módulos V19
- **`__init__.py`** — Vacío (no tiene código Python)
- **`migrations/19.0.14.99.0/post-migrate.py`** — Limpieza final de XML IDs huérfanos

> **IMPORTANTE:** Este módulo existe SOLO para la migración. Después de migrar,
> puede desinstalarse. Si se usa Odoo Enterprise (que tiene su propio `sale_commission`),
> eliminar el directorio `sale_commission/` del addons path.

---

### 1. `commission_oca`

#### Archivos nuevos
- **`hooks.py`** — `pre_init_hook` principal que maneja:
  - **Migración V14:** Detecta `sale_commission` instalado **Y** tabla `sale_commission` existe:
    - Renombrado de 6 modelos concretos (con tabla) y 4 abstractos/transitorios
    - Renombrado de tablas correspondientes
    - Renombrado de campo `res.partner.agent_ids` → `commission_agent_ids`
    - Limpia XML IDs técnicos, mueve datos a `commission_oca`
    - **NO** marca `sale_commission` como uninstalled (el bridge lo maneja)
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
1. Odoo detecta sale_commission (instalado V14) + bridge (addons V19) → to upgrade
2. Resuelve deps del bridge → commission_oca, account_commission_oca, sale_commission_oca
3. commission_oca pre_init_hook
   ├── Detecta sale_commission + tabla sale_commission → V14 migration!
   ├── Renombra modelos, tablas, campos
   ├── Limpia XML IDs técnicos, mueve datos
   └── NO marca sale_commission como uninstalled
4. commission_oca se instala (ORM encuentra tablas renombradas)
5. account_commission_oca pre_init_hook
   └── Detecta account_commission (V16-V18) → mueve XML IDs (no-op en V14)
6. account_commission_oca se instala
7. sale_commission_oca pre_init_hook
   └── Detecta sale_commission en 'to upgrade' → solo mueve XML IDs residuales
8. sale_commission_oca se instala
9. sale_commission (bridge) post-migrate.py
   └── Limpieza final de XML IDs huérfanos
```

## Comando de migración recomendado

```bash
# Asegurar que el directorio sale_commission/ (bridge) está en el addons path
# junto con commission_oca/, account_commission_oca/, sale_commission_oca/

# (Opcional) Instalar upgrade-util para migración más robusta
pip install odoo_upgrade@git+https://github.com/odoo/upgrade-util@master

# Ejecutar update all — el bridge se encarga de todo
odoo-bin -d DATABASE -u all --stop-after-init

# Si se usa Odoo Enterprise, después de migrar:
# 1. Desinstalar el bridge: sale_commission
# 2. Eliminar sale_commission/ del addons path
# 3. El módulo Enterprise sale_commission ya puede usarse
```

## Referencias

- [Odoo Upgrade Scripts](https://www.odoo.com/documentation/19.0/developer/reference/upgrades/upgrade_scripts.html)
- [Odoo Upgrade Utils](https://www.odoo.com/documentation/19.0/developer/reference/upgrades/upgrade_utils.html)
- [OCA/commission V14](https://github.com/OCA/commission/tree/14.0)
- [OCA/commission V19](https://github.com/OCA/commission/tree/19.0)
