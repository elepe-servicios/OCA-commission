# Migration Summary: account_commission → account_commission_oca

## Overview

This migration handles the module rename from `account_commission` to `account_commission_oca` in Odoo 18.0.

## Module Rename

The module was renamed to follow OCA naming conventions where all OCA modules should have the `_oca` suffix to distinguish them from other modules.

### Previous name (Odoo 17.0 and earlier)
- `account_commission`

### New name (Odoo 18.0+)
- `account_commission_oca`

## Migration Scripts

### pre-migration.py

This script is executed **before** the new module code is loaded. It performs:

1. **Module Rename**: Uses `util.rename_module()` to rename the module from `account_commission` to `account_commission_oca`
2. **Automatic Reference Updates**: The utility function automatically updates:
   - Module name in `ir_module_module`
   - All XML IDs (external identifiers)
   - Model references in `ir_model`
   - Field references in `ir_model_fields`
   - View references in `ir_ui_view`
   - Security group references in `res_groups`
   - Menu items in `ir_ui_menu`
   - Actions in `ir_actions_*`
   - All `ir_model_data` entries
   - Dependencies in other modules
   - All database constraints
   - All foreign key relationships

### post-migration.py

This script is executed **after** the new module code has been loaded. Currently, no post-migration actions are needed because `util.rename_module()` handles all necessary updates automatically.

## What Gets Migrated

The following data is automatically migrated by the `rename_module` utility:

- ✅ Module registration and dependencies
- ✅ All XML IDs (from `account_commission.*` to `account_commission_oca.*`)
- ✅ Security groups and access rights
- ✅ Menu items and actions
- ✅ Views and their references
- ✅ Models and fields metadata
- ✅ Translations
- ✅ Data records owned by the module
- ✅ Database constraints and indexes

## Models

No model name changes occurred. All models remain the same:
- `commission` (from `commission_oca` module)
- `commission.settlement` (from `commission_oca` module)
- `account.move` (extended)
- `account.move.line` (extended)
- `account.invoice.line.agent` (new model in this module)
- `commission.make.invoice` (wizard)
- `invoice.commission.analysis.report` (report)

## Compatibility

### Odoo.sh
These scripts are designed to run automatically on Odoo.sh during the upgrade process.

### Installation Requirements
The migration requires the `odoo-upgrade-util` library to be available. On Odoo.sh, this is automatically available in the upgrade path.

For local testing, ensure the upgrade-util is in your upgrade path:
```bash
odoo-bin --upgrade-path=/path/to/upgrade-util/src,[other-paths]
```

## Testing

To test this migration locally:

1. Install the old module version (`account_commission` from 17.0)
2. Create some test data (invoices with commissions, settlements, etc.)
3. Run the upgrade:
   ```bash
   odoo-bin -d DATABASE -u account_commission_oca \
     --upgrade-path=/path/to/upgrade-util/src \
     --stop-after-init
   ```
4. Verify that:
   - The module is now named `account_commission_oca`
   - All data is preserved
   - All XML IDs have been updated
   - All menu items and views work correctly
   - Settlements can still be created and invoiced

## Notes

- The migration is idempotent: it can be run multiple times without causing issues
- If the old module (`account_commission`) is not installed, the migration is skipped
- All customizations and data are preserved during the migration
- Third-party modules depending on `account_commission` will need to update their dependencies to `account_commission_oca`

## Related Modules

This migration is part of a larger rename effort in the commission suite:
- `commission` → `commission_oca` (already migrated)
- `account_commission` → `account_commission_oca` (this migration)
- `sale_commission` → `sale_commission_oca` (separate migration)
- `hr_commission` → `hr_commission_oca` (separate migration)

## References

- [Odoo Upgrade Scripts Documentation](https://www.odoo.com/documentation/18.0/developer/reference/upgrades/upgrade_scripts.html)
- [Odoo Upgrade Utils Documentation](https://www.odoo.com/documentation/18.0/developer/reference/upgrades/upgrade_utils.html)
- [OCA Commission Repository](https://github.com/OCA/commission)
