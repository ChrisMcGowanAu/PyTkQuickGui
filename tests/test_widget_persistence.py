import unittest
import tkinter as tk

import createWidget as cw
import project_format
import pytkguivars as my_vars
from layout_model import GridGeometry


class FakeWidget:
    widgetName = "ttk::button"

    def __init__(self):
        self._user_attrs = {
            "command": "run_report",
            "textvariable": "button_text",
        }
        self.values = {
            "text": "Run",
            "command": "140234567890callback",
            "textvariable": "PY_VAR0",
            "yscrollcommand": "140234567890set",
        }

    def place_info(self):
        return {}

    def grid_info(self):
        return {}

    def keys(self):
        return list(self.values)

    def __getitem__(self, key):
        return self.values[key]


class FakeContainer(FakeWidget):
    widgetName = "ttk::frame"

    def grid_size(self):
        return 7, 6


class StaleWidget(FakeWidget):
    def place_info(self):
        raise tk.TclError("bad window path name")

    def keys(self):
        raise tk.TclError("invalid command name")


class FakeCreateWidget:
    def __init__(self, widget):
        self.pythonName = "Widget0"
        self.widget = widget

    def capture_grid_geometry(self):
        return GridGeometry(
            parent="Widget9",
            row=3,
            column=4,
            columnspan=2,
            sticky="ew",
        )


class WidgetPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.old_names = cw.createWidget.widgetNameList
        self.old_objects = cw.createWidget.widgetObjectList
        self.old_manager = my_vars.geomManager
        self.old_root_name = getattr(my_vars, "rootWidgetName", None)

        self.widget = FakeWidget()
        self.cwo = FakeCreateWidget(self.widget)
        cw.createWidget.widgetNameList = [
            ["Widget0", "Widget9", self.widget, []],
        ]
        cw.createWidget.widgetObjectList = [self.cwo]
        my_vars.geomManager = "Grid"
        my_vars.rootWidgetName = "rootWidget"

    def tearDown(self):
        cw.createWidget.widgetNameList = self.old_names
        cw.createWidget.widgetObjectList = self.old_objects
        my_vars.geomManager = self.old_manager
        if self.old_root_name is not None:
            my_vars.rootWidgetName = self.old_root_name

    def test_save_uses_authoritative_grid_and_raw_command_values(self):
        saved = my_vars.saveWidgetAsDict("Widget0")["Widget0"]
        attributes = project_format.attribute_map("Widget0", saved)

        self.assertEqual(attributes["command"], "run_report")
        self.assertEqual(attributes["textvariable"], "button_text")
        self.assertNotIn("yscrollcommand", attributes)
        widget_definition = my_vars.buildAWidget(0, saved)
        self.assertIn("command='run_report'", widget_definition)
        self.assertIn("textvariable='button_text'", widget_definition)
        self.assertEqual(
            saved["GeomData"],
            {
                "row": "3",
                "column": "4",
                "columnspan": "2",
                "rowspan": "1",
                "sticky": "ew",
                "padx": "2",
                "pady": "2",
                "ipadx": "0",
                "ipady": "0",
            },
        )

    def test_rebuilt_widget_can_be_saved_again_without_losing_command(self):
        first_save = my_vars.saveWidgetAsDict("Widget0")["Widget0"]
        rebuilt = FakeWidget()
        rebuilt._user_attrs = {}
        project_format.remember_preserved_attributes(rebuilt, "Widget0", first_save)
        rebuilt_cwo = FakeCreateWidget(rebuilt)
        cw.createWidget.widgetNameList = [["Widget0", "Widget9", rebuilt, []]]
        cw.createWidget.widgetObjectList = [rebuilt_cwo]

        second_save = my_vars.saveWidgetAsDict("Widget0")["Widget0"]
        attributes = project_format.attribute_map("Widget0", second_save)

        self.assertEqual(attributes["command"], "run_report")
        self.assertEqual(attributes["textvariable"], "button_text")

    def test_container_internal_grid_dimensions_are_saved(self):
        self.widget = FakeContainer()
        self.cwo = FakeCreateWidget(self.widget)
        cw.createWidget.widgetNameList = [
            ["Widget0", "rootWidget", self.widget, []],
        ]
        cw.createWidget.widgetObjectList = [self.cwo]

        saved = my_vars.saveWidgetAsDict("Widget0")["Widget0"]

        self.assertEqual(
            saved["ContainerGrid"],
            {"columns": "7", "rows": "6"},
        )

    def test_plain_live_callback_is_migrated_to_explicit_metadata(self):
        self.widget._user_attrs = {}
        self.widget.values["command"] = "run_report"

        saved = my_vars.saveWidgetAsDict("Widget0")["Widget0"]
        attributes = project_format.attribute_map("Widget0", saved)

        self.assertEqual(attributes["command"], "run_report")
        self.assertEqual(self.widget._user_attrs["command"], "run_report")

    def test_stale_widget_save_still_records_zero_attribute_count(self):
        self.widget = StaleWidget()
        self.cwo = FakeCreateWidget(self.widget)
        cw.createWidget.widgetNameList = [
            ["Widget0", "rootWidget", self.widget, []],
        ]
        cw.createWidget.widgetObjectList = [self.cwo]

        saved = my_vars.saveWidgetAsDict("Widget0")["Widget0"]

        self.assertEqual(saved["Widget0-KeyCount"], 0)
        self.assertEqual(list(project_format.iter_attributes("Widget0", saved)), [])

    def test_invalid_attribute_count_does_not_crash_widget_rebuild(self):
        malformed = {
            "WidgetName": "ttk::button",
            "WidgetParent": "rootWidget",
            "Widget0-KeyCount": None,
        }

        self.assertEqual(
            my_vars.buildAWidget(0, malformed),
            "ttk.Button(mainFrame)",
        )

    def test_saved_identity_gaps_never_reuse_an_existing_name(self):
        old_counter = cw.createWidget.widgetId
        old_names = cw.createWidget.widgetNameList
        try:
            cw.createWidget.widgetId = 0
            cw.createWidget.widgetNameList = []

            self.assertEqual(
                cw.createWidget._allocate_identity("Widget10"), (10, "Widget10")
            )
            cw.createWidget.widgetNameList.append(["Widget10", "rootWidget", None, []])
            self.assertEqual(
                cw.createWidget._allocate_identity("Widget12"), (12, "Widget12")
            )
            cw.createWidget.widgetNameList.append(["Widget12", "rootWidget", None, []])
            self.assertEqual(
                cw.createWidget._allocate_identity("Widget13"), (13, "Widget13")
            )
            self.assertEqual(cw.createWidget.widgetId, 14)
        finally:
            cw.createWidget.widgetId = old_counter
            cw.createWidget.widgetNameList = old_names


if __name__ == "__main__":
    unittest.main()
