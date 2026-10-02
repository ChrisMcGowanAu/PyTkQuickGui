# Rehearsing a PyTkQuickGui demo

A script for a how-to video, and the material for a website. The scenes are
ordered so each one has something new on screen; timings are a guide, not a
target. Everything here is done through the menus, so it can be recorded in one
take.

## One-time setup

1. Install and run as INSTALL.TXT describes (venv, then
   `venv/bin/python pytkquickgui.py`).
2. Put the shipped projects where the tool can open them:

   ```bash
   mkdir -p "$HOME/.config/pytkgui/examples"
   cp -r examples/* "$HOME/.config/pytkgui/examples/"
   ```

3. Make the UI readable on video. The default font is small at 1080p; **Tools >
   Set default label font** and **Tools > Set default style font** both take a
   larger size, and the window can be dragged to a 16:9 shape before recording.
4. Keep `docs/example_*.png` open in a second window: they are the stills for
   cutaways and for the website.

## The scenes

| Time | Do this | On screen |
|---|---|---|
| 0:00 | Cold open. Say what the finished thing is: a notebook, a form, a couple of buttons, in Flet and in Tk from one layout. | Show `docs/example_tabs_flet.png` as the target. |
| 0:15 | Launch the tool (`./run.sh`). | The designer with an empty canvas. Point out the menus: File, Edit, Theme, Tools, Help. |
| 0:30 | **File > Open Project**, then double-click `examples`, then `Calculator`. Drag a button with the mouse, then undo with Ctrl+Z and redo with Ctrl+Y. | A finished project appears; undo/redo works on the live canvas. |
| 1:00 | **File > New Project**, name it `Demo`, choose Place. Right-click the canvas, pick **Button**. Drag it to move, drag an edge to resize. Right-click it, choose **Edit**, change the text and the bootstyle, press Apply. If the widget has a `textvariable`, the text you type becomes that variable's value. | Placing, moving and editing by hand. |
| 1:45 | **File > Open Project > examples > tabs**. Click the body of a tab, right-click, choose **Edit**, and change the tab captions. | A notebook where every tab is an ordinary Frame you can fill. |
| 2:30 | **File > Trial Run**. | The real ttkbootstrap program, running. This is the first payoff. |
| 3:00 | **File > Generate Python**, save it as `demo.py`, open the file in an editor. Point out the readable widget calls, and that a callback you edited in a previous version is carried over rather than overwritten. | The generated Python at `demo.py`. |
| 3:45 | **File > Generate Flet**, then **File > Trial Run (Flet)**. | The same layout running as a Flet application. The Flet compatibility report is worth showing here: it lists anything that had to be approximated. |
| 4:30 | Optional second act: **File > Open Project > examples > sudokupack**, then **Tools > Edit Grid settings**, and drag a widget so it snaps. | Grid mode, and how a project's grid is configured. |
| 5:00 | **File > Save Project**, then Ctrl+Z a few times. Mention that each save keeps rolling `-saveN` backups, and where `examples/` came from. | The JSON project and the undo stack. |

## Before each take

- **Restart the tool after changing its code.** A running instance keeps the
  modules it started with, so a fix can look like it did nothing.
- **`flet.py` is safe to type in the save dialog.** The tool writes it as
  `flet1.py` and says why: a program called flet.py is imported in place of the
  Flet package and cannot start. The same applies to `tkinter.py` and
  `ttkbootstrap.py`.
- **Close each Trial Run window before the next take.** A Flet window can
  outlive the Python process that started it, leaving a window on screen that
  belongs to nothing.
- **A Grid project opens at the size its layout asks for**, and stretches from
  there as you resize the window. If a Grid project looks sparse, the grid
  itself is larger than the content - tighten it under Tools > Edit Grid
  settings.

## Stills

`docs/` holds the stills used by README.md, and they can all be regenerated:

```bash
tools/screenshots.sh                # every project in examples/
tools/screenshots.sh tabs sudoku3   # just these
```

The script opens each project in both backends off screen, screenshots the real
window and writes `docs/example_<name>_tk.png` and `_flet.png`. It needs a
desktop session, so it is a local tool rather than something CI can run.
