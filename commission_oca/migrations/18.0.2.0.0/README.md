# Migration from commission to commission_oca

## Overview

This migration handles the module rename from `commission` (v17.0) to `commission_oca` (v18.0).

## What does this migration do?

### Pre-migration (pre-migration.py)

Executed **before** the module is loaded:

1. **Checks** if the old module `commission` is installed
2. **Renames the module** using `util.rename_module()` which automatically updates:
   - Module name in `ir_module_module`
   - All XML IDs from `commission.*` to `commission_oca.*`
   - Module dependencies in other modules
   - All references throughout the database

### Post-migration (post-migration.py)

Executed **after** the module and its dependencies are loaded:

1. **Verifies** the module exists with the new name
2. **Updates** module category names if needed
3. **Validates** all models are properly registered
4. **Checks** menu items and security groups

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

These scripts will execute automatically when:

1. The database is upgraded to Odoo 18.0
2. The `commission_oca` module is being updated
3. The version in the migration folder (18.0.1.0.0) is higher than the installed version

### Execution Order

1. **Pre-migration phase**: Runs BEFORE module code is loaded
2. **Module loading**: Odoo loads the new module code
3. **Post-migration phase**: Runs AFTER module is loaded

## Important Notes

### For Odoo.sh Users

✅ **Safe to use**: These scripts are designed for automatic execution on Odoo.sh
✅ **Idempotent**: Can be run multiple times safely
✅ **Rollback safe**: Uses transactions and checks before modifications

### For Module Developers

If you have custom modules depending on `commission`:

1. **Dependencies are auto-updated**: The migration automatically updates module dependencies
2. **XML IDs in code**: If you reference XML IDs in Python code, they remain unchanged (e.g., `self.env.ref('commission_oca.some_xmlid')` works the same)
3. **Inherits**: Model inheritance statements don't need changes as model names remain the same

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
