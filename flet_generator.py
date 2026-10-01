"""Translate a saved PyTkQuickGui project into a standalone Flet program.

The designer stores every widget as a dictionary of raw Tk options
(``Attribute0`` … ``AttributeN``) plus geometry records shared with
:mod:`layout_model`.  This module is a pure translation of that data into
Flet 0.8x controls: it never touches Tk, so it can be unit tested and re-run
without a display.

Translation notes
-----------------
* Tk options with no Flet equivalent (``takefocus``, ``cursor`` …) are left
  out of the emitted code but listed in a comment per widget, so nothing
  disappears silently.
* ttkbootstrap theme names are not Flet themes: the project theme is emitted
  as a ``THEME`` constant for reference only.
* Geometry: ``Place`` becomes ``ft.Stack`` with absolute ``left``/``top``,
  ``Grid`` becomes nested ``ft.Column``/``ft.Row`` (``rowspan`` is
  approximate), ``Pack`` becomes ``ft.Row``/``ft.Column`` groups.
* The generated code targets the Flet 1.0 control API (``ft.Button``,
  ``ft.Tabs`` with a ``TabBar``/``TabBarView`` content, ``ft.DropdownOption``)
  while remaining compatible with the 0.8x releases.  Every program starts with
  a version guard so an older runtime says so instead of failing obscurely.
* Nested containers are emitted child-first: every control is assigned to a
  variable before its parent references it.
"""

from __future__ import annotations

import ast
import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import layout_model
import project_format
import tool_defaults

STUB_SENTINEL = "# AUTO-GENERATED STUB"

#: Flet API level the generated programs are written against.  They still run
#: on the older 0.8x releases, so the emitted guard warns by default; flip
#: :data:`DEFAULT_STRICT_FLET_VERSION` (or the generated file's own constant)
#: to refuse to start on anything older.
DEFAULT_MINIMUM_FLET_VERSION = "1.0"
DEFAULT_STRICT_FLET_VERSION = False

#: Palette exported from ttkbootstrap by ``tools/export_theme_colors.py``.
PALETTE_FILE = "flet_theme_colors.json"

#: The ttkbootstrap colour names a ``style`` option can start with.
BOOTSTYLES = (
    "primary",
    "secondary",
    "success",
    "info",
    "warning",
    "danger",
    "light",
    "dark",
)

#: Style segments that modify how a bootstyle is painted.
STYLE_VARIANTS = frozenset(
    {"outline", "inverse", "link", "striped", "vertical", "horizontal"}
)

#: Text metrics.  Tk's default font is 10pt (~13px); Flet's default is 14px,
#: which is wide enough to wrap short button captions like "Connect" inside a
#: designer-sized button, so both are pinned to the Tk sizes.
DEFAULT_TEXT_SIZE = 13
BUTTON_TEXT_SIZE = 12
BUTTON_PADDING_X = 6
BUTTON_PADDING_Y = 2
BUTTON_RADIUS = 4

#: A multiline ft.TextField takes its height from min_lines: Flet ignores an
#: explicit height on a multiline field (measured on 0.86.5 and 1.0.3, where
#: height=120 rendered 46px tall).  A line measures about 1.43 x the text size
#: and the field adds about 5px of padding and border, so the designer's height
#: is turned into a line count instead.
MULTILINE_LINE_RATIO = 1.43
MULTILINE_CHROME = 5

#: Flet's default field padding is tall enough to clip the text inside a ttk
#: sized row (32px), so fields are given explicit tight padding.
FIELD_PADDING_X = 6
FIELD_PADDING_Y = 2

#: Width of the up/down buttons beside a spinbox field, in pixels.
STEPPER_WIDTH = 28
STEPPER_ICON_SIZE = 12

#: Bounds for the window size worked out from a design.  A tall Pack project
#: can add up to several thousand pixels; the layout reflows, so the window
#: only has to open at a sensible size.
MIN_WINDOW_WIDTH = 320
MIN_WINDOW_HEIGHT = 240
MAX_WINDOW_WIDTH = 1280
MAX_WINDOW_HEIGHT = 900

#: Luminance above which a filled bootstyle colour gets black text instead of
#: white.  ttkbootstrap resolves the same way: tokyo-night's light green gets
#: black text, sandstone's dark blue gets white.
INK_LUMINANCE_THRESHOLD = 0.5

#: Arguments a widget option may override even when a theme supplied them.
#: Everything else themed is left alone by explicit Tk options.
STRUCTURAL_ARGUMENTS = frozenset(
    {
        "value",
        "content",
        "label",
        "options",
        "controls",
        "columns",
        "rows",
        "length",
        "scroll",
        "min",
        "max",
    }
)

SECTION_VARIABLES = "####### Flet variables #######"

#: Emitted when widgets take their caption from a textvariable.
_TEXT_BINDING_HELPERS = (
    "TEXT_BINDINGS = {}",
    "",
    "",
    "def set_text(page, name, value):",
    '    """Set a bound variable and refresh the control showing it.',
    "",
    "    ``name`` is the textvariable the designer recorded, for example",
    "    ``set_text(page, 'buttonvar11', '7')``.",
    '    """',
    "    globals()[name] = value",
    "    for control, attribute in TEXT_BINDINGS.get(name, ()):",
    "        setattr(control, attribute, value)",
    "    page.update()",
)
SECTION_FUNCTIONS = "####### Functions #######"
SECTION_WIDGETS = "####### Widgets #######"
SECTION_MAIN = "####### Main  #######"

NOTEBOOK_WIDGET_TYPE = "ttk::notebook"
CONTAINER_WIDGET_TYPES = (
    "ttk::frame",
    "ttk::labelframe",
    "ttk::panedwindow",
    "ttk::canvas",
    "frame",
    "labelframe",
    "panedwindow",
    "canvas",
)
TEXT_MEASURED_TYPES = ("listbox", "ttk::listbox", "text", "ttk::text")
#: A Tk text widget becomes a multiline field inside a Container, because a
#: multiline ft.TextField takes its height from min_lines and ignores a height.
TEXT_WIDGET_TYPES = ("text", "ttk::text")

#: Tk widget type (as stored in ``WidgetName``) -> Flet control constructor.
CONTROL_TYPES: dict[str, str] = {
    "ttk::label": "ft.Text",
    "ttk::button": "ft.Button",
    "button": "ft.Button",
    "ttk::entry": "ft.TextField",
    "ttk::combobox": "ft.Dropdown",
    "ttk::spinbox": "ft.TextField",
    "ttk::checkbutton": "ft.Checkbox",
    "ttk::radiobutton": "ft.RadioGroup",
    "ttk::scale": "ft.Slider",
    "ttk::progressbar": "ft.ProgressBar",
    "ttk::separator": "ft.Divider",
    "ttk::notebook": "ft.Tabs",
    "ttk::frame": "ft.Container",
    "ttk::labelframe": "ft.Container",
    "ttk::panedwindow": "ft.Row",
    "ttk::canvas": "ft.Container",
    "canvas": "ft.Container",
    "ttk::scrollbar": "ft.Container",
    "ttk::treeview": "ft.DataTable",
    "listbox": "ft.ListView",
    "ttk::listbox": "ft.ListView",
    "text": "ft.TextField",
    "ttk::text": "ft.TextField",
}

#: Widget types whose Tk widget scrolls, so a sibling/parent scrollbar can be
#: folded into the generated control instead of becoming a placeholder.
SCROLLABLE_WIDGET_TYPES = (
    "ttk::canvas",
    "canvas",
    "text",
    "ttk::text",
    "listbox",
    "ttk::listbox",
    "ttk::treeview",
    "treeview",
)

#: Scrollable widget types whose Flet control has no ``scroll`` slot, so the
#: control is wrapped in a scrolling ``ft.Column`` instead.
WRAPPED_SCROLL_TYPES = ("ttk::canvas", "canvas", "ttk::treeview", "treeview")

#: Scrollable widget types where the Flet control scrolls on its own.
SELF_SCROLLING_TYPES = ("text", "ttk::text")

#: Types Flet has no direct control for; the emitted placeholder explains why.
PLACEHOLDERS: dict[str, str] = {
    "listbox": "ft.ListView stands in for the Tk listbox",
    "ttk::listbox": "ft.ListView stands in for the Tk listbox",
    "ttk::treeview": (
        "Treeview rows are not stored in the project - ft.DataTable is emitted "
        "with the saved column headings and no rows"
    ),
    "ttk::spinbox": "Flet has no Spinbox control - ft.TextField stands in",
    "ttk::scrollbar": (
        "Flet scrollbars attach to a scrollable control "
        "(ft.Column(scroll=ft.Scrollbar())) - placeholder Container"
    ),
}

#: Options accepted by each generated control.
CONTROL_OPTIONS: dict[str, frozenset[str]] = {
    "ft.Text": frozenset(
        {
            "value",
            "color",
            "bgcolor",
            "size",
            "weight",
            "italic",
            "font_family",
            "text_align",
            "max_lines",
        }
    ),
    "ft.Button": frozenset({"content", "bgcolor", "color", "disabled"}),
    "ft.TextField": frozenset(
        {
            "value",
            "password",
            "read_only",
            "disabled",
            "text_align",
            "multiline",
            "label",
            "bgcolor",
            "color",
            "text_size",
        }
    ),
    "ft.Dropdown": frozenset({"value", "label", "options", "disabled", "bgcolor"}),
    "ft.Checkbox": frozenset({"label", "value", "disabled"}),
    "ft.RadioGroup": frozenset({"value", "content", "disabled"}),
    "ft.Slider": frozenset({"value", "min", "max", "disabled"}),
    "ft.ProgressBar": frozenset({"value", "color", "bgcolor", "disabled"}),
    "ft.Divider": frozenset({"color", "height", "thickness"}),
    "ft.Container": frozenset(
        {"content", "bgcolor", "padding", "alignment", "border_radius"}
    ),
    "ft.Row": frozenset({"controls", "spacing", "expand"}),
    "ft.Column": frozenset({"controls", "spacing", "expand"}),
    "ft.Stack": frozenset({"controls", "width", "height"}),
    "ft.Tabs": frozenset({"content", "length"}),
    "ft.ListView": frozenset({"controls", "spacing", "scroll"}),
    "ft.DataTable": frozenset({"columns", "rows"}),
    "ft.Scrollbar": frozenset({"thickness"}),
    "ft.Image": frozenset({"src"}),
}

#: Options accepted by every Flet control (positioning inside a Stack).
UNIVERSAL_OPTIONS = frozenset({"left", "top", "right", "bottom", "width", "height"})

#: Controls that are :class:`flet.LayoutControl` subclasses, i.e. the only ones
#: that can carry ``left``/``top``/``width``/``height`` inside a Stack.
POSITIONABLE_CONTROLS = frozenset(
    {
        "ft.Container",
        "ft.Stack",
        "ft.Row",
        "ft.Column",
        "ft.Text",
        "ft.Button",
        "ft.TextField",
        "ft.Dropdown",
        "ft.Checkbox",
        "ft.Slider",
        "ft.ProgressBar",
        "ft.Tabs",
        "ft.ListView",
        "ft.DataTable",
        "ft.Image",
    }
)

#: Tk/X11 colour names seen in saved projects, mapped to CSS hex.
TK_COLORS: dict[str, str] = {
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "yellow": "#ffff00",
    "orange": "#ffa500",
    "purple": "#800080",
    "brown": "#a52a2a",
    "pink": "#ffc0cb",
    "gray": "#808080",
    "grey": "#808080",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "gray96": "#f5f5f5",
    "grey96": "#f5f5f5",
    "skyblue": "#87ceeb",
    "skyblue1": "#87ceff",
    "skyblue2": "#7ec0ee",
    "skyblue3": "#6ca6cd",
    "skyblue4": "#4a708b",
    "steelblue": "#4682b4",
    "lightblue": "#add8e6",
    "lightsteelblue": "#b0c4de",
    "navy": "#000080",
    "teal": "#008080",
    "lime": "#00ff00",
    "maroon": "#800000",
    "olive": "#808000",
    "silver": "#c0c0c0",
    "systembuttonface": "#d9d9d9",
    "systemwindow": "#ffffff",
    "systembuttontext": "#000000",
    "systemhighlight": "#0078d7",
}

_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_FONT = re.compile(r"^\s*(?P<family>\S.*?)\s+(?P<size>-?\d+)\s*(?P<rest>.*)$")

#: Tk measures Entry/Combobox/Spinbox widths in characters; Flet uses pixels.
_AVERAGE_CHAR_WIDTH = 8
_CHAR_WIDTH_PADDING = 12
_LINE_HEIGHT = 18

