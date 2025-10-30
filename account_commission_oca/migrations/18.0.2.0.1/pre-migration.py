# Copyright 2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate from account_commission to account_commission_oca.
    
    This script handles the module rename that occurred in Odoo 18.0.
    The module 'account_commission' was renamed to 'account_commission_oca'
    to follow OCA naming conventions.
    
    This migration will:
    - Rename the module and all its references
    - Update XML IDs
    - Update model references
    - Update security groups
    - Remove old module entry to avoid duplicates
    """
    _logger.info("Starting migration from account_commission to account_commission_oca")
    
    # Check if old module exists and is installed
    if not util.module_installed(cr, "account_commission"):
        _logger.info(
            "Module 'account_commission' is not installed. "
            "Migration not needed."
        )
        return
    
    # Set noupdate=True for security group to prevent updates during migration
    _logger.info("Setting noupdate flag for group_invoicing_commission")
    util.force_noupdate(
        cr, 
        "account_commission.group_invoicing_commission",
        noupdate=True
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
