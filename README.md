# PyTkQuickGui

# Now able to export FLET code. Still experimental.

PyTkQuickGui is a visual drag-and-drop builder for Python desktop interfaces
using tkinter and ttkbootstrap. Design a window on the live canvas, edit widget
attributes and layout, save the project as JSON, then generate a readable Python
program.

The project is approaching beta. Grid and Place projects are usable and under
active testing; Pack remains disabled while the other two geometry managers are
stabilised.

### The examples, in both backends

Seven ready made projects ship in [`examples/`](examples) - INSTALL.TXT has the
one line that copies them into the tool's directory. Each of these is the same
project as rendered by the generated ttkbootstrap program and by the generated
Flet program:

| ttkbootstrap output | Flet output |
|---|---|
| ![Simple Calculator, ttkbootstrap output](docs/example_Calculator_tk.png) | ![Simple Calculator, Flet output](docs/example_Calculator_flet.png) |
| ![UserForm, ttkbootstrap output](docs/example_UserForm_tk.png) | ![UserForm, Flet output](docs/example_UserForm_flet.png) |
| ![FletAllWidgets, ttkbootstrap output](docs/example_FletAllWidgets_tk.png) | ![FletAllWidgets, Flet output](docs/example_FletAllWidgets_flet.png) |
| ![tabs, ttkbootstrap output](docs/example_tabs_tk.png) | ![tabs, Flet output](docs/example_tabs_flet.png) |

`examples/` also holds SimplePlace (a starter with one of each basic control),
Calculator (nineteen hand placed buttons), UserForm (entries, a combo box and a
notebook), sudoku3 (a 91 widget Grid project) and sudokupack (Grid, small).
Screenshots of all of them, in both backends, are in
[`docs/`](docs).

## What it does

- Builds ttkbootstrap interfaces visually on a live design surface.
- Uses responsive Grid layout by default, or free-form Place layout.
- Moves, resizes, duplicates, deep-clones, deletes, groups, and re-parents
  widgets.
- Edits widget attributes with colour, font, image, entry, combo, and spinbox
  controls.
- Gives Grid and Place widgets useful type-specific layout defaults.
- Keeps child layouts inside Frame, Labelframe, and Panedwindow containers.
- Saves human-readable JSON projects with atomic writes and rolling backups.
- Preserves design-time callback and Tk-variable names through save, reload,
  duplication, and code generation.
- Generates clean multiline Python calls and preserves callback bodies edited
  in a previously generated file.
- Supports undo and redo for the main editing operations.
- Applies ttkbootstrap themes to the builder and generated program.

## Requirements

- Python 3.10 or newer
- tkinter (sometimes supplied as a separate operating-system package)
- ttkbootstrap 2.0 or newer
- tkfontchooser
- coloredlogs
- Pillow

Flet is optional and only needed to run programs written by
**File → Generate Flet**. The designer itself never imports flet. Install
`flet>=1.0` — the generated programs target the 1.0 API (they still run on the
0.8x releases, with a version warning).

The complete Python dependency list is in
[`requirments.txt`](requirments.txt). The filename is retained for compatibility
with existing setup instructions.

On Debian or Ubuntu, install tkinter if it is not already present:

```bash
sudo apt install python3-tk
```

## Installation

```bash
sudo apt install python3.13-full

git clone https://github.com/ChrisMcGowanAu/PyTkQuickGui.git
cd PyTkQuickGui

python -m venv venv
source venv/bin/activate
pip install -r requirments.txt
python pytkquickgui.py
```

On Windows, activate the environment with:

```powershell
venv\Scripts\activate
```

## Quick start

1. Run `python pytkquickgui.py`.
2. Select **File → New Project**, enter a project name, and choose Grid or
   Place.
3. Right-click the design surface and choose a widget.
4. Drag the widget to move it. In Place mode, drag an edge to resize it.
   In Grid mode, movement changes its row and column and edge drags adjust its
   span.
5. Right-click the widget and use **Edit** for attributes or **Layout** for
   geometry.
