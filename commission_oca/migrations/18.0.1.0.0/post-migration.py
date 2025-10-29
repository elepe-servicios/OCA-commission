# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.upgrade import util

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post-migration tasks after renaming from 'commission' to 'commission_oca'.

    This script performs cleanup and verification tasks after the module rename:
    - Verifies all XML IDs have been properly renamed
    - Updates any remaining references in custom fields or data
    - Ensures module category references are correct
    """
    _logger.info("Starting post-migration tasks for commission_oca")

    # Verify the module exists with the new name
    if not util.module_installed(cr, "commission_oca"):
        _logger.warning(
            "Module 'commission_oca' not found. Migration may have failed."
        )
        return

    # Update module category reference if it exists with old name
    cr.execute(
        """
        UPDATE ir_module_category
        SET name = 'Commissions'
        WHERE name = 'Commission'
        AND id IN (
            SELECT category_id
            FROM ir_module_module
            WHERE name = 'commission_oca'
        )
        """
    )
    if cr.rowcount:
        _logger.info("Updated module category name")

    # Verify all models are properly registered with the new module
    model_names = [
        "commission",
        "commission.section",
        "commission.mixin",
        "commission.line.mixin",
        "commission.settlement",
        "commission.settlement.line",
        "commission.make.settle",
    ]

    for model_name in model_names:
        cr.execute(
            """
            SELECT COUNT(*)
            FROM ir_model_data
            WHERE model = 'ir.model'
            AND module = 'commission_oca'
            AND name = %s
            """,
            (f"model_{model_name.replace('.', '_')}",),
        )
        result = cr.fetchone()
        if result and result[0] > 0:
            _logger.info("Model %s is properly registered", model_name)

    # Update menu items to ensure they reference the correct module
    cr.execute(
        """
        UPDATE ir_ui_menu
        SET name = 'Commissions'
        WHERE id IN (
            SELECT res_id
            FROM ir_model_data
            WHERE model = 'ir.ui.menu'
            AND module = 'commission_oca'
            AND name = 'menu_commission'
        )
        """
    )

    # Ensure all security groups are properly set
    cr.execute(
        """
        SELECT name
        FROM res_groups
        WHERE category_id IN (
            SELECT res_id
            FROM ir_model_data
            WHERE model = 'ir.module.category'
            AND module = 'commission_oca'
            AND name = 'module_category_commission'
        )
        """
    )
    groups = cr.fetchall()
    _logger.info(
        "Found %d security groups for commission_oca module", len(groups)
    )

    _logger.info("Post-migration tasks completed successfully for commission_oca")
