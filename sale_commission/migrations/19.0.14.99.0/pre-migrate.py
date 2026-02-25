# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Pre-migration for the sale_commission bridge module.

EXECUTION ORDER:
  1. Odoo resolves bridge dependencies → commission_oca, account_commission_oca,
     sale_commission_oca are marked 'to install'.
  2. commission_oca installs → pre_init_hook performs V14 migration (PRIMARY).
  3. account_commission_oca installs → pre_init_hook handles accounting rename.
  4. sale_commission_oca installs → pre_init_hook handles sale rename.
  5. THIS script runs → tables already migrated → logs status + safety cleanup.

By the time this script executes, commission_oca's pre_init_hook has already
done the heavy lifting (table renames, model reference updates, field renames,
XML ID cleanup). This script is ONLY a safety net and logging checkpoint.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Bridge pre-migrate: log + safety check."""
    msg = (
        "\n"
        "=" * 70 + "\n"
        "SALE_COMMISSION BRIDGE: pre-migrate starting\n"
        "  Installed version: %s\n"
        "  Target version: 19.0.14.99.0\n"
        "=" * 70
    ) % (version or "unknown",)
    _logger.info(msg)
    print(msg)

    # At this point, commission_oca's hook should have already renamed tables.
    # Check if that happened:
    v14_still_exists = _table_exists(cr, "sale_commission")
    v19_exists = _table_exists(cr, "commission")

    if v19_exists and not v14_still_exists:
        msg = (
            ">>> Bridge pre-migrate: V14 tables already migrated by "
            "commission_oca hook. Nothing to do."
        )
        _logger.info(msg)
        print(msg)
    elif v14_still_exists:
        # This should NOT happen if commission_oca's hook ran correctly.
        # Log a warning — the ORM will create new tables and data may be lost.
        msg = (
            ">>> WARNING: V14 table 'sale_commission' still exists! "
            "commission_oca's pre_init_hook may not have run. "
            "The ORM may create duplicate tables."
        )
        _logger.warning(msg)
        print(msg)
    else:
        msg = ">>> Bridge pre-migrate: No V14 or V19 commission tables found."
        _logger.info(msg)
        print(msg)

    msg = "SALE_COMMISSION BRIDGE: pre-migrate completed"
    _logger.info(msg)
    print(">>> " + msg)


def _table_exists(cr, table):
    cr.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_name = %s AND table_schema = 'public'",
        (table,),
    )
    return bool(cr.fetchone())
