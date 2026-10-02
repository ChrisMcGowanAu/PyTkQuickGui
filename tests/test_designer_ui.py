"""Designer UI behaviour: exported window size, output file names, clicks.

Window size regression: buildPython used to take the design canvas *as
rendered* (grid_bbox) as the exported window size, so the export followed the
designer rather than the project - two unrelated Grid projects both came out at
908x772.  It now uses the layout's requested size, which Tk works out from the
cells and their contents.

Output name: a generated program called flet.py cannot run, because ``import
flet`` loads the file itself instead of the package.  Both export call sites are
covered, with the save dialog and the message box stubbed out.

Secondary click: the widget menus must open from every gesture that means
"right click", not just Button-3, or a Mac without a three button mouse cannot
reach them.

These tests start the real designer, so they need a display and are skipped
where there is not one (CI runs headless).
"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import tkinter as tk
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
    import createWidget as cw
    import project_format
    import pytkguivars as my_vars
    import pytkquickgui as app

    IMPORT_ERROR = None
except Exception as error:  # noqa: BLE001 - no display, no ttkbootstrap, ...
    app = None
    IMPORT_ERROR = error

EXAMPLE = os.path.join(PROJECT_ROOT, "examples", "sudokupack", "sudokupack.json")
WORK = None
ORIGINAL_STDOUT = None


def setUpModule():
    global WORK, ORIGINAL_STDOUT
    if app is None:
        return
    WORK = tempfile.mkdtemp(prefix="designer-exports-")
    ORIGINAL_STDOUT = sys.stdout
    start_designer()


def tearDownModule():
    # The Tk root is deliberately left alive: other designer test modules share
    # it, and destroying it here made the next module's setUpModule fail.
    if ORIGINAL_STDOUT is not None:
        sys.stdout = ORIGINAL_STDOUT


def start_designer():
    """Create the designer's window once, however many modules need it."""
    if getattr(app, "_test_gui_ready", False):
        return
    app.rootWin.withdraw()
    app.myVars.initVars()
    app.buildMainGui()
    app._test_gui_ready = True


