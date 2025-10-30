# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Hook executed after module installation/update.

    This hook ensures that the old 'commission' module is completely removed
    after installing or updating 'commission_oca'. This prevents conflicts and
    duplications that may occur during the migration from v17 to v18.

    The hook performs:
    1. Checks if old 'commission' module exists
    2. Uses util.remove_module() to completely remove it
    3. Cleans up any remaining references
    """
    from odoo.upgrade import util

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
        return

    module_id, module_name, module_state = old_module
    _logger.warning(
        f"Found old 'commission' module (ID: {module_id}, state: {module_state})"
    )

    # If module is installed or in any state other than uninstalled, remove it
    if module_state != "uninstalled":
        _logger.info("Removing old 'commission' module using util.remove_module()...")

        try:
            # util.remove_module completely removes the module and all its data
            # This is equivalent to uninstall + removal of all references
            util.remove_module(cr, "commission")
            _logger.info("✓ Successfully removed old 'commission' module")

        except Exception as e:
            _logger.error(
                f"Failed to remove old 'commission' module automatically: {e}"
            )
            _logger.warning(
                "The module may need to be removed manually. "
                "See TROUBLESHOOTING.md for instructions."
            )
            # Don't raise - allow installation to complete
            # The end-cleanup.py script will handle this in next update
    else:
        _logger.info("Old 'commission' module is already uninstalled")

    # Additional cleanup: ensure no residual XML IDs
    cr.execute(
        """
        SELECT COUNT(*)
        FROM ir_model_data
        WHERE module = 'commission'
        """
    )
    xmlid_count = cr.fetchone()[0]

    if xmlid_count > 0:
        _logger.warning(
            f"Found {xmlid_count} XML IDs still referencing 'commission' module"
        )
        _logger.info("Cleaning up residual XML IDs...")

        # Remove duplicate XML IDs (where same exists in commission_oca)
        cr.execute(
            """
            DELETE FROM ir_model_data
            WHERE module = 'commission'
            AND id IN (
                SELECT old.id
                FROM ir_model_data old
                INNER JOIN ir_model_data new
                    ON old.name = new.name
                    AND old.model = new.model
                    AND old.res_id = new.res_id
                WHERE old.module = 'commission'
                AND new.module = 'commission_oca'
            )
            """
        )
        removed = cr.rowcount
        if removed:
            _logger.info(f"  - Removed {removed} duplicate XML IDs")

        # Migrate orphaned XML IDs to commission_oca
        cr.execute(
            """
            UPDATE ir_model_data
            SET module = 'commission_oca'
            WHERE module = 'commission'
            AND NOT EXISTS (
                SELECT 1
                FROM ir_model_data new
                WHERE new.module = 'commission_oca'
                AND new.name = ir_model_data.name
                AND new.model = ir_model_data.model
            )
            """
        )
        migrated = cr.rowcount
        if migrated:
            _logger.info(f"  - Migrated {migrated} orphaned XML IDs to commission_oca")

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
    _logger.info(f"  Old 'commission' modules remaining: {remaining_modules}")
    _logger.info(f"  Old 'commission' XML IDs remaining: {remaining_xmlids}")

    if remaining_modules == 0 and remaining_xmlids == 0:
        _logger.info("  ✓ Cleanup successful - no traces of old module")
    else:
        _logger.warning(
            "  ⚠ Some residual data remains - see TROUBLESHOOTING.md"
        )

    _logger.info("=" * 70)
