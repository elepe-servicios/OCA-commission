# Copyright 2025 Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# MIGRATION BRIDGE MODULE
# =======================
# This module exists ONLY to handle the V14 → V19 migration when using
# ``odoo-bin -u all``.
#
# WHY THIS IS NEEDED:
# In V14, the OCA ``sale_commission`` module contained ALL commission
# functionality. In V19, it's been split into commission_oca,
# account_commission_oca, and sale_commission_oca.
#
# With ``-u all``, Odoo only upgrades modules already installed in the DB.
# Since the V19 modules don't exist in the V14 DB, they're never triggered.
# This bridge uses the OLD name ``sale_commission`` so Odoo finds it as an
# upgrade for the V14 module.
#
# HOW IT WORKS:
# The bridge depends on the three V19 OCA modules. During ``-u all``, Odoo
# resolves dependencies and INSTALLS them first (topological order). Each
# V19 module's ``pre_init_hook`` performs the actual migration work:
#   1. commission_oca's hook renames V14 tables, models, and fields.
#   2. account_commission_oca's hook handles accounting module rename.
#   3. sale_commission_oca's hook handles sale commission module rename.
# After the dependencies are installed, the bridge's own migration scripts
# run (they're essentially no-ops since the hooks already did everything).
#
# ENTERPRISE CONFLICT (Odoo.sh):
# Odoo 19 Enterprise has its own ``sale_commission`` module (with different
# models: sale.commission.plan, sale.commission.achievement).
#
# On Odoo.sh, you CANNOT control the addons path order, so Enterprise's
# ``sale_commission`` may be found INSTEAD of this bridge. This is FINE:
#   - Enterprise upgrades its own module (creates sale.commission.plan, etc.)
#   - V14 orphan tables (sale_commission, etc.) remain in the database.
#   - The user installs commission_oca manually from the Apps menu.
#   - commission_oca's pre_init_hook detects V14 tables and migrates them.
#   - Enterprise's data is NOT touched (all cleanup is Enterprise-safe).
#
# In environments where you CAN control addons path order:
#   - Place OCA addons BEFORE Enterprise so this bridge is found first.
#   - The bridge auto-installs the three V19 OCA modules via dependencies.
#
# POST-MIGRATION:
# After the migration is complete, this bridge can be uninstalled and the
# ``sale_commission/`` directory removed from the addons path.
{
    "name": "Sale Commission (V14 Migration Bridge)",
    "version": "19.0.14.99.0",
    "category": "Hidden",
    "summary": "V14→V19 migration bridge - auto-installs OCA commission modules",
    "author": "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "commission_oca",
        "account_commission_oca",
        "sale_commission_oca",
    ],
    "installable": True,
    "auto_install": False,
}
