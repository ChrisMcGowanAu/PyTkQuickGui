"""Pure helpers for the JSON project format.

Values such as ``command`` are design-time Python names, not live Tk callback
objects.  Tkinter may transform callback values into internal Tcl command
names, so these fields must be preserved explicitly rather than reconstructed
from ``widget.cget()``.
"""

from __future__ import annotations

import json
import keyword
import os
import re
import shutil
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

FORMAT_VERSION = 2

#: Records the value a variable should start with: the text or number the
#: widget showed for it in the designer.  Written by saveWidgetAsDict and read
#: by both generators, so a variable is no longer always initialised to '0.0'.
VAR_VALUE_KEY = "var_value"

#: Attributes the designer records for its own purposes.  They are not Tk
#: options, so they must never be handed to a widget constructor - and they do
#: not appear in ``widget.keys()``, so they have to be captured explicitly.
DESIGN_ONLY_KEYS = ("tab_count", "tab_labels", VAR_VALUE_KEY)


def is_design_only(key: Any) -> bool:
    """Whether *key* is designer metadata rather than a Tk widget option."""
    return str(key) in DESIGN_ONLY_KEYS


#: The widget types a project may contain: the palette, the containers, and the
#: plain Tk widgets the designer can place.  ``fixWidgetTypeName`` accepts three
#: spellings of the same thing ("ttk::button", "ttk.Button", "tk.button"), so
#: the check normalises to the bare name.
KNOWN_WIDGET_TYPES = frozenset(
    {
        "button",
        "canvas",
        "checkbutton",
        "combobox",
        "entry",
        "frame",
        "labelframe",
        "label",
        "listbox",
        "notebook",
        "panedwindow",
        "progressbar",
        "radiobutton",
        "scale",
        "scrollbar",
        "separator",
        "sizegrip",
        "spinbox",
        "text",
        "treeview",
    }
)

#: A Tk option name.  Anything else cannot be one - and is exactly what a hand
#: crafted project file would use to break out of the widget call, which is
#: assembled as a string and evaluated.
_OPTION_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def base_widget_name(widget_type: Any) -> str:
    """Return a widget type without its namespace prefix, lower case."""
    name = str(widget_type or "").strip()
    for prefix in ("ttk::", "ttk.", "tk."):
        if name.startswith(prefix):
            return name[len(prefix) :].lower()
    return name.lower()


def is_known_widget_type(widget_type: Any) -> bool:
    """Whether *widget_type* is one this tool creates."""
    return base_widget_name(widget_type) in KNOWN_WIDGET_TYPES


def is_safe_option_key(key: Any) -> bool:
    """Whether *key* can be a Tk option name."""
    return bool(_OPTION_KEY.match(str(key or "")))


CALLBACK_KEYS = ("command", "postcommand")
VARIABLE_KEYS = ("textvariable", "variable")
PRESERVED_STRING_KEYS = CALLBACK_KEYS + VARIABLE_KEYS
RUNTIME_CALLABLE_KEYS = ("yscrollcommand", "xscrollcommand")


def format_python_call(call_expression: str, arguments: Iterable[str]) -> str:
    """Format a generated Python call with one argument per line."""
    values = [str(value) for value in arguments if str(value)]
    if not values:
        return f"{call_expression}()"
    body = "\n".join(f"    {value}," for value in values)
    return f"{call_expression}(\n{body}\n)"


def generated_dialog_defaults(
    project_name: str,
    save_directory: str,
    generated_file: str,
    home_directory: str,
    suffix: str = "",
) -> tuple[str, str]:
    """Return the output directory and filename offered when generating.

    The first suggestion is ``<home>/<project>/`` with the backend named in the
    file, so the two outputs of one project sit together and cannot be mistaken
    for each other: ``Calculator/Calculator_ttk.py`` and
    ``Calculator/Calculator_flet.py``.  Once a file has been saved, its own
    directory is offered again.
    """
    name = str(project_name).strip() or "project"
    previous_directory = os.path.dirname(generated_file) if generated_file else ""
    directory = previous_directory or save_directory or os.path.join(
        home_directory, name
    )
    filename = f"{name}_{suffix}.py" if suffix else f"{name}.py"
    return directory, filename


def write_project_json(
    file_name: str,
    file_type: str,
    project_data: Mapping[str, Any],
    backup_count: int = 5,
) -> str:
    """Atomically write a validated project and rotate prior versions.

    The live project remains in place until the complete replacement has been
    written and parsed successfully.  Returns the resulting JSON filename.
    """
    current = file_name + file_type
    temporary = current + ".tmp"
    backup_staging = current + ".backup-tmp"
    try:
        if os.path.isfile(backup_staging):
            os.unlink(backup_staging)
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(project_data, handle, indent=2, default=str)
            handle.flush()
            os.fsync(handle.fileno())
        with open(temporary, "r", encoding="utf-8") as handle:
            json.load(handle)

        if os.path.isfile(current) and backup_count > 0:
            shutil.copy2(current, backup_staging)
            for index in range(backup_count, 1, -1):
                previous = f"{file_name}-save{index - 1}{file_type}"
                destination = f"{file_name}-save{index}{file_type}"
                if os.path.isfile(previous):
                    os.replace(previous, destination)
            os.replace(backup_staging, f"{file_name}-save1{file_type}")
        os.replace(temporary, current)
        return current
    except (json.JSONDecodeError, TypeError, OSError):
        for staging_name in (temporary, backup_staging):
            try:
                if os.path.isfile(staging_name):
                    os.unlink(staging_name)
            except OSError:
                pass
        raise


