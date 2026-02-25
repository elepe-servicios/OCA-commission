# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Migration hooks for commission_oca module.

This is the PRIMARY migration mechanism for V14 → V19.
It runs as ``pre_init_hook`` when commission_oca is installed.

SUPPORTED SCENARIOS:
  1. **Bridge module present** (``-u all`` without Enterprise):
     The ``sale_commission`` bridge module depends on commission_oca, so Odoo
     installs commission_oca FIRST (dependency resolution). This hook renames
     V14 tables/models/fields BEFORE the ORM loads V19 model classes.

  2. **Enterprise captures sale_commission** (Odoo.sh):
     Enterprise's ``sale_commission`` module upgrades instead of the bridge.
     V14 orphan tables (sale_commission, sale_commission_settlement, etc.)
     remain in the database. The user installs commission_oca manually, and
     this hook detects the orphan tables and migrates them.
     IMPORTANT: All cleanup is Enterprise-safe — only V14 model records are
     modified; Enterprise's sale.commission.plan / sale.commission.achievement
     records are never touched.

  3. **No bridge, no Enterprise** (manual install):
     The user installs commission_oca directly. This hook detects V14 tables
     (if present) and performs the migration.

  4. **V16-V18 intermediate** (commission → commission_oca rename):
     Tables already use V19 names but the module is called ``commission``.
     This hook renames module references and field metadata.

  5. **Fresh installation**:
     No migration needed — hook exits immediately.
