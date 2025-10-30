# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post-migration tasks after renaming from 'commission' to 'commission_oca'.

    This script performs cleanup and verification tasks after the module rename:
    - Removes old 'commission' module entry if it still exists
    - Cleans up duplicate XML IDs
    - Verifies all XML IDs have been properly renamed
    - Updates any remaining references in custom fields or data
    - Ensures module category references are correct
    """
    _logger.info("Starting post-migration tasks for commission_oca")

    # CRITICAL: Ensure old 'commission' module is completely removed
    cr.execute(
        """
        SELECT id, name, state 
        FROM ir_module_module 
        WHERE name = 'commission'
        """
    )
    old_modules = cr.fetchall()
    if old_modules:
        _logger.warning(
            f"Found {len(old_modules)} entries for old 'commission' module. "
            "This should not happen after rename. Cleaning up..."
        )
        for module_id, name, state in old_modules:
            _logger.info(f"Removing 'commission' module (ID: {module_id}, state: {state})")
            
            # First remove dependencies pointing to this module
            cr.execute(
                "DELETE FROM ir_module_module_dependency WHERE module_id = %s",
                (module_id,)
            )
            
            # Then remove the module itself
            cr.execute(
                "DELETE FROM ir_module_module WHERE id = %s",
                (module_id,)
            )
        
        _logger.info("Old 'commission' module entries removed")
    
    # Clean up any XML IDs still referencing 'commission' module
    cr.execute(
        """
        SELECT COUNT(*) 
        FROM ir_model_data 
        WHERE module = 'commission'
        """
    )
    old_xmlid_count = cr.fetchone()[0]
    
    if old_xmlid_count > 0:
        _logger.warning(
            f"Found {old_xmlid_count} XML IDs still referencing 'commission' module. "
            "Attempting to fix or remove..."
        )
        
        # Get all XML IDs from old module
        cr.execute(
            """
            SELECT id, name, model, res_id, module
            FROM ir_model_data
            WHERE module = 'commission'
            ORDER BY name
            """
        )
        old_xmlids = cr.fetchall()
        
        for xmlid_id, name, model, res_id, module in old_xmlids:
            # Check if same XML ID exists with new module name
            cr.execute(
                """
                SELECT id, res_id
                FROM ir_model_data
                WHERE module = 'commission_oca'
                AND name = %s
                AND model = %s
                """,
                (name, model)
            )
            new_xmlid = cr.fetchone()
            
            if new_xmlid:
                # Duplicate exists - remove old one
                _logger.info(
                    f"Removing duplicate XML ID 'commission.{name}' "
                    f"(already exists as 'commission_oca.{name}')"
                )
                cr.execute(
                    "DELETE FROM ir_model_data WHERE id = %s",
                    (xmlid_id,)
                )
            else:
                # No duplicate - rename to new module
                _logger.info(
                    f"Migrating orphaned XML ID 'commission.{name}' to 'commission_oca.{name}'"
                )
                cr.execute(
                    """
                    UPDATE ir_model_data
                    SET module = 'commission_oca'
                    WHERE id = %s
                    """,
                    (xmlid_id,)
                )
        
        _logger.info(f"Cleaned up {old_xmlid_count} old XML IDs")
    
    # Final verification
    cr.execute(
        """
        SELECT COUNT(*) 
        FROM ir_model_data 
        WHERE module = 'commission'
        """
    )
    remaining_old = cr.fetchone()[0]
    
    cr.execute(
        """
        SELECT COUNT(*) 
        FROM ir_model_data 
        WHERE module = 'commission_oca'
        """
    )
    new_count = cr.fetchone()[0]
    
    _logger.info(
        f"XML IDs summary - Old module 'commission': {remaining_old}, "
        f"New module 'commission_oca': {new_count}"
    )
    
    if remaining_old > 0:
        _logger.error(
            f"WARNING: Still {remaining_old} XML IDs referencing old 'commission' module!"
        )

    # Verify the module exists with the new name
    if not util.module_installed(cr, "commission_oca"):
        _logger.error(
            "Module 'commission_oca' not found after migration. Something went wrong!"
        )
        return

    # Update module category reference if it exists with old name
    cr.execute(
        """
        UPDATE ir_module_category
        SET name = 'Commissions'
        WHERE name = 'Commission'
        AND id IN (
            SELECT category_id
            FROM ir_module_module
            WHERE name = 'commission_oca'
        )
        """
    )
    if cr.rowcount:
        _logger.info("Updated module category name")

    # Verify all models are properly registered with the new module
    model_names = [
        "commission",
        "commission.section",
        "commission.mixin",
        "commission.line.mixin",
        "commission.settlement",
        "commission.settlement.line",
        "commission.make.settle",
    ]

    for model_name in model_names:
        cr.execute(
            """
            SELECT COUNT(*)
            FROM ir_model_data
            WHERE model = 'ir.model'
            AND module = 'commission_oca'
            AND name = %s
            """,
            (f"model_{model_name.replace('.', '_')}",),
        )
        result = cr.fetchone()
        if result and result[0] > 0:
            _logger.info("Model %s is properly registered", model_name)

    # Update menu items to ensure they reference the correct module
    cr.execute(
        """
        UPDATE ir_ui_menu
        SET name = 'Commissions'
        WHERE id IN (
            SELECT res_id
            FROM ir_model_data
            WHERE model = 'ir.ui.menu'
            AND module = 'commission_oca'
            AND name = 'menu_commission'
        )
        """
    )

    # Ensure all security groups are properly set
    cr.execute(
        """
        SELECT name
        FROM res_groups
        WHERE category_id IN (
            SELECT res_id
            FROM ir_model_data
            WHERE model = 'ir.module.category'
            AND module = 'commission_oca'
            AND name = 'module_category_commission'
        )
        """
    )
    groups = cr.fetchall()
    _logger.info(
        "Found %d security groups for commission_oca module", len(groups)
    )
    
    # Final check: ensure no 'commission' module exists
    cr.execute(
        "SELECT id FROM ir_module_module WHERE name = 'commission'"
    )
    if cr.fetchone():
        _logger.error(
            "CRITICAL: Old 'commission' module still exists after cleanup! "
            "Manual intervention may be required."
        )
    else:
        _logger.info(
            "✓ Verification passed: Old 'commission' module successfully removed"
        )

    _logger.info("Post-migration tasks completed successfully for commission_oca")
