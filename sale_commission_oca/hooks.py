# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Migration hooks for sale_commission_oca module.

Handles the V16-V18 module rename: sale_commission → sale_commission_oca.

For V14 → V19 migrations:
  - commission_oca's pre_init_hook handles ALL table/model/field renames.
  - This hook only handles residual XML ID moves from the old module name.

For Enterprise coexistence (Odoo.sh):
  - If Enterprise's sale_commission is installed, its state is 'installed'
    (not 'to upgrade' like the bridge). We detect Enterprise by checking
    for the sale_commission_plan table. When Enterprise is active, we skip
    module cleanup to avoid breaking Enterprise data.
"""

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Prepare the database for sale_commission_oca installation."""
    print("\n>>> sale_commission_oca pre_init_hook: STARTED")
    _logger.info("sale_commission_oca: pre_init_hook starting")

    cr = env.cr

    # Detect Enterprise sale_commission (different models)
    enterprise_active = _table_exists(cr, "sale_commission_plan")

    # Check state of sale_commission module
    cr.execute(
        "SELECT state FROM ir_module_module WHERE name = 'sale_commission'"
    )
    row = cr.fetchone()

    if not row:
        _logger.info("No sale_commission module found. Fresh installation.")
        print(">>> sale_commission_oca: Fresh installation - nothing to migrate.")
        print(">>> sale_commission_oca pre_init_hook: FINISHED\n")
        return

    state = row[0]
    _logger.info(
        "sale_commission module state=%s, enterprise=%s", state, enterprise_active
    )
    print(
        ">>> sale_commission_oca: sale_commission state=%s, enterprise=%s"
        % (state, enterprise_active)
    )

    if enterprise_active:
        # Enterprise's sale_commission is active. Don't touch its records.
        # commission_oca's hook already migrated V14 data Enterprise-safely.
        _logger.info(
            "Enterprise sale_commission detected. "
            "Skipping module cleanup to preserve Enterprise data."
        )
        print(">>> Enterprise detected - skipping sale_commission cleanup.")
    elif state == 'to upgrade':
        # Bridge module is active (V14 migration path).
        # commission_oca's hook already handled table/model renames.
        # Just move any residual data XML IDs that belong to sale-specific
        # functionality (sale.order.line.agent, etc.).
        _logger.info(
            "sale_commission is in 'to upgrade' (bridge active). "
            "Moving residual sale-specific XML IDs."
        )
        _move_sale_xmlids(cr)
    elif state == 'installed':
        # V16-V18 direct migration: rename OCA sale_commission module.
        _logger.info("Renaming V16-V18 sale_commission -> sale_commission_oca")
        print(">>> Renaming V16-V18 sale_commission -> sale_commission_oca")
        _rename_v16_sale_commission(cr)
    else:
        _logger.info(
            "sale_commission state=%s - no action needed", state
        )

    print(">>> sale_commission_oca pre_init_hook: FINISHED\n")
    _logger.info("sale_commission_oca: pre_init_hook finished")


def _table_exists(cr, table):
    cr.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_name = %s AND table_schema = 'public'",
        (table,),
    )
    return bool(cr.fetchone())


def _move_sale_xmlids(cr):
    """Move sale-specific XML IDs from sale_commission to sale_commission_oca."""
    # Only move non-technical records that are sale-specific.
    # Technical records (ir.model, ir.model.fields) were already handled
    # by commission_oca's hook.
    cr.execute(
        """
        UPDATE ir_model_data SET module = 'sale_commission_oca'
        WHERE module = 'sale_commission'
          AND model NOT IN (
            'ir.model', 'ir.model.fields', 'ir.model.fields.selection',
            'ir.model.access', 'ir.model.constraint', 'ir.rule',
            'ir.ui.view', 'ir.ui.menu',
            'ir.actions.act_window', 'ir.actions.report',
            'ir.module.category', 'ir.model.relation'
          )
        """
    )
    if cr.rowcount:
        _logger.info(
            "Moved %d residual XML IDs to sale_commission_oca", cr.rowcount
        )


def _rename_v16_sale_commission(cr):
    """Full rename of V16-V18 OCA sale_commission → sale_commission_oca."""
    cr.execute(
        "UPDATE ir_model_data SET module = 'sale_commission_oca' "
        "WHERE module = 'sale_commission'"
    )
    _logger.info("Moved %d XML IDs", cr.rowcount)

    cr.execute(
        "UPDATE ir_module_module_dependency SET name = 'sale_commission_oca' "
        "WHERE name = 'sale_commission'"
    )

    # Mark old module as uninstalled
    cr.execute(
        "SELECT id FROM ir_module_module WHERE name = 'sale_commission'"
    )
    mod_row = cr.fetchone()
    if mod_row:
        cr.execute(
            "DELETE FROM ir_module_module_dependency WHERE module_id = %s",
            (mod_row[0],),
        )
        cr.execute(
            "UPDATE ir_module_module SET state = 'uninstalled' WHERE id = %s",
            (mod_row[0],),
        )
        _logger.info("Marked sale_commission as uninstalled")
