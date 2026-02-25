# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Pre-migration script for sale_commission_oca 19.0.1.6.0.

This runs during UPGRADES (not fresh installs). For cross-version migration
(V14 or V16-V18), use the pre_init_hook in hooks.py instead.

This script handles intra-V19 upgrades and cleanup of old OCA sale_commission
references to avoid conflicts with Enterprise sale_commission.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Pre-migration for sale_commission_oca intra-V19 upgrade."""
    _logger.info(
        "sale_commission_oca pre-migrate 19.0.1.6.0 "
        "(installed version: %s)",
        version,
    )

    # Clean up any residual 'sale_commission' references (OCA module)
    cr.execute(
        "UPDATE ir_model_data SET module = 'sale_commission_oca' "
        "WHERE module = 'sale_commission'"
    )
    if cr.rowcount:
        _logger.info(
            "Moved %d orphaned XML IDs from 'sale_commission'",
            cr.rowcount,
        )

    # Update dependencies pointing to old module name
    cr.execute(
        "UPDATE ir_module_module_dependency SET name = 'sale_commission_oca' "
        "WHERE name = 'sale_commission'"
    )
