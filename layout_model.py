"""Geometry records shared by the designer, persistence, and undo/redo.

Tkinter's ``grid_info()`` describes the geometry manager's current state, but
PyTkQuickGui temporarily switches a widget to ``place()`` while it is dragged.
During that interval ``grid_info()`` is empty or stale.  ``GridGeometry`` is
therefore the authoritative, serialisable Grid state used by every code path.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

GRID_CONTAINER_TYPES = (
    "ttk::frame",
    "ttk::labelframe",
    "ttk::panedwindow",
    "frame",
    "labelframe",
    "panedwindow",
)


def _as_int(value: Any, default: int) -> int:
    """Return a tolerant integer for values read from Tk or legacy JSON."""
    if value in (None, ""):
        return default
    try:
        # Some Tk values stringify as ``"2 2"``; the first value is the one
        # older PyTkQuickGui code consistently used.
        return int(str(value).split()[0])
    except (TypeError, ValueError):
        return default


def is_grid_container_type(widget_type: Any) -> bool:
    """Return whether *widget_type* can contain designer Grid children."""
    return str(widget_type or "").lower() in GRID_CONTAINER_TYPES


def container_grid_dimensions(
    widget_data: Mapping[str, Any] | None,
    default_columns: int = 4,
    default_rows: int = 4,
) -> tuple[int, int]:
    """Return the persisted internal Grid dimensions for a container.

    Older projects did not save this information, so they retain the
    historical 4×4 container grid.
    """
    values = widget_data if isinstance(widget_data, Mapping) else {}
    saved = values.get("ContainerGrid")
    if not isinstance(saved, Mapping):
        saved = {}
    return (
        max(1, _as_int(saved.get("columns"), default_columns)),
        max(1, _as_int(saved.get("rows"), default_rows)),
    )


@dataclass(frozen=True)
class GridGeometry:
    """Complete Grid geometry for one designer widget."""

    parent: str = "rootWidget"
    row: int = 0
    column: int = 0
    columnspan: int = 1
    rowspan: int = 1
    sticky: str = "nsew"
    padx: int = 2
    pady: int = 2
    ipadx: int = 0
    ipady: int = 0

    @classmethod
    def from_mapping(
        cls, data: Mapping[str, Any] | None, parent: str = "rootWidget"
    ) -> GridGeometry:
        """Build a normalised record from saved ``GeomData``."""
        values = data or {}
        return cls(
            parent=str(parent or "rootWidget"),
            row=max(0, _as_int(values.get("row"), 0)),
            column=max(0, _as_int(values.get("column"), 0)),
            columnspan=max(1, _as_int(values.get("columnspan"), 1)),
            rowspan=max(1, _as_int(values.get("rowspan"), 1)),
            sticky=str(values.get("sticky", "nsew") or ""),
            padx=max(0, _as_int(values.get("padx"), 2)),
            pady=max(0, _as_int(values.get("pady"), 2)),
            ipadx=max(0, _as_int(values.get("ipadx"), 0)),
            ipady=max(0, _as_int(values.get("ipady"), 0)),
        )

    def updated(self, **changes: Any) -> GridGeometry:
        """Return a copy with selected fields replaced and normalised."""
        return GridGeometry.from_mapping(
            {
                "row": changes.get("row", self.row),
                "column": changes.get("column", self.column),
                "columnspan": changes.get("columnspan", self.columnspan),
                "rowspan": changes.get("rowspan", self.rowspan),
                "sticky": changes.get("sticky", self.sticky),
                "padx": changes.get("padx", self.padx),
                "pady": changes.get("pady", self.pady),
                "ipadx": changes.get("ipadx", self.ipadx),
                "ipady": changes.get("ipady", self.ipady),
            },
            parent=str(changes.get("parent", self.parent)),
        )

    def to_json(self) -> dict[str, str]:
        """Return the backwards-compatible JSON representation."""
        return {
            "row": str(self.row),
            "column": str(self.column),
            "columnspan": str(self.columnspan),
            "rowspan": str(self.rowspan),
            "sticky": self.sticky,
            "padx": str(self.padx),
            "pady": str(self.pady),
            "ipadx": str(self.ipadx),
            "ipady": str(self.ipady),
        }


def is_saved_notebook_tab(
    project_data: Mapping[str, Any], widget_name: str, root_name: str
) -> bool:
    """Return whether a saved frame is managed as a Notebook tab."""
    widget_data = project_data.get(widget_name)
    if not isinstance(widget_data, Mapping):
        return False
    parent_name = str(widget_data.get("WidgetParent", root_name) or root_name)
    if parent_name == root_name:
        return False
    parent_data = project_data.get(parent_name)
    return (
        isinstance(parent_data, Mapping)
        and parent_data.get("WidgetName") == "ttk::notebook"
        and widget_data.get("WidgetName")
        in ("ttk::frame", "ttk::labelframe", "frame", "labelframe")
    )


def grid_layout_requirements(
    project_data: Mapping[str, Any],
    widget_order: Iterable[str],
    root_name: str,
    container_columns: int = 4,
    container_rows: int = 4,
) -> dict[str, tuple[int, int]]:
    """Return ``parent -> (column_count, row_count)`` for generated code."""
    requirements: dict[str, list[int]] = {
        root_name: [
            max(2, _as_int(project_data.get("gridCols"), 25)),
            max(2, _as_int(project_data.get("gridRows"), 25)),
        ]
    }
    for widget_name in widget_order:
        if widget_name == root_name:
            continue
        widget_data = project_data.get(widget_name)
        if not isinstance(widget_data, Mapping):
            continue
        parent = str(widget_data.get("WidgetParent", root_name) or root_name)
        state = GridGeometry.from_mapping(widget_data.get("GeomData"), parent=parent)
        if not is_saved_notebook_tab(project_data, widget_name, root_name):
            extent = requirements.setdefault(parent, [0, 0])
            extent[0] = max(extent[0], state.column + state.columnspan)
            extent[1] = max(extent[1], state.row + state.rowspan)
        if is_grid_container_type(widget_data.get("WidgetName")):
            saved_columns, saved_rows = container_grid_dimensions(
                widget_data,
                default_columns=container_columns,
                default_rows=container_rows,
            )
            container_extent = requirements.setdefault(widget_name, [0, 0])
            container_extent[0] = max(container_extent[0], saved_columns)
            container_extent[1] = max(container_extent[1], saved_rows)
    return {
        parent: (max(1, values[0]), max(1, values[1]))
        for parent, values in requirements.items()
    }


def compact_grid_geometries(
    states: Iterable[GridGeometry],
    configured_columns: int,
    configured_rows: int,
    minimum_columns: int = 2,
    minimum_rows: int = 2,
) -> tuple[list[GridGeometry], int, int, int, int]:
    """Close unused root-grid gaps and return new dimensions and removal counts."""
    original = list(states)
    if not original:
        return (
            [],
            max(minimum_columns, configured_columns),
            max(minimum_rows, configured_rows),
            0,
            0,
        )

    used_columns = {
        column
        for state in original
        for column in range(state.column, state.column + state.columnspan)
    }
    used_rows = {
        row for state in original for row in range(state.row, state.row + state.rowspan)
    }
    column_map = {
        old_column: new_column
        for new_column, old_column in enumerate(sorted(used_columns))
    }
    row_map = {old_row: new_row for new_row, old_row in enumerate(sorted(used_rows))}
    compacted = [
        state.updated(column=column_map[state.column], row=row_map[state.row])
        for state in original
    ]
    column_count = max(
        minimum_columns,
        max(state.column + state.columnspan for state in compacted),
    )
    row_count = max(
        minimum_rows,
        max(state.row + state.rowspan for state in compacted),
    )
    old_column_count = max(
        configured_columns,
        max(state.column + state.columnspan for state in original),
    )
    old_row_count = max(
        configured_rows,
        max(state.row + state.rowspan for state in original),
    )
    return (
        compacted,
        column_count,
        row_count,
        max(0, old_column_count - column_count),
        max(0, old_row_count - row_count),
    )
