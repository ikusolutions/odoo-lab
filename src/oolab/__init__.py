"""
odoo-lab (oolab) - CLI scaffolder for multi-project Odoo development workspaces.

Copyright (c) 2026 IKU Solutions SAS
Author: Yan Chirino <yan.chirino@iku.solutions>
Website: https://www.iku.solutions
License: LGPL-3.0-or-later
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("odoo-lab")
except PackageNotFoundError:
    __version__ = "0.0.0+local"

__author__ = "Yan Chirino"
__email__ = "yan.chirino@iku.solutions"
__company__ = "IKU Solutions SAS"
__website__ = "https://www.iku.solutions"