"""

import logging

_logger = logging.getLogger(__name__)

# ── All V14 model names (after rename) used for Enterprise-safe filtering ────
# These are the V14 OCA models AFTER the rename (sale.commission → commission).
# Enterprise models (sale.commission.plan, sale.commission.achievement) are
# NEVER included, ensuring Enterprise data is untouched.
V14_RENAMED_MODELS = (
    "commission",
    "commission.section",
    "commission.settlement",
    "commission.settlement.line",
    "commission.mixin",
    "commission.line.mixin",
    "commission.make.settle",
    "commission.make.invoice",
)


def pre_init_hook(env):
    """Prepare the database for commission_oca installation.

    This hook runs BEFORE the module's models and data are loaded.
    It renames tables, columns, and model references so that the ORM
    finds existing data when creating V19 models.
    """
    # Use print() for critical messages to ensure visibility regardless
    # of logging configuration
    print("\n>>> commission_oca pre_init_hook: STARTED")
    _logger.info("=" * 70)
    _logger.info("commission_oca: pre_init_hook starting")
    _logger.info("=" * 70)

    cr = env.cr

    # Check database state
    v14_table_exists = _table_exists(cr, "sale_commission")
    v19_table_exists = _table_exists(cr, "commission")
    commission_module = _module_installed(cr, "commission")
    enterprise_active = _table_exists(cr, "sale_commission_plan")

    _logger.info(
        "State check: sale_commission table=%s, commission table=%s, "
        "commission module=%s, enterprise=%s",
        v14_table_exists, v19_table_exists,
        commission_module, enterprise_active,
    )
    print(
        ">>> commission_oca pre_init_hook: "
        "sale_commission table=%s, commission table=%s, "
        "commission module=%s, enterprise=%s"
        % (v14_table_exists, v19_table_exists,
           commission_module, enterprise_active)
    )

    if v14_table_exists:
        # V14 tables still exist → migrate
        # This covers: bridge scenario (hook runs first), Enterprise scenario
        # (orphan tables), and direct install.
        print(">>> V14 tables detected - performing PRIMARY migration from hook")
        _handle_v14_migration(cr, enterprise_active)
    elif v19_table_exists and commission_module:
        # V16-V18 case: tables already renamed, just rename the module
        print(">>> Intermediate (V16-V18) detected - renaming module")
        _handle_intermediate_migration(cr)
    elif v19_table_exists:
        # Tables already renamed (previous migration or manual), nothing to do
        _logger.info(
            "Tables already use V19 names (commission, etc.). Nothing to do."
        )
        print(">>> Tables already migrated. Nothing to do.")
    else:
        # Fresh installation, no V14 or intermediate data
        _logger.info("No existing commission data found. Fresh installation.")
        print(">>> Fresh installation - no migration needed.")

    print(">>> commission_oca pre_init_hook: FINISHED\n")
    _logger.info("commission_oca: pre_init_hook finished")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _table_exists(cr, table):
    cr.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_name = %s AND table_schema = 'public'",
        (table,),
    )
    return bool(cr.fetchone())


def _column_exists(cr, table, column):
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s AND table_schema = 'public'",
        (table, column),
    )
    return bool(cr.fetchone())


def _module_installed(cr, module):
    """Check if a module is installed or marked for upgrade."""
    cr.execute(
        "SELECT 1 FROM ir_module_module "
        "WHERE name = %s AND state IN ('installed', 'to upgrade')",
        (module,),
    )
    return bool(cr.fetchone())


def _rename_table(cr, old_table, new_table):
    """Rename a table and its primary key sequence if they exist."""
    if not _table_exists(cr, old_table):
        return False
    if _table_exists(cr, new_table):
        _logger.info(
            "Table '%s' already exists, skipping rename from '%s'",
            new_table, old_table,
        )
        return False
    _logger.info("Renaming table %s -> %s", old_table, new_table)
    cr.execute('ALTER TABLE "%s" RENAME TO "%s"' % (old_table, new_table))
    # Rename primary key sequence
    old_seq = "%s_id_seq" % old_table
    new_seq = "%s_id_seq" % new_table
    cr.execute(
        "SELECT 1 FROM pg_class WHERE relname = %s AND relkind = 'S'",
        (old_seq,),
    )
    if cr.fetchone():
        cr.execute('ALTER SEQUENCE "%s" RENAME TO "%s"' % (old_seq, new_seq))
    return True


def _update_model_references(cr, old_model, new_model):
    """Update all references to a model name in metadata tables."""
    _logger.info("Updating model references: %s -> %s", old_model, new_model)

    # NOTE: ir_model_constraint.model is an INTEGER FK to ir_model.id in
    # Odoo 19 (not a text column). It does NOT need updating here because
    # renaming ir_model.model already fixes the referenced record.
    for table, column in [
        ("ir_model", "model"),
        ("ir_model_fields", "model"),
        ("ir_model_fields", "relation"),
        ("ir_model_data", "model"),
        ("ir_attachment", "res_model"),
    ]:
        if _table_exists(cr, table):
            cr.execute(
                'UPDATE "%s" SET "%s" = %%s WHERE "%s" = %%s'
                % (table, column, column),
                (new_model, old_model),
            )

    # ir_property
    if _table_exists(cr, "ir_property"):
        cr.execute(
            "UPDATE ir_property SET res_id = REPLACE(res_id, %s, %s) "
            "WHERE res_id LIKE %s",
            (old_model + ",", new_model + ",", old_model + ",%"),
        )
    # mail_message
    if _table_exists(cr, "mail_message"):
        cr.execute(
            "UPDATE mail_message SET model = %s WHERE model = %s",
            (new_model, old_model),
        )
    # mail_followers
    if _table_exists(cr, "mail_followers"):
        cr.execute(
            "UPDATE mail_followers SET res_model = %s WHERE res_model = %s",
            (new_model, old_model),
        )

    # Update xmlid names (exact model match only — Enterprise-safe)
    old_u = old_model.replace(".", "_")
    new_u = new_model.replace(".", "_")
    cr.execute(
        "UPDATE ir_model_data SET name = %s "
        "WHERE name = %s AND model = 'ir.model'",
        ("model_%s" % new_u, "model_%s" % old_u),
    )
    # Field xmlids: use exact prefix with double-underscore.
    # REPLACE only substitutes the exact substring, so Enterprise field
    # xmlids (field_sale_commission_plan__*) are NOT affected even if
    # the LIKE matches them (because the substring doesn't occur).
    cr.execute(
        "UPDATE ir_model_data SET name = REPLACE(name, %s, %s) "
        "WHERE name LIKE %s AND model = 'ir.model.fields'",
        ("field_%s__" % old_u, "field_%s__" % new_u,
         "field_%s__" % old_u + "%"),
    )


def _rename_field_in_metadata(cr, model, old_field, new_field):
    """Rename a field in ir_model_fields and related metadata."""
    cr.execute(
        "SELECT 1 FROM ir_model_fields WHERE model = %s AND name = %s",
        (model, old_field),
    )
    if not cr.fetchone():
        return
    cr.execute(
        "UPDATE ir_model_fields SET name = %s WHERE model = %s AND name = %s",
        (new_field, model, old_field),
    )
    _logger.info("Renamed field: %s.%s -> %s.%s", model, old_field, model, new_field)
    # Update xmlid
    model_u = model.replace(".", "_")
    cr.execute(
        "UPDATE ir_model_data SET name = %s "
        "WHERE name = %s AND model = 'ir.model.fields'",
        ("field_%s__%s" % (model_u, new_field),
         "field_%s__%s" % (model_u, old_field)),
    )


def _cleanup_old_module(cr, module_name):
    """Mark an old module as uninstalled and clean up its registration."""
    cr.execute(
        "SELECT id FROM ir_module_module WHERE name = %s",
        (module_name,),
    )
    row = cr.fetchone()
    if not row:
        return
    module_id = row[0]
    cr.execute(
        "DELETE FROM ir_module_module_dependency WHERE module_id = %s",
        (module_id,),
    )
    cr.execute(
        "UPDATE ir_module_module SET state = 'uninstalled' WHERE id = %s",
        (module_id,),
    )
    _logger.info("Marked module '%s' (id=%s) as uninstalled", module_name, module_id)


# ---------------------------------------------------------------------------
# V14 Migration (sale_commission -> split into 3 modules)
# ---------------------------------------------------------------------------

V14_TABLE_RENAMES = [
    ("sale_commission", "commission"),
    ("sale_commission_section", "commission_section"),
    ("sale_commission_settlement", "commission_settlement"),
    ("sale_commission_settlement_line", "commission_settlement_line"),
]

V14_MODEL_RENAMES = [
    ("sale.commission", "commission"),
    ("sale.commission.section", "commission.section"),
    ("sale.commission.settlement", "commission.settlement"),
    ("sale.commission.settlement.line", "commission.settlement.line"),
    ("sale.commission.mixin", "commission.mixin"),
    ("sale.commission.line.mixin", "commission.line.mixin"),
    ("sale.commission.make.settle", "commission.make.settle"),
    ("sale.commission.make.invoice", "commission.make.invoice"),
]


def _handle_v14_migration(cr, enterprise_active=False):
    """Migrate from V14 where only sale_commission existed.

    This is the PRIMARY migration path. It handles:
    - Table renames (sale_commission → commission, etc.)
    - Model reference updates in all metadata tables
    - Field rename (agent_ids → commission_agent_ids)
    - Enterprise-safe XML ID cleanup
    - Module dependency updates

    Args:
        enterprise_active: True if Enterprise sale_commission is detected
            (sale_commission_plan table exists). When True, XML ID cleanup
            is more conservative to avoid breaking Enterprise data.
    """
    _logger.info("=" * 70)
    _logger.info("V14 MIGRATION (PRIMARY): Starting")
    if enterprise_active:
        _logger.info("  Enterprise sale_commission detected — using safe cleanup")
    _logger.info("=" * 70)

    # Step 1: Rename tables
    for old_table, new_table in V14_TABLE_RENAMES:
        _rename_table(cr, old_table, new_table)

    # Step 2: Update model references
    for old_model, new_model in V14_MODEL_RENAMES:
        _update_model_references(cr, old_model, new_model)

    # Step 3: Rename field
    _rename_field_in_metadata(cr, "res.partner", "agent_ids", "commission_agent_ids")
    _rename_field_in_metadata(cr, "res.users", "agent_ids", "commission_agent_ids")

    # Step 4: Enterprise-safe XML ID cleanup
    _cleanup_v14_xmlids(cr, enterprise_active)

    # Step 5: Update module dependencies
    _update_v14_dependencies(cr)

    _logger.info("V14 migration (PRIMARY) completed")
    print(">>> V14 migration completed successfully")


def _cleanup_v14_xmlids(cr, enterprise_active=False):
    """Clean up V14 XML IDs from sale_commission module.

    ENTERPRISE-SAFE: Uses JOINs with actual model tables to target ONLY
    records that reference V14 models (now renamed to commission.*).
    Enterprise models (sale.commission.plan, sale.commission.achievement)
    are never affected.
    """
    # --- Delete auto-generated ir.model records for V14 models only ---
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'sale_commission'
          AND model = 'ir.model'
          AND res_id IN (
            SELECT id FROM ir_model WHERE model IN %s
          )
        """,
        (tuple(V14_RENAMED_MODELS),),
    )
    count_model = cr.rowcount
    _logger.info("Removed %d V14 ir.model XML IDs", count_model)

    # --- Delete auto-generated ir.model.fields records for V14 models ---
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'sale_commission'
          AND model = 'ir.model.fields'
          AND res_id IN (
            SELECT id FROM ir_model_fields WHERE model IN %s
          )
        """,
        (tuple(V14_RENAMED_MODELS),),
    )
    count_fields = cr.rowcount
    _logger.info("Removed %d V14 ir.model.fields XML IDs", count_fields)

    # --- Delete auto-generated ir.model.fields.selection records ---
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'sale_commission'
          AND model = 'ir.model.fields.selection'
          AND res_id IN (
            SELECT s.id FROM ir_model_fields_selection s
            JOIN ir_model_fields f ON s.field_id = f.id
            WHERE f.model IN %s
          )
        """,
        (tuple(V14_RENAMED_MODELS),),
    )
    count_sel = cr.rowcount
    _logger.info("Removed %d V14 ir.model.fields.selection XML IDs", count_sel)

    # --- Delete auto-generated ir.model.constraint records ---
    # NOTE: ir_model_constraint.model is an INTEGER FK to ir_model.id in
    # Odoo 19, so we join through ir_model to filter by model name.
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'sale_commission'
          AND model = 'ir.model.constraint'
          AND res_id IN (
            SELECT c.id FROM ir_model_constraint c
            JOIN ir_model m ON c.model = m.id
            WHERE m.model IN %s
          )
        """,
        (tuple(V14_RENAMED_MODELS),),
    )
    count_cst = cr.rowcount
    _logger.info("Removed %d V14 ir.model.constraint XML IDs", count_cst)

    if enterprise_active:
        # Enterprise is active — only move V14-specific data records.
        # Use model reference to identify V14 records (commission.*).
        # Enterprise records (sale.commission.plan, etc.) are left alone.
        cr.execute(
            """
            UPDATE ir_model_data SET module = 'commission_oca'
            WHERE module = 'sale_commission'
              AND model NOT IN (
                'ir.model', 'ir.model.fields', 'ir.model.fields.selection',
                'ir.model.constraint', 'ir.model.relation'
              )
              AND (
                -- V14 data records: reference renamed models
                model IN %s
                -- V14 views/actions that reference commission models
                -- (identified by name pattern — V14 used sale_commission.* xmlids)
                OR name LIKE 'view_commission%%'
                OR name LIKE 'action_commission%%'
                OR name LIKE 'menu_commission%%'
                OR name LIKE 'access_commission%%'
              )
            """,
            (tuple(V14_RENAMED_MODELS),),
        )
        if cr.rowcount:
            _logger.info(
                "Moved %d V14 data XML IDs to commission_oca (Enterprise-safe)",
                cr.rowcount,
            )
    else:
        # No Enterprise — safe to move ALL remaining sale_commission records.
        cr.execute(
            """
            DELETE FROM ir_model_data
            WHERE module = 'sale_commission'
              AND model IN (
                'ir.model.access', 'ir.rule',
                'ir.ui.view', 'ir.ui.menu',
                'ir.actions.act_window', 'ir.actions.report',
                'ir.module.category', 'ir.model.relation'
              )
            """
        )
        _logger.info(
            "Removed %d technical (views/actions/access) XML IDs", cr.rowcount
        )

        cr.execute(
            "UPDATE ir_model_data SET module = 'commission_oca' "
            "WHERE module = 'sale_commission'"
        )
        if cr.rowcount:
            _logger.info(
                "Moved %d data XML IDs from sale_commission to commission_oca",
                cr.rowcount,
            )

    _logger.info(
        "V14 XML ID cleanup done (enterprise_active=%s)", enterprise_active
    )


def _update_v14_dependencies(cr):
    """Update module dependencies from sale_commission → commission_oca."""
    cr.execute(
        """
        UPDATE ir_module_module_dependency SET name = 'commission_oca'
        WHERE name = 'sale_commission'
          AND module_id NOT IN (
            SELECT id FROM ir_module_module WHERE name = 'sale_commission'
          )
        """
    )
    if cr.rowcount:
        _logger.info(
            "Updated %d module dependencies: sale_commission -> commission_oca",
            cr.rowcount,
        )


# ---------------------------------------------------------------------------
# Intermediate Migration (V16-V18: commission -> commission_oca)
# ---------------------------------------------------------------------------

def _handle_intermediate_migration(cr):
    """Migrate from V16-V18 where 'commission' module exists."""
    _logger.info("=" * 70)
    _logger.info("INTERMEDIATE MIGRATION: Renaming commission -> commission_oca")
    _logger.info("=" * 70)

    cr.execute(
        "UPDATE ir_model_data SET module = 'commission_oca' "
        "WHERE module = 'commission'"
    )
    _logger.info("Moved %d XML IDs from commission to commission_oca", cr.rowcount)

    cr.execute(
        "UPDATE ir_module_module_dependency SET name = 'commission_oca' "
        "WHERE name = 'commission'"
    )

    _rename_field_in_metadata(cr, "res.partner", "agent_ids", "commission_agent_ids")
    _rename_field_in_metadata(cr, "res.users", "agent_ids", "commission_agent_ids")

    _cleanup_old_module(cr, "commission")

    _logger.info("Intermediate migration completed")
