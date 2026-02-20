# Migration from commission to commission_oca

## Overview

This migration handles the module rename from `commission` (v17.0) to `commission_oca` (v18.0).

## Components

### Migration Scripts (run once during upgrade)

Migration scripts execute automatically during version upgrades in the following order:

1. **pre-migration.py** - Before module load
2. **post-migration.py** - After module load
3. **end-cleanup.py** - After all modules loaded

### Post-Installation Hook (runs every install/update)

The module includes a `post_init_hook` (in `hooks.py`) that runs **every time** the module is installed or updated, providing an additional safety layer to ensure the old module is completely removed.

## What does this migration do?

### Pre-migration (pre-migration.py)

Executed **before** the module is loaded:

1. **Checks** if the old module `commission` is installed
2. **Renames the module** using `util.rename_module()` which automatically updates:
   - Module name in `ir_module_module`
   - All XML IDs from `commission.*` to `commission_oca.*`
   - Module dependencies in other modules
   - All references throughout the database
3. **Cleans residual entries** that may remain after rename

### Post-migration (post-migration.py)

Executed **after** the module and its dependencies are loaded:

1. **Removes old module entries** from `ir_module_module`
2. **Cleans duplicate XML IDs** (keeps commission_oca version, removes commission version)
3. **Migrates orphan XML IDs** without duplicates to commission_oca
4. **Provides detailed logging** of all operations

### End-cleanup (end-cleanup.py)

Executed **after all modules** have been loaded and migrated:

1. **Final verification** that old module is completely removed
2. **Removes any remaining dependencies** on the old module
3. **Cleans remaining XML ID duplicates**
4. **Provides comprehensive status report** with ✓/✗ indicators

### Post-Installation Hook (hooks.py)

Executed **every time** the module is installed or updated:

1. **Checks** if old `commission` module still exists
2. **Removes it completely** using `util.remove_module()`
3. **Cleans any remaining XML IDs** from the old module
4. **Provides detailed logging** for debugging

This hook provides a safety net that ensures cleanup even if:
- Migration scripts didn't run
- Database was restored from backup
- Module was manually installed instead of upgraded

## Technical Details

### Module Rename Function

The `util.rename_module(cr, old, new)` function from odoo.upgrade.util handles:

- Renaming in `ir_module_module` table
- Updating all `ir_model_data` records (XML IDs)
- Updating `ir_module_module_dependency` records
- Updating dependencies in all dependent modules
- All other internal references

### Models Affected

All models remain with the same technical name:
- `commission`
- `commission.section`
- `commission.mixin`
- `commission.line.mixin`
- `commission.settlement`
- `commission.settlement.line`
- `commission.make.settle`

Only the **module name** and **XML ID prefixes** change.

### XML IDs Renamed

All XML IDs are automatically renamed from:
- `commission.some_xmlid` → `commission_oca.some_xmlid`

Examples:
- `commission.model_commission` → `commission_oca.model_commission`
- `commission.menu_commission` → `commission_oca.menu_commission`
- `commission.group_commission_user` → `commission_oca.group_commission_user`

### Dependencies Updated

Modules depending on `commission` will have their dependencies automatically updated to `commission_oca`:
- `account_commission_oca`
- `sale_commission_oca`
- `hr_commission_oca`
- `sale_commission_salesman`
- Any custom modules

## Execution on Odoo.sh

### Migration Scripts

These scripts will execute automatically when:

1. The database is upgraded to Odoo 18.0
2. The `commission_oca` module is being updated
3. The version in the migration folder (18.0.2.0.0) is higher than the installed version

#### Execution Order

1. **Pre-migration phase**: Runs BEFORE module code is loaded
2. **Module loading**: Odoo loads the new module code
3. **Post-migration phase**: Runs AFTER module is loaded
4. **End-migration phase**: Runs AFTER all modules are loaded

### Post-Installation Hook

The hook executes automatically **every time**:

1. The module is installed for the first time
2. The module is updated to a new version
3. An Odoo.sh upgrade is performed

This provides an additional safety layer beyond the one-time migration scripts.

## Important Notes

### For Odoo.sh Users

✅ **Safe to use**: Migration scripts and hook are designed for automatic execution on Odoo.sh  
✅ **Idempotent**: Can be run multiple times safely  
✅ **Rollback safe**: Uses transactions and checks before modifications  
✅ **Multiple safety layers**: Migration scripts + post-installation hook ensure complete cleanup

### For Module Developers

If you have custom modules depending on `commission`:

1. **Dependencies are auto-updated**: The migration automatically updates module dependencies
2. **XML IDs in code**: If you reference XML IDs in Python code, they remain unchanged (e.g., `self.env.ref('commission_oca.some_xmlid')` works the same)
3. **Inherits**: Model inheritance statements don't need changes as model names remain the same

### How the Safety Layers Work

1. **Migration scripts** (run once during upgrade):
   - pre-migration.py: Renames module and cleans residuals
   - post-migration.py: Removes duplicates and orphans
   - end-cleanup.py: Final verification and cleanup

2. **Post-installation hook** (runs every install/update):
   - Checks if old module exists
   - Removes it completely if found
   - Cleans any remaining XML IDs
   - Provides safety net for edge cases

### Migration Path

| Source Version | Target Version | Action |
|---------------|----------------|---------|
| 17.0 (commission) | 18.0 (commission_oca) | **Run these scripts** |
| 18.0 (commission_oca) | 18.0 (commission_oca) | **No migration needed** |

## Testing the Migration

### Before Production

1. **Test on a copy** of your database
2. **Verify** all commission data is intact
3. **Check** dependent modules still work
4. **Validate** reports and views display correctly

### Verification Queries

After migration, verify with:

```sql
-- Check module is renamed
SELECT name, state FROM ir_module_module WHERE name LIKE '%commission%';

-- Check XML IDs are updated
SELECT module, name FROM ir_model_data 
WHERE module IN ('commission', 'commission_oca') 
LIMIT 10;

-- Check dependencies are updated
SELECT name FROM ir_module_module 
WHERE id IN (
    SELECT module_id FROM ir_module_module_dependency 
    WHERE name = 'commission_oca'
);
```

## Troubleshooting

### If migration fails

1. **Check logs**: Look for detailed error messages
2. **Verify old module**: Ensure `commission` was installed in v17
3. **Check conflicts**: No manual changes to module names between versions

### If dependent modules fail

The migration automatically updates dependencies, but if issues occur:

1. Check that dependent modules are compatible with v18
2. Update dependent modules to their v18 versions
3. Review upgrade.log for specific errors

## References

- [Odoo Upgrade Scripts Documentation](https://www.odoo.com/documentation/18.0/developer/reference/upgrades/upgrade_scripts.html)
- [Odoo Upgrade Utils](https://www.odoo.com/documentation/18.0/developer/reference/upgrades/upgrade_utils.html)
- [OCA Commission Repository](https://github.com/OCA/commission)
