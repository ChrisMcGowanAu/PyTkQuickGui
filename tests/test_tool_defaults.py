import json
import os
import tempfile
import unittest

import pytkguivars as my_vars
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

    def test_flet_policy_defaults_to_full_and_accepts_overrides(self):
        self.assertEqual(tool_defaults.flet_policy("ttk::label"), "full")
        self.assertEqual(tool_defaults.flet_policy("sizegrip"), "full")
        policies = tool_defaults.normalise_flet_policy({"treeview": "skip"})
        self.assertEqual(policies["treeview"], "skip")
        self.assertEqual(policies["default"], "full")
        self.assertEqual(tool_defaults.flet_policy("ttk::treeview", policies), "skip")

    def test_flet_policy_ignores_unknown_values(self):
        policies = tool_defaults.normalise_flet_policy(
            {"label": "explode", "button": "PLACEHOLDER"}
        )
        self.assertEqual(tool_defaults.flet_policy("label", policies), "full")
        self.assertEqual(tool_defaults.flet_policy("button", policies), "placeholder")

    def test_flet_grid_mode_is_validated(self):
        self.assertEqual(tool_defaults.normalise({})["fletGridMode"], "responsive")
        self.assertEqual(
            tool_defaults.normalise({"fletGridMode": "absolute"})["fletGridMode"],
            "absolute",
        )
        self.assertEqual(
            tool_defaults.normalise({"fletGridMode": "sideways"})["fletGridMode"],
            "responsive",
        )

    def test_flet_grid_mode_round_trips_through_save(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "tool_defaults.json")
            data = tool_defaults.normalise(
                {"fletGridMode": "absolute", "fletWidgetPolicy": {"canvas": "skip"}}
            )
            tool_defaults.write(path, data)
            reloaded = tool_defaults.read(path)
            self.assertEqual(reloaded["fletGridMode"], "absolute")
            self.assertEqual(
                tool_defaults.flet_policy("canvas", reloaded["fletWidgetPolicy"]),
                "skip",
            )

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


class FontSpecTests(unittest.TestCase):
    """checkFontDict() must not touch the dictionary it is given.

    It escaped the family in place, so the escaped name was saved as the tool
    default and escaped again on every later use - which is what left Tk unable
    to find the family and made every widget look wrong after a restart.
    """

    FONT = {
        "family": "Noto Sans",
        "size": 14,
        "weight": "normal",
        "slant": "roman",
        "underline": False,
        "overstrike": False,
    }

    def test_the_dictionary_is_left_alone(self):
        font = dict(self.FONT)
        spec = my_vars.checkFontDict(font)
        self.assertEqual(font["family"], "Noto Sans")
        self.assertEqual(spec, "Noto\\ Sans 14 normal roman")

    def test_an_unset_size_is_left_out(self):
        font = dict(self.FONT, size=0)
        self.assertEqual(my_vars.checkFontDict(font), "Noto\\ Sans normal roman")

    def test_a_negative_size_is_kept(self):
        font = dict(self.FONT, size=-13)
        self.assertEqual(my_vars.checkFontDict(font), "Noto\\ Sans -13 normal roman")


class StyleFontTests(unittest.TestCase):
    """The style font is a tool default, so it has to survive the round trip.

    It used to be applied live only, so it was gone after a restart, and no
    generated program ever saw it.
    """

    FONT = {
        "family": "DejaVu Sans",
        "size": 13,
        "weight": "bold",
        "slant": "roman",
        "underline": False,
        "overstrike": False,
    }

    def test_a_font_is_kept(self):
        self.assertEqual(tool_defaults.normalise_style_font(self.FONT), self.FONT)

    def test_a_font_without_a_family_is_dropped(self):
        self.assertEqual(tool_defaults.normalise_style_font({"size": 13}), {})
        self.assertEqual(tool_defaults.normalise_style_font(None), {})

    def test_an_escaped_family_is_healed(self):
        # a build that stored Tk's escaping must not keep the backslash
        healed = tool_defaults.normalise_style_font(
            {"family": "Noto\\ Sans", "size": 14}
        )
        self.assertEqual(healed["family"], "Noto Sans")

    def test_a_negative_size_is_kept(self):
        healed = tool_defaults.normalise_style_font(
            {"family": "Noto Sans", "size": -13}
        )
        self.assertEqual(healed["size"], -13)

    def test_it_survives_write_and_read(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = os.path.join(directory.name, "tool_defaults.json")

        tool_defaults.write(path, {"styleFont": self.FONT})
        restored = tool_defaults.normalise(tool_defaults.read(path))

        self.assertEqual(restored["styleFont"], self.FONT)


if __name__ == "__main__":
    unittest.main()