_ALIGNMENTS = {
    "left": "ft.TextAlign.LEFT",
    "right": "ft.TextAlign.RIGHT",
    "center": "ft.TextAlign.CENTER",
    "justify": "ft.TextAlign.JUSTIFY",
    "w": "ft.TextAlign.LEFT",
    "e": "ft.TextAlign.RIGHT",
    "n": "ft.TextAlign.CENTER",
    "s": "ft.TextAlign.CENTER",
}
_CONTAINER_ALIGNMENTS = {
    "left": "ft.Alignment.TOP_LEFT",
    "w": "ft.Alignment.TOP_LEFT",
    "right": "ft.Alignment.TOP_RIGHT",
    "e": "ft.Alignment.TOP_RIGHT",
    "center": "ft.Alignment.CENTER",
    "n": "ft.Alignment.CENTER",
    "s": "ft.Alignment.CENTER",
}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _number(value: Any, default: int | float | None = None) -> int | float | None:
    """Return *value* as a number, or *default* when blank or not numeric."""
    raw = _text(value).strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return default


#: Flet positions are pixels; Tk accepts unit suffixes in geometry values.
#: Conversion assumes the usual 96 dpi desktop, where 1i = 72p = 96px.
_TK_UNITS = {"p": 96 / 72, "i": 96.0, "m": 96 / 25.4, "c": 96 / 2.54}


def tk_length(value: Any, default: int = 0) -> int:
    """Convert a Tk geometry value (``"5m"``, ``"120"``, ``""``) to pixels."""
    raw = _text(value).strip()
    if not raw or raw.lower() in ("none", "0"):
        return default
    suffix = raw[-1].lower()
    if suffix in _TK_UNITS:
        number = _number(raw[:-1])
        if number is None:
            return default
        return max(0, int(round(float(number) * _TK_UNITS[suffix])))
    number = _number(raw)
    return default if number is None else max(0, int(number))


def _indent_lines(block: str, indent: int) -> str:
    """Indent every line of *block* by *indent* spaces."""
    pad = " " * indent
    return "\n".join(pad + line for line in block.split("\n"))


def _call(prefix: str, arguments: Sequence[str]) -> str:
    """Format ``prefix(arg, arg)`` with one argument per line."""
    values = [argument for argument in arguments if argument]
    if not values:
        return f"{prefix}()"
    body = ",\n".join(_indent_lines(value, 4) for value in values)
    return f"{prefix}(\n{body},\n)"


def _list_expression(elements: Sequence[str], width: int = 78) -> str:
    """Return a ``[…]`` list, one element per line when that reads better."""
    if not elements:
        return "[]"
    inline = f"[{', '.join(elements)}]"
    if len(elements) <= 3 and len(inline) <= width and "\n" not in inline:
        return inline
    body = _indent_lines(",\n".join(elements), 4)
    return f"[\n{body},\n]"


def _list_argument(keyword: str, elements: Sequence[str]) -> str:
    """Return ``keyword=[…]`` using :func:`_list_expression` formatting."""
    return f"{keyword}={_list_expression(elements)}"


def tk_color(value: Any) -> str | None:
    """Return a Flet-safe colour for a Tk colour name, or ``None`` to drop it."""
    raw = _text(value).strip()
    if not raw:
        return None
    if _HEX_COLOR.match(raw):
        return raw.lower()
    return TK_COLORS.get(raw.replace(" ", "").lower())


def parse_font(value: Any) -> dict[str, str]:
    """Translate a Tk font description into Flet text properties.

    Two forms turn up in saved projects: the font chooser writes a dict such as
    ``{'family': 'Liberation Mono', 'size': 18, 'weight': 'normal', …}``, and
    hand written or older files use the X11 ``"family size style…"`` string.
    Symbolic fonts such as ``TkDefaultFont`` return an empty mapping.
    """
    raw = _text(value).strip().replace("\\", "")
    if not raw or raw.startswith("Tk"):
        return {}
    if raw.startswith("{"):
        chosen = _parse_font_dict(raw)
        if chosen:
            return chosen
    match = _FONT.match(raw)
    if not match:
        return {}
    size = _number(match.group("size"))
    rest = match.group("rest").lower()
    properties: dict[str, str] = {"font_family": repr(match.group("family"))}
    if isinstance(size, (int, float)) and size:
        pixels = int(abs(size) * 1.33) if size > 0 else int(abs(size))
        properties["size"] = repr(pixels)
    if "bold" in rest:
        properties["weight"] = "ft.FontWeight.BOLD"
    if "italic" in rest or "oblique" in rest:
        properties["italic"] = "True"
    return properties


def _parse_font_dict(raw: str) -> dict[str, str]:
    """Return Flet text properties from a font chooser dict, or ``{}``."""
    try:
        chosen = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        return {}
    if not isinstance(chosen, Mapping):
        return {}
    properties: dict[str, str] = {}
    family = _text(chosen.get("family")).strip()
    if family:
        properties["font_family"] = repr(family)
    size = _number(chosen.get("size"))
    if isinstance(size, (int, float)) and size:
        properties["size"] = repr(abs(int(size)))
    if _text(chosen.get("weight")).strip().lower() in ("bold", "heavy"):
        properties["weight"] = "ft.FontWeight.BOLD"
    if _text(chosen.get("slant")).strip().lower() in ("italic", "oblique"):
        properties["italic"] = "True"
    return properties


def parse_values(value: Any) -> list[str]:
    """Split a saved Tk ``values`` option into individual entries.

    Values arrive either as the designer's ``"(a b c)"`` form or as a plain
    space separated string, with ``{braced groups}`` for entries containing
    spaces.
    """
    raw = _text(value).strip().strip("[]()")
    if not raw:
        return []
    entries: list[str] = []
    current = ""
    depth = 0
    quote = ""
    for character in raw:
        if quote:
            if character == quote:
                quote = ""
            else:
                current += character
            continue
        if character in "\"'":
            quote = character
            continue
        if character == "{":
            depth += 1
            continue
        if character == "}":
            depth = max(0, depth - 1)
            continue
        if character.isspace() and depth == 0:
            if current:
                entries.append(current)
                current = ""
            continue
        current += character
    if current:
        entries.append(current)
    return entries


