# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Final cleanup script to ensure complete migration.

    This end-migration script runs after all modules have been loaded.
    It performs a final cleanup to ensure:
    - No residual 'commission' module exists
    - No duplicate XML IDs remain
    - All references point to 'commission_oca'
    
    This is particularly useful if the pre/post scripts didn't complete
    the cleanup properly on first run.
    """
    _logger.info("=" * 70)
    _logger.info("FINAL CLEANUP: Ensuring complete migration to commission_oca")
    _logger.info("=" * 70)

    # 1. Check and remove old 'commission' module
    cr.execute(
        """
        SELECT id, name, state, latest_version
        FROM ir_module_module
        WHERE name = 'commission'
        """
    )
    old_modules = cr.fetchall()
    
    if old_modules:
        _logger.warning(
            f"Found {len(old_modules)} 'commission' module entries that need removal"
        )
        for module_id, name, state, version in old_modules:
            _logger.info(
                f"Removing old 'commission' module: "
                f"ID={module_id}, state={state}, version={version}"
            )
            
            # Remove module dependencies first
            cr.execute(
                """
                DELETE FROM ir_module_module_dependency 
                WHERE module_id = %s OR name = 'commission'
                """,
                (module_id,)
            )
            deleted_deps = cr.rowcount
            if deleted_deps:
                _logger.info(f"  - Removed {deleted_deps} module dependencies")
            
            # Remove the module entry
            cr.execute(
                "DELETE FROM ir_module_module WHERE id = %s",
                (module_id,)
            )
            _logger.info(f"  - Removed module entry")
    else:
        _logger.info("✓ No old 'commission' module found (good)")

    # 2. Clean up duplicate or orphaned XML IDs
    cr.execute(
        """
        SELECT id, name, model, res_id
        FROM ir_model_data
        WHERE module = 'commission'
        ORDER BY model, name
        """
    )
    old_xmlids = cr.fetchall()
    
    if old_xmlids:
        _logger.warning(
            f"Found {len(old_xmlids)} XML IDs still using 'commission' module"
        )
        
        fixed_count = 0
        removed_count = 0
        
        for xmlid_id, name, model, res_id in old_xmlids:
            # Check if there's a corresponding XML ID in commission_oca
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
                new_xmlid_id, new_res_id = new_xmlid
                if res_id == new_res_id:
                    # Perfect duplicate - safe to remove old one
                    cr.execute(
                        "DELETE FROM ir_model_data WHERE id = %s",
                        (xmlid_id,)
                    )
                    removed_count += 1
                    _logger.debug(
                        f"  - Removed duplicate: commission.{name} "
                        f"(exists as commission_oca.{name})"
                    )
                else:
                    # Different res_id - something is wrong, log it
                    _logger.error(
                        f"  - CONFLICT: commission.{name} (res_id={res_id}) vs "
                        f"commission_oca.{name} (res_id={new_res_id})"
                    )
            else:
                # No corresponding XML ID in new module - migrate it
                cr.execute(
                    """
                    UPDATE ir_model_data
                    SET module = 'commission_oca'
                    WHERE id = %s
                    """,
                    (xmlid_id,)
                )
                fixed_count += 1
                _logger.info(
                    f"  - Migrated orphan: commission.{name} → commission_oca.{name}"
                )
        
        _logger.info(
            f"XML ID cleanup: {fixed_count} migrated, {removed_count} duplicates removed"
        )
    else:
        _logger.info("✓ No old 'commission' XML IDs found (good)")

    # 3. Final verification
    _logger.info("-" * 70)
    _logger.info("FINAL VERIFICATION:")
    _logger.info("-" * 70)
    
    # Check modules
    cr.execute(
        """
        SELECT name, state
        FROM ir_module_module
        WHERE name IN ('commission', 'commission_oca')
        ORDER BY name
        """
    )
    modules = cr.fetchall()
    for name, state in modules:
        status = "✓" if name == "commission_oca" else "✗"
        _logger.info(f"{status} Module '{name}': {state}")
    
    # Check XML IDs count
    for module_name in ['commission', 'commission_oca']:
        cr.execute(
            "SELECT COUNT(*) FROM ir_model_data WHERE module = %s",
            (module_name,)
        )
        count = cr.fetchone()[0]
        status = "✓" if (module_name == 'commission_oca' and count > 0) or \
                       (module_name == 'commission' and count == 0) else "✗"
        _logger.info(f"{status} XML IDs in '{module_name}': {count}")
    
    # Check dependencies
    cr.execute(
        """
        SELECT DISTINCT m.name
        FROM ir_module_module m
        JOIN ir_module_module_dependency d ON d.module_id = m.id
        WHERE d.name = 'commission'
        """
    )
    modules_depending_on_old = cr.fetchall()
    if modules_depending_on_old:
        _logger.warning(
            f"✗ Found {len(modules_depending_on_old)} modules still depending on 'commission':"
        )
        for (mod_name,) in modules_depending_on_old:
            _logger.warning(f"    - {mod_name}")
            # Fix the dependency
            cr.execute(
                """
                UPDATE ir_module_module_dependency
                SET name = 'commission_oca'
                WHERE name = 'commission'
                AND module_id IN (
                    SELECT id FROM ir_module_module WHERE name = %s
                )
                """,
                (mod_name,)
            )
        _logger.info("  Fixed dependencies to point to 'commission_oca'")
    else:
        _logger.info("✓ No modules depending on old 'commission' module")
    
    cr.execute(
        """
        SELECT DISTINCT m.name
        FROM ir_module_module m
        JOIN ir_module_module_dependency d ON d.module_id = m.id
        WHERE d.name = 'commission_oca'
        """
    )
    modules_depending_on_new = cr.fetchall()
    _logger.info(
        f"✓ {len(modules_depending_on_new)} modules correctly depend on 'commission_oca'"
    )

    _logger.info("=" * 70)
    _logger.info("CLEANUP COMPLETED")
    _logger.info("=" * 70)
