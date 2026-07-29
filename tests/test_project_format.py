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
            project_format.generated_python_dialog_defaults(
                "gridtest16",
                "/tmp/older",
                "/home/chris/previous-name.py",
                "/home/chris",
            ),
            ("/home/chris", "gridtest16.py"),
        )
        self.assertEqual(
            project_format.generated_python_dialog_defaults(
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


if __name__ == "__main__":
    unittest.main()
