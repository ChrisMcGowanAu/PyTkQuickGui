"""Build every saved project as Flet code and check that Flet accepts it.

The Flet generator emits controls in code, and several mappings rest on
measured Flet behaviour (a multiline field is sized by ``min_lines``, a text
style with no weight is drawn bold, Material paints a checkbox fill in every
state, the Tabs API takes a ``TabBar``/``TabBarView`` content).  A Flet upgrade
can change any of those without changing the major version, so this tool
generates and *builds* every project the designer has and reports what breaks.

It needs flet installed and no display.  Run it after a generator change or a
Flet upgrade:

    python3 tools/smoke_flet_generated.py                 # the saved projects
    python3 tools/smoke_flet_generated.py --all           # including backups
    python3 tools/smoke_flet_generated.py ~/projects/*.json

Exits non-zero when anything fails, so it can go in a CI job.
"""

from __future__ import annotations

import ast
import glob
import io
import os
import sys
from contextlib import redirect_stderr

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet_generator  # noqa: E402  # pylint: disable=wrong-import-position

try:
    import flet as ft
except ImportError:  # pragma: no cover - a clear message beats a traceback
    sys.exit("flet is not installed: pip install -r requirments.txt")

try:
    import importlib.metadata as _metadata

    FLET_VERSION = _metadata.version("flet")
except Exception:  # pragma: no cover - metadata is best effort
    FLET_VERSION = getattr(ft, "__version__", "unknown")

#: Modes each project is generated in: the default, the exact-position Grid
#: output, and one that omits every widget a tool default could skip.
MODES = (
    ("default", {}),
    ("absolute-grid", {"grid_mode": "absolute"}),
    (
        "skip-optional",
        {
            "policy": {
                "default": "full",
                "canvas": "skip",
                "listbox": "skip",
                "scrollbar": "skip",
                "text": "skip",
                "treeview": "skip",
            }
        },
    ),
)


class FakeWindow:
    """Stands in for page.window, which a generated program sets."""

    width = None
    height = None
    resizable = None


class FakePage:
    """Stands in for ft.Page so the controls are built without a session."""

    def __init__(self) -> None:
        self.title = None
        self.padding = None
        self.bgcolor = None
        self.theme = None
        self.theme_mode = None
        self.window = FakeWindow()
        self.controls: list = []

    def add(self, *controls) -> None:
        self.controls.extend(controls)

    def update(self) -> None:
        pass


def widget_order(project_data):
    """Return the widget names in the order the designer creates them."""
    names = [
        name
        for name, data in project_data.items()
        if isinstance(data, dict) and "WidgetName" in data
    ]
    names.sort(key=lambda name: int(name[6:]) if name[6:].isdigit() else 0)
    return ["rootWidget"] + names


def build_program(source):
    """Execute *source* with ft.run stubbed and build the page.

    Returns the page, or raises whatever Flet raised: constructing the controls
    is the check, so an invalid keyword or value has to surface.
    """
    namespace: dict = {}
    captured: dict = {}
    original_run = ft.run
    ft.run = lambda entry, *args, **kwargs: captured.setdefault("main", entry)
    try:
        with redirect_stderr(io.StringIO()):  # the version guard writes there
            # Running the generated module is the whole point of the tool.
            exec(  # noqa: S102  # pylint: disable=exec-used
                compile(source, "<generated flet>", "exec"), namespace
            )
    finally:
        ft.run = original_run
    entry = captured.get("main")
    if entry is None:
        raise AssertionError("the generated program never called ft.run()")
    page = FakePage()
    entry(page)
    return page


def check_project(path):
    """Return failure descriptions for one project file, or None if not one."""
    import json

    failures = []
    try:
        with open(path, encoding="utf-8") as handle:
            project_data = json.load(handle)
    except (OSError, ValueError) as error:
        return [f"cannot read the project: {error}"]
    if not isinstance(project_data, dict) or "widgetCount" not in project_data:
        return None  # not a project file (a tool default, a theme, ...)
    order = widget_order(project_data)
    for label, options in MODES:
        try:
            source = flet_generator.emit_program(
                project_data, order, "rootWidget", **options
            )
            ast.parse(source)
        except Exception as error:  # noqa: BLE001 - any failure is a finding
            failures.append(f"{label}: generation failed: {error!r}")
            continue
        try:
            build_program(source)
        except Exception as error:  # noqa: BLE001
            failures.append(f"{label}: Flet refused the program: {error!r}")
    return failures


def main(argv) -> int:
    args = list(argv)
    include_backups = "--all" in args
    args = [arg for arg in args if arg != "--all"]
    if args:
        paths = [path for pattern in args for path in sorted(glob.glob(pattern))]
    else:
        paths = sorted(glob.glob(os.path.expanduser("~/.config/pytkgui/*/*.json")))
        if not include_backups:
            paths = [p for p in paths if "-save" not in os.path.basename(p)]

    print(f"flet {FLET_VERSION}: checking {len(paths)} file(s)")
    checked = 0
    broken: set[str] = set()
    failures: list[tuple[str, str]] = []
    for path in paths:
        problems = check_project(path)
        if problems is None:
            continue  # not a project file
        checked += 1
        for problem in problems:
            broken.add(os.path.basename(path))
            failures.append((os.path.basename(path), problem))
    for name, problem in failures[:20]:
        print(f"  FAIL {name}: {problem}")
    if len(failures) > 20:
        print(f"  ... and {len(failures) - 20} more")
    print(
        f"{checked - len(broken)} of {checked} project(s) built cleanly, "
        f"{len(broken)} with failures"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