6. Use **File → Save Project** to save the JSON project.
7. Use **File → Trial Run** to preview it or **File → Generate Python** to
   write a program. **File → Generate Flet** writes the same layout as a
   [Flet](https://flet.dev) application.

Several ready made projects ship in `examples/`. Copy them into the tool's
directory and open one to see a finished project, or to compare the Python and
Flet output:

```bash
mkdir -p "$HOME/.config/pytkgui/examples"
cp -r examples/* "$HOME/.config/pytkgui/examples/"
```

Then **File → Open Project** and pick a folder such as
`~/.config/pytkgui/examples/Calculator`. See INSTALL.TXT for the Windows
equivalent and a list of what each example shows.

## Interface

The top toolbar shows the active layout manager. Grid projects also expose:

- **Rows** and **Cols** controls for the root design grid.
- **Grid settings** for guide colour, row and column minimum sizes, padding,
  and saving the current settings as tool defaults.
- An undo status at the right.

The geometry manager is selected for the project. Once widgets exist, switching
manager is blocked because mixing managers in one Tk parent leads to invalid
layouts. Start a new project to use a different manager.

### Main menus

| Menu | Important actions |
|---|---|
| File | New, open, close, save, save as, Trial Run, Generate Python, Trial Run (Flet), Generate Flet |
| Edit | Undo, redo, group selected widgets, ungroup |
| Theme | Light, dark, and legacy ttkbootstrap themes |
| Tools | Label borders, default fonts/styles, backups, widget tree, Compact Grid |
| Help | Welcome and the in-application guide |

## Working with widgets

Right-click empty space to open the widget palette. The current palette contains
these container widgets:

- Frame
- Labelframe
- Panedwindow

These regular widgets are currently enabled:

- Label
- Button
- Entry
- Combobox
- Spinbox
- Checkbutton
- Radiobutton
- Scale
- Progressbar
- Canvas
- Text
- Listbox
- Separator

Other Tk and ttkbootstrap widget implementations remain in the source while
their designer behaviour is completed, but they are not offered in the palette.

### Widget context menu

| Action | Result |
|---|---|
| Edit | Opens the scrollable attribute editor |
| Layout | Opens geometry values for the current manager |
| Duplicate | Copies one widget |
| Clone | Deep-copies a container and its children |
| Re-Parent | Places the widget in the enclosing container, or back at the root |
| Delete | Removes the widget |
| Add to Selection | Adds the widget to the current multi-selection |
| Group Selected | Creates a logical group from selected widgets |

The Edit and Layout popups put the action buttons at both the top and bottom.
The duplicate controls are intentional: short forms remain convenient while
long forms do not force the user to scroll to a particular end. Popups can be
moved with the yellow drag handle.

The attribute editor stores callback fields such as `command` and variable
fields such as `textvariable` as Python names, rather than trusting Tk's
internal Tcl command strings. Use valid top-level Python identifiers for these
values, for example `save_record` or `customer_name`.

If a widget has both a `text` and a `textvariable`, the text you type is also
written into the variable. Tk ignores `text` once `textvariable` is set, so
without that the caption would be dropped - the design would keep showing
whatever the variable held, and the generated program would fall back to its own
default. Writing it to the variable keeps the design, the saved project and the
generated program in agreement. A widget that keeps its *state* in a `variable`
(a checkbutton or radiobutton) is left alone: its caption stays in `text`.

## Geometry managers

### Grid

Grid is the default and is recommended for responsive forms. Widgets use
`row`, `column`, `columnspan`, `rowspan`, `padx`, `pady`, `ipadx`, `ipady`, and
`sticky`.

New widgets receive type-specific defaults. For example, entries span more
columns than labels, while text areas and containers span several rows and
columns. Open a widget's **Layout** popup and select **Save default** to make
its current Grid layout the default for future widgets of that type.

Rows and columns expand with the design surface. Container widgets keep their
own internal grid dimensions, including extra tracks created while editing.
Those dimensions are stored in the project and reproduced in Trial Run and
generated Python.

Use **Tools → Compact Grid** to remove unoccupied gaps and reduce the configured
root grid to its occupied extent.

Example generated geometry:

```python
Widget0.grid(
    row=2,
    column=1,
    columnspan=3,
    rowspan=1,
    sticky="nsew",
    padx=2,
    pady=2,
)
```

### Place

Place is useful for free-form prototypes and fixed-position controls. It stores
`x`, `y`, `width`, and `height`.

The drop position always follows the pointer. Initial `width` and `height` are
type-specific: containers and text areas start larger than buttons and labels.
Resize a widget, open **Layout**, and select **Save default** to use that size
for future widgets of the same type.

Example generated geometry:

```python
Widget0.place(
    x=80,
    y=48,
    width=180,
    height=32,
    anchor="nw",
    bordermode="inside",
)
```

### Pack

Pack is disabled for new projects. Compatibility code remains for older project
files, but its visual editing model is deferred until Grid and Place are stable.

## Tool defaults

`tool_defaults.py` contains the built-in Grid and Place defaults. Optional
`tool_defaults.json` files are layered in this order, from lowest to highest
precedence:

1. `/etc/pytkgui/tool_defaults.json`
2. `tool_defaults.json` beside the PyTkQuickGui source modules
3. `tool_defaults.json` in the directory from which the tool was launched
4. The user's configuration file

The user file is normally:

- Linux: `~/.config/pytkgui/tool_defaults.json`
- Linux with `XDG_CONFIG_HOME`: `$XDG_CONFIG_HOME/pytkgui/tool_defaults.json`
- Windows: `%APPDATA%\pytkgui\tool_defaults.json`

Missing files are ignored. Files may contain only the values they need to
override; nested widget defaults are merged field by field. The user file has
highest priority so **Save as tool default** and **Save default** take effect
without modifying a system or source installation.

The top-level Grid settings are:

```json
{
  "gridRows": 25,
  "gridCols": 25,
  "gridLineColor": "",
  "gridRowMinsize": "2.5m",
  "gridColMinsize": "5m",
  "gridRowPad": "2.5m",
  "gridColPad": "5m"
}
```

Per-widget records live under `gridWidgetDefaults` and
`placeWidgetDefaults`. Place records contain only `width` and `height`.

Flet output is configured by two further keys, described under
[Generating Flet](#generating-flet): `fletGridMode` (`responsive` or
`absolute`) and `fletWidgetPolicy` (per widget type: `full`, `placeholder` or
`skip`).

Grid rows, columns, guide colour, minimum sizes, and padding are also saved in
each project. Project values override tool defaults when that project is
opened; tool defaults remain the starting values for new projects.

## Project files

New projects are stored below the platform configuration directory, normally:

```text
~/.config/pytkgui/MyProject/
```

The active file is `MyProject.json`. Each save is written to a temporary file,
parsed for validation, and atomically replaces the active file. Up to five
earlier versions are rotated as:

```text
MyProject-save1.json
MyProject-save2.json
...
MyProject-save5.json
```

**Tools → Open backup file** can load a saved backup.

Project JSON includes:

- project name, theme, and geometry manager
- window and Grid settings
- widget identity and creation order
- parent/child relationships
- Place or Grid geometry
- container Grid dimensions
- editable widget attributes
- callback and Tk-variable design names
- image references and logical groups
- the last generated Python path, when available

Older `.pk1` pickle projects can still be detected and opened. Because pickle
can execute code while loading, open legacy files only when you trust their
source. The next save writes the project in JSON format.

## Generating Python

**File → Generate Python** proposes `<project-name>.py` in the last output
directory. Widget constructors and geometry calls are formatted one argument
per line:

```python
Widget1 = ttk.Frame(
    rootWidget,
    width="0",
    height="0",
    cursor="arrow",
    style="primary.TFrame",
)
```

The generated file contains marked sections for Tk variables, callback
functions, widgets, and the main program. Callback names referenced by widgets
receive an initial stub:

```python
def save_record():
    # AUTO-GENERATED STUB
    print("save_record")
```

When the same generated file is selected again, PyTkQuickGui preserves edited
callback bodies and customised Tk-variable initialisers. Widget construction
and geometry sections are rebuilt from the current project. User functions no
longer referenced by a widget are also retained, and so are functions the
generator never wrote at all - a helper you add to the file survives the next
save.

Keep your own copy all the same. Put the generated file under version control,
and move a larger body of your own code into a separate module that imports the
generated one: the file is rebuilt from the project on every save, so it is not
the place to keep anything you would miss.

**Trial Run** writes and launches a temporary generated file. It is intended for
layout testing and does not replace the explicitly saved Python file.

## Generating Flet

**File → Generate Flet** writes a standalone [Flet](https://flet.dev) program
(`import flet as ft`, `def main(page)`, `ft.run(main)`) from the same project
data. The translation lives in `flet_generator.py` and is a pure function of the
project, so it can be tested without a display.

Run one in a browser to test it without a desktop build, and to open it from
another machine:

```bash
venv/bin/flet run --web ~/Calculator/Calculator_flet.py       # add --port 8550
```

The generated program is unchanged either way - `flet run --web` serves the same
file, and `python <program>.py` still runs it as a desktop application.
INSTALL.TXT has the details, including `--host 0.0.0.0`.

| Designer | Flet output |
|---|---|
| Place | `ft.Stack` with absolute `left`/`top`/`width`/`height` |
| Grid (default) | nested `ft.Column`/`ft.Row`; rows share the space and a widget with `sticky=nsew` fills its cell, so the layout stretches with the window the way ttk does |
| Grid (exact positions) | `ft.Stack` with `rowspan`/`columnspan` reproduced exactly; cells are sized from the widgets themselves (the designer's measurements, the tool default per type as a floor, minsize only as a floor like Tk) |
| Pack | `ft.Row`/`ft.Column` groups by `side` |
| Frame / Canvas | `ft.Container` (background preserved) holding an `ft.Stack` |
| Labelframe | `ft.Container` with the caption above the content (below for a south `labelanchor`), aligned as the designer's `labelanchor` says - centred for the default `n`. A `borderwidth` of 0 draws no box, as ttk does |
| Notebook | a panel `ft.Container` holding `ft.Tabs` with `ft.TabBar` and `ft.TabBarView`; the tab bar is pinned to ttk's manner (compact padding, left aligned, bootstyle accent on the selected tab) because Material's defaults are roomier and overflowed small notebooks |
| Panedwindow | `ft.Row`/`ft.Column` (Flet has no draggable splitter) |
| Label / Button / Entry / Combobox / Checkbutton / Radiobutton / Scale / Progressbar / Separator | `ft.Text` / `ft.Button` / `ft.TextField` / `ft.Dropdown` / `ft.Checkbox` / `ft.RadioGroup` / `ft.Slider` / `ft.ProgressBar` / `ft.Divider` |
| Spinbox | `ft.Row` of a numeric `ft.TextField` and ↑/↓ `ft.IconButton`s, stepping by the saved `from`/`to`/`increment` through a generated `_step_value` helper |
| Treeview | `ft.DataTable` with the saved column headings (rows are never stored in the project) |
| Listbox | `ft.ListView` |
| Scrollbar | folded into the widget it scrolls: `scroll=ft.Scrollbar(...)` on a `ft.ListView`, or a scrolling `ft.Column` wrapped around a canvas/table |
| Text | a multiline `ft.TextField` inside a `ft.Container` that gives it the designer's exact box (Flet sizes a multiline field from its line count, not from a height); its own scrollbar is dropped |
| `command`, `textvariable`, `variable` | `on_click`/`on_change`, plain Python values, `bool(...)` for check buttons |
| Tk colours | CSS hex (named Tk colours are mapped, unknown names are dropped) |

Things worth knowing:

- The output targets the **Flet 1.0** control API (`ft.Button`,
  `ft.DropdownOption`, `TabBar`/`TabBarView`) while staying compatible with the
  0.8x releases. Flet 1.0 removes `ft.ElevatedButton`, so buttons are emitted
  as `ft.Button`, which both generations provide.
- Every generated program opens with a version guard. It compares the running
  Flet against `MINIMUM_FLET_VERSION` (`'1.0'`) and, when the runtime is older,
  names the installed version and the upgrade command:

  ```
  warning: This program targets Flet 1.0 or later. Installed: 0.86.5.
  Upgrade with:  pip install --upgrade flet
  ```

  The program still runs — the 0.8x API is compatible — but set
  `FLET_VERSION_STRICT = True` in the generated file to make it refuse to
  start instead of warning.
- Tk options with no Flet equivalent (`takefocus`, `cursor`, `style`, …) are left
  out and listed in a `Translation notes` comment per widget, so nothing
  disappears silently.
- `relief` with a `borderwidth` above zero draws a border, as ttk does - the
  designer's own signal, so a label or frame the designer gave `relief=solid,
  borderwidth=1` comes out bordered rather than flat.
- Flet attaches scrollbars to a scrollable control
  (`ft.Column(scroll=ft.Scrollbar())`) rather than exposing a free-standing
  widget, and `ft.RadioGroup`/`ft.Divider` are not positional controls, so
  they are wrapped in a `ft.Container` to keep the designer's coordinates.
- A variable starts at **the value its widget showed in the designer** rather
  than a fixed `'0.0'`: type the value into the widget on the canvas (or tick a
  checkbutton), save or generate, and that is what the generated program
  initialises. A variable with nothing captured still starts at `'0.0'`, and
  the Python backend emits it as `tk.StringVar(rootWin, '123')`.
- A widget bound to a `textvariable` (a sudoku cell, a calculator display, a
  text area) keeps that binding: the generated program declares the variable,
  points the control at it, and provides `set_text(name, value)` to change it -
  which updates the variable *and* every control showing it, the way a Tk
  variable does. One variable can drive many controls.
- Each generated handler stub starts with `global <variables>`, so a plain
  assignment in your own code updates the module variable rather than creating
  a local name (Flet controls hold plain Python values, so unlike a
  `tk.StringVar` there is nothing to `.set()`). Use `set_text('calcvar', '4')`
  when you also want the widgets refreshed; `set_text` uses the page recorded
  in `main()`, so no page argument is needed. The same tip is written into the
  generated file's **Flet variables** section, next to the variables it is
  about.
- The window opens at a size worked out from the design rather than a fixed
  800x600: Grid and Pack from the widgets and their spans, Place from the
  furthest edge anything is placed at. It is clamped to 1280x900 and written to
  the generated file as `WINDOW_WIDTH`/`WINDOW_HEIGHT` with a comment, so
  adjusting it is a one line edit. Grid and Pack layouts reflow as the window
  is resized; Place positions are absolute, so they stay where the designer put
  them (a widget using relative width/height still stretches).
- Text style is pinned to a normal weight: Flet renders a `ft.TextStyle` whose
  weight is left unset in bold, which made button captions and check/radio
  labels heavier than the ttk originals.
- Notebook tab captions are stored as `tab_labels` metadata ("Home,Config")
  next to the widget, because they live on the tab ids rather than in the
  notebook's options — a label typed in the attribute editor now survives a
  save and reload, and both backends write it (`notebook.add(frame, text=…)`
  and `ft.Tab(label=…)`). A tab with no label is called "Tab".
- **Trial Run (Flet)** launches the generated program with `python3`.
- Regeneration keeps your work: a handler you have taken over - the
  `# AUTO-GENERATED STUB` line removed - and a variable line you have changed
  are carried over from the file you last generated to, exactly as the Python
  backend does. Untouched stubs are regenerated.
- ttkbootstrap themes are not Flet themes; the project theme is emitted as a
  `THEME` constant for reference only.

### Which geometry manager to use for Flet

**Place is the recommended target for Flet output.** It translates one to one:
every widget keeps the coordinates the designer gave it, the result looks like
the Trial Run, and there is nothing to interpret. If a Flet app is the goal,
design in Place.

**Grid works, but it is an interpretation, and it may need size tweaks.** Flet
has no grid layout at all - no spans, no minsize, no weights - so a Grid
project is rebuilt from rows and columns of `expand` weights. Known differences:

- `rowspan` is approximated: a widget that covers several rows occupies one
  band, at its designed size, instead of stretching down across the rows.
  **Exact positions** (the dialog option, or Tools → Flet: exact Grid
  positions) reproduces spans properly, at the cost of not reflowing.
- `minsize` is only a floor in Tk, and the designer's minsizes are Tk units
  (`2.5m` is about 9 pixels), so cell sizes are worked out from the widgets
  themselves. A design that relies on minsizes for its proportions will look
  different.
- `sticky` decides which axes a widget fills; partial stickies (`ew`, `w`) keep
  the designed size on the axes they do not fill.

**Pack** is the weakest of the three and is best avoided for Flet output.

### Writing or generating a project file by hand

A project is just JSON, so a program can be produced without opening the
designer - useful for scripted or generated UIs. The designer opens such a file
with **File → Open Project** as usual, and `flet_generator.emit_program()` /
`buildPython()` accept the same dictionary directly.

The smallest useful file needs the project keys plus one record per widget:

```json
{
  "formatVersion": 2,
  "ProjectName": "handwritten",
  "geomManager": "Place",
  "theme": "darkly",
  "backgroundColor": "skyBlue3",
  "imageFileNames": [],
  "widgetCount": 2,
  "Widget0": {
    "WidgetName": "ttk::button",
    "WidgetParent": "rootWidget",
    "Place": {"x": "16", "y": "16", "width": "120", "height": "32", "anchor": "nw"},
    "GeomData": {},
    "Attribute0": {"Key": "text", "Value": "Say hello"},
    "Attribute1": {"Key": "style", "Value": "success.TButton"},
    "Widget0-KeyCount": 2
  }
}
```

- `WidgetName` is the Tk widget type (`ttk::button`, `ttk::frame`, `canvas`,
  `text`, `listbox`, …); `WidgetParent` is another widget name or `rootWidget`.
- Attributes are Tk options: `text`, `textvariable`, `command`, `style`,
  `values`, `from`/`to`/`increment`, and so on. Keys Flet cannot express are
  reported in the generated file rather than silently dropped.
- Coordinates are relative to the parent, exactly as the designer stores them.
- `widgetNameList` is optional here: the loader rebuilds it from the widgets'
  parents if it is missing, and the designer writes it back on the next save.
- `theme` is what drives Flet colours, so it is worth setting even by hand.

### Theme colours

Project colours come from the ttkbootstrap theme named in the project, so a
Flet build looks like the Trial Run rather than like Flet's defaults. Your
widgets carry a `style` such as `primary.TButton`, `secondary.Outline.TButton`
or `success.Inverse.TLabel`, and the generator resolves each one:

| Style | Flet result |
|---|---|
| `primary.TButton` | filled with the theme's primary colour, text in black or white depending on the fill |
| `secondary.Outline.TButton` | theme background, primary-coloured border and caption |
| `primary.TLabel` | theme text colour (no background) |
| `success.Inverse.TLabel` | filled with the bootstyle colour, contrasting text |
| `primary.TFrame` | filled with the bootstyle colour |
| `primary.TLabelframe` | theme surface, bootstyle border, theme text caption |
| `primary.TEntry` / `TCombobox` / `TSpinbox` | the theme's input surface and text, with the theme's border colour |
| `primary.Horizontal.TProgressbar` | bootstyle-coloured bar on the theme's trough colour |
| `primary.Horizontal.TScale` | bootstyle-coloured track and thumb |
| `primary.TCheckbutton` / `TRadiobutton` | bootstyle-coloured indicator, theme-coloured caption |
| `primary.TNotebook` | theme surface with the theme's border |
| (window) | the theme's background, with Flet's own theme set to dark or light to match |

The colours are **exported from ttkbootstrap itself** into
`flet_theme_colors.json` by `tools/export_theme_colors.py`: each theme's
bootstyle colours and the resolved colours of real widgets, probed with
`style.lookup`. That matters because the Bootswatch-derived themes shade their
bootstyle colour (minty's buttons are `#609b8a`, not its `#78c2ad` slot) and
because ttk chooses black or white text per fill. The generator reads the JSON
only, so it still needs neither Tk nor ttkbootstrap.

Regenerate the palette after upgrading ttkbootstrap:

```bash
python3 tools/export_theme_colors.py     # needs ttkbootstrap 2.x and a display
```

Approximations worth knowing: a ttk progressbar draws its fill from a shaded
image, so the Flet bar uses the bootstyle colour directly; the same applies to
scale tracks and separator lines. If a project's theme is missing from the
palette (a custom theme, or a very old project), generation still works and
falls back to the palette slot colours — **Tools → Flet compatibility report**
says which happened.

### Flet compatibility report and per-type policy

**Tools → Flet compatibility report** lists every widget in the project with the
control it becomes, or why it cannot be one:

```
Widget0   canvas            ft.Container + ft.Stack (3 children)
Widget6   ttk::scrollbar    wraps Widget0 in a scrolling ft.Column (...)  [folded]

Summary: 7 widgets - 6 mapped, 1 folded into a scroll target, 0 placeholder, 0 skipped
```

**Generate Flet** and **Trial Run (Flet)** ask how to lay out a Grid project
before writing anything, because the two mappings suit different purposes:

- **Responsive** - rows and columns grow with the window, so the layout
  stretches the way a Flet app is expected to. A widget with `sticky=nsew`
  fills its cell; one with `sticky=ew` keeps the height the designer gave it.
  Row heights follow their content, so a one line widget is not stretched to
  the height of the tallest row.
- **Exact positions** - a `ft.Stack` that reproduces the designer's pixel
  layout, including `rowspan` and `columnspan`, but stays fixed when the window
  is resized.

The dialog shows the window size it worked out from the design and remembers
your answer in `tool_defaults.json` as `fletGridMode`. Place and Pack projects
have a single mapping, so they are not asked. **Tools → Flet: exact Grid
positions** still sets the remembered default without generating.

Both settings live in `tool_defaults.json`, next to the existing geometry
defaults, so they can be edited by hand or layered per project:

```json
{
  "fletGridMode": "responsive",
  "fletWidgetPolicy": {
    "default": "full",
    "treeview": "skip",
    "canvas": "placeholder"
  }
}
```

The policy is per widget type, using the same lower-case keys as
`gridWidgetDefaults`:

| Policy | Effect |
|---|---|
| `full` (default) | Emit the best mapping above; fall back to a placeholder only when Flet has no equivalent at all |
| `placeholder` | Emit a plain `ft.Container` with a note instead of the mapping — useful when a lossy mapping would be more misleading than an obvious gap |
| `skip` | Leave the widget out of the generated program entirely; children of a skipped container are promoted to its parent |

Skipping a widget never removes it from the project or from the Python
backend — it only affects Flet output.

## Themes

The Theme menu groups ttkbootstrap 2.0 light and dark themes and retains legacy
theme names for older projects. The selected theme is stored in the project and
used by generated Python.

Changing a theme can alter requested widget sizes. Grid layouts normally absorb
those differences; check a Trial Run when exact Place dimensions matter.

## Troubleshooting

- If a project JSON was hand-edited, validate its JSON syntax first.
- If a generated callback is skipped, check that its name is a valid Python
  identifier and not a Python keyword.
- If Grid guides appear stale after resizing, resize the main window once and
  report the project JSON and steps needed to reproduce it.
- Use the most recent `-saveN.json` backup if an active project file is damaged.
- Runtime detail is written through Python logging. Benign Tk lookups on a
  widget already destroyed during cleanup are logged at debug level.

### Debugging a crash

Tk and Flet both carry C code, so a fault can end the process with a segfault
rather than a traceback. Three things make that diagnosable:

- **A Python traceback on a fatal signal.** `faulthandler` is enabled at
  startup, so a crash prints the Python frame that was running to stderr.
  `kill -USR1 <pid>` prints a traceback of every thread on demand, which is the
  quickest way to see where a hung window is stuck.
- **Core dumps are kept by systemd.** No `ulimit` needed - the kernel pipes
  cores to `systemd-coredump`:

  ```bash
  coredumpctl list                 # every crash, with pid and time
  coredumpctl info <pid>           # summary and stack trace
  coredumpctl gdb <pid>            # load it in gdb: bt, py-bt
  coredumpctl dump <pid> --output=core   # then: gdb -batch -ex bt /usr/bin/python3.12 core
  ```

- **Python frames in gdb** need `sudo apt install python3.12-dbg`; without it a
  core shows only C frames (`_PyEval_EvalFrameDefault` and friends), with it
  `py-bt` names the Python function.

A crash seen here in the wild, for reference: `Tk_Get3DBorderFromObj` inside
`Tk_Free3DBorderFromObj` inside `Tk_FreeConfigOptions`, reached from
`Tk_BindEvent` - Tk freeing a widget's border while a binding was still running,
i.e. a widget destroyed from inside a binding or a `validate=` callback. If you
hit it, the traceback from the steps above points at the Python line.

## Current limitations

- Pack cannot be selected for a new project.
- The palette deliberately exposes a smaller widget set while remaining widgets
  are stabilised.
- Some complex widgets require application-specific setup that a visual builder
  cannot infer, such as connecting scrollbars to targets.
- **Place is the default** for a new project, and the recommended target for
  Flet output: it translates one to one, where Grid has to be interpreted.
- Generated files are suggested as `<home>/<project>/<project>_ttk.py` and
  `<project>_flet.py`, so both outputs of a project sit together; the path you
  choose is remembered with the project and used for edit preservation.
- Flet has no draggable splitter, and a Tk scrollbar with no scrollable target
  (or a horizontal one) stays a placeholder Container.
- **Exact Grid positions** sizes a cell from the widgets in it, not from the
  stored minsize: `2.5m` is only 9px, and Tk treats minsize as a floor too. A
  designer widget that measures small because its caption comes from an empty
  `textvariable` never shrinks below the tool default for its type. Exact mode
  keeps the layout fixed instead of reflowing, so use it for position parity,
  not for a window the user is expected to resize.
- In Grid output the empty columns the designer draws still take a share of the
  width, because the Python backend gives every column `weight=1` - so a board
  that spans 9 of 10 columns leaves a strip on the right in both backends.
- Trial Run and visual editing require a desktop session with Tk support.
- Legacy pickle compatibility is temporary and should be treated as a migration
  path to JSON.

## Development and testing

Run the unit tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

When contributing:

1. Work on a focused branch.
2. Keep generated and persistence formats backwards-compatible where practical.
3. Use `logging` instead of diagnostic `print` calls in application code.
4. Test both Grid and Place, including a child widget inside a container.
5. Test a save, reload, Trial Run, and generated Python file.
6. Run the Flet generator over the same project (`Generate Flet`) when widget
   mapping or geometry changes, and re-run `tools/export_theme_colors.py` when
   ttkbootstrap itself is upgraded.
7. Check at least one light and one dark ttkbootstrap theme.

Bug reports are most useful when they include the project JSON, the selected
geometry manager, the sequence of editing actions, and the complete traceback.

### Checking generated Flet code after an upgrade

Several Flet mappings rest on *measured* behaviour - a multiline field takes its
height from `min_lines`, a `ft.TextStyle` with no weight is drawn bold, Material
paints a check/radio fill in every state, `ft.Tabs` takes a
`TabBar`/`TabBarView` content - and a Flet upgrade can change any of them
without changing the major version. `tools/smoke_flet_generated.py` is the
answer: it generates every saved project (default, exact-position Grid and
skip-optional modes), parses the result, builds the controls with the installed
Flet and exits non-zero on failure.

```bash
venv/bin/python tools/smoke_flet_generated.py          # the saved projects
venv/bin/python tools/smoke_flet_generated.py --all    # including backups
venv/bin/python tools/smoke_flet_generated.py ~/elsewhere/*.json
```

## License

MIT. See [`LICENSE`](LICENSE).

## Releases

Notable changes by version are in [`CHANGELOG.md`](CHANGELOG.md).

PyTkQuickGui — Chris McGowan, 2024–2026.
