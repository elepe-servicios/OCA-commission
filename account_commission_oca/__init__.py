from . import models
from . import wizards
from . import report


def post_init_hook(env):
    """Clean up old account_commission module references if it exists.
    
    This hook is executed after the module is installed or updated.
    It ensures that the old 'account_commission' module references are
    properly migrated to 'account_commission_oca' without losing any data.
    
    Instead of removing the module, we migrate any remaining references
    to preserve all data.
    """
    import logging
    
    _logger = logging.getLogger(__name__)
    cr = env.cr
    
    # Check if the old module still exists
    cr.execute(
        """
        SELECT id, state
        FROM ir_module_module
        WHERE name = 'account_commission'
        """
    )
    old_module = cr.fetchone()
    
    if not old_module:
        _logger.info(
            "Old module 'account_commission' not found. No cleanup needed."
        )
        return
    
    module_id, module_state = old_module
    _logger.info(
        "Found old module 'account_commission' (ID: %s, state: %s). "
        "Migrating remaining references...",
        module_id, module_state
    )
    
    try:
        # Migrate any remaining XML IDs from old module to new one
        cr.execute(
            """
            UPDATE ir_model_data
            SET module = 'account_commission_oca'
            WHERE module = 'account_commission'
            AND NOT EXISTS (
                SELECT 1
                FROM ir_model_data imd
                WHERE imd.module = 'account_commission_oca'
                AND imd.name = ir_model_data.name
                AND imd.model = ir_model_data.model
            )
            """
        )
        migrated_xmlids = cr.rowcount
        if migrated_xmlids:
            _logger.info("Migrated %s XML IDs to account_commission_oca", migrated_xmlids)
        
        # Remove duplicate XML IDs (where same record exists in both modules)
        cr.execute(
            """
            DELETE FROM ir_model_data
            WHERE module = 'account_commission'
            AND EXISTS (
                SELECT 1
                FROM ir_model_data imd
                WHERE imd.module = 'account_commission_oca'
                AND imd.name = ir_model_data.name
                AND imd.model = ir_model_data.model
                AND imd.res_id = ir_model_data.res_id
            )
            """
        )
        deleted_duplicates = cr.rowcount
        if deleted_duplicates:
            _logger.info("Removed %s duplicate XML IDs", deleted_duplicates)
        
        # Update module dependencies
        cr.execute(
            """
            UPDATE ir_module_module_dependency
            SET name = 'account_commission_oca'
            WHERE name = 'account_commission'
            """
        )
        updated_deps = cr.rowcount
        if updated_deps:
            _logger.info("Updated %s module dependencies", updated_deps)
        
        # Set old module to uninstalled state
        cr.execute(
            """
            UPDATE ir_module_module
            SET state = 'uninstalled'
            WHERE name = 'account_commission'
            """
        )
        
        # Remove the old module entry
        cr.execute(
            """
            DELETE FROM ir_module_module
            WHERE name = 'account_commission'
            """
        )
        
        _logger.info(
            "Successfully migrated all references from 'account_commission' to "
            "'account_commission_oca'. All data has been preserved."
        )
        
    except Exception as e:
        _logger.warning(
            "Could not complete migration of old module references: %s. "
            "Manual cleanup may be required.",
            str(e)
        )
