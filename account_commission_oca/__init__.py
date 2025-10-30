from . import models
from . import wizards
from . import report


def post_init_hook(cr, registry):
    """Remove old account_commission module if it exists.
    
    This hook is executed after the module is installed or updated.
    It ensures that the old 'account_commission' module is completely
    removed from the system to avoid duplicates and conflicts.
    """
    from odoo.upgrade import util
    import logging
    
    _logger = logging.getLogger(__name__)
    
    # Check if the old module still exists
    if util.module_installed(cr, "account_commission"):
        _logger.info(
            "Old module 'account_commission' found. Proceeding to remove it."
        )
        
        try:
            # Use remove_module to completely eliminate the old module
            util.remove_module(cr, "account_commission")
            _logger.info(
                "Successfully removed old module 'account_commission'. "
                "Only 'account_commission_oca' should remain."
            )
        except Exception as e:
            _logger.warning(
                "Could not remove old module 'account_commission': %s. "
                "Manual cleanup may be required.",
                str(e)
            )
    else:
        _logger.info(
            "Old module 'account_commission' not found. No cleanup needed."
        )
