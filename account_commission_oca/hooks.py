# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Migration hooks for account_commission_oca module.

Handles migration from:
- V14: All accounting commission functionality was in ``sale_commission``.
  The table/model renames and field renames are handled by commission_oca's
  pre_init_hook. This hook only needs to handle the ``account_commission``
  module rename if it exists (V16-V18 intermediate).
- V16-V18: ``account_commission`` was a separate module that needs renaming
  to ``account_commission_oca``.

Enterprise-safe: This hook does not touch ``sale_commission`` records at all.
It only handles the ``account_commission`` → ``account_commission_oca`` rename.
"""

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Prepare the database for account_commission_oca installation."""
    print("\n>>> account_commission_oca pre_init_hook: STARTED")
    _logger.info("account_commission_oca: pre_init_hook starting")
    cr = env.cr
    _handle_intermediate_migration(cr)
    print(">>> account_commission_oca pre_init_hook: FINISHED\n")
    _logger.info("account_commission_oca: pre_init_hook finished")


def _module_installed(cr, module):
    cr.execute(
        "SELECT 1 FROM ir_module_module "
        "WHERE name = %s AND state IN ('installed', 'to upgrade')",
        (module,),
    )
    return bool(cr.fetchone())


def _handle_intermediate_migration(cr):
    """Handle migration from V16-V18 where 'account_commission' exists."""
    if not _module_installed(cr, "account_commission"):
        _logger.info("No account_commission module found. Nothing to migrate.")
        print(">>> account_commission_oca: No intermediate module found.")
        return

    _logger.info("=" * 70)
    _logger.info(
        "INTERMEDIATE MIGRATION: Detected installed 'account_commission' module"
    )
    _logger.info("Renaming to account_commission_oca")
    _logger.info("=" * 70)
    print(">>> Renaming account_commission -> account_commission_oca")

    # Move XML IDs from 'account_commission' to 'account_commission_oca'
    cr.execute(
        "UPDATE ir_model_data SET module = 'account_commission_oca' "
        "WHERE module = 'account_commission'"
    )
    _logger.info(
        "Moved %d XML IDs from account_commission to account_commission_oca",
        cr.rowcount,
    )

    # Update module dependencies
    cr.execute(
        "UPDATE ir_module_module_dependency SET name = 'account_commission_oca' "
        "WHERE name = 'account_commission'"
    )

    # Clean up old module entry
    cr.execute(
        "SELECT id FROM ir_module_module WHERE name = 'account_commission'",
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
        _logger.info("Marked 'account_commission' as uninstalled")

    _logger.info("Intermediate migration completed for account_commission_oca")
