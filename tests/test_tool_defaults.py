import json
import os
import tempfile
import unittest

import tool_defaults


class ToolDefaultsTests(unittest.TestCase):
    def test_widget_layouts_have_useful_type_specific_spans(self):
        label = tool_defaults.widget_layout("ttk::label")
        text = tool_defaults.widget_layout("text")
        frame = tool_defaults.widget_layout("ttk::frame")

        self.assertEqual((label["columnspan"], label["rowspan"]), (2, 1))
        self.assertEqual((text["columnspan"], text["rowspan"]), (5, 5))
        self.assertEqual((frame["columnspan"], frame["rowspan"]), (5, 5))
        label["columnspan"] = 99
        self.assertEqual(
            tool_defaults.widget_layout("ttk::label")["columnspan"],
            2,
        )

    def test_saved_values_are_normalised_and_round_trip(self):
        supplied = {
            "gridRows": 1,
            "gridCols": 150,
            "gridRowMinsize": "3m",
            "gridWidgetDefaults": {
                "Label": {"columnspan": "4", "rowspan": 0, "sticky": "ew"}
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, tool_defaults.FILE_NAME)
            tool_defaults.write(path, supplied)
            loaded = tool_defaults.read(path)
            with open(path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)

        self.assertEqual((loaded["gridRows"], loaded["gridCols"]), (2, 100))
        self.assertEqual(loaded["gridRowMinsize"], "3m")
        self.assertEqual(loaded["gridWidgetDefaults"]["label"]["columnspan"], 4)
        self.assertEqual(loaded["gridWidgetDefaults"]["label"]["rowspan"], 1)
        self.assertEqual(loaded["gridWidgetDefaults"]["label"]["sticky"], "ew")
        self.assertEqual(raw["formatVersion"], tool_defaults.FORMAT_VERSION)

    def test_widget_update_preserves_manually_edited_grid_defaults(self):
        supplied = {
            "gridRows": 12,
            "gridCols": 14,
            "gridRowMinsize": "4m",
            "gridColMinsize": "8m",
            "gridRowPad": "1m",
            "gridColPad": "2m",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, tool_defaults.FILE_NAME)
            tool_defaults.write(path, supplied)
            tool_defaults.update_widget_layout(
                path,
                "ttk::label",
                {
                    "columnspan": 4,
                    "rowspan": 2,
                    "padx": 3,
                    "pady": 3,
                    "ipadx": 0,
                    "ipady": 0,
                    "sticky": "ew",
                },
            )
            loaded = tool_defaults.read(path)

        self.assertEqual(loaded["gridRowMinsize"], "4m")
        self.assertEqual(loaded["gridColMinsize"], "8m")
        self.assertEqual(loaded["gridRowPad"], "1m")
        self.assertEqual(loaded["gridColPad"], "2m")
        self.assertEqual(loaded["gridWidgetDefaults"]["label"]["columnspan"], 4)
        self.assertEqual(loaded["gridWidgetDefaults"]["label"]["rowspan"], 2)


if __name__ == "__main__":
    unittest.main()
