import unittest

import layout_model


class GridGeometryTests(unittest.TestCase):
    def test_legacy_json_is_normalised(self):
        state = layout_model.GridGeometry.from_mapping(
            {
                "row": "3",
                "column": "4",
                "columnspan": "0",
                "rowspan": "-2",
                "sticky": "ew",
                "padx": "7",
                "pady": "",
            },
            parent="Widget1",
        )

        self.assertEqual(state.parent, "Widget1")
        self.assertEqual((state.row, state.column), (3, 4))
        self.assertEqual((state.columnspan, state.rowspan), (1, 1))
        self.assertEqual(state.sticky, "ew")
        self.assertEqual((state.padx, state.pady), (7, 2))

    def test_updated_state_keeps_unspecified_geometry(self):
        original = layout_model.GridGeometry(
            parent="rootWidget",
            row=2,
            column=3,
            columnspan=2,
            rowspan=4,
            sticky="nsew",
            ipadx=5,
        )

        moved = original.updated(parent="Widget9", row=7, column=8)

        self.assertEqual(moved.parent, "Widget9")
        self.assertEqual((moved.row, moved.column), (7, 8))
        self.assertEqual((moved.columnspan, moved.rowspan), (2, 4))
        self.assertEqual(moved.ipadx, 5)
        self.assertEqual(original.parent, "rootWidget")

    def test_json_shape_remains_backwards_compatible(self):
        state = layout_model.GridGeometry(parent="Widget2", row=1, column=2, rowspan=3)

        self.assertEqual(
            state.to_json(),
            {
                "row": "1",
                "column": "2",
                "columnspan": "1",
                "rowspan": "3",
                "sticky": "nsew",
                "padx": "2",
                "pady": "2",
                "ipadx": "0",
                "ipady": "0",
            },
        )

    def test_generated_grid_extents_cover_nested_spans_but_not_notebook_tabs(self):
        project = {
            "gridCols": 3,
            "gridRows": 2,
            "Widget0": {
                "WidgetName": "ttk::frame",
                "WidgetParent": "rootWidget",
                "GeomData": {"row": "1", "column": "2", "columnspan": "2"},
            },
            "Widget1": {
                "WidgetName": "ttk::button",
                "WidgetParent": "Widget0",
                "GeomData": {"row": "4", "column": "5", "rowspan": "2"},
            },
            "Widget2": {
                "WidgetName": "ttk::notebook",
                "WidgetParent": "rootWidget",
                "GeomData": {"row": "0", "column": "0"},
            },
            "Widget3": {
                "WidgetName": "ttk::frame",
                "WidgetParent": "Widget2",
                "GeomData": {"row": "99", "column": "99"},
            },
        }

        requirements = layout_model.grid_layout_requirements(
            project,
            ["rootWidget", "Widget0", "Widget1", "Widget2", "Widget3"],
            "rootWidget",
        )

        self.assertEqual(requirements["rootWidget"], (4, 2))
        self.assertEqual(requirements["Widget0"], (6, 6))
        self.assertNotIn("Widget2", requirements)
        self.assertEqual(requirements["Widget3"], (4, 4))
        self.assertTrue(
            layout_model.is_saved_notebook_tab(project, "Widget3", "rootWidget")
        )


if __name__ == "__main__":
    unittest.main()
