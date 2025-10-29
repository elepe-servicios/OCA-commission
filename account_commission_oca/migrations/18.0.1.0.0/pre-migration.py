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
    """
    _logger.info("Starting migration from account_commission to account_commission_oca")
    
    # Check if old module exists and is installed
    if not util.module_installed(cr, "account_commission"):
        _logger.info(
            "Module 'account_commission' is not installed. "
            "Migration not needed."
        )
        return
    
    _logger.info("Renaming module 'account_commission' to 'account_commission_oca'")
    
    # Rename the module - this will update all references automatically
    util.rename_module(cr, "account_commission", "account_commission_oca")
    
    _logger.info(
        "Successfully renamed module from 'account_commission' to "
        "'account_commission_oca'"
    )
