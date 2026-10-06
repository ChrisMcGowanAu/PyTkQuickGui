# Building the Calculator — a shot list

The goal: a *working* calculator, drawn in the tool, then running as a normal
ttkbootstrap application and as a Flet one. Around six minutes.

This is the second video, so it can assume the tool is installed. It uses the
`Calculator` project that ships in `examples/`, which INSTALL.TXT copies into
the tool's directory.

## Before you record

- **Set the style font first** (Tools → Set default style font). With the
  shipped default the digits and operators look cramped, and it is easier to do
  before anything is placed. This is the one thing that makes the calculator
  look right on camera.
- **Clear the two leftover fonts.** The display entry and the "Simple
  Calculator" label still carry an old font (`C059`) saved as a dictionary. No
  output uses it now, but the attribute editor shows it, and it looks like a
  bug. Select each widget → Edit → clear the font field → Apply.
- **Restart the tool** if you have changed its code — a running instance keeps
  the modules it started with.
- Have `docs/example_Calculator_tk.png` and `docs/example_Calculator_flet.png`
  open in a second window: they are the opening and closing cards.

## The scenes

| Time | Do this | On screen |
|---|---|---|
| 0:00 | Say what you are making: a working calculator, drawn once, running as a desktop app and in a browser. | `example_Calculator_flet.png` as the target. |
| 0:15 | **File → Open Project → examples → Calculator**. | The finished layout: a title, the display, nineteen buttons. |
| 0:30 | Drag a button to move it, then Ctrl+Z. Point out the dotted grid and `Layout: Place` in the toolbar. | Editing the layout by hand. |
| 0:50 | Right-click the canvas → **Button**. Drag it into place. Right-click it → **Edit**, set its text and bootstyle, Apply. | Adding one more button (`%`, or a `←`). |
| 1:30 | One line on Place versus Grid: Place for free-form, Grid for rows and columns. | Optional — the concept, without a detour. |
| 2:00 | Right-click each button → **Edit** → set `command` to a function name (`clicked_7`, `clicked_plus`, …). | The wiring: nothing runs yet, but each button knows its handler. |
| 3:00 | **File → Generate Python**, save as `calculator.py`, open it in an editor. | The generated program: widgets, the variables section, one stub per button. |
| 3:30 | Type your own `do_calculation`, `append` and `remove_last_ch` into the file, above the stubs. | **Your code**, in the generated file. |
| 4:30 | **File → Generate Python** again, and scroll back to the same place. | **Your functions are still there.** This is the beat the video is for. |
| 5:00 | **File → Trial Run**. Click `7`, `+`, `5`, `=` on camera. | The calculator working as a ttkbootstrap app. |
| 5:30 | **File → Generate Flet**, then **File → Trial Run (Flet)**. | The same calculator, running in Flet. |
| 6:00 | Close: one layout, two backends, and the code you write is kept. Mention `examples/` and INSTALL.TXT. | `example_Calculator_flet.png`, side by side with the ttk one if you can. |

## On camera, avoid

- **A stale Flet window.** A Flet desktop client can outlive the application, so
  a change can look like it did nothing. Close the window (or `pkill flet`) and
  run it again.
- **Naming an exported Flet program `flet.py`** — it would import itself. Any
  other name is fine, and the tool renames that one to `flet1.py` anyway.

Timings are a guide. The beats that matter: the font before placing, the
regenerated file keeping your functions, and Flet running the same layout.
