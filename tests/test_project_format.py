import json
import tempfile
import unittest
from pathlib import Path

import project_format


def widget_data(attributes):
    data = {
        "WidgetName": "ttk::button",
        "WidgetParent": "rootWidget",
        "Widget0-KeyCount": len(attributes),
    }
    for index, (key, value) in enumerate(attributes):
        data[f"Attribute{index}"] = {"Key": key, "Value": value}
    return data


class FakeWidget:
    pass


class ProjectFormatTests(unittest.TestCase):
    def test_generated_calls_are_readable_multiline_python(self):
        formatted = project_format.format_python_call(
            "Widget1 = ttk.Frame",
            (
                "rootWidget",
                "width='0'",
                "style='primary.TFrame'",
            ),
        )

        self.assertEqual(
            formatted,
            "Widget1 = ttk.Frame(\n"
            "    rootWidget,\n"
            "    width='0',\n"
            "    style='primary.TFrame',\n"
            ")",
        )

    def test_generated_filename_uses_project_name_and_last_directory(self):
        self.assertEqual(
            project_format.generated_dialog_defaults(
                "gridtest16",
                "/tmp/older",
                "/home/chris/previous-name.py",
                "/home/chris",
            ),
            ("/home/chris", "gridtest16.py"),
        )
        self.assertEqual(
            project_format.generated_dialog_defaults(
                "new-project",
                "/common/python",
                "",
                "/home/chris",
            ),
            ("/common/python", "new-project.py"),
        )

    def test_callbacks_and_variables_survive_attribute_round_trip(self):
        data = widget_data(
            [
                ("text", "Run"),
                ("command", "run_report"),
                ("textvariable", "button_text"),
            ]
        )
        project = {"Widget0": data}

        self.assertEqual(
            project_format.callback_names(
                project, ["rootWidget", "Widget0"], "rootWidget"
            ),
            ["run_report"],
        )
        self.assertEqual(
            project_format.variable_names(
                project, ["rootWidget", "Widget0"], "rootWidget"
            ),
            ["button_text"],
        )

        rebuilt = FakeWidget()
        project_format.remember_preserved_attributes(rebuilt, "Widget0", data)
        self.assertEqual(rebuilt._user_attrs["command"], "run_report")
        self.assertEqual(rebuilt._user_attrs["textvariable"], "button_text")

    def test_mangled_or_invalid_callback_is_not_emitted_as_python(self):
        project = {
            "Widget0": widget_data(
                [
                    ("command", "140234567890callback"),
                    ("postcommand", "valid_postcommand"),
                ]
            )
        }

        self.assertEqual(
            project_format.callback_names(project, ["Widget0"], "rootWidget"),
            ["valid_postcommand"],
        )

    def test_explicit_raw_value_wins_over_tk_fallback(self):
        widget = FakeWidget()
        widget._user_attrs = {"command": "human_readable_name"}

        self.assertEqual(
            project_format.preserved_widget_value(
                widget, "command", "140234567890callback"
            ),
            "human_readable_name",
        )

    def test_duplicate_names_are_emitted_once_in_creation_order(self):
        project = {
            "Widget0": widget_data([("command", "shared_handler")]),
            "Widget1": {
                **widget_data([("command", "shared_handler")]),
                "Widget1-KeyCount": 1,
            },
        }

        self.assertEqual(
            project_format.callback_names(
                project, ["Widget0", "Widget1"], "rootWidget"
            ),
            ["shared_handler"],
        )

    def test_atomic_json_writer_keeps_five_previous_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            project_name = str(Path(directory) / "Demo")
            for version in range(7):
                result = project_format.write_project_json(
                    project_name,
                    ".json",
                    {
                        "version": version,
                        "Widget0": widget_data([("command", "run_report")]),
                    },
                )
                self.assertEqual(result, project_name + ".json")

            with open(result, encoding="utf-8") as handle:
                rebuilt = json.load(handle)
            self.assertEqual(rebuilt["version"], 6)
            self.assertEqual(
                project_format.callback_names(
                    rebuilt, ["rootWidget", "Widget0"], "rootWidget"
                ),
                ["run_report"],
            )
            for backup_index, expected_version in enumerate(range(5, 0, -1), start=1):
                with open(
                    f"{project_name}-save{backup_index}.json", encoding="utf-8"
                ) as handle:
                    self.assertEqual(json.load(handle)["version"], expected_version)
            self.assertFalse(Path(f"{project_name}-save6.json").exists())
            self.assertFalse(Path(result + ".tmp").exists())
            self.assertFalse(Path(result + ".backup-tmp").exists())

    def test_variable_defaults_reads_the_designer_value(self):
        project = {
            "Widget1": {
                "WidgetName": "ttk::entry",
                "WidgetParent": "rootWidget",
                "Widget1-KeyCount": 2,
                "Attribute0": {"Key": "textvariable", "Value": "calcvar"},
                "Attribute1": {"Key": "var_value", "Value": "123"},
            },
            "Widget2": {
                "WidgetName": "ttk::checkbutton",
                "WidgetParent": "rootWidget",
                "Widget2-KeyCount": 2,
                "Attribute0": {"Key": "variable", "Value": "flag"},
                "Attribute1": {"Key": "var_value", "Value": "1"},
            },
            "Widget3": {
                "WidgetName": "ttk::entry",
                "WidgetParent": "rootWidget",
                "Widget3-KeyCount": 1,
                "Attribute0": {"Key": "textvariable", "Value": "empty"},
            },
        }

        defaults = project_format.variable_defaults(
            project, ["rootWidget", "Widget1", "Widget2", "Widget3"]
        )

        self.assertEqual(defaults, {"calcvar": "123", "flag": "1"})

    def test_variable_defaults_ignores_names_that_are_not_identifiers(self):
        project = {
            "Widget1": {
                "WidgetName": "ttk::entry",
                "WidgetParent": "rootWidget",
                "Widget1-KeyCount": 2,
                "Attribute0": {"Key": "textvariable", "Value": "PY_VAR0 "},
                "Attribute1": {"Key": "var_value", "Value": "1"},
            },
        }

        defaults = project_format.variable_defaults(
            project, ["rootWidget", "Widget1"]
        )

        self.assertEqual(defaults, {})

    def test_generated_filename_names_the_backend_and_defaults_to_a_folder(self):
        # A brand new project: <home>/<project>/<project>_<backend>.py
        self.assertEqual(
            project_format.generated_dialog_defaults(
                "Calculator", "", "", "/home/chris", suffix="flet"
            ),
            ("/home/chris/Calculator", "Calculator_flet.py"),
        )
        self.assertEqual(
            project_format.generated_dialog_defaults(
                "Calculator", "", "", "/home/chris", suffix="ttk"
            ),
            ("/home/chris/Calculator", "Calculator_ttk.py"),
        )
        # Once saved, its own directory is offered again.
        self.assertEqual(
            project_format.generated_dialog_defaults(
                "Calculator",
                "",
                "/home/chris/Calculator/Calculator_flet.py",
                "/home/chris",
                suffix="flet",
            ),
            ("/home/chris/Calculator", "Calculator_flet.py"),
        )

    def test_widget_type_whitelist_matches_the_palette(self):
        """Every type the designer can create has to be accepted."""
        import pytkguivars as my_vars

        for name in my_vars.widgetsUsed + my_vars.containerWidgetsUsed:
            for spelling in (name, "ttk::" + name.lower(), "ttk." + name):
                with self.subTest(widget=spelling):
                    self.assertTrue(project_format.is_known_widget_type(spelling))
        for extra in ("ttk::notebook", "ttk::scrollbar", "ttk::treeview", "text"):
            self.assertTrue(project_format.is_known_widget_type(extra))

    def test_widget_type_whitelist_refuses_anything_else(self):
        """A project file is data: an unknown type must never be run as code."""
        for bad in (
            "__import__('os').system",
            "os.system",
            "eval",
            "",
            None,
            "ttk::evil",
        ):
            with self.subTest(widget=bad):
                self.assertFalse(project_format.is_known_widget_type(bad))

    def test_option_name_check_stops_a_crafted_key(self):
        """The widget call is built by string and eval'd, so keys are checked."""
        for good in ("text", "background", "command", "onvalue", "from"):
            self.assertTrue(project_format.is_safe_option_key(good))
        for bad in (
            "a=1) or __import__('os').system('x') or dict(",
            "text=",
            "text value",
            "'quoted'",
            "",
            None,
        ):
            with self.subTest(key=bad):
                self.assertFalse(project_format.is_safe_option_key(bad))

    def test_the_marker_decides_who_owns_a_line(self):
        """One rule for both backends: no marker means the user wrote it."""
        source = (
            "calcvar = '0.0'   # AUTO-GENERATED default\n"
            "flag = '1'\n"
            "\n"
            "def clicked_4(e=None):\n"
            "    global calcvar\n"
            "    calcvar = '4'\n"
            "\n"
            "def clicked_5(e=None):\n"
            "    # AUTO-GENERATED STUB\n"
            "    print('clicked_5')\n"
        )

        functions, variables = project_format.preserved_pieces(
            source, ["clicked_4", "clicked_5"], ["calcvar", "flag"]
        )

        # The hand written handler is kept, the untouched stub is regenerated.
        self.assertEqual(list(functions), ["clicked_4"])
        # 'calcvar' carries the marker, so its value is refreshed from the
        # designer; 'flag' does not, so it is the user's.
        self.assertEqual(variables, {"flag": "flag = '1'"})

    def test_a_user_edited_variable_is_kept(self):
        source = "calcvar = '99'   # my own default\n"

        _functions, variables = project_format.preserved_pieces(
            source, [], ["calcvar"]
        )

        self.assertEqual(
            variables, {"calcvar": "calcvar = '99'   # my own default"}
        )

    def test_preserved_pieces_ignores_an_unparsable_file(self):
        functions, variables = project_format.preserved_pieces(
            "this is not python(", ["clicked_4"], ["calcvar"]
        )

        self.assertEqual(functions, {})
        self.assertEqual(variables, {})


if __name__ == "__main__":
    unittest.main()
