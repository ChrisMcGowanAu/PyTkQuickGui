"""Exports made by the running designer: window size and output file names.

Window size regression: buildPython used to take the design canvas *as
rendered* (grid_bbox) as the exported window size, so the export followed the
designer rather than the project - two unrelated Grid projects both came out at
908x772.  It now uses the layout's requested size, which Tk works out from the
cells and their contents.

Output name: a generated program called flet.py cannot run, because ``import
flet`` loads the file itself instead of the package.  Both export call sites are
covered, with the save dialog and the message box stubbed out.

These tests start the real designer, so they need a display and are skipped
where there is not one (CI runs headless).
"""

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
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


if __name__ == "__main__":
    unittest.main()
