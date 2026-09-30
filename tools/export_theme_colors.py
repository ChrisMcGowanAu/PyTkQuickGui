"""Export the ttkbootstrap theme palettes used by the Flet generator.

``flet_generator`` has to colour Flet controls the way ttkbootstrap colours the
equivalent ttk widgets, but it must not import ttkbootstrap (or Tk) itself: the
designer never needs Flet installed, and the generator is a pure function that
is unit tested without a display.  This script bridges the two by writing the
palette of every available theme to ``flet_theme_colors.json``.

Run it with an interpreter that has ttkbootstrap 2.x installed, from the
repository root:

    python3 tools/export_theme_colors.py

Legacy (pre-2.0) theme names are included because saved projects still use
them: ``install_legacy_themes()`` is called before the themes are read, which
requires the Style singleton to exist already, hence the throw-away window.
"""

from __future__ import annotations

import json
import os
import sys
import warnings

OUTPUT_NAME = "flet_theme_colors.json"

#: Palette slots copied for every theme.  These are the ttkbootstrap colours
#: the generated code needs: the bootstyle ramp, the surfaces, and the text
#: colours for inputs and selections.
SLOTS = (
    "primary",
    "secondary",
    "success",
    "info",
    "warning",
    "danger",
    "light",
    "dark",
    "bg",
    "fg",
    "selectbg",
    "selectfg",
    "border",
    "inputbg",
    "inputfg",
    "active",
)

#: Bootstyle colours.  ttkbootstrap resolves each one per theme, and for the
#: themes imported from Bootswatch the result is *not* simply the palette slot
#: (minty's primary slot is #78c2ad but its buttons are #609b8a), so the
#: resolved values are recorded rather than derived.
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


def _probe(style, widgets):
    """Return the resolved colours of one theme's ttkbootstrap styles.

    Lookups are taken from real widgets because ttkbootstrap applies bootstyle
    colours when a widget is created, not when the style name is spelled out.
    """
    resolved = {}
    for bootstyle in BOOTSTYLES:
        button = widgets["button"](bootstyle)
        outline = widgets["button"](f"{bootstyle}.Outline")
        label = widgets["label"](bootstyle)
        inverse = widgets["label"](f"{bootstyle}.Inverse")
        frame = widgets["frame"](bootstyle)
        labelframe = widgets["labelframe"](bootstyle)
        check = widgets["checkbutton"](bootstyle)

        def look(widget, *options):
            name = str(widget.cget("style"))
            return {option: style.lookup(name, option) for option in options}

        button_look = look(button, "background", "foreground")
        outline_look = look(outline, "background", "foreground", "bordercolor")
        label_look = look(label, "foreground")
        inverse_look = look(inverse, "background", "foreground")
        frame_look = look(frame, "background")
        labelframe_look = look(labelframe, "bordercolor")
        check_look = look(check, "foreground")
        resolved[bootstyle] = {
            "button_bg": button_look["background"],
            "button_fg": button_look["foreground"],
            "outline_bg": outline_look["background"],
            "outline_fg": outline_look["foreground"],
            "outline_border": outline_look["bordercolor"],
            "label_fg": label_look["foreground"],
            "inverse_bg": inverse_look["background"],
            "inverse_fg": inverse_look["foreground"],
            "frame_bg": frame_look["background"],
            "labelframe_border": labelframe_look["bordercolor"],
            "checkbutton_fg": check_look["foreground"],
        }
    entry = look_first(
        style,
        widgets["entry"]("primary"),
        "fieldbackground",
        "foreground",
        "bordercolor",
    )
    notebook = look_first(
        style, widgets["notebook"]("primary"), "background", "bordercolor"
    )
    labelframe_fg = look_first(
        style, widgets["labelframe"]("primary"), "foreground"
    )
    progressbar = look_first(
        style,
        widgets["progressbar"]("primary.Horizontal"),
        "troughcolor",
        "background",
    )
    scale = look_first(
        style, widgets["scale"]("primary.Horizontal"), "troughcolor"
    )
    return {
        "styles": resolved,
        "widgets": {
            "entry_bg": entry["fieldbackground"],
            "entry_fg": entry["foreground"],
            "entry_border": entry["bordercolor"],
            "notebook_bg": notebook["background"],
            "notebook_border": notebook["bordercolor"],
            "labelframe_fg": labelframe_fg["foreground"],
            "progressbar_trough": progressbar["troughcolor"],
            "progressbar_bg": progressbar["background"],
            "scale_trough": scale["troughcolor"],
        },
    }


def look_first(style, widget, *options):
    """Return the resolved lookup values for one widget."""
    name = str(widget.cget("style"))
    return {option: style.lookup(name, option) for option in options}


def export() -> dict:
    """Return ``{theme: {"colors": {...}, "styles": {...}, "widgets": {...}}}``."""
    warnings.simplefilter("ignore")
    import ttkbootstrap as ttk

    window = ttk.Window(theme="darkly")
    try:
        style = ttk.Style()
        ttk.install_legacy_themes()
        widgets = {
            "button": lambda bs: ttk.Button(window, text="x", bootstyle=bs),
            "label": lambda bs: ttk.Label(window, text="x", bootstyle=bs),
            "frame": lambda bs: ttk.Frame(window, bootstyle=bs),
            "labelframe": lambda bs: ttk.Labelframe(window, text="x", bootstyle=bs),
            "checkbutton": lambda bs: ttk.Checkbutton(window, text="x", bootstyle=bs),
            "entry": lambda bs: ttk.Entry(window, bootstyle=bs),
            "notebook": lambda bs: ttk.Notebook(window, bootstyle=bs),
            "progressbar": lambda bs: ttk.Progressbar(window, bootstyle=bs),
            "scale": lambda bs: ttk.Scale(window, bootstyle=bs),
        }
        table = {}
        for name in sorted(style.theme_names()):
            style.theme_use(name)
            colors = style.colors
            record = {
                "colors": {
                    slot: str(getattr(colors, slot))
                    for slot in SLOTS
                    if getattr(colors, slot, None)
                },
            }
            record.update(_probe(style, widgets))
            table[name] = record
        return table
    finally:
        window.destroy()


def main() -> int:
    target = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), OUTPUT_NAME
    )
    table = export()
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(table, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"Wrote {len(table)} themes to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