def load_theme_palette(path: str | None = None) -> dict[str, Any]:
    """Return the exported ttkbootstrap palettes.

    Missing or unreadable data is not fatal: without it the generator simply
    emits no theme colours, which is what it did before the palette existed.
    """
    target = path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), PALETTE_FILE
    )
    try:
        with open(target, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def theme_palette(theme: Any, palettes: Mapping[str, Any] | None = None) -> dict:
    """Return one theme's exported palette, keeping all three of its sections.

    ``colors`` holds the bootstyle slots, ``styles`` holds what ttkbootstrap
    resolves for each bootstyle (button text colour, outline colours, frame
    fill, the caption colour of a labelframe) and ``widgets`` holds the resolved
    surfaces (entry background, progressbar trough).  Dropping any of them
    silently falls back to the slot colours, losing ttk's own choices - such as
    white rather than black text on a borderline fill.
    """
    table = palettes if palettes is not None else load_theme_palette()
    record = table.get(_text(theme)) if isinstance(table, Mapping) else None
    if not isinstance(record, Mapping):
        return {}
    palette: dict[str, Any] = {}
    for section in ("colors", "styles", "widgets"):
        values = record.get(section)
        if isinstance(values, Mapping):
            palette[section] = {
                str(key): dict(value) if isinstance(value, Mapping) else value
                for key, value in values.items()
            }
    return palette


def parse_bootstyle(value: Any) -> tuple[str, frozenset[str]]:
    """Split a ttkbootstrap style into its bootstyle colour and variants.

    ``"secondary.Outline.TButton"`` -> ``("secondary", {"outline"})``,
    ``"primary.Horizontal.TScale"`` -> ``("primary", {"horizontal"})``.
    Unknown first segments (custom styles) yield an empty bootstyle.
    """
    parts = [part for part in _text(value).split(".") if part]
    if not parts:
        return "", frozenset()
    bootstyle = parts[0].lower()
    if bootstyle not in BOOTSTYLES:
        return "", frozenset(
            part.lower() for part in parts[1:] if part.lower() in STYLE_VARIANTS
        )
    variants = {
        part.lower()
        for part in parts[1:]
        if part.lower() in STYLE_VARIANTS and part.lower() != "horizontal"
        and part.lower() != "vertical"
    }
    orientations = {
        part.lower() for part in parts[1:] if part.lower() in ("horizontal", "vertical")
    }
    return bootstyle, frozenset(variants | orientations)


def hex_luminance(colour: Any) -> float:
    """Return the perceived luminance (0-1) of a ``#rrggbb`` colour."""
    raw = _text(colour).lstrip("#")
    if len(raw) == 3:
        raw = "".join(character * 2 for character in raw)
    if len(raw) < 6:
        return 0.5
    try:
        red, green, blue = (
            int(raw[start:start + 2], 16) for start in (0, 2, 4)
        )
    except ValueError:
        return 0.5
    return (0.299 * red + 0.587 * green + 0.114 * blue) / 255


def _ensure_span(
    widths: list[int],
    heights: list[int],
    column: int,
    row: int,
    columnspan: int,
    rowspan: int,
) -> tuple[list[int], list[int]]:
    """Extend the axis lists so a widget's span fits inside them."""
    widths = widths + [1] * max(0, column + columnspan - len(widths))
    heights = heights + [1] * max(0, row + rowspan - len(heights))
    return widths, heights


def _grow_axis(axis: list[int], start: int, span: int, needed: int) -> None:
    """Widen an axis so a widget needs at most ``needed`` pixels.

    Tk gives any shortfall to the last cell of the span, which is what the
    designer's own grid does, so the same rule is used here.
    """
    span = max(1, span)
    current = sum(axis[index] for index in range(start, start + span))
    if needed > current:
        axis[start + span - 1] += needed - current


def multiline_lines(height: Any, text_size: int = DEFAULT_TEXT_SIZE) -> int:
    """Return the ``min_lines`` that makes a multiline field as tall as *height*."""
    pixels = _number(height)
    if not pixels:
        return 0
    line = max(1.0, text_size * MULTILINE_LINE_RATIO)
    return max(1, int(round((float(pixels) - MULTILINE_CHROME) / line)))


def _widget_key(widget_type: Any) -> str:
    """Normalise a Tk widget type to a tool-defaults key."""
    return (
        _text(widget_type)
        .replace("ttk::", "")
        .replace("tk::", "")
        .replace("ttk.", "")
        .replace("tk.", "")
        .lower()
    )


def widget_control(widget_type: Any) -> str:
    """Return the Flet control constructor for a Tk widget type."""
    return CONTROL_TYPES.get(_text(widget_type), "ft.Container")


def is_container(widget_type: Any) -> bool:
    return _text(widget_type) in CONTAINER_WIDGET_TYPES


def window_size(
    project_data: Mapping[str, Any],
    widget_order: Sequence[str] = (),
    root_name: str = "rootWidget",
) -> tuple[int, int]:
    """Return a sensible window size for the generated Flet app."""
    width = 0
    height = 0
    for name in widget_order:
        widget_data = project_data.get(name)
        if not isinstance(widget_data, Mapping):
            continue
        parent = _text(widget_data.get("WidgetParent", root_name)) or root_name
        if parent != root_name:
            continue
        place = widget_data.get("Place") or {}
        x = _number(place.get("x"), 0) or 0
        y = _number(place.get("y"), 0) or 0
        widget_width = _number(place.get("width"), 0) or 0
        widget_height = _number(place.get("height"), 0) or 0
        width = max(width, int(x) + int(widget_width))
        height = max(height, int(y) + int(widget_height))
    if width <= 0 or height <= 0:
        return 800, 600
    return width + 20, height + 20


def translate_attributes(
    widget_type: str,
    attributes: Sequence[tuple[str, str]],
    context: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Translate saved Tk options into Flet properties.

    Returns ``(properties, unmapped_keys)``.  ``properties`` holds Python
    literals ready to emit, plus the internal markers ``text``, ``command``,
    ``values`` and ``image`` that the per-control emitters place on the
    correct keyword.
    """
    properties: dict[str, Any] = {}
    unmapped: list[str] = []
    callbacks = context["callbacks"]
    variables = context["variables"]
    images = context["images"]

    for key, value in attributes:
        raw = _text(value)
        if key == "text":
            properties["text"] = raw
        elif key in ("style", "bootstyle"):
            # Consumed by _style_arguments(), which needs the bootstyle.
            properties["style"] = raw
        elif key in project_format.CALLBACK_KEYS:
            if raw in callbacks:
                properties["command"] = raw
            else:
                unmapped.append(key)
        elif key in project_format.VARIABLE_KEYS:
            if raw in variables:
                properties["value"] = raw
            else:
                unmapped.append(key)
        elif key == "image":
            filename = images.get(context["name"])
            if filename:
                properties["image"] = filename
            else:
                unmapped.append(key)
        elif key == "values":
            values = parse_values(raw)
            if values:
                properties["values"] = values
            else:
                unmapped.append(key)
        elif key == "listvariable":
            # A listbox keeps its items in a Python list the application owns.
            # This is not one of project_format.VARIABLE_KEYS, so it is
            # validated here rather than looked up in the variable set.
            if project_format.valid_python_name(raw):
                properties["list_variable"] = raw
            else:
                unmapped.append(key)
        elif key == "columns":
            # Treeview heading names; the tool never stores row data.
            values = parse_values(raw)
            if values:
                properties["tree_columns"] = values
            else:
                unmapped.append(key)
        elif key == "font":
            font = parse_font(raw)
            if font:
                properties.update(font)
            else:
                unmapped.append(key)
        elif key in ("foreground", "fg", "insertbackground"):
            colour = tk_color(raw)
            if colour:
                properties["color"] = repr(colour)
            else:
                unmapped.append(key)
        elif key in ("background", "bg"):
            colour = tk_color(raw)
            if colour:
                properties["bgcolor"] = repr(colour)
            else:
                unmapped.append(key)
        elif key == "justify":
            align = _ALIGNMENTS.get(raw.strip().lower())
            if align:
                properties["text_align"] = align
            else:
                unmapped.append(key)
        elif key == "anchor":
            align = _CONTAINER_ALIGNMENTS.get(raw.strip().lower())
            if align:
                properties["alignment"] = align
            else:
                unmapped.append(key)
        elif key == "state":
            if raw == "disabled":
                properties["disabled"] = "True"
            elif raw in ("readonly", "read-only"):
                properties["read_only"] = "True"
        elif key == "show":
            if raw:
                properties["password"] = "True"
        elif key in ("from", "from_"):
            number = _number(raw)
            if number is None:
                unmapped.append(key)
            else:
                properties["minimum"] = float(number)
        elif key == "to":
            number = _number(raw)
            if number is None:
                unmapped.append(key)
            else:
                properties["maximum"] = float(number)
        elif key == "value":
            if widget_type == "ttk::radiobutton":
                # A radio's own value is an arbitrary label, not a number.
                properties["current"] = raw
            else:
                number = _number(raw)
                if number is None:
                    unmapped.append(key)
                else:
                    properties["current"] = float(number)
        elif key == "increment":
            number = _number(raw)
            if number is None:
                unmapped.append(key)
            else:
                properties["increment"] = float(number)
        elif key == "maximum":
            number = _number(raw)
            if number is None:
                unmapped.append(key)
            else:
                properties["range_maximum"] = float(number)
        elif key in ("length", "wraplength"):
            number = _number(raw)
            if number is None:
                unmapped.append(key)
            else:
                properties["width"] = int(number)
        elif key == "width":
            if widget_type in ("ttk::label", "ttk::progressbar", "ttk::scale"):
                number = _number(raw)
                if number is None:
                    unmapped.append(key)
                else:
                    properties["width"] = int(number)
            else:
                characters = _number(raw)
                if characters is None:
                    unmapped.append(key)
                else:
                    properties["width"] = (
                        int(characters) * _AVERAGE_CHAR_WIDTH + _CHAR_WIDTH_PADDING
                    )
        elif key == "height":
            if widget_type in TEXT_MEASURED_TYPES:
                lines = _number(raw)
                if lines is None:
                    unmapped.append(key)
                else:
                    properties["height"] = int(lines) * _LINE_HEIGHT
            else:
                number = _number(raw)
                if number is None:
                    unmapped.append(key)
                else:
                    properties["height"] = int(number)
        elif key == "orient":
            properties["orientation"] = raw.strip().lower()
        elif key == "padding":
            number = _number(raw)
            if number is None:
                unmapped.append(key)
            else:
                properties["padding"] = int(number)
        else:
            unmapped.append(key)

    return properties, unmapped


@dataclass(frozen=True)
class ScrollAttachment:
    """A Tk scrollbar folded into the control it scrolls.

    ``mode`` is one of:

    ``native``      the target control has a ``scroll`` slot (ListView)
    ``wrap``        the target must be wrapped in a scrolling ``ft.Column``
    ``self``        the target scrolls on its own, so the bar is dropped
    ``placeholder`` no target (or a horizontal bar) - keep a stand-in control
    """

    scrollbar: str
    orientation: str
    thickness: int
    target: str = ""
    mode: str = "placeholder"

    def scrollbar_call(self) -> str:
        """Return the ``ft.Scrollbar(...)`` expression for the target."""
        return f"ft.Scrollbar(thickness={self.thickness})"

    def summary(self) -> str:
        """Return a one line description for the translation notes."""
        if self.mode == "placeholder":
            return "no scrollable target found - placeholder Container"
        if self.mode == "self":
            return f"{self.target} scrolls on its own - scrollbar dropped"
        if self.mode == "native":
            return f"attached to {self.target} via scroll={self.scrollbar_call()}"
        return (
            f"wraps {self.target} in a scrolling ft.Column "
            f"({self.scrollbar_call()})"
        )


class _Project:
    """Read-only view of a saved project, shared by the emitters."""

    def __init__(
        self,
        project_data: Mapping[str, Any],
        widget_order: Sequence[str],
        root_name: str,
        geom_manager: str = "",
        images: Mapping[str, str] | None = None,
        grid_mode: str = "responsive",
        policy: Mapping[str, str] | None = None,
        palette: Mapping[str, Any] | None = None,
        natural_sizes: Mapping[str, Sequence[int]] | None = None,
    ) -> None:
        self.data = project_data
        self.root_name = root_name
        self.geom_manager = geom_manager or _text(project_data.get("geomManager"))
        self.grid_mode = grid_mode
        self.policy: Mapping[str, str] = dict(policy or {"default": "full"})
        self.theme = _text(project_data.get("theme"))
        self.palette = theme_palette(self.theme, palette)
        self.natural_sizes: dict[str, tuple[int, int]] = {}
        for name, size in dict(natural_sizes or {}).items():
            try:
                width, height = int(size[0]), int(size[1])
            except (IndexError, TypeError, ValueError):
                continue
            if width > 0 and height > 0:
                self.natural_sizes[name] = (width, height)
        self.images = dict(images or _image_files(project_data))
        self.order = [name for name in widget_order if name != root_name]
        self.callbacks = project_format.callback_names(self.data, self.order, root_name)
        self.variables = project_format.variable_names(self.data, self.order, root_name)
        self.children: dict[str, list[str]] = {}
        for name in self.order:
            widget_data = self.data.get(name)
            if not isinstance(widget_data, Mapping):
                continue
            parent = _text(widget_data.get("WidgetParent", root_name)) or root_name
            if parent != root_name and parent not in self.data:
                parent = root_name
            self.children.setdefault(parent, []).append(name)
        self.grid_requirements = (
            layout_model.grid_layout_requirements(self.data, self.order, root_name)
            if self.geom_manager == "Grid"
            else {}
        )
        self.scroll_attachments = self._find_scroll_attachments()
        self.scroll_targets = {
            attachment.target: attachment
            for attachment in self.scroll_attachments.values()
            if attachment.target and attachment.mode in ("native", "wrap")
        }

    def _find_scroll_attachments(self) -> dict[str, ScrollAttachment]:
        """Pair each Tk scrollbar with the widget it scrolls.

        The designer stores scrollbars either inside the widget they scroll
        (the usual canvas pattern) or as a sibling in the same parent, so both
        are considered.  Anything ambiguous keeps the placeholder behaviour.
        """
        attachments: dict[str, ScrollAttachment] = {}
        for name in self.order:
            if self.widget_type(name) != "ttk::scrollbar":
                continue
            orientation = self.option(name, "orient").lower() or "vertical"
            thickness = self._scrollbar_thickness(name, orientation)
            target = self._scroll_target(name)
            if not target or self.skipped(target):
                mode = "placeholder"
            elif orientation != "vertical":
                mode = "placeholder"
            elif self.widget_type(target) in SELF_SCROLLING_TYPES:
                mode = "self"
            elif self.widget_type(target) in WRAPPED_SCROLL_TYPES:
                mode = "wrap"
            else:
                mode = "native"
            attachments[name] = ScrollAttachment(
                scrollbar=name,
                orientation=orientation,
                thickness=thickness,
                target=target if mode in ("native", "wrap", "self") else "",
                mode=mode,
            )
        return attachments

    def _scroll_target(self, scrollbar: str) -> str:
        """Return the widget *scrollbar* scrolls, or ``""`` when ambiguous."""
        parent = _text(self.widget(scrollbar).get("WidgetParent", self.root_name))
        parent = parent or self.root_name
        if self.widget_type(parent) in SCROLLABLE_WIDGET_TYPES:
            return parent
        candidates = [
            child
            for child in self.children.get(parent, [])
            if child != scrollbar
            and self.widget_type(child) in SCROLLABLE_WIDGET_TYPES
        ]
        return candidates[0] if len(candidates) == 1 else ""

    def _scrollbar_thickness(self, name: str, orientation: str) -> int:
        """Return the pixel thickness of a scrollbar from its saved geometry."""
        place = self.widget(name).get("Place") or {}
        key = "height" if orientation == "horizontal" else "width"
        thickness = _number(place.get(key)) or _number(self.option(name, key))
        if not thickness:
            return 16
        return max(2, int(thickness))

    @property
    def list_variables(self) -> frozenset[str]:
        """Names used as a listbox ``listvariable``, i.e. list valued."""
        names = set()
        for name in self.order:
            candidate = self.option(name, "listvariable")
            if project_format.valid_python_name(candidate):
                names.add(candidate)
        return frozenset(names)

    def default_size(self, widget_type: Any) -> tuple[int, int]:
        """Return the designer's own size for a widget type."""
        size = tool_defaults.place_size(_text(widget_type))
        return int(size.get("width", 120)), int(size.get("height", 32))

    def colour(self, slot: Any) -> str | None:
        """Return one theme palette colour, or ``None`` when it is unknown."""
        value = self.palette.get("colors", {}).get(_text(slot))
        return value if isinstance(value, str) and value.startswith("#") else None

    def ink(self, colour: Any) -> str | None:
        """Return readable text for a filled colour, the way ttkbootstrap does.

        Verified against the resolved ttk styles: light fills get black text
        (tokyo-night, solar) and dark fills get white (darkly, sandstone).
        """
        if not colour:
            return self.colour("fg")
        if hex_luminance(colour) > INK_LUMINANCE_THRESHOLD:
            return "#000000"
        return "#ffffff"

    @property
    def dark_theme(self) -> bool:
        """Whether the theme's surface is dark, so Flet can match it."""
        surface = self.colour("bg")
        return bool(surface) and hex_luminance(surface) < 0.5

    def bootstyle_styles(self, bootstyle: Any) -> dict:
        """Return the resolved ttkbootstrap colours for one bootstyle."""
        styles = self.palette.get("styles")
        record = styles.get(_text(bootstyle)) if isinstance(styles, Mapping) else None
        return dict(record) if isinstance(record, Mapping) else {}

    def widget_surface(self, key: str) -> str | None:
        """Return a resolved theme widget colour such as ``entry_bg``."""
        widgets = self.palette.get("widgets")
        value = widgets.get(key) if isinstance(widgets, Mapping) else None
        return value if isinstance(value, str) and value.startswith("#") else None

    def style_of(self, name: str) -> tuple[str, frozenset[str]]:
        """Return the bootstyle colour and variants of a widget's style."""
        return parse_bootstyle(self.option(name, "style"))

    def policy_for(self, name: str) -> str:
        """Return the configured Flet policy for one widget's type."""
        key = _widget_key(self.widget_type(name))
        return str(self.policy.get(key, self.policy.get("default", "full")))

    def skipped(self, name: str) -> bool:
        """Return whether the tool defaults exclude *name* from Flet output."""
        return self.policy_for(name) == "skip"

    def hidden(self, name: str) -> bool:
        """Return whether *name* is folded into another control or skipped."""
        if self.skipped(name):
            return True
        attachment = self.scroll_attachments.get(name)
        return attachment is not None and attachment.mode in ("native", "wrap", "self")

    def visible_parent(self, name: str) -> str:
        """Return the nearest ancestor that is actually emitted."""
        parent = _text(self.widget(name).get("WidgetParent", self.root_name))
        parent = parent or self.root_name
        guard = 0
        while parent != self.root_name and self.hidden(parent) and guard < 32:
            parent = (
                _text(self.widget(parent).get("WidgetParent", self.root_name))
                or self.root_name
            )
            guard += 1
        return parent

    def visible_children(self, name: str) -> list[str]:
        """Return *name*'s children, promoting children of skipped widgets.

        A skipped container must not take its children down with it, so the
        grandchildren are spliced into the parent's list in place.
        """
        visible: list[str] = []
        for child in self.children.get(name, []):
            if self.hidden(child):
                visible.extend(self.visible_children(child))
            else:
                visible.append(child)
        return visible

    def attachment(self, name: str) -> ScrollAttachment | None:
        """Return the scrollbar attachment that targets *name*, if any."""
        return self.scroll_targets.get(name)

    @property
    def absolute_grid(self) -> bool:
        """Whether Grid is rendered with exact pixel positions."""
        return self.geom_manager == "Grid" and self.grid_mode == "absolute"

    def widget(self, name: str) -> Mapping[str, Any]:
        widget_data = self.data.get(name)
        return widget_data if isinstance(widget_data, Mapping) else {}

    def widget_type(self, name: str) -> str:
        return _text(self.widget(name).get("WidgetName"))

    def attributes(self, name: str) -> list[tuple[str, str]]:
        return list(project_format.iter_attributes(name, self.widget(name)))

    def option(self, name: str, key: str) -> str:
        """Return the last saved value of one Tk option, or ``""``."""
        for candidate, value in self.attributes(name):
            if candidate == key:
                return _text(value)
        return ""

    def is_tab(self, name: str) -> bool:
        return layout_model.is_saved_notebook_tab(self.data, name, self.root_name)

    def context(self, name: str) -> dict[str, Any]:
        return {
            "name": name,
            "root": self.root_name,
            "callbacks": set(self.callbacks),
            "variables": set(self.variables),
            "images": self.images,
        }


def _image_files(project_data: Mapping[str, Any]) -> dict[str, str]:
    """Return ``{widget name: filename}`` from the saved image list."""
    files: dict[str, str] = {}
    for entry in project_data.get("imageFileNames") or []:
        if isinstance(entry, str) or not isinstance(entry, Sequence):
            continue
        if len(entry) < 3:
            continue
        widget_name, filename = _text(entry[0]), _text(entry[2])
        if widget_name and filename:
            files[widget_name] = filename
    return files


class _Emitter:
    """Builds the generated program one control at a time."""

    def __init__(self, project: _Project) -> None:
        self.project = project
        self.lines: list[str] = []
        self.notes: list[str] = []
        self.defined: set[str] = set()
        self.helpers: list[str] = []
        self.text_bindings: dict[str, list[tuple[str, str]]] = {}

    # -- control emission ------------------------------------------------
    def _arguments(self, name: str, control: str) -> tuple[dict[str, str], list[str]]:
        """Return ``{keyword: bare expression}`` for one widget's control.

        Values carry no ``keyword=`` prefix; the caller adds it so the same
        arguments can be reused either directly or inside a wrapper control.
        """
        widget_type = self.project.widget_type(name)
        properties, unmapped = translate_attributes(
            widget_type, self.project.attributes(name), self.project.context(name)
        )
        arguments: dict[str, str] = dict(self._style_arguments(name, control))
        if control == "ft.Text":
            arguments["value"] = self._caption(name, "value", properties, arguments)
        elif control == "ft.Button":
            arguments["content"] = self._caption(
                name, "content", properties, arguments
            )
        elif control == "ft.Checkbox":
            arguments["label"] = repr(properties.pop("text", name))
            if "value" in properties:
                # Tk selects a checkbutton when its variable equals onvalue
                # (default "1"), not when the value is merely non-empty - a
                # variable holding the tool's usual '0.0' is *off*, and
                # bool('0.0') would have drawn it ticked.
                variable = properties.pop("value")
                onvalue = self.project.option(name, "onvalue") or "1"
                arguments["value"] = f"str({variable}) == {onvalue!r}"
        elif control == "ft.RadioGroup":
            # Tk: the widget is selected when the *variable* equals the
            # widget's own value.  So the group follows the variable and the
            # inner radio carries the widget's value - using the widget value
            # for both would make every radio look selected.
            widget_value = properties.pop("current", None)
            variable = properties.pop("value", None)
            radio_value = repr(_text(widget_value) if widget_value is not None else "0")
            if variable is not None:
                arguments["value"] = f"str({variable})"
            else:
                arguments["value"] = radio_value
            label = repr(properties.pop("text", name))
            arguments["content"] = (
                f"ft.Radio(value={radio_value}, label={label}"
                f"{self._radio_colours(name)})"
            )
        elif control == "ft.Dropdown":
            values = properties.pop("values", None)
            if values:
                options = ", ".join(
                    f"ft.DropdownOption(key={value!r}, text={value!r})"
                    for value in values
                )
                arguments["options"] = f"[{options}]"
        elif control == "ft.Slider":
            if properties.pop("value", None):
                self.notes.append(
                    f"# {name}: Tk variable is not bound to ft.Slider.value"
                )
            arguments.update(self._slider_arguments(properties))
            properties = {}
        elif control == "ft.ProgressBar":
            if properties.pop("value", None):
                self.notes.append(
                    f"# {name}: Tk variable is not bound to ft.ProgressBar.value"
                )
            arguments.update(self._progress_arguments(properties))
            properties = {}
        elif control == "ft.ListView":
            values = properties.pop("values", None)
            if values:
                arguments["controls"] = _list_expression(
                    [f"ft.Text({value!r})" for value in values]
                )
            if properties.pop("list_variable", None):
                self.notes.append(
                    f"# {name}: listbox items live in the module level list "
                    "of the same name - append to it and call page.update()"
                )
        elif control == "ft.Container" and self._is_filled_label(name):
            arguments.update(self._filled_label(name, properties))
        elif control == "ft.Container" and widget_type in TEXT_WIDGET_TYPES:
            arguments.update(self._text_area(name, properties))
        elif control == "ft.Container" and widget_type in (
            "ttk::frame",
            "ttk::canvas",
            "canvas",
            "frame",
        ):
            relief = self._relief_border(name)
            if relief:
                arguments["border"] = self._border(relief[1], relief[0])
        elif control == "ft.DataTable":
            columns = properties.pop("tree_columns", [])
            arguments["columns"] = (
                "["
                + ", ".join(
                    f"ft.DataColumn(label=ft.Text({name!r}))" for name in columns
                )
                + "]"
            )
            arguments["rows"] = "[]"
        elif control == "ft.TextField":
            if widget_type in TEXT_MEASURED_TYPES:
                arguments["multiline"] = "True"
        elif control == "ft.Divider":
            if properties.pop("orientation", "") == "vertical":
                self.notes.append(
                    f"# {name}: Tk vertical separator emitted as horizontal ft.Divider"
                )

        for keyword, value in properties.items():
            if keyword in (
                "text",
                "command",
                "image",
                "orientation",
                "style",
                "list_variable",
            ):
                continue
            if keyword == "size" and control in ("ft.TextField", "ft.Dropdown"):
                # A font size on an entry/combobox is ft text_size; neither
                # control has a "size" field, and passing one is a TypeError.
                keyword = "text_size"
            if keyword in arguments and keyword in STRUCTURAL_ARGUMENTS:
                continue
            if keyword not in CONTROL_OPTIONS.get(control, UNIVERSAL_OPTIONS):
                unmapped.append(keyword)
                continue
            if keyword == "disabled" and value == "False":
                continue
            arguments[keyword] = value

        if properties.get("image"):
            arguments["content"] = f"{name}image"
            self.notes.append(f"# {name}: Tk image emitted as the {name}image control")

        command = properties.get("command")
        if command:
            arguments[self._event_keyword(control)] = command

        return arguments, unmapped

    @staticmethod
    def _label_alignment(anchor: str) -> str:
        """Map a Tk label anchor onto an ft.Alignment."""
        mapping = {
            "w": "ft.Alignment.CENTER_LEFT",
            "nw": "ft.Alignment.TOP_LEFT",
            "sw": "ft.Alignment.BOTTOM_LEFT",
            "e": "ft.Alignment.CENTER_RIGHT",
            "ne": "ft.Alignment.TOP_RIGHT",
            "se": "ft.Alignment.BOTTOM_RIGHT",
            "n": "ft.Alignment.TOP_CENTER",
            "s": "ft.Alignment.BOTTOM_CENTER",
        }
        return mapping.get(anchor.strip().lower(), "ft.Alignment.CENTER")

    def _text_height(self, name: str) -> int:
        """Return the height the designer gave a widget, in pixels."""
        height = _number(self._placement_arguments(name).get("height"))
        if not height:
            natural = self._natural_size(name)
            height = natural[1] if natural else 0
        return int(height or 0)

    def _text_area(self, name: str, properties: dict[str, Any]) -> dict[str, str]:
        """Return a Container holding a multiline field sized to the design.

        Flet ignores an explicit height on a multiline field (measured: 120px
        rendered 46px) and sizes it from ``min_lines`` instead, which lands
        within about 10px.  The Container supplies the exact design box and
        clips, and both it and the field carry the widget's background so the
        fill is continuous.
        """
        style = dict(self._style_arguments(name, "ft.TextField"))
        background = properties.pop("bgcolor", None) or style.pop("bgcolor", None)
        # The style values are quoted literals; _border() wants the raw colour.
        border_colour = str(style.pop("border_color", "")).strip("'\"") or None
        border_width = style.pop("border_width", None)
        lines = multiline_lines(self._text_height(name))
        field_arguments = ["multiline=True", "border_width=0"]
        if lines:
            field_arguments.append(f"min_lines={lines}")
        value = self._caption(name, "value", properties, {})
        if value and value != "''":
            field_arguments.append(f"value={value}")
        for key in (
            "color",
            "text_size",
            "content_padding",
            "text_vertical_align",
            "disabled",
            "read_only",
        ):
            if key in style:
                field_arguments.append(f"{key}={style[key]}")
        if background:
            field_arguments.append(f"bgcolor={background}")
        arguments = {"content": _call("ft.TextField", field_arguments)}
        if background:
            arguments["bgcolor"] = background
        if border_colour:
            arguments["border"] = self._border(border_colour, int(border_width or 1))
        arguments["clip_behavior"] = "ft.ClipBehavior.HARD_EDGE"
        return arguments

    def _is_filled_label(self, name: str) -> bool:
        """Whether a label is drawn as a coloured box rather than plain text.

        ttk fills a label for the ``inverse`` style, and a designer can also set
        an explicit background.  A label the tool default has turned into a
        placeholder is not filled - it is a plain stand-in Container.
        """
        if self.project.widget_type(name) != "ttk::label":
            return False
        if self.project.policy_for(name) == "placeholder":
            return False
        _bootstyle, variants = self.project.style_of(name)
        if "inverse" in variants or self.project.option(name, "background"):
            return True
        return self._relief_border(name) is not None

    def _filled_label(self, name: str, properties: dict[str, Any]) -> dict[str, str]:
        """Return the arguments for a label drawn inside a coloured box."""
        style = dict(self._style_arguments(name, "ft.Text"))
        fill = properties.pop("bgcolor", None) or style.pop("bgcolor", None)
        style.pop("value", None)
        # _label_alignment below handles the anchor; the generic anchor mapping
        # is for plain containers and would lose the vertical centring.
        properties.pop("alignment", None)
        allowed = ("color", "size", "font_family", "weight", "italic", "text_align")
        inner = _call(
            "ft.Text",
            [f"value={properties.pop('text', '')!r}"]
            + [f"{key}={style[key]}" for key in allowed if key in style],
        )
        arguments = {"content": inner}
        if fill:
            arguments["bgcolor"] = fill
        relief = self._relief_border(name)
        if relief:
            arguments["border"] = self._border(relief[1], relief[0])
        arguments["alignment"] = self._label_alignment(
            self.project.option(name, "anchor")
        )
        return arguments

    def _caption(
        self,
        name: str,
        attribute: str,
        properties: dict[str, Any],
        arguments: dict[str, str],
    ) -> str:
        """Return the caption expression for a button or label.

        A designer widget often carries no literal ``text`` at all: the caption
        lives in a ``textvariable`` that the application sets at runtime, which
        is why a sudoku cell shows "11".  The variable drives the control here
        too, and the binding is recorded so generated code can refresh it.
        """
        text = _text(properties.pop("text", ""))
        if text:
            return repr(text)
        variable = properties.pop("value", None)
        if variable:
            # One variable can caption many widgets, as ttk variables do.
            self.text_bindings.setdefault(variable, []).append((name, attribute))
            arguments.pop("size", None)
            return variable
        return repr("")

    @staticmethod
    def _text_style(colour: str | None = None, size: int = DEFAULT_TEXT_SIZE) -> str:
        """Return an ``ft.TextStyle`` matching ttk's plain text.

        Flet renders a TextStyle that leaves the weight unset in *bold* (the
        field's default is None, and the Material label styles resolve that to
        a heavy face), which made button captions and check/radio labels look
        bolder than the ttk originals.  Both the weight and the letter spacing
        are therefore pinned.
        """
        parts = [f"size={size}", "weight=ft.FontWeight.NORMAL", "letter_spacing=0"]
        if colour:
            # Callers pass the raw colour, not a Python literal.
            parts.insert(0, f"color={str(colour).strip(chr(39) + chr(34))!r}")
        return _call("ft.TextStyle", parts)

    def _button_style(self, side: str | None = None) -> str:
        """Return the ``ft.ButtonStyle`` that matches a ttk button closely.

        Flet's default button padding is wide enough to wrap short captions
        inside the designer's button sizes, and its stadium shape does not look
        like a ttk button, so both are pinned here.
        """
        parts = [
            f"padding=ft.Padding(left={BUTTON_PADDING_X}, right={BUTTON_PADDING_X}"
            f", top={BUTTON_PADDING_Y}, bottom={BUTTON_PADDING_Y})",
            f"shape=ft.RoundedRectangleBorder(radius={BUTTON_RADIUS})",
            f"text_style={self._text_style(size=BUTTON_TEXT_SIZE)}",
        ]
        if side:
            parts.append(f"side=ft.BorderSide(1, {side!r})")
        return _call("ft.ButtonStyle", parts)

    def _relief_border(self, name: str) -> tuple[int, str] | None:
        """Return ``(width, colour)`` when the designer asked for a border.

        ttk draws a border for a relief other than flat/none and a borderwidth
        above zero - that pair is the designer's own signal, so it is honoured
        here rather than guessed at.  The colour comes from the theme's border.
        """
        relief = self.project.option(name, "relief").strip().lower()
        if relief in ("", "flat", "none"):
            return None
        width = _number(self.project.option(name, "borderwidth"))
        if width is None:
            width = _number(self.project.option(name, "bd"))
        if not width or int(width) <= 0:
            return None
        colour = (
            self.project.widget_surface("entry_border")
            or self.project.colour("border")
            or self.project.colour("fg")
        )
        if not colour:
            return None
        return int(width), colour

    @staticmethod
    def _border(colour: str, width: int = 1) -> str:
        """Return an ``ft.Border`` expression.

        Neither Flet 0.8x nor 1.0 provides ``ft.border.all()``, so the four
        sides are spelled out.
        """
        sides = [
            f"{side}=ft.BorderSide({width}, {colour!r})"
            for side in ("left", "top", "right", "bottom")
        ]
        return _call("ft.Border", sides)

    def _style_arguments(self, name: str, control: str) -> dict[str, str]:
        """Return Flet arguments that reproduce a ttkbootstrap widget style.

        Colours come from the palette exported by tools/export_theme_colors.py,
        which records what ttkbootstrap itself resolves for each theme and
        bootstyle (probed with ``style.lookup`` on real widgets).  That matters
        because the Bootswatch-derived themes shade the bootstyle colour rather
        than using the palette slot, and because ttk picks black or white text
        per fill.  When a theme is missing from the palette the slot colours
        and a luminance rule are used instead.
        """
        bootstyle, variants = self.project.style_of(name)
        resolved = self.project.bootstyle_styles(bootstyle) if bootstyle else {}
        slot = self.project.colour(bootstyle) if bootstyle else None
        surface = self.project.colour("bg") or "#ffffff"
        border = self.project.widget_surface("entry_border") or self.project.colour(
            "border"
        ) or surface
        muted = self.project.colour("fg") or "#ffffff"
        widget_type = self.project.widget_type(name)

        def value(key: str, fallback: str | None) -> str | None:
            return resolved.get(key) or fallback

        if control == "ft.Button":
            base = self._button_style()
            if "link" in variants:
                return {
                    "bgcolor": "None",
                    "color": repr(value("label_fg", slot) or muted),
                    "style": base,
                }
            if "outline" in variants:
                return {
                    "bgcolor": repr(value("outline_bg", surface) or surface),
                    "color": repr(value("outline_fg", slot) or muted),
                    "style": self._button_style(value("outline_border", slot)),
                }
            return {
                "bgcolor": repr(value("button_bg", slot) or surface),
                "color": repr(value("button_fg", self.project.ink(slot)) or muted),
                "style": base,
            }
        if control == "ft.Text":
            if "inverse" in variants:
                return {
                    "bgcolor": repr(value("inverse_bg", slot) or surface),
                    "color": repr(
                        value("inverse_fg", self.project.ink(slot)) or muted
                    ),
                    "size": str(DEFAULT_TEXT_SIZE),
                }
            # ttk paints a label with the theme's surface, which is what keeps
            # it readable on a bootstyle coloured frame.
            arguments = {
                "color": repr(value("label_fg", slot) or muted),
                "size": str(DEFAULT_TEXT_SIZE),
            }
            if surface:
                arguments["bgcolor"] = repr(surface)
            return arguments
        if control == "ft.Container":
            if widget_type == NOTEBOOK_WIDGET_TYPE:
                edge = self.project.widget_surface("notebook_border") or border
                return {
                    "bgcolor": repr(
                        self.project.widget_surface("notebook_bg") or surface
                    ),
                    "border": self._border(edge),
                }
            if widget_type == "ttk::labelframe":
                edge = value("labelframe_border", slot) or border
                stored_width = _number(self.project.option(name, "borderwidth"))
                if stored_width is not None and int(stored_width) <= 0:
                    # ttk draws no box for borderwidth=0: the caption alone
                    # marks the frame, as the Camera frame in Platypus shows.
                    return {"bgcolor": repr(surface)}
                relief = self._relief_border(name)
                width = relief[0] if relief else 1
                return {
                    "bgcolor": repr(surface),
                    "border": self._border(edge, width),
                }
            return {"bgcolor": repr(value("frame_bg", slot) or surface)}
        if control in ("ft.TextField", "ft.Dropdown"):
            arguments = {
                "bgcolor": repr(
                    self.project.widget_surface("entry_bg")
                    or self.project.colour("inputbg")
                    or surface
                ),
                "color": repr(
                    self.project.widget_surface("entry_fg")
                    or self.project.colour("inputfg")
                    or muted
                ),
                "border_color": repr(border),
                "border_width": "1",
                "text_size": str(DEFAULT_TEXT_SIZE),
                "content_padding": _call(
                    "ft.Padding",
                    [
                        f"left={FIELD_PADDING_X}",
                        f"right={FIELD_PADDING_X}",
                        f"top={FIELD_PADDING_Y}",
                        f"bottom={FIELD_PADDING_Y}",
                    ],
                ),
            }
            if control == "ft.TextField":
                # ft.Dropdown has no text_vertical_align.
                arguments["text_vertical_align"] = "ft.VerticalAlignment.CENTER"
            return arguments
        if control == "ft.ProgressBar":
            return {
                "color": repr(slot or surface),
                "bgcolor": repr(
                    self.project.widget_surface("progressbar_trough") or border
                ),
            }
        if control == "ft.Slider":
            return {
                "active_color": repr(slot or surface),
                "thumb_color": repr(slot or surface),
                "inactive_color": repr(
                    self.project.widget_surface("scale_trough") or border
                ),
            }
        if control == "ft.Divider":
            return {"color": repr(slot or border)}
        if control == "ft.Checkbox":
            caption = value("checkbutton_fg", muted) or muted
            # Only the tick colour is set here.  A fill colour would be painted
            # in both states, so the checked fill comes from the page's theme
            # seed - the project's primary colour - which keeps the box empty
            # while it is unchecked, as ttk draws it.
            return {
                "check_color": repr(self.project.ink(slot) or muted),
                "label_style": self._text_style(caption),
            }
        return {}

    def _theme_defaults(self, control: str) -> dict[str, str]:
        """Return surface colours for a widget with no ttkbootstrap style."""
        if control == "ft.Text":
            ink = self.project.colour("fg")
            surface = self.project.colour("bg")
            arguments = {"size": str(DEFAULT_TEXT_SIZE)}
            if ink:
                arguments["color"] = repr(ink)
            if surface:
                arguments["bgcolor"] = repr(surface)
            return arguments
        if control == "ft.Container":
            surface = self.project.colour("bg")
            return {"bgcolor": repr(surface)} if surface else {}
        if control == "ft.Checkbox":
            muted = self.project.colour("fg")
            if not muted:
                return {}
            return {"label_style": self._text_style(muted)}
        if control in ("ft.TextField", "ft.Dropdown"):
            return {
                "bgcolor": repr(self.project.colour("inputbg") or ""),
                "color": repr(self.project.colour("inputfg") or ""),
            }
        return {}

    def _radio_colours(self, name: str) -> str:
        """Return colour keywords for the ``ft.Radio`` inside a group.

        ttkbootstrap colours a radiobutton's indicator with the bootstyle and
        leaves the caption in the theme's text colour.
        """
        bootstyle, _variants = self.project.style_of(name)
        caption = self.project.bootstyle_styles(bootstyle).get(
            "checkbutton_fg"
        ) or self.project.colour("fg")
        parts = []
        if caption:
            parts.append(f"label_style={self._text_style(caption)}")
        return "".join(f", {part}" for part in parts)

    def _placement_arguments(self, name: str) -> dict[str, str]:
        """Return absolute Stack positioning for *name*.

        Used for ``Place`` and for ``Grid`` when the caller asked for the
        exact-position ("absolute") layout mode.
        """
        if self.project.is_tab(name):
            return {}
        if self.project.geom_manager == "Grid" and self.project.absolute_grid:
            return self._grid_placement(name)
        if self.project.geom_manager != "Place":
            return {}
        widget_data = self.project.widget(name)
        source = widget_data.get("Place") or widget_data.get("GeomData") or {}
        arguments: dict[str, str] = {}
        x = _number(source.get("x"))
        y = _number(source.get("y"))
        width = _number(source.get("width"))
        height = _number(source.get("height"))
        if x is not None:
            arguments["left"] = str(int(x))
        if y is not None:
            arguments["top"] = str(int(y))
        if _text(source.get("relwidth")).strip():
            arguments["right"] = "0"
        elif width is not None:
            arguments["width"] = str(int(width))
        if _text(source.get("relheight")).strip():
            arguments["bottom"] = "0"
        elif height is not None:
            arguments["height"] = str(int(height))
        return arguments

    def _grid_placement(self, name: str) -> dict[str, str]:
        """Return pixel positioning derived from a widget's Grid geometry."""
        widget_data = self.project.widget(name)
        parent = self.project.visible_parent(name)
        state = layout_model.GridGeometry.from_mapping(
            widget_data.get("GeomData") or {}, parent=parent
        )
        columns, rows = self._grid_lengths(parent)
        left = sum(columns[index] for index in range(state.column))
        left += state.padx * state.column
        top = sum(rows[index] for index in range(state.row)) + state.pady * state.row
        width = sum(
            columns[index]
            for index in range(state.column, state.column + state.columnspan)
        )
        width += state.padx * max(0, state.columnspan - 1)
        height = sum(
            rows[index] for index in range(state.row, state.row + state.rowspan)
        )
        height += state.pady * max(0, state.rowspan - 1)
        arguments = {
            "left": str(int(left + state.padx)),
            "top": str(int(top + state.pady)),
            "width": str(max(1, int(width - 2 * state.padx))),
            "height": str(max(1, int(height - 2 * state.pady))),
        }
        return arguments

    def _grid_lengths(
        self, parent_name: str, depth: int = 0
    ) -> tuple[list[int], list[int]]:
        """Return pixel column widths and row heights for a Grid parent.

        Tk sizes a column to the largest widget in it, with ``minsize`` only a
        floor - which is why the stored minsizes ('2.5m' is about 9px) must not
        be used as the cell size on their own.  Each widget's natural size is
        the designer's own measurement when available (``winfo_reqwidth``), the
        measured size of a container's children, or the tool default for its
        type.
        """
        columns, rows = self.project.grid_requirements.get(parent_name, (0, 0))
        if parent_name == self.project.root_name:
            data = self.project.data
            column_size = tk_length(data.get("gridColMinsize"), 20) or 20
            row_size = tk_length(data.get("gridRowMinsize"), 20) or 20
        else:
            # Mirrors the minsize the Python backend emits for containers.
            column_size, row_size = 40, 24
        widths = [max(1, column_size)] * max(1, columns)
        heights = [max(1, row_size)] * max(1, rows)
        for child in self.project.visible_children(parent_name):
            widget_data = self.project.widget(child)
            state = layout_model.GridGeometry.from_mapping(
                widget_data.get("GeomData") or {}, parent=parent_name
            )
            widths, heights = _ensure_span(
                widths,
                heights,
                state.column,
                state.row,
                state.columnspan,
                state.rowspan,
            )
            natural = self._natural_size(child, depth + 1)
            if not natural:
                continue
            _grow_axis(
                widths,
                state.column,
                state.columnspan,
                natural[0] + 2 * max(0, state.padx),
            )
            _grow_axis(
                heights,
                state.row,
                state.rowspan,
                natural[1] + 2 * max(0, state.pady),
            )
        return widths, heights

    def _natural_size(self, name: str, depth: int = 0) -> tuple[int, int] | None:
        """Return a widget's natural size in pixels, or ``None`` if unknown.

        The designer's measurement is used when it has one, but never below the
        tool default for that widget type: an empty ``textvariable`` makes a
        button request almost no width, and sizing cells from that would give
        the near-invisible layout this mode used to produce.  A container is
        measured from the grid inside it, the way Tk requests it.
        """
        known = self.project.natural_sizes.get(name)
        widget_type = self.project.widget_type(name)
        children = self.project.visible_children(name)
        is_box = is_container(widget_type) or widget_type == NOTEBOOK_WIDGET_TYPE
        if depth < 16 and children and is_box and self.project.geom_manager == "Grid":
            columns, rows = self._grid_lengths(name, depth)
            computed = (sum(columns), sum(rows))
            if known:
                return (max(computed[0], known[0]), max(computed[1], known[1]))
            return computed
        if is_box and not children and widget_type == NOTEBOOK_WIDGET_TYPE:
            return None
        default = self.project.default_size(widget_type)
        if known:
            return (max(known[0], default[0]), max(known[1], default[1]))
        return default

    def window_size(self) -> tuple[int, int]:
        """Return a starting window size worked out from the design.

        Every mode derives its size from the project rather than a fixed
        800x600: Grid and Pack from the widgets and their spans, Place from the
        furthest edge a widget is placed at.  The value only sets the size the
        program opens at - the layout reflows when the window is resized, and
        the generated ``WINDOW_WIDTH``/``WINDOW_HEIGHT`` constants are there to
        be edited.
        """
        if self.project.geom_manager == "Grid":
            if self.project.absolute_grid:
                # Exact positions follow Tk: the deficit of a spanning widget
                # goes to the last cell it covers.
                columns, rows = self._grid_lengths(self.project.root_name)
                used_columns, used_rows = self.project.grid_requirements.get(
                    self.project.root_name, (len(columns), len(rows))
                )
                return self._clamp_window(
                    sum(columns[:used_columns]), sum(rows[:used_rows])
                )
            # Responsive: the layout shares space evenly across a span, so the
            # window is sized the same way or the content overflows it.
            return self._clamp_window(
                sum(self._axis_weights(self.project.root_name, "column").values()),
                sum(self._axis_weights(self.project.root_name, "row").values()),
            )
        if self.project.geom_manager == "Pack":
            width = 0
            height = 0
            for child in self.project.visible_children(self.project.root_name):
                natural = self._natural_size(child)
                if not natural:
                    continue
                width = max(width, natural[0])
                height += natural[1]
            return self._clamp_window(width, height)
        return window_size(
            self.project.data, self.project.order, self.project.root_name
        )

    @staticmethod
    def _clamp_window(width: int, height: int) -> tuple[int, int]:
        """Return the design size, kept inside sensible window bounds."""
        return (
            max(MIN_WINDOW_WIDTH, min(MAX_WINDOW_WIDTH, int(width) + 20)),
            max(MIN_WINDOW_HEIGHT, min(MAX_WINDOW_HEIGHT, int(height) + 20)),
        )

    @staticmethod
    def _event_keyword(control: str) -> str:
        if control == "ft.Dropdown":
            return "on_select"
        if control in ("ft.Slider", "ft.TextField", "ft.Checkbox", "ft.RadioGroup"):
            return "on_change"
        return "on_click"

    @staticmethod
    def _slider_arguments(properties: Mapping[str, Any]) -> dict[str, str]:
        minimum = float(properties.get("minimum", 0.0) or 0.0)
        maximum = properties.get("maximum")
        current = properties.get("current")
        if maximum is None:
            maximum = max(minimum + 1.0, float(current or minimum))
        maximum = float(maximum)
        if maximum <= minimum:
            maximum = minimum + 1.0
        arguments = {"min": repr(minimum), "max": repr(maximum)}
        if current is not None:
            value = min(maximum, max(minimum, float(current)))
            arguments["value"] = repr(value)
        return arguments

    @staticmethod
    def _progress_arguments(properties: Mapping[str, Any]) -> dict[str, str]:
        maximum = float(properties.get("range_maximum", 100.0) or 100.0)
        current = properties.get("current")
        arguments: dict[str, str] = {}
        if current is not None:
            fraction = 0.0 if maximum <= 0 else float(current) / maximum
            arguments["value"] = repr(round(max(0.0, min(1.0, fraction)), 4))
        if "color" in properties:
            arguments["color"] = str(properties["color"])
        if "bgcolor" in properties:
            arguments["bgcolor"] = str(properties["bgcolor"])
        return arguments

    # -- structural expressions ------------------------------------------
    def _stack(self, children: Sequence[str]) -> str:
        names = [name for name in map(self._define, children) if name]
        return _call("ft.Stack", [_list_argument("controls", names)])

    def _rows(self, parent_name: str, children: Sequence[str]) -> str:
        columns, _rows = self.project.grid_requirements.get(parent_name, (0, 0))
        cells: dict[tuple[int, int], tuple[str, int, int, int | None, bool]] = {}
        row_indexes: set[int] = set()
        for child in children:
            geometry = self.project.widget(child).get("GeomData") or {}
            state = layout_model.GridGeometry.from_mapping(geometry)
            defined = self._define(child)
            if not defined:
                continue
            natural = self._natural_size(child)
            sticky = self._grid_sticky(child)
            # A widget that does not fill vertically keeps its designed height,
            # which the cell enforces so a stretched row cannot inflate it.
            fills_vertical = self._fills(sticky, "n", "s")
            cell_height = None
            if natural and not fills_vertical:
                cell_height = int(natural[1])
            cells[(state.row, state.column)] = (
                defined,
                state.columnspan,
                state.padx,
                cell_height,
                fills_vertical,
            )
            row_indexes.add(state.row)
            columns = max(columns, state.column + state.columnspan)
            if state.rowspan > 1:
                self.notes.append(
                    f"# {child}: grid rowspan={state.rowspan} is approximated in Flet"
                )
        if not columns or not row_indexes:
            return "ft.Column()"
        weights = self._row_weights(parent_name)
        rows: list[str] = []
        for row in sorted(row_indexes):
            row_cells: list[str] = []
            fills_vertical = False
            column = 0
            while column < columns:
                match = cells.get((row, column))
                if match:
                    child, span, pad, cell_height, fills = match
                    row_cells.append(
                        self._grid_cell(child, span, pad, cell_height, fills)
                    )
                    fills_vertical = fills_vertical or self._fills(
                        self._grid_sticky(child), "n", "s"
                    )
                    column += max(1, span)
                else:
                    row_cells.append("ft.Container(expand=1)")
                    column += 1
            arguments = [
                _list_argument("controls", row_cells),
                "spacing=0",
                # Rows share the extra space in proportion to their content, so
                # the grid grows with the window without stretching a one line
                # widget to the height of the tallest row.
                f"expand={max(1, weights.get(row, 1))}",
            ]
            if fills_vertical:
                # ttk's sticky=nsew stretches the widget to its cell, which is
                # what makes a sudoku board grow with the window.
                arguments.append(
                    "vertical_alignment=ft.CrossAxisAlignment.STRETCH"
                )
            rows.append(_call("ft.Row", arguments))
        return _call(
            "ft.Column",
            [_list_argument("controls", rows), "spacing=0", "expand=True"],
        )

    @staticmethod
    @staticmethod
    def _grid_cell(
        child: str,
        columnspan: int,
        padx: Any,
        height: int | None = None,
        fills_vertical: bool = False,
    ) -> str:
        """Return the cell that holds one grid widget.

        A widget with ``sticky=nsew`` has to be given a definite height, or the
        weighted rows inside it collapse: Flutter gives ``expand`` children no
        intrinsic size, so a frame sized to its content would shrink to a
        single row.  The cell therefore wraps those widgets in a stretched
        ``ft.Row``, and only pins a height for the ones that keep their own.
        """
        padding = _number(padx, 2) or 0
        expand = max(1, int(columnspan))
        if fills_vertical:
            inner = _call(
                "ft.Row",
                [
                    _list_argument("controls", [child]),
                    "spacing=0",
                    "expand=True",
                    "vertical_alignment=ft.CrossAxisAlignment.STRETCH",
                ],
            )
            return _call(
                "ft.Container",
                [f"content={inner}", f"expand={expand}", f"padding={int(padding)}"],
            )
        arguments = [
            f"content={child}",
            f"expand={expand}",
            f"padding={int(padding)}",
        ]
        if height:
            # The cell keeps the designer's height, so a stretched row cannot
            # inflate a control that is not meant to fill it (ttk semantics).
            arguments.append(f"height={int(height)}")
        return _call("ft.Container", arguments)

    def _axis_weights(self, parent_name: str, axis: str) -> dict[int, int]:
        """Return even-distributed content sizes for a grid parent's rows/cols.

        The responsive layout gives a widget's cell a share proportional to its
        span, so the rows and columns it covers share its natural size.  That
        is a different model from :meth:`_grid_lengths`, which follows Tk's
        "deficit to the last cell" rule for exact positions.
        """
        _columns, rows = self.project.grid_requirements.get(parent_name, (0, 0))
        count = rows if axis == "row" else _columns
        weights: dict[int, int] = {index: 0 for index in range(max(0, count))}
        for child in self.project.visible_children(parent_name):
            state = layout_model.GridGeometry.from_mapping(
                self.project.widget(child).get("GeomData") or {}, parent=parent_name
            )
            natural = self._natural_size(child)
            if not natural:
                continue
            if axis == "row":
                start, span = state.row, max(1, state.rowspan)
                size = natural[1] + 2 * max(0, state.pady)
                if span > 1:
                    # A row spanning widget occupies a single band here (the
                    # responsive layout cannot span rows), so it is given its
                    # own height rather than a share of the rows it covers.
                    # Without this it collapses to one row's weight and looks
                    # nothing like the designer.
                    self.notes.append(
                        f"# {child}: grid rowspan={span} is approximated in Flet"
                    )
            else:
                start, span = state.column, max(1, state.columnspan)
                size = natural[0] + 2 * max(0, state.padx)
            share = max(1, int(round(size / span))) if axis == "column" else max(
                1, int(size)
            )
            for index in range(start, start + span):
                weights[index] = max(weights.get(index, 0), share)
        return weights

    def _row_weights(self, parent_name: str) -> dict[int, int]:
        """Return a relative height weight for each row of a grid parent.

        Flet shares space by weight, so giving every row the same weight
        stretches a one line widget to the height of the tallest row.  Tk sizes
        a row to its content first and only then shares the extra space, so the
        weights follow the content: a widget's natural height spread over the
        rows it spans.
        """
        return self._axis_weights(parent_name, "row")

    def _grid_sticky(self, name: str) -> str:
        """Return a widget's grid ``sticky`` option in lower case."""
        geometry = self.project.widget(name).get("GeomData") or {}
        return _text(geometry.get("sticky")).lower()

    @staticmethod
    def _fills(sticky: str, first: str, second: str) -> bool:
        """Whether *sticky* stretches along the axis named by two letters."""
        return bool(sticky) and first in sticky and second in sticky

    def _packed(self, children: Sequence[str]) -> str:
        groups: dict[str, list[str]] = {
            "top": [],
            "bottom": [],
            "left": [],
            "right": [],
        }
        for child in children:
            geometry = self.project.widget(child).get("GeomData") or {}
            side = _text(geometry.get("side", "top")) or "top"
            expand = _text(geometry.get("expand", "0")) not in ("", "0", "False")
            fill = _text(geometry.get("fill", "none"))
            name = self._define(child)
            if not name:
                continue
            if expand:
                name = _call("ft.Container", [f"content={name}", "expand=True"])
            if fill not in ("none", "both", "x", "y", ""):
                self.notes.append(
                    f"# {child}: pack fill={fill!r} has no Flet equivalent"
                )
            groups.setdefault(side, []).append(name)

        sections: list[str] = list(groups.get("top", []))
        left, right = groups.get("left", []), groups.get("right", [])
        if left or right:
            middle: list[str] = []
            for column in (left, right):
                if column:
                    middle.append(
                        _call(
                            "ft.Column",
                            [
                                _list_argument("controls", column),
                                "spacing=0",
                                "expand=True",
                            ],
                        )
                    )
            sections.append(
                _call(
                    "ft.Row",
                    [_list_argument("controls", middle), "spacing=0", "expand=True"],
                )
            )
        sections.extend(groups.get("bottom", []))
        return _call(
            "ft.Column",
            [_list_argument("controls", sections), "spacing=0", "expand=True"],
        )

    def _notebook(self, children: Sequence[str]) -> str:
        """Return the ``ft.Column`` holding the tab bar and its pages."""
        tabs: list[str] = []
        panes: list[str] = []
        for index, child in enumerate(children, start=1):
            tabs.append(f"ft.Tab(label={'Tab ' + str(index)!r})")
            panes.append(self._define(child) or child)
        tab_bar = _call("ft.TabBar", [_list_argument("tabs", tabs)])
        view = _call(
            "ft.TabBarView", [_list_argument("controls", panes), "expand=True"]
        )
        return _call(
            "ft.Column",
            [_list_argument("controls", [tab_bar, view]), "expand=True", "spacing=0"],
        )

    # -- tree walking ----------------------------------------------------
    def _define(self, name: str) -> str:
        """Return the variable name for *name*, emitting it on first use."""
        if name in self.defined:
            return None if self.project.hidden(name) else name
        if self.project.hidden(name):
            # Folded into the control it scrolls; never emitted on its own.
            self.defined.add(name)
            return None
        self.defined.add(name)
        widget_type = self.project.widget_type(name)
        control = widget_control(widget_type)
        children = self.project.visible_children(name)
        if widget_type == "ttk::label":
            if self._is_filled_label(name) or self.project.option(name, "image"):
                # A filled label (ttk's inverse style, or an explicit
                # background) is wrapped: ft.Text only paints behind its
                # glyphs, so the fill has to come from the outer Container.
                control = "ft.Container"
        if widget_type in TEXT_WIDGET_TYPES:
            control = "ft.Container"
        if widget_type == "ttk::treeview" and not parse_values(
            self.project.option(name, "columns")
        ):
            control = "ft.Container"
            self.notes.append(
                f"# {name}: Treeview has no columns - placeholder Container"
            )
        if widget_type == NOTEBOOK_WIDGET_TYPE and not any(
            self.project.is_tab(child) for child in children
        ):
            # An empty notebook has no tabs to show; emit its frame instead.
            control = "ft.Container"
        if self.project.policy_for(name) == "placeholder":
            control = "ft.Container"
            self.notes.append(
                f"# {name}: placeholder requested by the Flet tool default for "
                f"{_widget_key(widget_type)}"
            )
        elif widget_type == "ttk::spinbox":
            self.defined.discard(name)
            self._define_spinbox(name)
            return name
        arguments, unmapped = self._arguments(name, control)
        if (
            self.project.geom_manager == "Grid"
            and not self.project.absolute_grid
        ):
            # ttk semantics: sticky decides which axes the widget fills. The
            # other axis keeps the widget's own size, which is also what stops
            # Flet's taller default controls (48px fields, 40px buttons) from
            # changing the designer's proportions.
            sticky = self._grid_sticky(name)
            natural = self._natural_size(name)
            if self._fills(sticky, "e", "w"):
                arguments["expand"] = "True"
            elif natural:
                arguments["width"] = str(int(natural[0]))
        attachment = self.project.attachment(name)
        if attachment is not None and attachment.mode == "native":
            arguments["scroll"] = attachment.scrollbar_call()

        if widget_type == NOTEBOOK_WIDGET_TYPE:
            tabs = [child for child in children if self.project.is_tab(child)]
            others = [child for child in children if child not in tabs]
            for child in others:
                self._define(child)
            if tabs:
                arguments["length"] = str(len(tabs))
                arguments["content"] = self._notebook(tabs)
            else:
                self.notes.append(
                    f"# {name}: Notebook has no tab frames - emitted as its frame"
                )
                if others:
                    arguments["content"] = self._stack(others)
        elif is_container(widget_type) and widget_type != "ttk::panedwindow":
            content: str | None = None
            if children:
                grid_columns = (
                    self.project.geom_manager == "Grid"
                    and not self.project.absolute_grid
                )
                if grid_columns:
                    content = self._rows(name, children)
                elif self.project.geom_manager == "Pack":
                    content = self._packed(children)
                else:
                    content = self._stack(children)
            captioned = self._captioned(name, widget_type, content)
            if captioned:
                arguments["content"] = captioned
        elif widget_type == "ttk::panedwindow":
            if children:
                arguments["controls"] = self._paned(name, children)
        else:
            for child in children:
                self._define(child)

        if unmapped:
            self.notes.append(
                f"# {name}: options with no Flet equivalent -> "
                f"{', '.join(sorted(set(unmapped)))}"
            )
        note = PLACEHOLDERS.get(widget_type)
        if note:
            self.notes.append(f"# {name}: {note}")

        arguments = self._render(name, control, arguments)
        call = _call(
            f"{name} = {arguments.pop('__control__')}", list(arguments.values())
        )
        self.lines.extend(_indent_lines(call, 4).split("\n"))
        return name

    def _render(
        self, name: str, control: str, arguments: dict[str, str]
    ) -> dict[str, str]:
        """Add ``keyword=`` prefixes, wrapping controls Flet cannot position.

        ``ft.RadioGroup`` and ``ft.Divider`` are not layout controls, so the
        designer's ``Place`` coordinates have to live on a ``ft.Container``
        that holds them.

        A widget scrolled by a Tk scrollbar is wrapped in a scrolling
        ``ft.Column`` when its Flet control has no ``scroll`` slot of its own.
        """
        placement = self._placement_arguments(name)
        if control == "ft.TextField" and arguments.get("multiline") == "True":
            natural = self._natural_size(name) or (0, 0)
            target = _number(placement.get("height")) or natural[1]
            lines = multiline_lines(target)
            if lines:
                arguments["min_lines"] = str(lines)
                # A multiline field ignores an explicit height, and leaving one
                # in would suggest it does something.
                placement.pop("height", None)
        if control not in POSITIONABLE_CONTROLS:
            # Size arguments belong to the wrapper, not to a control that has
            # no width/height of its own (ft.RadioGroup, ft.Divider).  In Grid
            # mode the sizes come from the widget's sticky, so they arrive here
            # rather than through _placement_arguments.
            for key in ("width", "height"):
                if key in arguments:
                    placement[key] = arguments.pop(key)
        attachment = self.project.attachment(name)
        if attachment is not None and attachment.mode == "wrap":
            inner = dict(arguments)
            inner.update(
                {
                    key: value
                    for key, value in placement.items()
                    if key in ("width", "height")
                }
            )
            inner_call = _call(
                control, [f"{key}={value}" for key, value in inner.items()]
            )
            rendered = {
                "__control__": "ft.Column",
                "scroll": f"scroll={attachment.scrollbar_call()}",
                "controls": _list_argument(
                    "controls", [f"ft.Container(content={inner_call})"]
                ),
            }
            rendered.update(
                {key: f"{key}={value}" for key, value in placement.items()}
            )
            return rendered
        if control in POSITIONABLE_CONTROLS:
            rendered = {"__control__": control}
            rendered.update({key: f"{key}={value}" for key, value in arguments.items()})
            rendered.update({key: f"{key}={value}" for key, value in placement.items()})
            return rendered
        inner = _call(
            control, [f"{key}={value}" for key, value in arguments.items()]
        )
        rendered = {"__control__": "ft.Container", "content": f"content={inner}"}
        rendered.update({key: f"{key}={value}" for key, value in placement.items()})
        return rendered

    def _define_spinbox(self, name: str) -> None:
        """Emit a Tk spinbox as a TextField with up/down stepper buttons.

        Flet has no Spinbox control.  A TextField plus two ``ft.IconButton``
        arrows reproduces the stepping behaviour, using the saved ``from``,
        ``to`` and ``increment`` values.
        """
        properties, unmapped = translate_attributes(
            "ttk::spinbox", self.project.attributes(name), self.project.context(name)
        )
        placement = self._placement_arguments(name)
        field_name = f"{name}_field"
        total_width = _number(str(placement.get("width", "")).strip()) or 140
        step = float(properties.get("increment", 1.0) or 1.0)
        minimum = float(properties.get("minimum", 0.0) or 0.0)
        maximum = properties.get("maximum")
        maximum = float(maximum) if maximum is not None else None
        if maximum is not None and maximum <= minimum:
            maximum = None

        field_style = self._style_arguments(name, "ft.TextField")
        field_arguments: list[str] = [
            f"{keyword}={value}" for keyword, value in field_style.items()
        ]
        if "value" in properties:
            field_arguments.append(f"value={properties['value']}")
        if properties.get("read_only"):
            field_arguments.append("read_only=True")
        if properties.get("disabled"):
            field_arguments.append("disabled=True")
        field_arguments.extend(
            (
                "keyboard_type=ft.KeyboardType.NUMBER",
                f"width={max(32, int(total_width) - STEPPER_WIDTH)}",
            )
        )
        self.lines.extend(
            _indent_lines(
                _call(f"{field_name} = ft.TextField", field_arguments), 4
            ).split("\n")
        )

        self._register_spin_helper()
        up = (
            "on_click=lambda e: _step_value("
            f"{field_name}, 1, {minimum!r}, {maximum!r}, {step!r})"
        )
        down = (
            "on_click=lambda e: _step_value("
            f"{field_name}, -1, {minimum!r}, {maximum!r}, {step!r})"
        )
        row_height = _number(str(placement.get("height", "")).strip()) or 32
        arrow_height = max(12, int(int(row_height) / 2))
        arrow = (
            f"width={STEPPER_WIDTH}, height={arrow_height}, "
            f"icon_size={STEPPER_ICON_SIZE}, padding=0"
        )
        stepper = _call(
            "ft.Column",
            [
                _list_argument(
                    "controls",
                    [
                        "ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_UP, "
                        f"{arrow}, {up})",
                        "ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_DOWN, "
                        f"{arrow}, {down})",
                    ],
                ),
                "spacing=0",
            ],
        )
        arguments: dict[str, str] = {
            "controls": _list_expression([field_name, stepper]),
            "spacing": "0",
        }
        arguments.update(placement)
        rendered = self._render(
            name, "ft.Row", {key: value for key, value in arguments.items()}
        )
        if unmapped:
            self.notes.append(
                f"# {name}: options with no Flet equivalent -> "
                f"{', '.join(sorted(set(unmapped)))}"
            )
        if properties.get("value"):
            self.notes.append(
                f"# {name}: Tk variable is not kept in sync by the stepper"
            )
        if properties.get("values"):
            self.notes.append(
                f"# {name}: spinbox value list is not reproduced - "
                "numeric stepping only"
            )
        call = _call(
            f"{name} = {rendered.pop('__control__')}", list(rendered.values())
        )
        self.lines.extend(_indent_lines(call, 4).split("\n"))

    def _register_spin_helper(self) -> None:
        """Register the stepping helper used by generated spinboxes."""
        if self.helpers:
            return
        self.helpers.extend(
            (
                "def _step_value(field, delta, minimum, maximum, step):",
                '    """Step a TextField value by *step*, clamped to the range."""',
                "    try:",
                "        value = float(field.value or minimum)",
                "    except (TypeError, ValueError):",
                "        value = minimum",
                "    value += delta * step",
                "    if maximum is not None:",
                "        value = min(maximum, value)",
                "    value = max(minimum, value)",
                '    field.value = f"{value:g}"',
                "    field.update()",
            )
        )

    def _captioned(
        self, name: str, widget_type: str, content: str | None
    ) -> str | None:
        """Prepend a labelframe caption, which ft.Container has no slot for."""
        if widget_type != "ttk::labelframe":
            return content
        caption = self.project.option(name, "text")
        if not caption:
            return content
        # ttk paints the caption in the frame's bootstyle colour - the same
        # colour as its border, measured on both the superhero and cyborg
        # themes - so that is preferred over the theme's text colour.
        bootstyle, _variants = self.project.style_of(name)
        styles = self.project.bootstyle_styles(bootstyle) if bootstyle else {}
        ink = (
            styles.get("labelframe_border")
            or self.project.widget_surface("labelframe_fg")
            or self.project.colour("fg")
        )
        style = f", color={ink!r}, size={DEFAULT_TEXT_SIZE}" if ink else ""
        row = _call(
            "ft.Row",
            [
                _list_argument("controls", [f"ft.Text(value={caption!r}{style})"]),
                "spacing=0",
                f"alignment={self._label_anchor_alignment(name)}",
            ],
        )
        if self._label_anchor_below(name):
            # labelanchor starting with "s" draws the caption under the frame.
            children = [content, row] if content else [row]
        else:
            children = [row, content] if content else [row]
        return _call(
            "ft.Column", [_list_argument("controls", children), "spacing=2"]
        )

    def _label_anchor(self, name: str) -> str:
        """Return a labelframe's labelanchor, defaulting to ttk's "n"."""
        return self.project.option(name, "labelanchor").strip().lower() or "n"

    def _label_anchor_below(self, name: str) -> bool:
        return self._label_anchor(name).startswith("s")

    def _label_anchor_alignment(self, name: str) -> str:
        """Map a labelframe labelanchor onto a Row alignment."""
        anchor = self._label_anchor(name)
        if anchor.endswith("w"):
            return "ft.MainAxisAlignment.START"
        if anchor.endswith("e"):
            return "ft.MainAxisAlignment.END"
        return "ft.MainAxisAlignment.CENTER"

    def _paned(self, parent_name: str, children: Sequence[str]) -> str:
        names = [name for name in map(self._define, children) if name]
        widget_type = self.project.widget_type(parent_name)
        vertical = (
            _text(self.project.option(parent_name, "orient")).lower() == "vertical"
        )
        builder = "ft.Column" if vertical else "ft.Row"
        self.notes.append(
            f"# {parent_name}: {widget_type} emitted as {builder} "
            "(Flet has no draggable splitter)"
        )
        return _call(builder, [f"controls=[{', '.join(names)}]", "spacing=0"])

    def root(self) -> str:
        """Emit every control and return the root expression.

        Place keeps the designer's absolute coordinates, so the root is a
        Stack; Grid and Pack build the same row/column structure the Tk
        geometry manager would have produced.
        """
        children = self.project.visible_children(self.project.root_name)
        if self.project.geom_manager == "Grid" and not self.project.absolute_grid:
            return self._rows(self.project.root_name, children)
        if self.project.geom_manager == "Pack":
            return self._packed(children)
        names = ", ".join(name for name in map(self._define, children) if name)
        width, height = self.window_size()
        return _call(
            "ft.Stack", [f"controls=[{names}]", f"width={width}", f"height={height}"]
        )


def emit_program(
    project_data: Mapping[str, Any],
    widget_order: Sequence[str],
    root_name: str,
    geom_manager: str = "",
    images: Mapping[str, str] | None = None,
    grid_mode: str = "responsive",
    policy: Mapping[str, str] | None = None,
    minimum_flet_version: str = DEFAULT_MINIMUM_FLET_VERSION,
    strict_flet_version: bool = DEFAULT_STRICT_FLET_VERSION,
    natural_sizes: Mapping[str, Sequence[int]] | None = None,
) -> str:
    """Return a complete, runnable Flet program for *project_data*.

    ``grid_mode`` selects how a Grid project is rendered: ``"responsive"``
    (nested ``ft.Row``/``ft.Column`` with expand weights, the default) or
    ``"absolute"`` (a ``ft.Stack`` positioned from the saved grid minsizes).

    ``policy`` maps widget type keys (``"treeview"``, ``"scrollbar"`` …) to
    ``"full"``, ``"placeholder"`` or ``"skip"``; the ``"default"`` key applies
    to types that are not listed.

    ``minimum_flet_version`` and ``strict_flet_version`` control the version
    guard emitted at the top of the program: it warns about an older Flet
    runtime, or refuses to start when ``strict_flet_version`` is true.

    ``natural_sizes`` maps widget names to the sizes the designer measured for
    them (``winfo_reqwidth``/``winfo_reqheight``).  Exact-position Grid output
    uses them to size cells the way Tk does; without them the tool defaults are
    used instead.
    """
    project = _Project(
        project_data,
        widget_order,
        root_name,
        geom_manager,
        images,
        grid_mode,
        policy,
        None,
        natural_sizes,
    )
    emitter = _Emitter(project)
    for scrollbar, attachment in project.scroll_attachments.items():
        if project.skipped(scrollbar):
            continue
        emitter.notes.append(f"# {scrollbar} (scrollbar): {attachment.summary()}")
    root_expression = emitter.root()
    width, height = emitter.window_size()
    theme = _text(project_data.get("theme"))
    palette_background = project.colour("bg")
    background = palette_background or tk_color(project_data.get("backgroundColor"))
    project_name = _text(project_data.get("ProjectName")) or root_name

    lines: list[str] = [
        '"""Flet UI generated by PyTkQuickGui.',
        "",
        f"Project : {project_name}",
        f"Layout  : {project.geom_manager or 'Place'}",
        f"Theme   : {theme or 'default'}  (ttkbootstrap theme - not a Flet theme)",
        "",
        "Regenerating this file overwrites it, so keep hand written changes in a",
        "separate module that imports this one.",
        '"""',
        "",
        "import flet as ft",
        "import sys",
        "",
        f"MINIMUM_FLET_VERSION = {minimum_flet_version!r}",
        f"FLET_VERSION_STRICT = {strict_flet_version!r}",
        "",
        "",
        "def _flet_major(version):",
        '    """Return the major part of a version string, or 0 when unparsable."""',
        "    try:",
        '        return int(str(version).split(".", maxsplit=1)[0])',
        "    except (TypeError, ValueError):",
        "        return 0",
        "",
        "",
        "def _check_flet_version("
        "minimum=MINIMUM_FLET_VERSION, strict=FLET_VERSION_STRICT"
        "):",
        '    """Warn (or stop) when the installed Flet is older than this file '
        'targets."""',
        '    installed = str(getattr(ft, "__version__", "") or "unknown")',
        "    if _flet_major(installed) >= _flet_major(minimum):",
        "        return",
        '    problem = f"This program targets Flet {minimum} or later."',
        '    problem += f" Installed: {installed}."',
        '    hint = "Upgrade with:  pip install --upgrade flet"',
        "    if strict:",
        '        raise SystemExit(problem + " " + hint)',
        '    print("warning: " + problem + " " + hint, file=sys.stderr)',
        "",
        "",
        "_check_flet_version()",
        "",
        f"PROJECT_NAME = {project_name!r}",
        f"THEME = {theme!r}",
        f"THEME_IS_DARK = {project.dark_theme!r}",
        "",
        "# Starting window size, worked out from the design. Edit these to",
        "# taste: Grid and Pack layouts reflow as the window is resized,",
        "# while Place positions stay where the designer put them.",
        f"WINDOW_WIDTH = {width}",
        f"WINDOW_HEIGHT = {height}",
    ]
    if background:
        lines.append(f"BACKGROUND_COLOR = {background!r}")

    lines.extend(("", SECTION_VARIABLES))
    if project.variables or project.list_variables:
        lines.append(
            "# Flet controls hold plain Python values - adjust types as needed."
        )
        declared = list(project.variables)
        for variable in sorted(project.list_variables):
            if variable not in declared:
                declared.append(variable)
        for variable in declared:
            if variable in project.list_variables:
                lines.append(f"{variable} = []   # listbox items")
            else:
                lines.append(f"{variable} = '0.0'")
    else:
        lines.append("# No widget variables are referenced by this project.")

    lines.extend(("", SECTION_FUNCTIONS))
    if project.callbacks:
        for callback in project.callbacks:
            lines.extend(
                (
                    "",
                    f"def {callback}(e=None):",
                    f"    {STUB_SENTINEL}",
                    f"    print({callback!r})",
                )
            )
    else:
        lines.append("# Add your event handlers here.")

    if emitter.text_bindings:
        lines.extend(("", "# ---- Text variables bound to controls ----", ""))
        lines.extend(_TEXT_BINDING_HELPERS)
        emitter.helpers = []

    if emitter.helpers:
        lines.extend(("", "# ---- Generated helpers ----", ""))
        lines.extend(emitter.helpers)

    if emitter.notes:
        lines.extend(("", "# ---- Translation notes ----"))
        lines.extend(sorted(set(emitter.notes)))

    lines.extend(
        (
            "",
            SECTION_MAIN,
            "",
            "def main(page: ft.Page):",
            "    page.title = PROJECT_NAME",
            "    page.theme_mode = ("
            "ft.ThemeMode.DARK if THEME_IS_DARK else ft.ThemeMode.LIGHT"
            ")",
            "    page.window.width = WINDOW_WIDTH",
            "    page.window.height = WINDOW_HEIGHT",
            "    page.padding = 0",
        )
    )
    if background:
        lines.append("    page.bgcolor = BACKGROUND_COLOR")
    seed = project.colour("primary")
    if seed:
        lines.extend(
            (
                "    # Seed Flet's Material theme with the project's primary",
                "    # colour so state-dependent controls fill with the theme",
                "    # colour: a ticked checkbox or a selected radio is painted,",
                "    # an untouched one stays empty, as ttk draws them.",
                f"    page.theme = ft.Theme(color_scheme_seed={seed!r})",
            )
        )
    if project.images:
        lines.extend(("", "    # ---- Images ----"))
        for widget_name, filename in project.images.items():
            lines.append(f"    {widget_name}image = ft.Image(src={filename!r})")
    lines.extend(("", f"    {SECTION_WIDGETS}"))
    lines.extend(emitter.lines)
    if emitter.text_bindings:
        lines.append("")
        for variable, controls in sorted(emitter.text_bindings.items()):
            pairs = [
                f"({control}, {attribute!r})" for control, attribute in controls
            ]
            statement = f"TEXT_BINDINGS[{variable!r}] = {_list_expression(pairs)}"
            lines.extend(_indent_lines(statement, 4).split("\n"))
        lines.append(
            f"    # {sum(len(v) for v in emitter.text_bindings.values())} captions "
            f"follow {len(emitter.text_bindings)} textvariables; call "
            "set_text(page, name, value) to change them"
        )
    lines.extend(
        (
            "",
            f"    {root_name} = {_indent_lines(root_expression, 4).lstrip()}",
            f"    page.add({root_name})",
            "",
            "",
            "ft.run(main)",
            "",
        )
    )
    return "\n".join(lines)


def _mapping_description(project: _Project, name: str) -> tuple[str, str]:
    """Return ``(category, description)`` for one widget's Flet mapping."""
    widget_type = project.widget_type(name)
    if project.skipped(name):
        return "skipped", "skipped by the Flet tool default"
    attachment = project.scroll_attachments.get(name)
    if attachment is not None and attachment.mode in ("native", "wrap", "self"):
        return "folded", attachment.summary()
    if project.policy_for(name) == "placeholder":
        return "placeholder", "placeholder Container (Flet tool default)"
    if widget_type not in CONTROL_TYPES:
        return "placeholder", f"placeholder Container (no control for {widget_type})"
    if widget_type == "ttk::treeview" and not parse_values(
        project.option(name, "columns")
    ):
        return "placeholder", "placeholder Container (treeview has no columns)"
    if widget_type == "ttk::spinbox":
        return "mapped", "ft.Row (TextField + stepper buttons)"
    if widget_type == NOTEBOOK_WIDGET_TYPE:
        return "mapped", "ft.Tabs (TabBar + TabBarView)"
    if widget_type in ("ttk::canvas", "canvas"):
        children = len(project.children.get(name, []))
        return "mapped", f"ft.Container + ft.Stack ({children} children)"
    if widget_type == "ttk::labelframe":
        return "mapped", "ft.Container + ft.Text caption"
    if widget_type == "ttk::panedwindow":
        return "mapped", "ft.Row/ft.Column (no draggable splitter)"
    return "mapped", widget_control(widget_type)


def window_size_for(
    project_data: Mapping[str, Any],
    widget_order: Sequence[str],
    root_name: str,
    geom_manager: str = "",
    grid_mode: str = "responsive",
    policy: Mapping[str, str] | None = None,
    natural_sizes: Mapping[str, Sequence[int]] | None = None,
) -> tuple[int, int]:
    """Return the window size a program would open at, without emitting it."""
    project = _Project(
        project_data,
        widget_order,
        root_name,
        geom_manager,
        None,
        grid_mode,
        policy,
        None,
        natural_sizes,
    )
    return _Emitter(project).window_size()


def compatibility_report(
    project_data: Mapping[str, Any],
    widget_order: Sequence[str],
    root_name: str,
    geom_manager: str = "",
    images: Mapping[str, str] | None = None,
    grid_mode: str = "responsive",
    policy: Mapping[str, str] | None = None,
) -> str:
    """Return a human readable summary of how a project maps to Flet.

    Used by Tools -> Flet compatibility report so the lossy parts of a
    translation are visible before the file is written.
    """
    project = _Project(
        project_data, widget_order, root_name, geom_manager, images, grid_mode, policy
    )
    rows: list[tuple[str, str, str, str]] = []
    counts: dict[str, int] = {"mapped": 0, "folded": 0, "placeholder": 0, "skipped": 0}
    for name in project.order:
        category, description = _mapping_description(project, name)
        counts[category] = counts.get(category, 0) + 1
        rows.append((name, project.widget_type(name), description, category))

    width = max((len(row[0]) for row in rows), default=8)
    type_width = max((len(row[1]) for row in rows), default=8)
    lines = [
        "Flet compatibility report",
        "",
        f"Project : {_text(project_data.get('ProjectName')) or root_name}",
        f"Theme   : {project.theme or 'default'}"
        + (
            " (ttkbootstrap palette applied)"
            if project.palette
            else " (no theme palette found - built-in colours only)"
        ),
        f"Layout  : {project.geom_manager or 'Place'}"
        + (
            " (absolute positions)"
            if project.absolute_grid
            else " (responsive rows and columns)"
            if project.geom_manager == "Grid"
            else ""
        ),
        "",
    ]
    if not rows:
        lines.append("This project has no widgets yet.")
        return "\n".join(lines)
    lines.append(f"{'Widget'.ljust(width)}  {'Type'.ljust(type_width)}  Flet output")
    lines.append(f"{'-' * width}  {'-' * type_width}  {'-' * 40}")
    for name, widget_type, description, category in rows:
        lines.append(
            f"{name.ljust(width)}  {widget_type.ljust(type_width)}  {description}"
            + (f"  [{category}]" if category != "mapped" else "")
        )
    lines.extend(
        (
            "",
            "Summary: {total} widgets - {mapped} mapped, {folded} folded into a "
            "scroll target, {placeholder} placeholder, {skipped} skipped".format(
                total=len(rows), **counts
            ),
            "",
            "Set a per-type policy with the fletWidgetPolicy entry in "
            "tool_defaults.json (full | placeholder | skip).",
        )
    )
    return "\n".join(lines)