def quiet(function, *args, **kwargs):
    """Run a designer function that prints, without polluting test output."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        return function(*args, **kwargs)


@unittest.skipIf(app is None, f"the designer cannot start here: {IMPORT_ERROR}")
class GridWindowSizeTests(unittest.TestCase):
    def setUp(self):
        quiet(app.loadProject, "sudokupack", EXAMPLE)
        # buildPython calls saveProject; keep its writes in the scratch dir.
        app.myVars.projectPath = WORK
        app.myVars.projectFileName = os.path.join(WORK, "sudokupack")

    def _exported_geometry(self):
        generated = quiet(app.buildPython)
        with open(generated, encoding="utf-8") as handle:
            source = handle.read()
        match = re.search(r"rootWin\.geometry\('(\d+x\d+)'\)", source)
        self.assertIsNotNone(match, "no rootWin.geometry() in the generated program")
        return match.group(1)

    def test_size_is_the_layouts_requested_size(self):
        app.geomWidgetFrame.update_idletasks()
        expected = (
            f"{app.geomWidgetFrame.winfo_reqwidth() + 20}"
            f"x{app.geomWidgetFrame.winfo_reqheight() + 20}"
        )
        self.assertEqual(self._exported_geometry(), expected)

    def test_grid_project_is_not_exported_at_the_canvas_size(self):
        # The canvas reports a much larger box than the layout needs; the old
        # code took that box (plus the 20px margin) as the window size.
        app.geomWidgetFrame.update_idletasks()
        columns, rows = app.geomWidgetFrame.grid_size()
        bbox = app.geomWidgetFrame.grid_bbox(columns - 1, rows - 1)
        as_canvas = f"{bbox[0] + bbox[2] + 20}x{bbox[1] + bbox[3] + 20}"
        self.assertNotEqual(self._exported_geometry(), as_canvas)


@unittest.skipIf(app is None, f"the designer cannot start here: {IMPORT_ERROR}")
class OutputNameTests(unittest.TestCase):
    """A generated file must not shadow a module the generated program imports."""

    def setUp(self):
        quiet(app.loadProject, "sudokupack", EXAMPLE)
        app.myVars.projectPath = WORK
        app.myVars.projectFileName = os.path.join(WORK, "sudokupack")
        app.myVars.generatedPyFile = ""
        app.myVars.generatedFletFile = ""
        self.messages = []
        self._saved = {
            "dialog": app.tk.filedialog.asksaveasfilename,
            "info": app.Messagebox.show_info,
            "options": app.askFletOptions,
            "save": app.saveProject,
        }
        app.Messagebox.show_info = lambda **kwargs: self.messages.append(kwargs)
        app.askFletOptions = lambda: True
        app.saveProject = lambda *args, **kwargs: True
        self.addCleanup(self._restore)

    def _restore(self):
        app.tk.filedialog.asksaveasfilename = self._saved["dialog"]
        app.Messagebox.show_info = self._saved["info"]
        app.askFletOptions = self._saved["options"]
        app.saveProject = self._saved["save"]

    def _export(self, function, chosen_name):
        chosen = os.path.join(WORK, chosen_name)
        app.tk.filedialog.asksaveasfilename = lambda **kwargs: chosen
        quiet(function)
        return chosen

    def test_flet_export_named_flet_py_is_written_as_flet1_py(self):
        chosen = self._export(app.generateFlet, "flet.py")
        self.assertFalse(os.path.exists(chosen), "a program named flet.py cannot run")
        self.assertTrue(os.path.isfile(os.path.join(WORK, "flet1.py")))
        self.assertEqual(app.myVars.generatedFletFile, os.path.join(WORK, "flet1.py"))
        self.assertTrue(self.messages, "the user was not told the name changed")

    def test_ttk_export_named_tkinter_py_is_written_as_tkinter1_py(self):
        chosen = self._export(app.generatePython, "tkinter.py")
        self.assertFalse(os.path.exists(chosen))
        self.assertTrue(os.path.isfile(os.path.join(WORK, "tkinter1.py")))
        self.assertEqual(app.myVars.generatedPyFile, os.path.join(WORK, "tkinter1.py"))

    def test_an_ordinary_name_is_used_as_chosen(self):
        chosen = self._export(app.generateFlet, "Calc_flet.py")
        self.assertTrue(os.path.isfile(chosen))
        self.assertEqual(self.messages, [], "no message should be shown")


@unittest.skipIf(app is None, f"the designer cannot start here: {IMPORT_ERROR}")
class SecondaryClickTests(unittest.TestCase):
    """Button-3 is not the only gesture that opens the widget menus.

    A Mac trackpad's two-finger tap arrives as Button-2 in some Tk builds and as
    Button-3 in others, and Control-click as Control-Button-1, so binding
    Button-3 alone leaves the menus unreachable without a three button mouse.
    """

    def setUp(self):
        # A synthetic event cannot be delivered to a withdrawn window, so this
        # checks the bindings rather than the events.
        self.frame = tk.Frame(app.rootWin)
        app._bindRightClick(self.frame, lambda event: None)
        self.addCleanup(self.frame.destroy)

    def test_every_secondary_click_gesture_is_bound(self):
        bound = self.frame.bind()
        for sequence in app.myVars.RIGHT_CLICK_BINDINGS:
            with self.subTest(sequence=sequence):
                self.assertIn(sequence, bound)

    def test_the_gestures_include_the_mac_trackpad_ones(self):
        self.assertIn("<Button-2>", app.myVars.RIGHT_CLICK_BINDINGS)
        self.assertIn("<Control-Button-1>", app.myVars.RIGHT_CLICK_BINDINGS)


@unittest.skipIf(app is None, f"the designer cannot start here: {IMPORT_ERROR}")
class OpenProjectDialogTests(unittest.TestCase):
    """Cancelling the directory dialog must be a no-op, not an error.

    Tk's askdirectory returns "" or () when it is cancelled, and loadProject
    only compared the result with the config path - so a cancel took the success
    path and os.path.join raised "expected str, bytes or os.PathLike object, not
    tuple", which is what the user saw immediately before a segfault.
    """

    def setUp(self):
        self.errors = []
        self._saved = {
            "directory": app.tk.filedialog.askdirectory,
            "error": app.Messagebox.show_error,
            "save": app.saveProject,
        }
        app.Messagebox.show_error = lambda **kwargs: self.errors.append(kwargs)
        app.saveProject = lambda *args, **kwargs: True
        self.addCleanup(self._restore)

    def _restore(self):
        app.tk.filedialog.askdirectory = self._saved["directory"]
        app.Messagebox.show_error = self._saved["error"]
        app.saveProject = self._saved["save"]

    def _cancel_returns(self, value):
        app.tk.filedialog.askdirectory = lambda **kwargs: value
        before = (app.myVars.projectName, app.myVars.projectPath)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            app.loadProject(None, None)
        return before

    def test_an_empty_tuple_cancel_is_a_no_op(self):
        before = self._cancel_returns(())
        self.assertEqual((app.myVars.projectName, app.myVars.projectPath), before)

    def test_an_empty_string_cancel_is_a_no_op(self):
        before = self._cancel_returns("")
        self.assertEqual((app.myVars.projectName, app.myVars.projectPath), before)

    def test_the_user_is_told_nothing_was_selected(self):
        self._cancel_returns(())
        self.assertTrue(self.errors, "no message was shown for a cancelled dialog")


def callback_project(path, command_name):
    """A one widget project whose spinbox carries a design-time callback name."""
    project = {
        "formatVersion": 2,
        "ProjectName": "cbtest",
        "geomManager": "Place",
        "theme": "cyborg",
        "widgetNameList": [["Widget0", "rootWidget", "", []]],
        "widgetCount": 1,
        "Widget0": {
            "WidgetName": "ttk::spinbox",
            "WidgetParent": "rootWidget",
            "Place": {"x": "0", "y": "0", "width": "100", "height": "32"},
            "GeomData": {},
            "Attribute0": {"Key": "command", "Value": command_name},
            "Attribute1": {"Key": "textvariable", "Value": "spin_value"},
            "Widget0-KeyCount": 2,
        },
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(project, handle)
    return path


@unittest.skipIf(app is None, f"the designer cannot start here: {IMPORT_ERROR}")
class DesignTimeCallbackTests(unittest.TestCase):
    """A stored callback is a Python name, not a command Tk can call yet.

    Handing it straight to widget.configure() left Tk invoking a command that
    does not exist, so using the widget on the canvas raised "invalid command
    name" from inside Tk's own bindings - and the name had to survive the next
    save, because it is what the generated program defines.
    """

    def setUp(self):
        self.path = callback_project(os.path.join(WORK, "cbtest.json"), "timeSpin")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            app.loadProject("cbtest", self.path)
        app.myVars.projectPath = WORK
        app.myVars.projectFileName = os.path.join(WORK, "cbtest")

    def _spinbox(self):
        entry = cw.findPythonWidgetNameList("Widget0")
        return entry[cw.WIDGET]

    def test_the_design_time_name_is_registered_as_a_command(self):
        registered = app.rootWin.tk.call("info", "commands", "timeSpin")
        self.assertTrue(registered, "Tk has no command named timeSpin")

    def test_invoking_it_is_harmless(self):
        # This is what Tk's spinbox does on an arrow click: it must not raise
        # (it used to be "invalid command name").  The stub returns nothing, so
        # Tcl hands back the string "None".
        self.assertIn(str(app.rootWin.tk.call("timeSpin")), ("", "None"))

    def test_the_widget_reports_the_name_unchanged(self):
        self.assertEqual(str(self._spinbox().cget("command")), "timeSpin")

    def test_the_name_survives_a_save(self):
        saved = my_vars.saveWidgetAsDict("Widget0")["Widget0"]
        attributes = project_format.attribute_map("Widget0", saved)
        self.assertEqual(attributes.get("command"), "timeSpin")
        self.assertEqual(attributes.get("textvariable"), "spin_value")


@unittest.skipIf(app is None, f"the designer cannot start here: {IMPORT_ERROR}")
class DestroyWidgetTests(unittest.TestCase):
    """Destroying must be safe from a binding, and must refuse to happen twice.

    A second destroy of a widget Tk has already taken down (a child of a parent
    destroyed first, say) double-frees its option table - the segfault the core
    dumps show - and a widget that validates re-enters Tk's config code while it
    is being torn down, so its validation is turned off first.
    """

    def test_validation_is_turned_off_across_the_subtree(self):
        frame = tk.Frame(app.rootWin)
        entry = tk.Entry(frame, validate="focusout")
        entry.pack()
        self.addCleanup(frame.destroy)
        cw.disableValidation(frame)
        self.assertEqual(str(entry.cget("validate")), "none")

    def test_the_widget_is_destroyed(self):
        frame = tk.Frame(app.rootWin)
        cw.destroyWidget(frame)
        app.rootWin.update()
        self.assertFalse(frame.winfo_exists())

    def test_destroying_it_again_is_harmless(self):
        frame = tk.Frame(app.rootWin)
        cw.destroyWidget(frame)
        app.rootWin.update()
        cw.destroyWidget(frame)  # must not raise
        app.rootWin.update()

    def test_a_child_of_a_destroyed_parent_is_skipped(self):
        parent = tk.Frame(app.rootWin)
        child = tk.Frame(parent)
        cw.destroyWidget(parent)
        app.rootWin.update()
        self.assertFalse(parent.winfo_exists())
        cw.destroyWidget(child)  # Tk already took it down with the parent
        app.rootWin.update()


if __name__ == "__main__":
    unittest.main()
