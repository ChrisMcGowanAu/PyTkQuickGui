"""Text typed in the attribute editor for a widget that uses a textvariable.

Tk ignores the ``text`` option once a ``textvariable`` is set, so a caption
typed in the editor used to be dropped: the design kept showing whatever the
variable held (often nothing), and the generated program fell back to its own
default.  The typed text is now written into the variable, so the design, the
saved project and both generated programs agree.

These tests open the real attribute editor, so they need a display and are
skipped where there is not one (CI runs headless).
"""
import contextlib
import io
import os
import sys
import tempfile
import tkinter as tk
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
    import createWidget as cw
    import editWidget as ew
    import project_format
    import pytkguivars as my_vars
    import pytkquickgui as app

    IMPORT_ERROR = None
except Exception as error:  # noqa: BLE001 - no display, no ttkbootstrap, ...
    app = None
    IMPORT_ERROR = error

WORK = None


def setUpModule():
    global WORK
    if app is None:
        return
    WORK = tempfile.mkdtemp(prefix="editor-text-")
    start_designer()


def tearDownModule():
    # The Tk root is shared with the other designer test modules; leave it up.
    pass


def start_designer():
    """Create the designer's window once, however many modules need it."""
    if getattr(app, "_test_gui_ready", False):
        return
    app.rootWin.withdraw()
    app.myVars.initVars()
    app.buildMainGui()
    app._test_gui_ready = True


def load(project):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        app.loadProject(project, os.path.join(PROJECT_ROOT, "examples", project,
                                              f"{project}.json"))
    app.myVars.projectPath = WORK
    app.myVars.projectFileName = os.path.join(WORK, project)


def widget_named(widget_name):
    entry = cw.findPythonWidgetNameList(widget_name)
    return entry[cw.WIDGET] if entry else None


def widget_with_class(class_name):
    """Return ``(name, widget)`` for the first loaded widget of that Tk class."""
    for name in app.workOutWidgetCreationOrder():
        widget = widget_named(name)
        if widget is None:
            continue
        try:
            if widget.winfo_class() == class_name:
                return name, widget
        except tk.TclError:
            continue
    return None, None


def type_text_in_editor(widget, widget_name, text):
    """Open the attribute editor, put *text* in the text field, press Apply."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
        io.StringIO()
    ):
        popup = ew.widgetEditPopup(app.rootWin, widget, widget_name)
        popup.createEditPopup()
        field = popup.stringDict.get("textWidget")
        if field is not None:
            field.delete(0, tk.END)
            field.insert(0, text)
            # Clicking Apply moves focus out of the entry first, which is what
            # copies the typed text into stringDict in the real editor.
            popup.popupCallback("text")
        else:  # no entry (no text option): fall back to the recorded value
            popup.addToStringDict("text", text)
        popup.applyEditSettings()
    return popup


def text_variable(widget):
    """The widget's textvariable name, or "" when it has no such option."""
    try:
        return str(widget.cget("textvariable") or "")
    except tk.TclError:
        return ""


def variable_value(widget):
    """What the widget's textvariable holds, or None if it has none."""
    name = text_variable(widget)
    if not name:
        return None
    try:
        return widget.getvar(name)
    except tk.TclError:
        return None


@unittest.skipIf(app is None, f"the designer cannot start here: {IMPORT_ERROR}")
class TextVariableTests(unittest.TestCase):
    def test_typed_caption_is_stored_in_the_textvariable(self):
        load("UserForm")
        label = widget_named("Widget15")
        self.assertEqual(text_variable(label), "usersGroup")
        # Explicit, so the result does not depend on what another test left in
        # the Tcl interpreter: a variable survives reloading a project.
        label.setvar("usersGroup", "")

        type_text_in_editor(label, "Widget15", "Everyone")

        self.assertEqual(variable_value(label), "Everyone")
        self.assertEqual(str(label.cget("text")), "Everyone")

    def test_the_stored_caption_is_saved_and_generated(self):
        load("UserForm")
        label = widget_named("Widget15")
        type_text_in_editor(label, "Widget15", "Everyone")

        saved = my_vars.saveWidgetAsDict("Widget15")["Widget15"]
        attributes = project_format.attribute_map("Widget15", saved)
        self.assertEqual(attributes.get(project_format.VAR_VALUE_KEY), "Everyone")

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            python_file = app.buildPython()
            flet_file = app.buildFlet()
        with open(python_file, encoding="utf-8") as handle:
            python_source = handle.read()
        with open(flet_file, encoding="utf-8") as handle:
            flet_source = handle.read()
        self.assertIn("usersGroup = tk.StringVar(rootWin,'Everyone')", python_source)
        self.assertIn("usersGroup = 'Everyone'", flet_source)

    def test_a_widget_without_a_textvariable_still_sets_text(self):
        load("Calculator")
        button_name, button = widget_with_class("TButton")
        self.assertIsNotNone(button, "the calculator has buttons")
        self.assertEqual(text_variable(button), "", "this button has no variable")

        type_text_in_editor(button, button_name, "7")

        self.assertEqual(str(button.cget("text")), "7")

    def test_a_state_variable_is_not_used_for_the_caption(self):
        # A checkbutton's 'text' is its caption and its 'variable' holds the
        # state, so the caption must not be pushed into the variable.
        load("SimplePlace")
        checkbutton_name, checkbutton = widget_with_class("TCheckbutton")
        self.assertIsNotNone(checkbutton, "SimplePlace has a checkbutton")
        # A variable of our own, so its value can be read back regardless of the
        # name the project happened to store.
        checkbutton.setvar("test_state", "0")   # Tk creates it lazily otherwise
        checkbutton.configure(variable="test_state")
        before = str(checkbutton.getvar("test_state"))

        type_text_in_editor(checkbutton, checkbutton_name, "Agree")

        self.assertEqual(str(checkbutton.cget("text")), "Agree")
        self.assertEqual(
            str(checkbutton.getvar("test_state")),
            before,
            "the checkbutton's state variable must not receive the caption",
        )


if __name__ == "__main__":
    unittest.main()
