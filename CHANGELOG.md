# Changelog

Notable changes to PyTkQuickGui, newest first. Version names are the tags as
released; entries up to `v1.00-RC1` are the release notes as published on
GitHub, kept close to their original wording.

## Unreleased — planned as v1.00

The Flet code generation of v1.00-RC1, plus the round of fixes that followed it:
the designer no longer crashes, the Flet output keeps a shared variable in step,
and the code you write into a generated file is kept rather than deleted.

**Fixed**

- The designer could segfault when a widget that validates was torn down.
  Destroying it fired focusout, focusout ran validatecommand while the widget
  was being destroyed, and Tk freed a 3D border twice. Validation is now
  switched off before anything is destroyed, and destroys are deferred out of
  the binding that triggered them. If it should ever happen again, the console
  names the last action and the last widget destroyed.
- A Grid project's exported window took its size from the designer's canvas
  instead of the project, so two unrelated projects came out at the same size.
- Cancelling the open-project dialog raised an error rather than simply saying
  nothing was selected.
- A generated program named after a module it imports — `flet.py` — cannot run,
  so it is written as `flet1.py` now.

**Flet output**

- A variable shared by two widgets — a spinbox and a scale, say — keeps both in
  step, the way Tk does.
- A widget's caption typed in the attribute editor becomes its variable's value,
  so the design, the saved project and the generated program agree.

**Designer**

- A multi-selection is visible: selected widgets are outlined on the canvas, and
  grouping uses the themed dialog and confirms what it did.
- Tools → Set default style font is saved with the tool defaults, so it survives
  a restart, and both generated programs carry it.
- On a Mac a two-finger tap or Control-click opens the widget menus, so a three
  button mouse is no longer needed.

**Generated code**

- Functions you add to a generated file are no longer deleted when it is
  regenerated — only the widget construction and the layout are rebuilt. Keep
  your own copy all the same, and put a larger body of your own code in a module
  that imports the generated one. The generated programs say this in their
  header, and Help explains it.

**Also**

- Seven example projects ship in `examples/`, each with its ttk and Flet
  screenshots in `docs/`, and INSTALL.TXT shows how to load them.
- `docs/walkthrough.md` is a script for recording a demo, including the style
  font tip that makes a Calculator readable on video.
- Development: flake8, ruff, isort, black and pylint are configured and run in
  CI, with a conda environment file and a smoke test that generates and builds
  every saved project.

## v1.00-RC1 — 2026-10-02

*Version 1.0 release candidate. Now includes flet code generation*

This is a very large release. A lot of bugs have been fixed, and the tool now
generates Flet code. Improvements have been made to make it easier to add your
back end code to the generated python. There are also examples to see how it
works. A video and a walkthrough on a website are planned.

## V0.92_Beta — 2026-10-01

*This release has the first cut of outputting FLET UI code*

Building a FLET GUI tool in FLET could be a very difficult task. This takes the
existing tool that generated Python/ttkbootstrap and generates python/FLET code.
Some of it works very well, but there is a mismatch between FLET and
TK/ttkbootstrap. Looking at that now and will try and fix most of the gremlins.

## V0.9_Beta_RC1 — 2026-07-30

This is the first Beta release.

Both Place and Grid work. A lot of work was done to make the
save/reopen/generate reliable and readable. This release requires ttkbootstrap
2.0 and uses ttkbootstrap widgets only. Some widgets are not included as they
need some effort to make them work, and will be added later. There is now an
editable json file with defaults for widget layout in place and grid.

## v0.8 — 2026-07-21

*Stable Place geometry*

Place geometry is quite stable. Grid does work, but it needs more work — for
simple Grid layouts it is OK. JSON saves, a geometry manager toolbar and new
widgets arrive in this release.

## 0.75A — 2026-06-16

*Release with fixes and more functionality*

Updated to the latest ttkbootstrap with various issues fixed. This version also
has more widgets, though some need more testing. Two layout styles work
reasonably well; Place and Grid work but Pack does not at this stage.

## v0.62alpha — 2024-08-25

*Fixes for Python 3.12*

Python always amazes me in breaking code that ran without error or warnings in
previous releases. Debian bookworm and therefore Ubuntu noble based distros have
done something weird when installing python packages. The pylint warnings are
not fixed yet — that is for the next release.

## v0.61alpha — 2024-08-20

*Save backups of projects and the ability to restore them*

Save backups of projects and the ability to restore them, as well as bug fixes
when excising the code. Added a new python file.

## v0.6alpha — 2024-07-24

*Loading and saving project improvements*

## v0.5alpha — 2024-07-19

*Images now working*

Images can be saved and restored and run in the generated python. Some old
project files may not work correctly until the project is saved. Images are hard
and a right pain to do: it copies the absolute path for all image files, which
is possibly OK for generated python as the paths are all in one spot and can be
edited to point to correct images on another machine.

## V0.1.5Alpha — 2024-07-16

*More tweaks to re-parenting and menu items*

## V0.4.0-Alpha — 2024-07-15

## V0.3.0-alpha — 2024-07-15

## v0.2.0-alpha — 2024-07-04

The three tags above were released without notes.
