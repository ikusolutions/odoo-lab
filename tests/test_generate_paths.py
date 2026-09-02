import json

import oolab.cli  # noqa: F401  # carga el paquete en el orden correcto (registro por side-effect)
from oolab.commands.generate import _to_win_paths, get_template_env


def test_win_paths_are_valid_json_backslash():
    win = _to_win_paths("${workspaceFolder}/tenants/cli")
    assert win == "${workspaceFolder}\\\\tenants\\\\cli"
    assert json.loads(f'"{win}"') == "${workspaceFolder}\\tenants\\cli"


def _render_launch(is_windows):
    ctx = {
        "venv_name": ".venv-v18",
        "is_windows": is_windows,
        "tenants": [
            {
                "display_name": "Cliente",
                "name": "cliente",
                "venv_name": ".venv-v18",
                "enterprise": True,
                "db_filter": "cliente-testdb",
                "addon_paths": ["tenants/cliente"],
            }
        ],
    }
    content = get_template_env().get_template("launch.json.j2").render(**ctx)
    if is_windows:
        content = _to_win_paths(content)
    return content


def test_launch_json_valid_both_platforms():
    win = _render_launch(True)
    unix = _render_launch(False)
    json.loads(win)
    json.loads(unix)
    assert "\\\\" in win  # separadores backslash en Windows
    assert "python.exe" in win
    assert "/tenants/cliente" in unix  # forward slash en Unix


if __name__ == "__main__":
    test_win_paths_are_valid_json_backslash()
    test_launch_json_valid_both_platforms()
    print("ok")
