# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migration script for renaming sale_commission to sale_commission_oca.

    This script handles the module rename from sale_commission to sale_commission_oca
    in Odoo 18.0. The rename is necessary to follow OCA naming conventions and avoid
    conflicts with the enterprise module sale_commission.
    """
    # Check if the old module exists and needs to be renamed
    if not util.module_installed(cr, "sale_commission"):
        _logger.info(
            "Module 'sale_commission' not installed, skipping migration to "
            "'sale_commission_oca'"
        )
        return

    _logger.info(
        "Renaming module 'sale_commission' to 'sale_commission_oca' and updating "
        "all references"
    )

    # Rename the module and all its references
    # This utility function automatically handles:
    # - Module name in ir_module_module
    # - All XML IDs (external identifiers)
    # - Model references
    # - View references
    # - Security group references
    # - Menu items
    # - Actions
    # - Dependencies in other modules
    # - Database constraints
    # - Foreign key relationships
    util.rename_module(cr, "sale_commission", "sale_commission_oca")

    _logger.info(
        "Successfully renamed module 'sale_commission' to 'sale_commission_oca'"
    )
