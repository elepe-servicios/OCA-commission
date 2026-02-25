# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Post-migration script for sale_commission to sale_commission_oca rename.

    This script is executed after the new module code has been loaded.
    Currently, no post-migration actions are needed because util.rename_module()
    in the pre-migration script handles all necessary updates automatically.
    """
    _logger.info(
        "Post-migration for sale_commission_oca completed. "
        "All references were updated in pre-migration."
    )
