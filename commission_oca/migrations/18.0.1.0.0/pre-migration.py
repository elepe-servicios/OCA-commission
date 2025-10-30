# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Rename module from 'commission' to 'commission_oca'.

    This script handles the migration when upgrading from Odoo v17 where the module
    was named 'commission' to Odoo v18 where it's renamed to 'commission_oca'.

    The script renames:
    - Module name and all its references
    - XML IDs from 'commission.' to 'commission_oca.'
    - Model references
    - Dependencies in other modules
    """
    _logger.info("Starting migration: Renaming 'commission' to 'commission_oca'")

    # Check if the old module 'commission' exists and is installed
    if not util.module_installed(cr, "commission"):
        _logger.info(
            "Module 'commission' not found or not installed. "
            "Skipping rename migration."
        )
        return

    _logger.info("Renaming module 'commission' to 'commission_oca'")
    
    # First, get the module ID before renaming
    cr.execute(
        "SELECT id FROM ir_module_module WHERE name = 'commission' AND state != 'uninstalled'"
    )
    old_module = cr.fetchone()
    if not old_module:
        _logger.warning("Module 'commission' not found in installed state")
        return
    
    old_module_id = old_module[0]
    _logger.info(f"Found old module 'commission' with ID {old_module_id}")

    # Rename the module and all its references
    # This will update:
    # - ir_module_module table
    # - ir_model_data (XML IDs)
    # - ir_module_module_dependency
    # - All other module dependencies
    util.rename_module(cr, "commission", "commission_oca")

    # Verify and clean up any remaining references
    cr.execute(
        "SELECT id FROM ir_module_module WHERE name = 'commission'"
    )
    remaining = cr.fetchone()
    if remaining:
        _logger.info("Removing residual 'commission' module entry")
        cr.execute(
            "DELETE FROM ir_module_module WHERE name = 'commission'"
        )
    
    # Clean up any duplicate XML IDs that might remain with 'commission' module
    cr.execute(
        """
        SELECT COUNT(*) 
        FROM ir_model_data 
        WHERE module = 'commission'
        """
    )
    count = cr.fetchone()[0]
    if count > 0:
        _logger.warning(
            f"Found {count} XML IDs still referencing 'commission' module. "
            "These should have been renamed."
        )
        # Log them for debugging
        cr.execute(
            """
            SELECT name, model, res_id 
            FROM ir_model_data 
            WHERE module = 'commission'
            LIMIT 10
            """
        )
        for row in cr.fetchall():
            _logger.warning(f"Remaining XML ID: commission.{row[0]} (model: {row[1]}, res_id: {row[2]})")

    _logger.info(
        "Successfully renamed module from 'commission' to 'commission_oca'"
    )
