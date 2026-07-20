# PyTkQuickGui

Note: This is in active development. It is "alpha" code with quite a few knows glitches and errors. At this stage it is usefull enough to try out and do simple tasks. At present some widgest are not included as there are issues to resolve. Only two grid methods are available, the "Place" gridder being the most stable, "Grid" works reasonably well but re-parenting is an issue.  "Pack" is greayed out for now, this will be tackeked later.

**A visual drag-and-drop GUI builder for Python / ttkbootstrap applications.**

PyTkQuickGui lets you lay out tkinter widgets by dragging, resizing, and editing them on a live canvas, then generates a complete, ready-to-run Python file with all the boilerplate already written.  You fill in the business logic; PyTkQuickGui handles the widget creation and placement code.

> **Status:** Alpha – functional and actively used, but still growing.  Some widget types have not been fully integrated. Feedback and contributions are very welcome.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Interface Overview](#interface-overview)
6. [Working with Widgets](#working-with-widgets)
7. [Geometry Managers](#geometry-managers)
8. [Project Files (JSON)](#project-files-json)
9. [Generating Python Code](#generating-python-code)
10. [Keyboard & Mouse Reference](#keyboard--mouse-reference)
11. [Widget Reference](#widget-reference)
12. [Themes](#themes)
13. [Known Limitations](#known-limitations)
14. [Contributing](#contributing)
15. [License](#license)

---

## Features

| Feature | Details |
|---|---|
| **Visual layout** | Drag, resize and re-parent widgets on a live canvas |
| **Geometry managers** | Choose **Place**, **Grid**, or **Pack** per project via the toolbar |
| **ttkbootstrap widgets** | Label, Button, Entry, Combobox, Spinbox, Checkbutton, Radiobutton, Scale, Progressbar, Floodgauge, Meter, Notebook, Canvas, Frame, Labelframe, Panedwindow |
| **Standard tk/ttk widgets** | Text, Listbox, Treeview, Scrollbar, Separator, Sizegrip |
| **Widget editor** | Edit every configurable attribute through generated combo/spinbox/entry controls |
| **Colour & font pickers** | Integrated colour chooser and font dialog |
| **Image support** | Attach PNG/JPG images to Label or Button widgets |
| **Themes** | All ttkbootstrap themes available from the Theme menu |
| **Code generation** | Produces a single, clean Python file – import + window setup + all widgets + blank callbacks + tk variables |
| **JSON project files** | Human-readable save format; easily version-controlled or hand-edited |
| **Legacy format** | Old `.pk1` (pickle) project files are detected and loaded automatically; re-saved as JSON |
| **Rolling backups** | Up to 5 automatic backup copies (`.json-save1` … `.json-save5`) |

---

## Requirements

```
Python >= 3.10
ttkbootstrap >= 1.10
tkfontchooser
coloredlogs
Pillow
```

See `requirments.txt` for the full list.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/ChrisMcGowanAu/PyTkQuickGui.git
cd PyTkQuickGui

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirments.txt

# 4. Run
python pytkquickgui.py
```

On Linux you may need `python3-tk` installed at the system level:

```bash
sudo apt install python3-tk
```

---

## Quick Start

1. **Launch** `python pytkquickgui.py`
2. **New project** → *File ▸ New Project* – enter a name and click OK.
3. **Add a widget** → right-click anywhere on the canvas; pick a widget from the pop-up menu.  It appears under your cursor.
4. **Move** → left-click and drag.
5. **Resize** → left-click near an edge and drag.
6. **Edit** → right-click a widget → *Edit* to change text, colour, font, style, etc.
7. **Save** → *File ▸ Save Project* (saves a `.json` file).
8. **Generate** → *File ▸ Generate Python* – choose where to save the `.py` file and open it in your IDE.

---

## Interface Overview

```
┌──────────────────────────────────────────────────────────────┐
│  Menu bar: File | Theme | Tools | Help                        │
├──────────────────────────────────────────────────────────────┤
│  Toolbar: [Geometry Manager] Place | Grid | Pack   Layout: X │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   Canvas  (drag & drop widgets here)                         │
│                                                              │
│                                                        ▣     │  ← size-grip
└──────────────────────────────────────────────────────────────┘
```

### Menu Items

| Menu | Item | Action |
|---|---|---|
| File | New Project | Create a new project folder |
| File | Open last Project | Reload the most recently saved project |
| File | Open Project | Browse to a project directory |
| File | Save Project | Save to JSON |
| File | Trial Run | Generate code and run it in a subprocess |
| File | Generate Python | Generate code and save to a location you choose |
| File | Exit | Save-prompt then quit |
| Theme | (theme names) | Switch ttkbootstrap theme live |
| Tools | Hide/Show Label Borders | Toggle 1-pixel border on all Labels |
| Tools | Set default label font | Change font on all Label widgets |
| Tools | Set default style font | Change font for all ttk widget types |
| Tools | Open backup file | Load one of the rolling `.json-saveN` backups |
| Tools | Widget Tree | Print widget hierarchy to the terminal |
| Help | Welcome | About box |
| Help | Help | In-app tabbed help window |

---

## Working with Widgets

### Adding a Widget
Right-click on the **canvas** to open the widget palette.  Container widgets (Frame, Labelframe, Panedwindow) appear at the top, followed by all other widget types.  Click a name and the widget is placed at the cursor position.

### Selecting and Moving
Left-click and hold anywhere in the middle of a widget, then drag to reposition.

### Resizing
Left-click and hold **near an edge** (within ~8 pixels) of a widget, then drag.  Each edge acts independently:

| Drag zone | Effect |
|---|---|
| Right edge | Expand / shrink width |
| Left edge | Move left edge (changes x and width) |
| Bottom edge | Expand / shrink height |
| Top edge | Move top edge (changes y and height) |

After release, the position and size are snapped to a 16-pixel grid.

### Right-Click Context Menu (on a widget)

| Item | Effect |
|---|---|
| Edit | Opens the attribute editor popup |
| Layout | Opens the x / y / width / height editor (Place manager only) |
| Clone | Creates a copy at the same position |
| DeepClone | Copies a container widget *and* all its children |
| Re-Parent | Drops the widget into whichever container currently encloses it |
| Delete | Removes the widget |

### Attribute Editor
The **Edit** popup shows every configurable key for the selected widget.  Controls are chosen based on the key type:

* **Combobox** – anchor, relief, justify, orient, cursor, style/bootstyle
* **Spinbox** – height, width, borderwidth, padding
* **Button** – font picker, colour picker, image selector
* **Entry** – everything else (text, command, variable names, etc.)

Click **Apply** to commit changes; **Close** to discard.

### Re-parenting
When you release a widget on top of a container (Frame, Labelframe, etc.), the tool automatically detects the overlap and re-parents the widget.  You can also trigger this manually via the right-click *Re-Parent* command.

---

## Geometry Managers

PyTkQuickGui supports all three Tk geometry managers.  Select the one you want from the **toolbar** before placing widgets – the setting is saved with the project.

### Place (default)
Widgets are positioned with absolute `x`, `y`, `width`, `height` coordinates.  Best for pixel-perfect layouts and quick prototyping.

```python
myWidget.place(x=80, y=40, width=120, height=28, anchor='nw', bordermode='inside')
```

### Grid
Widgets snap to a row/column grid.  Dropping a widget calculates the nearest grid cell.  Generated code uses `grid(row=…, column=…, sticky=…, padx=…, pady=…)`.  Best for forms and tables.

```python
myWidget.grid(row=1, column=2, sticky='WE', padx=2, pady=2)
```

### Pack
Widgets are stacked sequentially.  Dragging and dropping still places widgets, but the pack order is determined by creation order.  Generated code uses `pack(side=…, fill=…, expand=…)`.  Best for simple vertical or horizontal stacks.

```python
myWidget.pack(side='top', fill='none', expand=0, padx=4, pady=4)
```

> **Tip:** You can change the geometry manager at any time during design.  The saved project records which manager was active so reloading restores it automatically.

---

## Project Files (JSON)

Projects are stored as plain **JSON** files in `~/.config/pytkgui/<ProjectName>/`.  The file format is intentional – you can open a `.json` project in any text editor and tweak values directly.

```
~/.config/pytkgui/
└── MyProject/
    ├── MyProject.json          ← current save
    ├── MyProject-save1.json    ← previous save
    ├── MyProject-save2.json
    └── ...
```

### File structure (excerpt)
```json
{
  "ProjectName": "MyProject",
  "theme": "cyborg",
  "geomManager": "Place",
  "widgetCount": 3,
  "widgetNameList": [...],
  "Widget0": {
    "WidgetName": "ttk::button",
    "WidgetParent": "rootWidget",
    "Place": {"x": "80", "y": "48", "width": "120", "height": "32", ...},
    "Widget0-KeyCount": 4,
    "Attribute0": {"Key": "text",  "Value": "Click Me"},
    "Attribute1": {"Key": "style", "Value": "primary"},
    ...
  }
}
```

### Legacy pickle files (`.pk1`)
Projects saved by older versions of PyTkQuickGui used Python's `pickle` format (`.pk1` extension).  The loader **automatically detects** whether a file is JSON or pickle — no manual conversion needed:

1. When you open a project directory PyTkQuickGui looks for `<name>.json` first, then `<name>.pk1`.
2. When you use *File ▸ Open backup file* both `.json` and `.pk1` entries appear in the file dialog.
3. A one-time info dialog tells you the file was loaded from the legacy format and will be re-saved as JSON on next save.

> **Warning:** Hand-editing JSON is powerful but risky.  An invalid JSON file will prevent the project from loading.  Keep a backup copy before editing.

---

## Generating Python Code

*File ▸ Generate Python* produces a single `.py` file structured in clearly-marked sections:

```python
import tkinter as tk
import ttkbootstrap as tboot

themeName = 'cyborg'
title     = 'MyProject'
rootWin   = tboot.Window(themename=themeName, title=title)
rootWidget = tboot.Frame(rootWin, ...)

####### TK variables #######
myStringVar = tk.StringVar(rootWin, '0.0')

####### Functions #######
def onClickMe():
    # AUTO-GENERATED STUB
    print('onClickMe')

####### Widgets #######
Widget0 = tboot.Button(rootWidget, text='Click Me', command=onClickMe, ...)
Widget0.place(x=80, y=48, width=120, height=32, ...)

####### Main  #######
rootWin.geometry('800x600')
rootWin.mainloop()
```

### Preserving your code across re-generations

Re-generating **does not overwrite code you have already written**.  The tool uses the section markers and a stub-sentinel comment to decide what to keep:

| Section | Behaviour on re-generate |
|---|---|
| `####### TK variables #######` | Variables still at the default `StringVar(rootWin,'0.0')` are replaced; ones you've changed are **preserved** |
| `####### Functions #######` | Stubs containing `# AUTO-GENERATED STUB` are replaced with a fresh stub; functions you've edited (sentinel removed / real code added) are **preserved verbatim** |
| `####### Widgets #######` | Always regenerated from the current builder state |
| `####### Main  #######` | Always regenerated |

**Recommended workflow:**
1. Build the layout in PyTkQuickGui.
2. *File ▸ Generate Python* → choose (or accept) a `.py` path.
3. Open that file in your IDE and write your logic (remove the `# AUTO-GENERATED STUB` lines as you go).
4. Return to PyTkQuickGui, adjust the layout, re-run *Generate Python* — PyTkQuickGui auto-fills the dialog with the last used path and merges your code back in.

> **Note:** *File ▸ Trial Run* generates a **temporary** internal file and runs it.  It does **not** update your saved `.py` file and does not trigger code preservation — it is intended only for a quick layout preview.

---

## Keyboard & Mouse Reference

| Action | Gesture |
|---|---|
| Add widget | Right-click canvas → select widget name |
| Move widget | Left-drag widget (centre area) |
| Resize widget | Left-drag near widget edge |
| Widget context menu | Right-click widget |
| Snap-to-grid size | 16 px (fixed) |

---

## Widget Reference

### ttkbootstrap Widgets

| Widget | Notes |
|---|---|
| **Frame** | Container; can hold other widgets |
| **Labelframe** | Frame with a title label |
| **Panedwindow** | Splitter container |
| **Label** | Static text or image |
| **Button** | Clickable button; supports `command`, `image`, `style` |
| **Entry** | Single-line text input; supports `textvariable` |
| **Combobox** | Drop-down selection; set `values` in the editor |
| **Spinbox** | Numeric or list spinner |
| **Checkbutton** | Tick-box; supports `variable` |
| **Radiobutton** | Radio selector; supports `variable`, `value` |
| **Scale** | Slider; supports `from_`, `to`, `orient` |
| **Progressbar** | Progress indicator; supports `value`, `orient` |
| **Floodgauge** | ttkbootstrap animated fill gauge |
| **Meter** | ttkbootstrap circular gauge; supports `metertype` (`full`/`semi`) |
| **Notebook** | Tabbed container; use the editor to set tab count |
| **Canvas** | Drawing surface; scrollbars can be added via the editor |

### Standard tk / ttk Widgets

| Widget | Notes |
|---|---|
| **Text** | Multi-line text area |
| **Listbox** | Scrollable list; set `selectmode` in the editor |
| **Treeview** | Table / tree view; add columns via the editor |
| **Scrollbar** | Attach to Canvas / Text / Listbox via the editor |
| **Separator** | Horizontal or vertical divider line |
| **Sizegrip** | Resize handle for the window corner |

---

## Themes

PyTkQuickGui uses **ttkbootstrap** themes.  The *Theme* menu lists all available themes.  Selecting one applies it live to both the builder and to the project (it is saved and used in generated code).

Popular themes: `cosmo`, `flatly`, `journal`, `litera`, `lumen`, `minty`, `pulse`, `sandstone`, `united`, `yeti` (light) · `cyborg`, `darkly`, `solar`, `superhero`, `vapor` (dark).

---

## Known Limitations

* **Meter widget** – the ttkbootstrap `Meter` widget has some quirks when used inside containers; if it does not display correctly, try running a Trial Run and see how it looks in the generated app.
* **Scrollbar attachment** – automatic scrollbar wiring (via the Edit → `vertical_scrollbar` / `horizontal_scrollbar` controls) currently works only with the **Grid** manager.
* **Notebook tabs** – tab count is set in the Edit popup; individual tab frames need to be re-parented manually.
* **Pack ordering** – in Pack mode, widget draw-order follows creation order, not drag position.  Re-ordering requires editing the generated code.
* **No undo** – accidental deletions cannot be undone from the GUI; use *File ▸ Open backup file* to recover from a save point.

---

## Contributing

Pull requests are welcome!  Please:

1. Fork the repository and create a feature branch.
2. Follow the existing code style (PEP 8, `log.xxx()` for logging).
3. Test manually with at least the `cyborg` and `flatly` themes.
4. Open a PR with a clear description of the change.

Areas that need work:

- [ ] Undo / redo history
- [ ] Notebook tab management in the editor
- [ ] More widget attributes exposed in the editor (e.g. Treeview columns)
- [ ] Pack mode drag re-ordering
- [ ] Website / video tutorial

---

## License

MIT – see [LICENSE](LICENSE) for details.

---

*PyTkQuickGui – Chris McGowan 2024-2026*
