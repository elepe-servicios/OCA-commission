# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Migration hooks for sale_commission_oca module.

Handles migration from:
- V14: ``sale_commission`` was the only module. The heavy migration
  (model renames, field renames) is handled by commission_oca's
  pre_init_hook. This hook handles any remaining cleanup.
- V16-V18: ``sale_commission`` (OCA) needs renaming to ``sale_commission_oca``
  to avoid conflicts with the Odoo 19 Enterprise ``sale_commission`` module.

IMPORTANT: Odoo 19 Enterprise introduces an official ``sale_commission``
module with different models (sale.commission.plan, sale.commission.achievement).
The OCA module must use the ``sale_commission_oca`` name to avoid conflicts.
This hook ensures the OCA module data is properly migrated and the old
module entry is cleaned up so it doesn't interfere with the Enterprise module.
"""

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Prepare the database for sale_commission_oca installation."""
    cr = env.cr
    _handle_intermediate_migration(cr)
    _handle_enterprise_conflict(cr)


def _module_installed(cr, module):
    cr.execute(
        "SELECT 1 FROM ir_module_module "
        "WHERE name = %s AND state IN ('installed', 'to upgrade')",
        (module,),
    )
    return bool(cr.fetchone())


def _handle_intermediate_migration(cr):
    """Handle migration from V16-V18 where OCA 'sale_commission' exists."""
    if not _module_installed(cr, "sale_commission"):
        return

    _logger.info("=" * 70)
    _logger.info(
        "MIGRATION: Detected installed 'sale_commission' module"
    )
    _logger.info("Renaming to sale_commission_oca")
    _logger.info("=" * 70)

    # Move XML IDs from 'sale_commission' to 'sale_commission_oca'
    cr.execute(
        "UPDATE ir_model_data SET module = 'sale_commission_oca' "
        "WHERE module = 'sale_commission'"
    )
    _logger.info(
        "Moved %d XML IDs from sale_commission to sale_commission_oca",
        cr.rowcount,
    )

    # Update module dependencies
    cr.execute(
        "UPDATE ir_module_module_dependency SET name = 'sale_commission_oca' "
        "WHERE name = 'sale_commission'"
    )

    # Clean up old module entry
    cr.execute(
        "SELECT id FROM ir_module_module WHERE name = 'sale_commission'",
    )
    row = cr.fetchone()
    if row:
        module_id = row[0]
        cr.execute(
            "DELETE FROM ir_module_module_dependency WHERE module_id = %s",
            (module_id,),
        )
        cr.execute(
            "UPDATE ir_module_module SET state = 'uninstalled' WHERE id = %s",
            (module_id,),
        )
        _logger.info("Marked 'sale_commission' as uninstalled")

    _logger.info("Migration completed for sale_commission_oca")


def _handle_enterprise_conflict(cr):
    """Ensure no conflicts with Odoo 19 Enterprise sale_commission module.

    The Enterprise module uses different models (sale.commission.plan,
    sale.commission.achievement) so there should be no data conflicts.
    We just need to ensure our renamed module doesn't interfere.
    """
    # Check if Enterprise sale_commission exists alongside our OCA one
    cr.execute(
        "SELECT COUNT(*) FROM ir_module_module WHERE name = 'sale_commission'"
    )
    count = cr.fetchone()[0]
    if count > 1:
        _logger.warning(
            "Multiple 'sale_commission' entries found in ir_module_module. "
            "This may indicate a conflict between OCA and Enterprise modules."
        )
    elif count == 1:
        # There's one sale_commission entry. If it was already handled by
        # commission_oca's hook (V14 case) or the intermediate migration
        # above, it should be 'uninstalled'. If it's the Enterprise module
        # being installed, leave it alone.
        cr.execute(
            "SELECT state, latest_version FROM ir_module_module "
            "WHERE name = 'sale_commission'"
        )
        row = cr.fetchone()
        if row and row[0] in ("installed", "to upgrade"):
            state, ver = row
            _logger.info(
                "sale_commission module found (state=%s, version=%s). "
                "If this is the Enterprise module, no action needed. "
                "If this is residual OCA data, it should have been handled "
                "by commission_oca's pre_init_hook.",
                state,
                ver,
            )
