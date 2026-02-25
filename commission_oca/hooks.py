# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Migration hooks for commission_oca module.

Handles migration from:
- V14: Only ``sale_commission`` existed (single module for all commission functionality)
- V16-V18: ``commission`` was the base module (already split but different name)

In V14, the OCA ``sale_commission`` module contained ALL models:
  sale.commission, sale.commission.section, sale.commission.settlement,
  sale.commission.settlement.line, sale.commission.mixin,
  sale.commission.line.mixin, account.invoice.line.agent,
  sale.order.line.agent, etc.

In V19, this is split into:
  - commission_oca (base models: commission, commission.section, etc.)
  - account_commission_oca (accounting: account.invoice.line.agent, etc.)
  - sale_commission_oca (sales: sale.order.line.agent, etc.)

Additionally, Odoo 19 Enterprise introduces an official ``sale_commission``
module with different models (sale.commission.plan, sale.commission.achievement).
This hook ensures no conflicts arise.

IMPORTANT: Migration scripts in ``migrations/`` only run during module UPGRADES,
not INSTALLATIONS. Since these modules did not exist in V14 (or V16-V18 under
different names), they are treated as fresh installations and migration scripts
are skipped. ``pre_init_hook`` is the only reliable entry point for migration.
"""

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Prepare the database for commission_oca installation.

    This hook runs BEFORE the module's models and data are loaded.
    It renames tables, columns, and model references so that the ORM
    finds existing data when creating V19 models.
    """
    cr = env.cr
    _handle_v14_migration(cr)
    _handle_intermediate_migration(cr)


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
            new_table,
            old_table,
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
    # ir_model
    cr.execute(
        "UPDATE ir_model SET model = %s WHERE model = %s",
        (new_model, old_model),
    )
    # ir_model_fields (model column)
    cr.execute(
        "UPDATE ir_model_fields SET model = %s WHERE model = %s",
        (new_model, old_model),
    )
    # ir_model_fields (relation / comodel)
    cr.execute(
        "UPDATE ir_model_fields SET relation = %s WHERE relation = %s",
        (new_model, old_model),
    )
    # ir_model_data (model column - references to records of this model)
    cr.execute(
        "UPDATE ir_model_data SET model = %s WHERE model = %s",
        (new_model, old_model),
    )
    # ir_model_constraint
    cr.execute(
        "UPDATE ir_model_constraint SET model = %s WHERE model = %s",
        (new_model, old_model),
    )
    # ir_property (res_id format: 'model,id')
    if _table_exists(cr, "ir_property"):
        cr.execute(
            "UPDATE ir_property SET res_id = REPLACE(res_id, %s, %s) "
            "WHERE res_id LIKE %s",
            (old_model + ",", new_model + ",", old_model + ",%"),
        )
    # mail_message (model column)
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
    # ir_attachment
    cr.execute(
        "UPDATE ir_attachment SET res_model = %s WHERE res_model = %s",
        (new_model, old_model),
    )
    # ir_model_data: update the xmlid name for the model definition itself
    old_xmlid_suffix = "model_%s" % old_model.replace(".", "_")
    new_xmlid_suffix = "model_%s" % new_model.replace(".", "_")
    cr.execute(
        "UPDATE ir_model_data SET name = %s WHERE name = %s AND model = 'ir.model'",
        (new_xmlid_suffix, old_xmlid_suffix),
    )
    # ir_model_data: update field xmlid names
    old_field_prefix = "field_%s__" % old_model.replace(".", "_")
    new_field_prefix = "field_%s__" % new_model.replace(".", "_")
    cr.execute(
        "UPDATE ir_model_data SET name = REPLACE(name, %s, %s) "
        "WHERE name LIKE %s AND model = 'ir.model.fields'",
        (old_field_prefix, new_field_prefix, old_field_prefix + "%"),
    )


