# Migration from V17 to V18: Module Rename

## Summary

In version 18.0, the module has been renamed from `commission` to `commission_oca` to follow OCA naming conventions.

## Automatic Cleanup Mechanisms

This module includes **multiple safety layers** to ensure the old `commission` module is completely removed during migration:

### 1. Migration Scripts (Run Once During Upgrade)

Located in `migrations/18.0.2.0.0/`:

- **pre-migration.py**: Renames the module before loading
- **post-migration.py**: Cleans duplicates and orphaned XML IDs
- **end-cleanup.py**: Final verification and comprehensive cleanup

These scripts execute automatically when upgrading from V17 to V18 on Odoo.sh.

### 2. Post-Installation Hook (Runs Every Install/Update)

Located in `hooks.py`:

The `post_init_hook` function provides an additional safety layer that runs **every time** the module is:
- Installed for the first time
- Updated to a new version
- Upgraded as part of an Odoo.sh platform upgrade

#### What the Hook Does

```python
def post_init_hook(cr, registry):
    """
    Post-installation hook to ensure the old 'commission' module is removed.
    
    This hook runs every time the module is installed or updated, providing
    a safety net in case:
    - Migration scripts didn't execute
    - Database was restored from backup
    - Module was manually installed instead of upgraded
    """
```

The hook:
1. Checks if the old `commission` module exists in the database
2. If found, uses `odoo.upgrade.util.remove_module()` to remove it completely
3. Cleans any remaining XML IDs from the old module
4. Provides detailed logging for troubleshooting

#### Why Both Migration Scripts AND a Hook?

| Mechanism | When It Runs | Purpose |
|-----------|--------------|---------|
| **Migration Scripts** | Once, during version upgrade | Primary cleanup during V17→V18 upgrade |
| **Post-Installation Hook** | Every install/update | Safety net for edge cases |

### Edge Cases Handled by the Hook

1. **Database restored from V17 backup**: Migration scripts won't run again, but hook will execute on module update
2. **Manual module installation**: If someone manually installs `commission_oca` without upgrading, hook ensures cleanup
3. **Failed migration**: If migration scripts partially failed, hook provides recovery
4. **Odoo.sh automatic updates**: Hook runs during platform upgrades as an additional verification

## For Developers

### Registering the Hook

In `__manifest__.py`:
```python
{
    'name': 'Commission OCA',
    'version': '18.0.2.0.0',
    # ... other manifest data ...
    'post_init_hook': 'post_init_hook',
}
```

In `__init__.py`:
```python
from . import models
from . import wizards
from .hooks import post_init_hook
```

### Hook Execution Log

The hook provides detailed logging:

```
[HOOK] Starting post-installation cleanup for commission_oca module
[HOOK] Checking if old 'commission' module exists...
[HOOK] ✓ Old 'commission' module found - proceeding with removal
[HOOK] ✓ Successfully removed old 'commission' module
[HOOK] Cleaning remaining XML IDs from old module...
[HOOK] ✓ Removed 15 XML IDs from old module
[HOOK] ✓ Post-installation cleanup completed successfully
```

## Migration Documentation

For complete migration documentation, see:
- `migrations/18.0.2.0.0/README.md` - Detailed migration guide
- `migrations/18.0.2.0.0/TROUBLESHOOTING.md` - Problem resolution guide
- `migrations/MIGRATION_SUMMARY.md` - Technical summary

## Testing

After upgrading or installing:

1. Check module state:
```sql
SELECT name, state FROM ir_module_module 
WHERE name IN ('commission', 'commission_oca');
```

Expected result:
- `commission_oca`: `installed`
- `commission`: No rows (completely removed)

2. Check XML IDs:
```sql
SELECT COUNT(*) FROM ir_model_data WHERE module = 'commission';
```

Expected result: `0` (no XML IDs from old module)

## Support

If you encounter issues during migration:

1. Check Odoo logs for `[HOOK]` and `[MIGRATION]` prefixed messages
2. Review `migrations/18.0.2.0.0/TROUBLESHOOTING.md`
3. Verify both migration scripts and hook executed successfully
4. Contact OCA community if issues persist
