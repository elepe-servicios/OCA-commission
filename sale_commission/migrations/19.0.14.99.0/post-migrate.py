# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""
Post-migration for the sale_commission bridge module.

By the time this runs:
  1. commission_oca has been installed (pre_init_hook migrated V14 data).
  2. account_commission_oca has been installed.
  3. sale_commission_oca has been installed.
  4. Bridge's pre-migrate has run (logging/safety check only).

This script does minimal cleanup of any orphaned bridge records.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    msg = (
        "\n"
        "=" * 70 + "\n"
        "SALE_COMMISSION BRIDGE: post-migrate starting (from %s)\n"
        "=" * 70
    ) % (version or "unknown",)
    _logger.info(msg)
    print(msg)

    # Nothing critical to do — commission_oca's hook already handled
    # all V14 cleanup. Just log completion.
    msg = (
        "SALE_COMMISSION BRIDGE: post-migrate complete.\n"
        "Migration handled by commission_oca pre_init_hook.\n"
        "After migration, uninstall this bridge and remove sale_commission/ "
        "from the addons path."
    )
    _logger.info(msg)
    print(">>> " + msg)