def iter_attributes(
    widget_name: str, widget_data: Mapping[str, Any]
) -> Iterator[tuple[str, str]]:
    """Yield saved ``(key, value)`` attributes in their stored order."""
    try:
        count = int(widget_data.get(f"{widget_name}-KeyCount", 0))
    except (TypeError, ValueError):
        count = 0
    for index in range(max(0, count)):
        attribute = widget_data.get(f"Attribute{index}")
        if not isinstance(attribute, Mapping):
            continue
        key = str(attribute.get("Key", ""))
        if not key:
            continue
        yield key, str(attribute.get("Value", ""))


def attribute_map(widget_name: str, widget_data: Mapping[str, Any]) -> dict[str, str]:
    """Return the last saved value for each attribute key."""
    return dict(iter_attributes(widget_name, widget_data))


def remember_preserved_attributes(
    widget: Any, widget_name: str, widget_data: Mapping[str, Any]
) -> None:
    """Restore raw callback/variable names on a newly rebuilt widget."""
    saved = attribute_map(widget_name, widget_data)
    raw = getattr(widget, "_user_attrs", None)
    if not isinstance(raw, dict):
        raw = {}
        widget._user_attrs = raw
    for key in PRESERVED_STRING_KEYS:
        if key in saved:
            raw[key] = saved[key]


def preserved_widget_value(widget: Any, key: str, fallback: Any = "") -> Any:
    """Return a raw design-time value before consulting Tkinter."""
    raw = getattr(widget, "_user_attrs", {})
    if key in PRESERVED_STRING_KEYS and isinstance(raw, dict) and key in raw:
        return raw[key]
    return fallback


def remember_widget_value(widget: Any, key: str, value: Any) -> None:
    """Store a raw design-time callback or Tk-variable name."""
    if key not in PRESERVED_STRING_KEYS:
        return
    raw = getattr(widget, "_user_attrs", None)
    if not isinstance(raw, dict):
        raw = {}
        widget._user_attrs = raw
    raw[key] = "" if value is None else str(value)


def referenced_names(
    project_data: Mapping[str, Any],
    widget_order: Iterable[str],
    keys: tuple[str, ...],
    root_name: str,
) -> list[str]:
    """Return unique non-empty design names referenced by widget attributes."""
    found: list[str] = []
    seen: set[str] = set()
    for widget_name in widget_order:
        if widget_name == root_name:
            continue
        widget_data = project_data.get(widget_name)
        if not isinstance(widget_data, Mapping):
            continue
        values = attribute_map(widget_name, widget_data)
        for key in keys:
            value = values.get(key, "").strip()
            if value and value not in seen:
                seen.add(value)
                found.append(value)
    return found


def valid_python_name(value: str) -> bool:
    """Return True for a top-level Python identifier suitable for codegen."""
    return bool(value) and value.isidentifier() and not keyword.iskeyword(value)


def callback_names(
    project_data: Mapping[str, Any], widget_order: Iterable[str], root_name: str
) -> list[str]:
    return [
        name
        for name in referenced_names(
            project_data, widget_order, CALLBACK_KEYS, root_name
        )
        if valid_python_name(name)
    ]


def variable_names(
    project_data: Mapping[str, Any], widget_order: Iterable[str], root_name: str
) -> list[str]:
    return [
        name
        for name in referenced_names(
            project_data, widget_order, VARIABLE_KEYS, root_name
        )
        if valid_python_name(name)
    ]


def variable_defaults(
    project_data: Mapping[str, Any],
    widget_order: Iterable[str],
    root_name: str = "rootWidget",
) -> dict[str, str]:
    """Return ``{variable: starting value}`` captured from the designer.

    A widget bound to a ``textvariable`` or ``variable`` records the value it
    showed as ``var_value`` metadata.  The first non-empty value wins, so
    several widgets sharing one variable agree; a variable with nothing
    captured is simply absent and the generators fall back to "0.0".
    """
    defaults: dict[str, str] = {}
    for name in widget_order:
        if name == root_name:
            continue
        widget_data = project_data.get(name)
        if not isinstance(widget_data, Mapping):
            continue
        attributes = attribute_map(name, widget_data)
        variable = attributes.get("textvariable") or attributes.get("variable")
        value = attributes.get(VAR_VALUE_KEY)
        if not variable or not value:
            continue
        if valid_python_name(variable) and variable not in defaults:
            defaults[variable] = str(value)
    return defaults
