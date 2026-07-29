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

    def test_place_sizes_are_type_specific_and_detached(self):
        button = tool_defaults.place_size("ttk::button")
        text = tool_defaults.place_size("text")

        self.assertEqual(button, {"width": 100, "height": 32})
        self.assertEqual(text, {"width": 320, "height": 220})
        text["width"] = 1
        self.assertEqual(tool_defaults.place_size("text")["width"], 320)

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

    def test_discovered_files_are_layered_in_documented_order(self):
        with tempfile.TemporaryDirectory() as directory:
            system = os.path.join(directory, "etc")
            module = os.path.join(directory, "module")
            current = os.path.join(directory, "current")
            user = os.path.join(directory, "user", tool_defaults.FILE_NAME)
            paths = tool_defaults.search_paths(
                "pytkgui",
                current_directory=current,
                module_directory=module,
                user_path=user,
                system_directory=system,
            )
            for path, data in (
                (
                    paths[0],
                    {
                        "gridRows": 10,
                        "gridWidgetDefaults": {"label": {"columnspan": 3}},
                    },
                ),
                (
                    paths[1],
                    {
                        "gridCols": 11,
                        "placeWidgetDefaults": {"button": {"width": 150}},
                    },
                ),
                (
                    paths[2],
                    {
                        "gridRows": 12,
                        "gridWidgetDefaults": {"label": {"rowspan": 2}},
                    },
                ),
                (
                    paths[3],
                    {
                        "gridRows": 14,
                        "placeWidgetDefaults": {"button": {"height": 44}},
                    },
                ),
            ):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(data, handle)

            loaded, loaded_paths = tool_defaults.read_discovered(
                "pytkgui",
                current_directory=current,
                module_directory=module,
                user_path=user,
                system_directory=system,
            )

        self.assertEqual(loaded_paths, paths)
        self.assertEqual((loaded["gridRows"], loaded["gridCols"]), (14, 11))
        self.assertEqual(loaded["gridWidgetDefaults"]["label"]["columnspan"], 3)
        self.assertEqual(loaded["gridWidgetDefaults"]["label"]["rowspan"], 2)
        self.assertEqual(loaded["placeWidgetDefaults"]["button"]["width"], 150)
        self.assertEqual(loaded["placeWidgetDefaults"]["button"]["height"], 44)

    def test_place_update_preserves_other_manual_defaults(self):
        supplied = {
            "gridRowMinsize": "4m",
            "placeWidgetDefaults": {
                "label": {"width": 222, "height": 41},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, tool_defaults.FILE_NAME)
            tool_defaults.write(path, supplied)
            tool_defaults.update_place_widget_layout(
                path,
                "ttk::button",
                {"width": 180, "height": 48},
            )
            loaded = tool_defaults.read(path)

        self.assertEqual(loaded["gridRowMinsize"], "4m")
        self.assertEqual(
            loaded["placeWidgetDefaults"]["label"],
            {"width": 222, "height": 41},
        )
        self.assertEqual(
            loaded["placeWidgetDefaults"]["button"],
            {"width": 180, "height": 48},
        )


if __name__ == "__main__":
    unittest.main()