def _rename_field_in_metadata(cr, model, old_field, new_field):
    """Rename a field in ir_model_fields and related metadata."""
    # ir_model_fields
    cr.execute(
        "UPDATE ir_model_fields SET name = %s "
        "WHERE model = %s AND name = %s",
        (new_field, model, old_field),
    )
    if cr.rowcount:
        _logger.info(
            "Renamed field reference: %s.%s -> %s.%s",
            model,
            old_field,
            model,
            new_field,
        )
    # ir_model_data for the field xmlid
    old_xmlid = "field_%s__%s" % (model.replace(".", "_"), old_field)
    new_xmlid = "field_%s__%s" % (model.replace(".", "_"), new_field)
    cr.execute(
        "UPDATE ir_model_data SET name = %s WHERE name = %s AND model = 'ir.model.fields'",
        (new_xmlid, old_xmlid),
    )
    # Also rename in inheriting models (res.users inherits from res.partner)
    cr.execute(
        "UPDATE ir_model_fields SET name = %s "
        "WHERE name = %s AND model IN ("
        "  SELECT model FROM ir_model_fields "
        "  WHERE name = %s AND ttype = 'many2many'"
        ")",
        (new_field, old_field, old_field),
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
    # Remove module dependencies
    cr.execute(
        "DELETE FROM ir_module_module_dependency WHERE module_id = %s",
        (module_id,),
    )
    # Mark as uninstalled
    cr.execute(
        "UPDATE ir_module_module SET state = 'uninstalled' WHERE id = %s",
        (module_id,),
    )
    _logger.info("Marked module '%s' (id=%s) as uninstalled", module_name, module_id)


# ---------------------------------------------------------------------------
# V14 Migration (sale_commission -> split into 3 modules)
# ---------------------------------------------------------------------------

def _handle_v14_migration(cr):
    """Migrate from V14 where only sale_commission existed."""
    if not _module_installed(cr, "sale_commission"):
        return

    _logger.info("=" * 70)
    _logger.info("V14 MIGRATION: Detected installed 'sale_commission' module")
    _logger.info("Migrating to commission_oca + account_commission_oca + sale_commission_oca")
    _logger.info("=" * 70)

    # Try to use upgrade-util for robust migration
    try:
        from odoo.upgrade import util

        _migrate_v14_with_util(cr, util)
    except ImportError:
        _logger.warning(
            "odoo-upgrade-util not available. Using direct SQL. "
            "For best results, install: pip install "
            "odoo_upgrade@git+https://github.com/odoo/upgrade-util@master"
        )
        _migrate_v14_with_sql(cr)

    _logger.info("V14 migration completed successfully")


def _migrate_v14_with_util(cr, util):
    """V14 migration using upgrade-util (preferred method)."""
    # --- Step 1: Rename concrete models (have tables) ---
    concrete_renames = [
        ("sale.commission", "commission"),
        ("sale.commission.section", "commission.section"),
        ("sale.commission.settlement", "commission.settlement"),
        ("sale.commission.settlement.line", "commission.settlement.line"),
    ]
    for old_model, new_model in concrete_renames:
        _logger.info("Renaming model %s -> %s", old_model, new_model)
        try:
            util.rename_model(cr, old_model, new_model)
        except Exception as e:
            _logger.warning("Could not rename model %s: %s", old_model, e)
            # Fallback to SQL
            old_table = old_model.replace(".", "_")
            new_table = new_model.replace(".", "_")
            _rename_table(cr, old_table, new_table)
            _update_model_references(cr, old_model, new_model)

    # --- Step 2: Rename abstract/transient models (no table) ---
    abstract_renames = [
        ("sale.commission.mixin", "commission.mixin"),
        ("sale.commission.line.mixin", "commission.line.mixin"),
        ("sale.commission.make.settle", "commission.make.settle"),
        ("sale.commission.make.invoice", "commission.make.invoice"),
    ]
    for old_model, new_model in abstract_renames:
        try:
            util.rename_model(cr, old_model, new_model, rename_table=False)
        except Exception as e:
            _logger.debug("Non-critical model rename %s: %s", old_model, e)
            _update_model_references(cr, old_model, new_model)

    # --- Step 3: Rename field agent_ids -> commission_agent_ids ---
    _rename_agent_field_util(cr, util)

    # --- Step 4: Handle module entry ---
    _finalize_v14_module(cr)


def _migrate_v14_with_sql(cr):
    """V14 migration using direct SQL (fallback when util is unavailable)."""
    # --- Step 1: Rename tables ---
    table_renames = [
        ("sale_commission", "commission"),
        ("sale_commission_section", "commission_section"),
        ("sale_commission_settlement", "commission_settlement"),
        ("sale_commission_settlement_line", "commission_settlement_line"),
    ]
    for old_table, new_table in table_renames:
        _rename_table(cr, old_table, new_table)

    # --- Step 2: Update model references ---
    model_renames = [
        ("sale.commission", "commission"),
        ("sale.commission.section", "commission.section"),
        ("sale.commission.settlement", "commission.settlement"),
        ("sale.commission.settlement.line", "commission.settlement.line"),
        ("sale.commission.mixin", "commission.mixin"),
        ("sale.commission.line.mixin", "commission.line.mixin"),
        ("sale.commission.make.settle", "commission.make.settle"),
        ("sale.commission.make.invoice", "commission.make.invoice"),
    ]
    for old_model, new_model in model_renames:
        _update_model_references(cr, old_model, new_model)

    # --- Step 3: Rename field ---
    _rename_agent_field_sql(cr)

    # --- Step 4: Handle module entry ---
    _finalize_v14_module(cr)


def _rename_agent_field_util(cr, util):
    """Rename res.partner.agent_ids -> commission_agent_ids using util."""
    cr.execute(
        "SELECT 1 FROM ir_model_fields "
        "WHERE model = 'res.partner' AND name = 'agent_ids'"
    )
    if not cr.fetchone():
        _logger.info("Field agent_ids not found on res.partner - already renamed or absent")
        return
    _logger.info("Renaming field res.partner.agent_ids -> commission_agent_ids")
    try:
        util.rename_field(
            cr,
            "res.partner",
            "agent_ids",
            "commission_agent_ids",
            update_references=True,
        )
    except Exception as e:
        _logger.warning("util.rename_field failed: %s - falling back to SQL", e)
        _rename_agent_field_sql(cr)


def _rename_agent_field_sql(cr):
    """Rename res.partner.agent_ids -> commission_agent_ids using SQL."""
    cr.execute(
        "SELECT 1 FROM ir_model_fields "
        "WHERE model = 'res.partner' AND name = 'agent_ids'"
    )
    if not cr.fetchone():
        return
    _rename_field_in_metadata(cr, "res.partner", "agent_ids", "commission_agent_ids")
    # Also update res.users (inherits from res.partner)
    _rename_field_in_metadata(cr, "res.users", "agent_ids", "commission_agent_ids")


def _finalize_v14_module(cr):
    """Clean up the old V14 sale_commission module entry."""
    # Remove configuration/metadata XML IDs from the old module.
    # These will be recreated by the new V19 modules during installation.
    # We keep data XML IDs (actual commission records, etc.) to avoid data loss.
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'sale_commission'
          AND model IN (
            'ir.model', 'ir.model.fields', 'ir.model.access',
            'ir.model.constraint', 'ir.rule',
            'ir.ui.view', 'ir.ui.menu',
            'ir.actions.act_window', 'ir.actions.report',
            'ir.module.category', 'ir.model.relation'
        )
        """
    )
    deleted = cr.rowcount
    _logger.info(
        "Removed %d configuration XML IDs from sale_commission", deleted
    )

    # Move remaining data XML IDs to sale_commission_oca
    # (these are records like demo data that reference actual DB records)
    cr.execute(
        """
        UPDATE ir_model_data
        SET module = 'sale_commission_oca'
        WHERE module = 'sale_commission'
        """
    )
    moved = cr.rowcount
    if moved:
        _logger.info(
            "Moved %d remaining XML IDs from sale_commission to sale_commission_oca",
            moved,
        )

    # Update module dependencies pointing to the old module
    cr.execute(
        """
        UPDATE ir_module_module_dependency
        SET name = 'sale_commission_oca'
        WHERE name = 'sale_commission'
        """
    )

    # Mark old module as uninstalled
    _cleanup_old_module(cr, "sale_commission")


# ---------------------------------------------------------------------------
# Intermediate Migration (V16-V18: commission -> commission_oca)
# ---------------------------------------------------------------------------

def _handle_intermediate_migration(cr):
    """Migrate from V16-V18 where 'commission' module exists."""
    if not _module_installed(cr, "commission"):
        return

    _logger.info("=" * 70)
    _logger.info("INTERMEDIATE MIGRATION: Detected installed 'commission' module")
    _logger.info("Renaming to commission_oca")
    _logger.info("=" * 70)

    # Move XML IDs from 'commission' to 'commission_oca'
    cr.execute(
        "UPDATE ir_model_data SET module = 'commission_oca' WHERE module = 'commission'"
    )
    _logger.info("Moved %d XML IDs from commission to commission_oca", cr.rowcount)

    # Update module dependencies
    cr.execute(
        "UPDATE ir_module_module_dependency SET name = 'commission_oca' "
        "WHERE name = 'commission'"
    )

    # Rename field if still agent_ids
    _rename_agent_field_sql(cr)

    # Clean up old module entry
    _cleanup_old_module(cr, "commission")

    _logger.info("Intermediate migration completed successfully")
