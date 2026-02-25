# Copyright 2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Pre-migration script for account_commission_oca 19.0.1.0.1.

This runs during UPGRADES (not fresh installs). For cross-version migration
(V14 or V16-V18), use the pre_init_hook in hooks.py instead.

This script handles intra-V19 upgrades (e.g., 19.0.1.0.0 -> 19.0.1.0.1).
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Pre-migration for account_commission_oca intra-V19 upgrade."""
    _logger.info(
        "account_commission_oca pre-migrate 19.0.1.0.1 "
        "(installed version: %s)",
        version,
    )

    # Clean up any residual 'account_commission' references
    cr.execute(
        "UPDATE ir_model_data SET module = 'account_commission_oca' "
        "WHERE module = 'account_commission'"
    )
    if cr.rowcount:
        _logger.info(
            "Moved %d orphaned XML IDs from 'account_commission'",
            cr.rowcount,
        )
    )
    
    _logger.info("Renaming module 'account_commission' to 'account_commission_oca'")
    
    # Rename the module - this will update all references automatically
    util.rename_module(cr, "account_commission", "account_commission_oca")
    
    # Remove any remaining references to the old module name
    _logger.info("Cleaning up old module references")
    cr.execute(
        """
        DELETE FROM ir_module_module
        WHERE name = 'account_commission'
        AND id != (SELECT id FROM ir_module_module WHERE name = 'account_commission_oca')
        """
    )
    
    # Clean up any orphaned ir_model_data entries for the old module
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'account_commission'
        AND name NOT IN (
            SELECT name FROM ir_model_data WHERE module = 'account_commission_oca'
        )
        """
    )
    
    _logger.info(
        "Successfully renamed module from 'account_commission' to "
        "'account_commission_oca' and cleaned up old references"
    )
