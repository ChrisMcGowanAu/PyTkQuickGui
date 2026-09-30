"""Startup validation that must run before any Tk window is created.

The ttkbootstrap version guard used to run after ``ttk.Window()`` so that it
could report the problem in a message box.  On an incompatible install that
window never exists: ``ttk.Window(theme=…)`` raises ``TypeError`` first, and
the user sees a traceback instead of the explanation.  These helpers are kept
free of Tk so the check can run — and be tested — before anything is built.
"""

from __future__ import annotations

import importlib.metadata as metadata
from collections.abc import Callable
from typing import Any

PACKAGE = "ttkbootstrap"
MINIMUM_MAJOR = 2
UPGRADE_COMMAND = "pip install --upgrade ttkbootstrap"

_VERSION_ATTRIBUTES = ("__version__", "VERSION", "version")


def major_version(version: Any) -> int:
    """Return the major part of a version string, or 0 when unparsable."""
    try:
        return int(str(version).split(".", maxsplit=1)[0])
    except (AttributeError, TypeError, ValueError):
        return 0


def installed_version(
    module: Any = None, lookup: Callable[[str], str] | None = None
) -> str:
    """Return the installed *PACKAGE* version, best effort.

    Package metadata is preferred because it is present even when the module
    does not expose a version attribute.  ``module`` and ``lookup`` are
    injectable for testing.
    """
    resolver = lookup or metadata.version
    try:
        version = resolver(PACKAGE)
    except Exception:  # pylint: disable=broad-except
        version = ""
    if version:
        return str(version)
    for attribute in _VERSION_ATTRIBUTES:
        value = getattr(module, attribute, None)
        if value and str(value) not in ("", "0.0"):
            return str(value)
    return "0.0"


def check_ttkbootstrap(
    module: Any = None,
    lookup: Callable[[str], str] | None = None,
    minimum: int = MINIMUM_MAJOR,
) -> str | None:
    """Return an error message when ttkbootstrap is too old, else ``None``.

    The message is plain text: it is shown on the console (and in the log)
    before the application window exists, when a message box is not an option.
    """
    version = installed_version(module, lookup)
    if major_version(version) >= minimum:
        return None
    return (
        f"PyTkQuickGui requires ttkbootstrap {minimum}.0 or later.\n"
        f"Installed version: {version}\n"
        f"Please upgrade:  {UPGRADE_COMMAND}\n"
        "The application will now exit."
    )
