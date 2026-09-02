import json
from pathlib import Path

import oolab.cli  # noqa: F401  # carga el paquete en el orden correcto (registro por side-effect)
from oolab.commands.generate import _rel_addon_path

WS = Path("/ws")
ADDON = WS / "tenants" / "cli"


def test_unix_uses_forward_slash():
    assert _rel_addon_path(ADDON, WS, is_windows=False) == "tenants/cli"


def test_windows_double_backslash_is_valid_json():
    rel = _rel_addon_path(ADDON, WS, is_windows=True)
    assert rel == "tenants\\\\cli"
    # embedded in a JSON string, decodes back to a single-backslash path
    assert json.loads(f'"{rel}"') == "tenants\\cli"


if __name__ == "__main__":
    test_unix_uses_forward_slash()
    test_windows_double_backslash_is_valid_json()
    print("ok")
