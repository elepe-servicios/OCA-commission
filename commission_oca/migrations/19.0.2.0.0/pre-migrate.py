# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Pre-migration script for commission_oca 19.0.2.0.0.

This script runs ONLY when the module is being UPGRADED (not on fresh install).
It handles the field rename agent_ids -> commission_agent_ids introduced in V19.

Cross-version migrations (V14 -> V19, V16-V18 -> V19) are handled by
the pre_init_hook in hooks.py instead.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Rename agent_ids -> commission_agent_ids on res.partner.

    This runs when upgrading from an earlier 19.0 version of commission_oca
    (e.g., 19.0.1.x.x -> 19.0.2.0.0) where agent_ids was not yet renamed.
    """
    _logger.info(
        "commission_oca pre-migrate 19.0.2.0.0: checking field rename "
        "(installed version: %s)",
        version,
    )

    try:
        from odoo.upgrade import util
    except ImportError:
        _logger.warning("upgrade-util not available, skipping field rename")
        return

    # Only rename if the old field still exists
    cr.execute(
        "SELECT 1 FROM ir_model_fields "
        "WHERE model = 'res.partner' AND name = 'agent_ids'"
    )
    if not cr.fetchone():
        _logger.info("Field agent_ids already renamed or absent - nothing to do")
        return

    _logger.info("Renaming field res.partner.agent_ids -> commission_agent_ids")
    util.rename_field(
        cr,
        "res.partner",
        "agent_ids",
        "commission_agent_ids",
        update_references=True,
    )




