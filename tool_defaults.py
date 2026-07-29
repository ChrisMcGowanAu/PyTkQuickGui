"""Tool-wide Grid defaults and their JSON persistence."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

FILE_NAME = "tool_defaults.json"
FORMAT_VERSION = 1

GRID_DEFAULTS: dict[str, Any] = {
    "gridRows": 25,
    "gridCols": 25,
    "gridLineColor": "",
    "gridRowMinsize": "2.5m",
    "gridColMinsize": "5m",
    "gridRowPad": "2.5m",
    "gridColPad": "5m",
}

_BASE_LAYOUT = {
    "columnspan": 2,
    "rowspan": 1,
    "padx": 2,
    "pady": 2,
    "ipadx": 0,
    "ipady": 0,
    "sticky": "nsew",
}

# These defaults deliberately use the names returned by fixWidgetName(), in
# lower case. They are also written to tool_defaults.json so they can be tuned
# without changing the application source.
GRID_WIDGET_DEFAULTS: dict[str, dict[str, Any]] = {
    "default": deepcopy(_BASE_LAYOUT),
    "label": deepcopy(_BASE_LAYOUT),
    "button": deepcopy(_BASE_LAYOUT),
    "entry": {**_BASE_LAYOUT, "columnspan": 3},
    "combobox": {**_BASE_LAYOUT, "columnspan": 3},
    "spinbox": {**_BASE_LAYOUT, "columnspan": 3},
    "checkbutton": deepcopy(_BASE_LAYOUT),
    "radiobutton": deepcopy(_BASE_LAYOUT),
    "scale": {**_BASE_LAYOUT, "columnspan": 4},
    "progressbar": {**_BASE_LAYOUT, "columnspan": 4},
    "separator": {**_BASE_LAYOUT, "columnspan": 4, "sticky": "ew"},
    "canvas": {**_BASE_LAYOUT, "columnspan": 5, "rowspan": 5},
    "text": {**_BASE_LAYOUT, "columnspan": 5, "rowspan": 5},
    "listbox": {**_BASE_LAYOUT, "columnspan": 4, "rowspan": 5},
    "treeview": {**_BASE_LAYOUT, "columnspan": 5, "rowspan": 5},
    "frame": {**_BASE_LAYOUT, "columnspan": 5, "rowspan": 5},
    "labelframe": {**_BASE_LAYOUT, "columnspan": 5, "rowspan": 5},
    "panedwindow": {**_BASE_LAYOUT, "columnspan": 6, "rowspan": 5},
    "notebook": {**_BASE_LAYOUT, "columnspan": 6, "rowspan": 5},
    "scrollbar": {**_BASE_LAYOUT, "columnspan": 1, "rowspan": 4, "sticky": "ns"},
    "sizegrip": {**_BASE_LAYOUT, "columnspan": 1, "sticky": "se"},
}

_INTEGER_LAYOUT_FIELDS = (
    "columnspan",
    "rowspan",
    "padx",
    "pady",
    "ipadx",
    "ipady",
)


def _widget_key(widget_name: str) -> str:
    return (
        str(widget_name)
        .replace("ttk::", "")
        .replace("tk::", "")
        .replace("ttk.", "")
        .replace("tk.", "")
        .lower()
    )


def default_path(program_name: str = "pytkgui") -> str:
    """Return the platform-appropriate tool_defaults.json path."""
    if "APPDATA" in os.environ:
        config_home = os.environ["APPDATA"]
    elif "XDG_CONFIG_HOME" in os.environ:
        config_home = os.environ["XDG_CONFIG_HOME"]
    else:
        config_home = os.path.join(os.environ["HOME"], ".config")
    return os.path.join(config_home, program_name, FILE_NAME)


def normalise_widget_layouts(
    value: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Merge saved per-widget values over the shipped layout table."""
    layouts = deepcopy(GRID_WIDGET_DEFAULTS)
    if not isinstance(value, Mapping):
        return layouts
    for raw_name, raw_layout in value.items():
        if not isinstance(raw_layout, Mapping):
            continue
        name = _widget_key(str(raw_name)) or "default"
        base = deepcopy(layouts.get(name, layouts["default"]))
        for field in _INTEGER_LAYOUT_FIELDS:
            if field not in raw_layout:
                continue
            try:
                minimum = 1 if field in ("columnspan", "rowspan") else 0
                base[field] = max(minimum, int(raw_layout[field]))
            except (TypeError, ValueError):
                pass
        if "sticky" in raw_layout:
            base["sticky"] = str(raw_layout["sticky"])
        layouts[name] = base
    return layouts


def normalise(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a complete, validated tool-defaults dictionary."""
    source = data if isinstance(data, Mapping) else {}
    result = deepcopy(GRID_DEFAULTS)
    for name in ("gridRows", "gridCols"):
        try:
            result[name] = max(2, min(100, int(source.get(name, result[name]))))
        except (TypeError, ValueError):
            pass
    result["gridLineColor"] = str(source.get("gridLineColor", "") or "")
    for name in ("gridRowMinsize", "gridColMinsize", "gridRowPad", "gridColPad"):
        value = str(source.get(name, result[name]) or "").strip()
        if value:
            result[name] = value
    result["gridWidgetDefaults"] = normalise_widget_layouts(
        source.get("gridWidgetDefaults")
    )
    result["formatVersion"] = FORMAT_VERSION
    return result


def widget_layout(
    widget_name: str, layouts: Mapping[str, Mapping[str, Any]] | None = None
) -> dict[str, Any]:
    """Return a detached Grid layout record for one widget type."""
    table = layouts if isinstance(layouts, Mapping) else GRID_WIDGET_DEFAULTS
    default = table.get("default", _BASE_LAYOUT)
    return deepcopy(table.get(_widget_key(widget_name), default))


def read(path: str) -> dict[str, Any]:
    """Read defaults from *path*, returning shipped defaults when absent."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return normalise(json.load(handle))
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
        return normalise(None)


def write(path: str, data: Mapping[str, Any]) -> str:
    """Atomically write validated tool defaults and return *path*."""
    defaults = normalise(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(defaults, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except (OSError, TypeError):
        try:
            if os.path.isfile(temporary):
                os.unlink(temporary)
        except OSError:
            pass
        raise
    return path


def update_widget_layout(
    path: str,
    widget_name: str,
    layout: Mapping[str, Any],
) -> str:
    """Update one widget layout without replacing other on-disk defaults.

    This intentionally reads the file again at save time. A project may have
    its own Grid dimensions active in memory; saving a widget-type layout must
    not write those project values over manually edited tool defaults.
    """
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as handle:
            source = json.load(handle)
    else:
        source = {}
    defaults = normalise(source)
    widget_key = _widget_key(widget_name) or "default"
    defaults["gridWidgetDefaults"] = normalise_widget_layouts(
        {
            **defaults["gridWidgetDefaults"],
            widget_key: layout,
        }
    )
    return write(path, defaults)
