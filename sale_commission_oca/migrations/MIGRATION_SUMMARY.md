# Migration Summary: sale_commission → sale_commission_oca

## Overview

This migration handles the module rename from `sale_commission` to `sale_commission_oca` in Odoo 18.0.

## Module Rename

The module was renamed to follow OCA naming conventions where all OCA modules should have the `_oca` suffix to distinguish them from other modules, particularly to avoid conflicts with the enterprise module `sale_commission`.

### Previous name (Odoo 17.0 and earlier)
- `sale_commission`

### New name (Odoo 18.0+)
- `sale_commission_oca`

## Conflict Analysis with Enterprise Module

### Enterprise Module: `sale_commission`
The Odoo Enterprise edition includes a module named `sale_commission` with completely different functionality:

**Enterprise module models:**
- `sale.commission.plan` - Commission plans with targets and achievements
- `sale.commission.achievement` - Manual adjustments for salesperson achievements
- `sale.commission.plan.achievement` - Achievement types (amount sold, invoiced, qty, margin)
- `sale.commission.report` - Commission reports

**OCA module models:**
- `sale.order.line.agent` - Agent details for commission lines in sale orders
- Extends `sale.order` and `sale.order.line` with commission functionality

**Conclusion:** ✅ **NO MODEL CONFLICTS** - The two modules use completely different model structures and can coexist. The rename to `sale_commission_oca` eliminates the only potential conflict (module name).

## Migration Scripts

### pre-migration.py

This script is executed **before** the new module code is loaded. It performs:

1. **Module Rename**: Uses `util.rename_module()` to rename the module from `sale_commission` to `sale_commission_oca`
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
- ✅ All XML IDs (from `sale_commission.*` to `sale_commission_oca.*`)
- ✅ Security groups and access rights
- ✅ Menu items and actions
- ✅ Views and their references
- ✅ Models and fields metadata
- ✅ Translations
- ✅ Data records owned by the module
- ✅ Database constraints and indexes

## Models

No model name changes occurred. All models remain the same:
- `sale.order` (extended)
- `sale.order.line` (extended with `commission.mixin`)
- `sale.order.line.agent` (new model in this module)

## Dependencies

### Module Dependencies
The module depends on:
- `sale` - Core sales module
- `account_commission_oca` - OCA commission base module (already migrated)

### Dependent Modules
The following modules depend on `sale_commission_oca` and will have their dependencies automatically updated:
- `sale_commission_salesman` (will become `sale_commission_salesman` if renamed, or update dependency)
- Any custom modules depending on the old `sale_commission`

## Compatibility

### Odoo.sh
These scripts are designed to run automatically on Odoo.sh during the upgrade process.

### Enterprise Compatibility
- ✅ **Compatible** with enterprise `sale_commission` module
- ✅ Can be installed alongside enterprise module
- ✅ No model name conflicts
- ✅ No XML ID conflicts after rename

### Installation Requirements
The migration requires the `odoo-upgrade-util` library to be available. On Odoo.sh, this is automatically available in the upgrade path.

For local testing, ensure the upgrade-util is in your upgrade path:
```bash
odoo-bin --upgrade-path=/path/to/upgrade-util/src,[other-paths]
```

## Testing

To test this migration locally:

1. Install the old module version (`sale_commission` from 17.0)
2. Create some test data (sale orders with commissions, agents, etc.)
3. Run the upgrade:
   ```bash
   odoo-bin -d DATABASE -u sale_commission_oca \
     --upgrade-path=/path/to/upgrade-util/src \
     --stop-after-init
   ```
4. Verify that:
   - The module is now named `sale_commission_oca`
   - All data is preserved
   - All XML IDs have been updated
   - All menu items and views work correctly
   - Commission agents and lines are correctly displayed in sales orders
   - Commission amounts are correctly calculated

## Notes

- The migration is idempotent: it can be run multiple times without causing issues
- If the old module (`sale_commission`) is not installed, the migration is skipped
- All customizations and data are preserved during the migration
- Third-party modules depending on `sale_commission` will need to update their dependencies to `sale_commission_oca`
- The enterprise module `sale_commission` can be installed alongside this module without conflicts

## Related Modules

This migration is part of a larger rename effort in the commission suite:
- `commission` → `commission_oca` (already migrated)
- `account_commission` → `account_commission_oca` (already migrated)
- `sale_commission` → `sale_commission_oca` (this migration)
- `hr_commission` → `hr_commission_oca` (separate migration if exists)

## Version Comparison: V17 vs V18

### Changes Identified
After comparing with the V17 version from OCA repository, the module structure remains essentially the same:

**Models (unchanged):**
- `sale.order` - Extended with commission fields
- `sale.order.line` - Extended with agent management
- `sale.order.line.agent` - Commission line details

**Key Fields (unchanged):**
- `commission_total` - Total commissions on sale order
- `partner_agent_ids` - Agents assigned to order
- `agent_ids` - Agents per order line
- `commission_free` - Flag to exclude from commissions

**Functionality (unchanged):**
- Commission calculation based on sale order lines
- Agent auto-population from customer configuration
- Transfer of commission data to invoice lines
- Settlement creation from sale order commissions

**No Breaking Changes Detected** - The migration only needs to handle the module rename.

## References

- [Odoo Upgrade Scripts Documentation](https://www.odoo.com/documentation/18.0/developer/reference/upgrades/upgrade_scripts.html)
- [Odoo Upgrade Utils Documentation](https://www.odoo.com/documentation/18.0/developer/reference/upgrades/upgrade_utils.html)
- [OCA Commission Repository](https://github.com/OCA/commission)
- [Enterprise Sale Commission Module](https://github.com/elepe-servicios/enterprise/tree/18.0/sale_commission)
