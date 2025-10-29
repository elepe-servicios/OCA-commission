# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Rename module from 'commission' to 'commission_oca'.

    This script handles the migration when upgrading from Odoo v17 where the module
    was named 'commission' to Odoo v18 where it's renamed to 'commission_oca'.

    The script renames:
    - Module name and all its references
    - XML IDs from 'commission.' to 'commission_oca.'
    - Model references
    - Dependencies in other modules
    """
    _logger.info("Starting migration: Renaming 'commission' to 'commission_oca'")

    # Check if the old module 'commission' exists and is installed
    if not util.module_installed(cr, "commission"):
        _logger.info(
            "Module 'commission' not found or not installed. "
            "Skipping rename migration."
        )
        return

    # Rename the module and all its references
    # This will update:
    # - ir_module_module table
    # - ir_model_data (XML IDs)
    # - ir_module_module_dependency
    # - All other module dependencies
    _logger.info("Renaming module 'commission' to 'commission_oca'")
    util.rename_module(cr, "commission", "commission_oca")

    _logger.info(
        "Successfully renamed module from 'commission' to 'commission_oca'"
    )
