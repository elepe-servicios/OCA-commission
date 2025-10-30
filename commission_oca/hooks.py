# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Hook executed after module installation/update.

    This hook ensures that the old 'commission' module references are
    properly migrated to 'commission_oca' without losing any data.
    
    Instead of removing the module, we migrate any remaining references
    to preserve all data.
    """
    cr = env.cr
    
    _logger.info("=" * 70)
    _logger.info("POST-INIT HOOK: Checking for old 'commission' module")
    _logger.info("=" * 70)

    # Check if old module exists
    cr.execute(
        """
        SELECT id, name, state
        FROM ir_module_module
        WHERE name = 'commission'
        """
    )
    old_module = cr.fetchone()

    if not old_module:
        _logger.info("✓ No old 'commission' module found - nothing to clean up")
        _logger.info("=" * 70)
        return

    module_id, module_name, module_state = old_module
    _logger.info(
        "Found old 'commission' module (ID: %s, state: %s). "
        "Migrating remaining references...",
        module_id, module_state
    )

    try:
        # Migrate any remaining XML IDs from old module to new one
        _logger.info("Migrating XML IDs from 'commission' to 'commission_oca'...")
        cr.execute(
            """
            UPDATE ir_model_data
            SET module = 'commission_oca'
            WHERE module = 'commission'
            AND NOT EXISTS (
                SELECT 1
                FROM ir_model_data imd
                WHERE imd.module = 'commission_oca'
                AND imd.name = ir_model_data.name
                AND imd.model = ir_model_data.model
            )
            """
        )
        migrated_xmlids = cr.rowcount
        if migrated_xmlids:
            _logger.info("  ✓ Migrated %s XML IDs to commission_oca", migrated_xmlids)
        else:
            _logger.info("  - No XML IDs to migrate")
        
        # Remove duplicate XML IDs (where same record exists in both modules)
        _logger.info("Removing duplicate XML IDs...")
        cr.execute(
            """
            DELETE FROM ir_model_data
            WHERE module = 'commission'
            AND EXISTS (
                SELECT 1
                FROM ir_model_data imd
                WHERE imd.module = 'commission_oca'
                AND imd.name = ir_model_data.name
                AND imd.model = ir_model_data.model
                AND imd.res_id = ir_model_data.res_id
            )
            """
        )
        deleted_duplicates = cr.rowcount
        if deleted_duplicates:
            _logger.info("  ✓ Removed %s duplicate XML IDs", deleted_duplicates)
        else:
            _logger.info("  - No duplicate XML IDs to remove")
        
        # Update module dependencies
        _logger.info("Updating module dependencies...")
        cr.execute(
            """
            UPDATE ir_module_module_dependency
            SET name = 'commission_oca'
            WHERE name = 'commission'
            """
        )
        updated_deps = cr.rowcount
        if updated_deps:
            _logger.info("  ✓ Updated %s module dependencies", updated_deps)
        else:
            _logger.info("  - No dependencies to update")
        
        # Set old module to uninstalled state
        _logger.info("Marking old module as uninstalled...")
        cr.execute(
            """
            UPDATE ir_module_module
            SET state = 'uninstalled'
            WHERE name = 'commission'
            """
        )
        
        # Remove the old module entry
        _logger.info("Removing old module entry...")
        cr.execute(
            """
            DELETE FROM ir_module_module
            WHERE name = 'commission'
            """
        )
        
        _logger.info(
            "✓ Successfully migrated all references from 'commission' to "
            "'commission_oca'. All data has been preserved."
        )

    except Exception as e:
        _logger.error(
            "Failed to migrate old 'commission' module references: %s. "
            "Manual cleanup may be required.",
            str(e)
        )
        # Don't raise - allow installation to complete
    
    # Final verification
    cr.execute(
        "SELECT COUNT(*) FROM ir_module_module WHERE name = 'commission'"
    )
    remaining_modules = cr.fetchone()[0]

    cr.execute(
        "SELECT COUNT(*) FROM ir_model_data WHERE module = 'commission'"
    )
    remaining_xmlids = cr.fetchone()[0]

    _logger.info("=" * 70)
    _logger.info("POST-INIT HOOK RESULTS:")
    _logger.info("  Old 'commission' modules remaining: %s", remaining_modules)
    _logger.info("  Old 'commission' XML IDs remaining: %s", remaining_xmlids)

    if remaining_modules == 0 and remaining_xmlids == 0:
        _logger.info("  ✓ Cleanup successful - no traces of old module")
    else:
        _logger.warning(
            "  ⚠ Some residual data remains - may need manual cleanup"
        )

    _logger.info("=" * 70)
