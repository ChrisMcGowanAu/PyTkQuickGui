import ast
import contextlib
import io
import os
import re
import tempfile
import unittest

try:
    import flet as ft

    FLET_AVAILABLE = True
except ImportError:  # pragma: no cover - flet is an optional dependency
    ft = None
    FLET_AVAILABLE = False

import flet_generator


def widget(
    name,
    widget_type,
    parent="rootWidget",
    attributes=(),
    place=None,
    geom=None,
    container_grid=None,
):
    data = {
        "WidgetName": widget_type,
        "WidgetParent": parent,
        "Place": dict(place or {}),
        "GeomData": dict(geom or {}),
    }
    if container_grid:
        data["ContainerGrid"] = container_grid
    for index, (key, value) in enumerate(attributes):
        data[f"Attribute{index}"] = {"Key": key, "Value": value}
    data[f"{name}-KeyCount"] = len(attributes)
    return {name: data}


def project(geom_manager="Place", widgets=(), **extra):
    data = {
        "ProjectName": "test",
        "geomManager": geom_manager,
        "theme": "default",
        "backgroundColor": "skyBlue3",
        "widgetCount": len(widgets),
    }
    for widget_data in widgets:
        data.update(widget_data)
    data.update(extra)
    return data


def widget_names(*names):
    return ["rootWidget", *names]


ROOT = "rootWidget"


class FakeWindow:
    width = None
    height = None
    resizable = None


class FakePage:
    def __init__(self):
        self.title = None
        self.padding = None
        self.bgcolor = None
        self.window = FakeWindow()
        self.controls = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        pass


def load_generated(source):
    """Execute *source* with ``ft.run`` stubbed; return ``(namespace, main)``."""
    namespace = {}
    captured = {}
    original_run = ft.run
    ft.run = lambda main, *args, **kwargs: captured.setdefault("main", main)
    try:
        # The generated program is data produced by this tool, not user input.
        # Its Flet version guard writes to stderr; keep test output readable.
        with contextlib.redirect_stderr(io.StringIO()):
            exec(  # pylint: disable=exec-used
                compile(source, "<generated flet>", "exec"), namespace
            )
    finally:
        ft.run = original_run
    return namespace, captured.get("main")


def run_generated(source):
    """Execute *source* with ``ft.run`` stubbed and return the built page."""
    _namespace, main = load_generated(source)
    page = FakePage()
    main(page)
    return page


class FletGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generated_program_is_valid_python(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "Hello"), ("takefocus", "ttk::takefocus")),
                    place={"x": "16", "y": "24", "width": "120", "height": "32"},
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        ast.parse(source)
        self.assertIn("import flet as ft", source)
        self.assertIn("Widget1 = ft.Text(", source)
        self.assertIn("page.add(rootWidget)", source)

    def test_place_layout_keeps_designer_coordinates(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "Run"),),
                    place={"x": "48", "y": "16", "width": "80", "height": "32"},
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        self.assertIn("left=48", source)
        self.assertIn("top=16", source)
        self.assertIn("width=80", source)
        self.assertIn("height=32", source)
        self.assertIn("rootWidget = ft.Stack(", source)

    def test_relative_place_sizes_stretch_to_their_parent(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    place={
                        "x": "0",
                        "y": "0",
                        "width": "",
                        "height": "",
                        "relwidth": "1",
                        "relheight": "1",
                    },
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        self.assertIn("right=0", source)
        self.assertIn("bottom=0", source)
        self.assertNotIn("width=", source.split("Widget1")[1])

    def test_grid_layout_builds_rows_and_columns(self):
        data = project(
            geom_manager="Grid",
            gridRows=6,
            gridCols=6,
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    geom={"row": "0", "column": "0", "columnspan": "2", "padx": "3"},
                ),
                widget(
                    "Widget2",
                    "ttk::entry",
                    geom={"row": "1", "column": "1", "columnspan": "1"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget1", "Widget2"), ROOT
        )

        ast.parse(source)
        self.assertIn("rootWidget = ft.Column(", source)
        self.assertIn("ft.Row(", source)
        self.assertIn("content=Widget1", source)
        self.assertIn("expand=2", source)
        self.assertIn("padding=3", source)

    def test_pack_layout_groups_widgets_by_side(self):
        data = project(
            geom_manager="Pack",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "top"),),
                    geom={"side": "top", "expand": "1"},
                ),
                widget(
                    "Widget2",
                    "ttk::label",
                    attributes=(("text", "left"),),
                    geom={"side": "left"},
                ),
                widget(
                    "Widget3",
                    "ttk::label",
                    attributes=(("text", "right"),),
                    geom={"side": "right"},
                ),
                widget(
                    "Widget4",
                    "ttk::label",
                    attributes=(("text", "bottom"),),
                    geom={"side": "bottom"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget1", "Widget2", "Widget3", "Widget4"), ROOT
        )

        ast.parse(source)
        self.assertIn("expand=True", source)
        self.assertIn("ft.Column(", source)
        self.assertIn("ft.Row(", source)
        self.assertLess(source.index("Widget2"), source.index("Widget3"))

    def test_notebook_frames_become_tabs(self):
        data = project(
            widgets=(
                widget("Widget4", "ttk::notebook", place={"x": "0", "y": "0"}),
                widget("Widget6", "ttk::frame", parent="Widget4"),
                widget("Widget7", "ttk::frame", parent="Widget4"),
                widget(
                    "Widget9",
                    "ttk::label",
                    parent="Widget6",
                    attributes=(("text", "T1"),),
                ),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget4", "Widget6", "Widget7", "Widget9"), ROOT
        )

        ast.parse(source)
        self.assertIn("ft.Tabs(", source)
        self.assertIn("length=2", source)
        self.assertIn("ft.TabBar(", source)
        self.assertIn("ft.TabBarView(", source)
        # ttk's default: every tab is called "Tab" (the Python backend too).
        self.assertIn("ft.Tab(label='Tab')", source)
        self.assertNotIn("Tab 1", source)

    def test_tk_colours_are_translated_or_dropped(self):
        self.assertEqual(flet_generator.tk_color("skyBlue3"), "#6ca6cd")
        self.assertEqual(flet_generator.tk_color("#ABCDEF"), "#abcdef")
        self.assertIsNone(flet_generator.tk_color("no-such-colour"))
        self.assertIsNone(flet_generator.tk_color(""))

    def test_unmapped_options_are_reported(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "B"), ("takefocus", "ttk::takefocus")),
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        self.assertIn("Translation notes", source)
        self.assertIn("takefocus", source)

    def test_only_valid_names_are_emitted_as_callbacks_and_variables(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "B"), ("command", "run_report")),
                ),
                widget(
                    "Widget2",
                    "ttk::entry",
                    attributes=(("textvariable", "entry_text"),),
                ),
                widget(
                    "Widget3",
                    "ttk::label",
                    attributes=(
                        ("text", "L"),
                        ("command", "132659090261440yview"),
                        ("textvariable", "PY_VAR2"),
                    ),
                ),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget1", "Widget2", "Widget3"), ROOT
        )

        ast.parse(source)
        self.assertIn("def run_report(e=None):", source)
        self.assertIn("entry_text = '0.0'", source)
        self.assertIn("on_click=run_report", source)
        self.assertIn("value=entry_text", source)
        self.assertNotIn("132659090261440yview", source)

    def test_combobox_values_become_dropdown_options(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::combobox",
                    attributes=(("values", "(one two three)"),),
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        ast.parse(source)
        self.assertIn("ft.DropdownOption(key='one', text='one')", source)
        self.assertIn("ft.DropdownOption(key='three', text='three')", source)

    def test_containers_hold_their_children(self):
        data = project(
            widgets=(
                widget(
                    "Widget0",
                    "ttk::labelframe",
                    attributes=(("text", "Options"),),
                    place={"x": "8", "y": "8", "width": "160", "height": "96"},
                ),
                widget(
                    "Widget1",
                    "ttk::checkbutton",
                    parent="Widget0",
                    attributes=(("text", "On"),),
                    place={"x": "8", "y": "24", "width": "80", "height": "24"},
                ),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget0", "Widget1"), ROOT
        )

        ast.parse(source)
        self.assertIn("ft.Text(value='Options')", source)
        self.assertIn("ft.Stack(", source)
        self.assertIn("controls=[Widget1]", source)
        self.assertIn("Widget1 = ft.Checkbox(", source)

    def test_window_size_follows_placed_widgets(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    place={"x": "100", "y": "50", "width": "60", "height": "30"},
                ),
            )
        )

        self.assertEqual(
            flet_generator.window_size(data, widget_names("Widget1"), ROOT), (180, 100)
        )

    def test_every_palette_widget_type_has_a_control(self):
        palette = [
            "Label",
            "Button",
            "Entry",
            "Combobox",
            "Spinbox",
            "Checkbutton",
            "Radiobutton",
            "Scale",
            "Progressbar",
            "Canvas",
            "Text",
            "Listbox",
            "Separator",
            "Notebook",
        ] + ["Frame", "Labelframe", "Panedwindow"]

        for name in palette:
            with self.subTest(widget=name):
                control = flet_generator.widget_control("ttk::" + name.lower())
                self.assertTrue(control.startswith("ft."), name)

    def test_canvas_keeps_its_children_and_background(self):
        data = project(
            widgets=(
                widget(
                    "Widget0",
                    "ttk::canvas",
                    attributes=(("background", "skyBlue3"),),
                    place={"x": "8", "y": "8", "width": "200", "height": "120"},
                ),
                widget(
                    "Widget1",
                    "ttk::label",
                    parent="Widget0",
                    attributes=(("text", "inside"),),
                    place={"x": "4", "y": "4", "width": "80", "height": "24"},
                ),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget0", "Widget1"), ROOT
        )

        ast.parse(source)
        self.assertIn("bgcolor='#6ca6cd'", source)
        self.assertIn("ft.Stack(", source)
        self.assertIn("controls=[Widget1]", source)
        self.assertNotIn("placeholder", source)

    def test_treeview_uses_the_saved_column_headings(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::treeview",
                    attributes=(("columns", "name size"),),
                    place={"x": "0", "y": "0", "width": "240", "height": "160"},
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        ast.parse(source)
        self.assertIn("Widget1 = ft.DataTable(", source)
        self.assertIn("ft.DataColumn(label=ft.Text('name'))", source)
        self.assertIn("ft.DataColumn(label=ft.Text('size'))", source)
        self.assertIn("rows=[]", source)

    def test_treeview_without_columns_is_a_placeholder(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::treeview",
                    place={"x": "0", "y": "0", "width": "240", "height": "160"},
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        self.assertIn("Widget1 = ft.Container(", source)
        self.assertIn("no columns", source)

    def test_scrollbar_next_to_a_listbox_becomes_scroll_on_it(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "listbox",
                    place={"x": "0", "y": "0", "width": "200", "height": "160"},
                ),
                widget(
                    "Widget2",
                    "ttk::scrollbar",
                    attributes=(("orient", "vertical"),),
                    place={"x": "200", "y": "0", "width": "20", "height": "160"},
                ),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget1", "Widget2"), ROOT
        )

        ast.parse(source)
        # The list sits in a Container so the listbox paints its background,
        # and the scroll belongs on the list rather than the Container.
        self.assertIn("Widget1 = ft.Container(", source)
        self.assertIn("content=ft.ListView(", source)
        self.assertIn("scroll=ft.Scrollbar(thickness=20)", source)
        self.assertNotIn("Widget2 =", source)
        self.assertIn("attached to Widget1", source)

    def test_scrollbar_inside_a_canvas_wraps_it(self):
        data = project(
            widgets=(
                widget(
                    "Widget0",
                    "ttk::canvas",
                    place={"x": "10", "y": "10", "width": "200", "height": "160"},
                ),
                widget(
                    "Widget1",
                    "ttk::label",
                    parent="Widget0",
                    attributes=(("text", "inside"),),
                    place={"x": "4", "y": "4", "width": "80", "height": "24"},
                ),
                widget(
                    "Widget2",
                    "ttk::scrollbar",
                    parent="Widget0",
                    attributes=(("orient", "vertical"),),
                    place={
                        "x": "180",
                        "y": "0",
                        "width": "20",
                        "height": "",
                        "relheight": "1",
                    },
                ),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget0", "Widget1", "Widget2"), ROOT
        )

        ast.parse(source)
        self.assertIn("Widget0 = ft.Column(", source)
        self.assertIn("scroll=ft.Scrollbar(thickness=20)", source)
        self.assertIn("wraps Widget0", source)
        self.assertNotIn("Widget2 =", source)

    def test_scrollbar_without_a_target_is_dropped_for_text(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "text",
                    place={"x": "0", "y": "0", "width": "200", "height": "160"},
                ),
                widget(
                    "Widget2",
                    "ttk::scrollbar",
                    parent="Widget1",
                    attributes=(("orient", "vertical"),),
                    place={"x": "184", "y": "0", "width": "16", "height": "160"},
                ),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names("Widget1", "Widget2"), ROOT
        )

        self.assertIn("scrolls on its own - scrollbar dropped", source)
        self.assertNotIn("Widget2 =", source)

    def test_spinbox_becomes_a_stepper_with_bounds(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::spinbox",
                    attributes=(
                        ("from", "0"),
                        ("to", "10"),
                        ("increment", "0.5"),
                        ("textvariable", "count"),
                    ),
                    place={"x": "8", "y": "8", "width": "140", "height": "32"},
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        ast.parse(source)
        self.assertIn("Widget1_field = ft.TextField(", source)
        self.assertIn("keyboard_type=ft.KeyboardType.NUMBER", source)
        self.assertIn("Widget1 = ft.Row(", source)
        self.assertIn("ft.Icons.KEYBOARD_ARROW_UP", source)
        self.assertIn("_step_value(Widget1_field, 1, 0.0, 10.0, 0.5)", source)
        self.assertIn("def _step_value(", source)
        self.assertIn("not kept in sync", source)

    def test_generated_stepper_helper_clamps_the_value(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::spinbox",
                    attributes=(("from", "0"), ("to", "10"), ("increment", "0.5")),
                    place={"x": "0", "y": "0", "width": "140", "height": "32"},
                ),
            )
        )
        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)
        namespace, _main = load_generated(source)

        class FakeField:
            value = ""

            def update(self):
                pass

        field = FakeField()
        step = namespace["_step_value"]
        step(field, 1, 0.0, 10.0, 0.5)
        self.assertEqual(field.value, "0.5")
        for _ in range(40):
            step(field, 1, 0.0, 10.0, 0.5)
        self.assertEqual(field.value, "10")
        field.value = "not a number"
        step(field, 1, 2.0, 10.0, 1.0)
        self.assertEqual(field.value, "3")

    def test_grid_absolute_mode_sizes_cells_to_the_widgets(self):
        """Cells follow the widgets; minsize is only a floor, as in Tk."""
        data = project(
            geom_manager="Grid",
            gridRows=4,
            gridCols=4,
            gridColMinsize="10",
            gridRowMinsize="10",
            gridColPad="0",
            gridRowPad="0",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    geom={"row": "0", "column": "0", "padx": "0", "pady": "0"},
                ),
                widget(
                    "Widget2",
                    "ttk::label",
                    attributes=(("text", "M"),),
                    geom={"row": "1", "column": "1", "padx": "0", "pady": "0"},
                ),
                widget(
                    "Widget3",
                    "ttk::label",
                    attributes=(("text", "N"),),
                    geom={
                        "row": "2",
                        "column": "0",
                        "rowspan": "2",
                        "padx": "0",
                        "pady": "0",
                    },
                ),
            ),
        )
        # Measured sizes are used when they exceed the tool default, which is
        # the floor for a widget type (a label defaults to 120x32).
        natural = {"Widget1": (200, 60), "Widget2": (120, 32), "Widget3": (10, 10)}

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1", "Widget2", "Widget3"),
            ROOT,
            grid_mode="absolute",
            natural_sizes=natural,
        )

        ast.parse(source)
        self.assertIn("rootWidget = ft.Stack(", source)
        widget1 = source[source.index("Widget1 = ") : source.index("Widget2 = ")]
        self.assertIn("width=200", widget1)  # the label's measured 200px
        self.assertIn("height=60", widget1)
        widget2 = source[source.index("Widget2 = ") : source.index("Widget3 = ")]
        self.assertIn("left=200", widget2)  # after column 0
        self.assertIn("top=60", widget2)  # after row 0
        self.assertIn("width=120", widget2)  # its own 120px
        widget3 = source[source.index("Widget3 = ") :]
        self.assertIn("top=92", widget3)  # rows 0 and 1 are 60 + 32
        self.assertIn("height=32", widget3)  # rowspan of two 16px rows

    def test_grid_absolute_mode_keeps_the_tool_default_as_a_floor(self):
        """An empty textvariable makes a widget measure small; do not shrink."""
        data = project(
            geom_manager="Grid",
            gridRows=2,
            gridCols=2,
            gridColMinsize="10",
            gridRowMinsize="10",
            gridColPad="0",
            gridRowPad="0",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("textvariable", "cell"),),
                    geom={"row": "0", "column": "0", "padx": "0", "pady": "0"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data,
            [ROOT, "Widget1"],
            ROOT,
            grid_mode="absolute",
            natural_sizes={"Widget1": (8, 27)},  # an empty caption measures 8px
        )

        widget1 = source[source.index("Widget1 = ") :]
        self.assertIn("width=100", widget1)  # the tool default for a button
        self.assertIn("height=32", widget1)

    def test_grid_absolute_mode_keeps_minsize_as_a_floor(self):
        data = project(
            geom_manager="Grid",
            gridRows=2,
            gridCols=2,
            gridColMinsize="40",
            gridRowMinsize="30",
            gridColPad="0",
            gridRowPad="0",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    geom={"row": "0", "column": "0", "padx": "0", "pady": "0"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1"),
            ROOT,
            grid_mode="absolute",
            natural_sizes={"Widget1": (12, 10)},
        )

        widget1 = source[source.index("Widget1 = ") :]
        # The label's own design size (120x32) is larger than the 40x30
        # minsize, so the minsize is not what decides the cell here.
        self.assertIn("width=120", widget1)
        self.assertIn("height=32", widget1)

    def test_grid_absolute_mode_measures_containers_from_their_children(self):
        """A frame is as large as the grid inside it, like Tk's requested size."""
        data = project(
            geom_manager="Grid",
            gridRows=2,
            gridCols=2,
            gridColMinsize="10",
            gridRowMinsize="10",
            gridColPad="0",
            gridRowPad="0",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::frame",
                    geom={"row": "0", "column": "0", "padx": "0", "pady": "0"},
                    container_grid={"columns": "2", "rows": "1"},
                ),
                widget(
                    "Widget2",
                    "ttk::button",
                    parent="Widget1",
                    attributes=(("text", "A"),),
                    geom={"row": "0", "column": "0", "padx": "0", "pady": "0"},
                ),
                widget(
                    "Widget3",
                    "ttk::button",
                    parent="Widget1",
                    attributes=(("text", "B"),),
                    geom={"row": "0", "column": "1", "padx": "0", "pady": "0"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1", "Widget2", "Widget3"),
            ROOT,
            grid_mode="absolute",
            natural_sizes={"Widget2": (30, 20), "Widget3": (30, 20)},
        )

        ast.parse(source)
        # The frame is emitted after its children (child-first ordering).
        frame = source[source.index("Widget1 = ") :]
        # Container grids use the 40x24 minsize the Python backend emits, and
        # the buttons themselves default to 100x32, so the frame is two 100px
        # cells wide and 32px tall.
        self.assertIn("width=200", frame)
        self.assertIn("height=32", frame)

    def test_grid_responsive_mode_is_the_default(self):
        data = project(
            geom_manager="Grid",
            gridRows=2,
            gridCols=2,
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    geom={"row": "0", "column": "0"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        self.assertIn("rootWidget = ft.Column(", source)
        self.assertIn("ft.Row(", source)

    def test_tk_length_conversion(self):
        self.assertEqual(flet_generator.tk_length("120"), 120)
        self.assertEqual(flet_generator.tk_length(""), 0)
        self.assertEqual(flet_generator.tk_length("None", 20), 20)
        self.assertEqual(flet_generator.tk_length("1i"), 96)
        self.assertEqual(flet_generator.tk_length("5m"), 19)

    def test_skip_policy_omits_widgets_and_promotes_children(self):
        data = project(
            widgets=(
                widget(
                    "Widget0",
                    "ttk::frame",
                    place={"x": "0", "y": "0", "width": "200", "height": "120"},
                ),
                widget(
                    "Widget1",
                    "ttk::label",
                    parent="Widget0",
                    attributes=(("text", "kept"),),
                    place={"x": "4", "y": "4", "width": "80", "height": "24"},
                ),
                widget(
                    "Widget2",
                    "ttk::button",
                    attributes=(("text", "dropped"),),
                    place={"x": "4", "y": "40", "width": "80", "height": "24"},
                ),
            )
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget0", "Widget1", "Widget2"),
            ROOT,
            policy={"default": "full", "frame": "skip", "button": "skip"},
        )

        ast.parse(source)
        self.assertNotIn("Widget0 =", source)
        self.assertNotIn("Widget2 =", source)
        self.assertIn("Widget1 = ft.Text(", source)
        self.assertIn("controls=[Widget1]", source)

    def test_placeholder_policy_forces_a_stand_in(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    place={"x": "0", "y": "0", "width": "80", "height": "24"},
                ),
            )
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1"),
            ROOT,
            policy={"default": "placeholder"},
        )

        ast.parse(source)
        self.assertIn("Widget1 = ft.Container(", source)
        self.assertNotIn("ft.Text(", source)
        self.assertIn("placeholder requested", source)

    def test_compatibility_report_lists_every_widget(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    place={"x": "0", "y": "0", "width": "80", "height": "24"},
                ),
                widget(
                    "Widget2",
                    "ttk::treeview",
                    place={"x": "0", "y": "40", "width": "200", "height": "120"},
                ),
            )
        )

        report = flet_generator.compatibility_report(
            data, widget_names("Widget1", "Widget2"), ROOT
        )

        self.assertIn("Flet compatibility report", report)
        self.assertIn("Widget1", report)
        self.assertIn("ft.Text", report)
        self.assertIn("placeholder Container", report)
        self.assertIn("0 folded into a scroll target", report)
        self.assertIn("Summary: 2 widgets", report)

    def test_generated_program_guards_the_flet_version(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    place={"x": "0", "y": "0", "width": "80", "height": "24"},
                ),
            )
        )

        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)

        ast.parse(source)
        self.assertIn("MINIMUM_FLET_VERSION = '1.0'", source)
        self.assertIn("FLET_VERSION_STRICT = False", source)
        self.assertIn("_check_flet_version()", source)
        self.assertLess(
            source.index("_check_flet_version()"), source.index("def main(page")
        )

    def test_generated_guard_can_be_told_a_different_minimum(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    place={"x": "0", "y": "0", "width": "80", "height": "24"},
                ),
            )
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1"),
            ROOT,
            minimum_flet_version="2.0",
            strict_flet_version=True,
        )

        self.assertIn("MINIMUM_FLET_VERSION = '2.0'", source)
        self.assertIn("FLET_VERSION_STRICT = True", source)

    @unittest.skipUnless(FLET_AVAILABLE, "flet is not installed")
    def test_generated_version_helpers_behave(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    place={"x": "0", "y": "0", "width": "80", "height": "24"},
                ),
            )
        )
        source = flet_generator.emit_program(data, widget_names("Widget1"), ROOT)
        namespace, _main = load_generated(source)

        major = namespace["_flet_major"]
        self.assertEqual(major("1.0.3"), 1)
        self.assertEqual(major("0.86.5"), 0)
        self.assertEqual(major(""), 0)
        self.assertEqual(major(None), 0)
        self.assertEqual(major("not-a-version"), 0)

        check = namespace["_check_flet_version"]
        # An unreachable minimum stops a strict program and only warns
        # otherwise; a reachable one is silent either way.
        with self.assertRaises(SystemExit) as raised:
            check(minimum="99.0", strict=True)
        self.assertIn("pip install --upgrade flet", str(raised.exception))
        with contextlib.redirect_stderr(io.StringIO()) as captured:
            self.assertIsNone(check(minimum="99.0", strict=False))
        self.assertIn("warning:", captured.getvalue())
        self.assertIsNone(check(minimum="0.0", strict=True))

    def test_theme_colours_follow_the_resolved_ttkbootstrap_palette(self):
        """tokyo-night-dark: primary #95b5f9 with black ink, entry #1f202d."""
        data = project(
            theme="tokyo-night-dark",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "Start"), ("style", "primary.TButton")),
                    place={"x": "0", "y": "0", "width": "80", "height": "32"},
                ),
                widget(
                    "Widget2",
                    "ttk::button",
                    attributes=(
                        ("text", "Stop"),
                        ("style", "secondary.Outline.TButton"),
                    ),
                    place={"x": "0", "y": "40", "width": "80", "height": "32"},
                ),
                widget(
                    "Widget3",
                    "ttk::label",
                    attributes=(("text", "Voltage"), ("style", "primary.TLabel")),
                    place={"x": "0", "y": "80", "width": "64", "height": "32"},
                ),
                widget(
                    "Widget4",
                    "ttk::frame",
                    attributes=(("style", "primary.TFrame"),),
                    place={"x": "0", "y": "120", "width": "80", "height": "32"},
                ),
                widget(
                    "Widget5",
                    "ttk::entry",
                    attributes=(("style", "primary.TEntry"),),
                    place={"x": "0", "y": "160", "width": "80", "height": "32"},
                ),
            ),
        )
        order = widget_names(*[f"Widget{index}" for index in range(1, 6)])

        source = flet_generator.emit_program(data, order, ROOT)

        ast.parse(source)
        self.assertIn("bgcolor='#95b5f9'", source)
        self.assertIn("color='#000000'", source)  # ink on a light fill
        self.assertIn("bgcolor='#1a1b26'", source)  # outline keeps the surface
        self.assertIn("ft.BorderSide(1, '#c9aef9')", source)
        self.assertIn("bgcolor='#1f202d'", source)  # entry surface
        # Theme border, not the bootstyle colour, spelled as Flet 1.0 wants.
        self.assertIn("ft.OutlineInputBorder(side=ft.BorderSide(1, '#3f3f49'))", source)
        self.assertIn("color='#c0caf5'", source)  # entry text

    def test_styles_are_translated_not_dropped(self):
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "Go"), ("style", "success.TButton")),
                    place={"x": "0", "y": "0", "width": "80", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        self.assertIn("bgcolor='#00bc8c'", source)
        self.assertNotIn("no Flet equivalent -> style", source)

    def test_unknown_theme_still_generates(self):
        data = project(
            theme="not-a-real-theme",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "Go"), ("style", "primary.TButton")),
                    place={"x": "0", "y": "0", "width": "80", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("Widget1 = ft.Button(", source)

    def test_parse_bootstyle_splits_colour_and_variants(self):
        self.assertEqual(
            flet_generator.parse_bootstyle("secondary.Outline.TButton"),
            ("secondary", frozenset({"outline"})),
        )
        self.assertEqual(
            flet_generator.parse_bootstyle("success.Inverse.TLabel"),
            ("success", frozenset({"inverse"})),
        )
        self.assertEqual(
            flet_generator.parse_bootstyle("primary.Horizontal.TScale")[0], "primary"
        )
        self.assertEqual(flet_generator.parse_bootstyle("TNotebook")[0], "")
        self.assertEqual(flet_generator.parse_bootstyle("")[0], "")

    def test_ink_matches_ttkbootstrap_contrast(self):
        data = project(theme="tokyo-night-dark")
        project_view = flet_generator._Project(data, [ROOT], ROOT)
        ink = project_view.ink
        self.assertEqual(ink("#b1d888"), "#000000")  # light fill -> black
        self.assertEqual(ink("#375a7f"), "#ffffff")  # dark fill -> white
        self.assertEqual(ink(""), "#c0caf5")  # falls back to theme fg

    def test_palette_covers_the_themes_the_projects_use(self):
        palette = flet_generator.load_theme_palette()
        self.assertGreater(len(palette), 40)
        for theme in ("tokyo-night-dark", "solar", "darkly", "catppuccin-light"):
            with self.subTest(theme=theme):
                self.assertIn(theme, palette)
                record = palette[theme]
                self.assertIn("colors", record)
                self.assertIn("styles", record)
                self.assertIn("widgets", record)
                self.assertTrue(record["styles"]["primary"]["button_bg"])

    def test_labelframe_caption_matches_the_frame_border(self):
        """Measured on the ttk output: the caption is the bootstyle colour."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::labelframe",
                    attributes=(("text", "Group"), ("style", "primary.TLabelframe")),
                    place={"x": "0", "y": "0", "width": "160", "height": "96"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        # darkly's primary, the same colour ttk paints the border with.
        self.assertIn("ft.Text(value='Group', color='#375a7f'", source)
        self.assertIn("ft.BorderSide(1, '#375a7f')", source)

    def test_palette_keeps_the_resolved_style_and_widget_sections(self):
        """The resolved tables must survive loading, or ttk's own choices go."""
        palette = flet_generator.theme_palette("darkly")

        self.assertEqual(palette["styles"]["primary"]["button_bg"], "#375a7f")
        self.assertEqual(palette["widgets"]["entry_bg"], "#282828")

    def test_resolved_button_ink_beats_the_luminance_rule(self):
        """bootstrap-dark's primary sits on the boundary; ttk chooses white."""
        data = project(
            theme="bootstrap-dark",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "Go"), ("style", "primary.TButton")),
                    place={"x": "0", "y": "0", "width": "80", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        self.assertIn("bgcolor='#3d8bfd'", source)
        self.assertIn("color='#ffffff'", source)  # not the rule's black

    def test_report_names_the_theme(self):
        data = project(theme="darkly")
        report = flet_generator.compatibility_report(data, [ROOT], ROOT)
        self.assertIn("Theme   : darkly", report)
        report = flet_generator.compatibility_report(
            project(theme="nope"), [ROOT], ROOT
        )
        self.assertIn("no theme palette", report)

    def test_listbox_listvariable_becomes_a_module_level_list(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "listbox",
                    attributes=(
                        ("listvariable", "listvar"),
                        ("selectmode", "browse"),
                    ),
                    place={"x": "0", "y": "0", "width": "160", "height": "120"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("listvar = []   # AUTO-GENERATED default", source)
        self.assertIn("listbox items live in the module level list", source)
        self.assertNotIn("listvariable", source)

    def test_listbox_inline_values_become_items(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "listbox",
                    attributes=(("values", "(alpha beta)"),),
                    place={"x": "0", "y": "0", "width": "160", "height": "120"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("ft.Text('alpha')", source)
        self.assertIn("ft.Text('beta')", source)

    def test_invalid_listvariable_is_not_emitted_as_code(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "listbox",
                    attributes=(("listvariable", "132659090261440yview"),),
                    place={"x": "0", "y": "0", "width": "160", "height": "120"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertNotIn("132659090261440yview", source)

    def test_grid_sizes_reach_the_wrapper_for_non_positionable_controls(self):
        """ft.RadioGroup and ft.Divider accept no width/height of their own."""
        data = project(
            geom_manager="Grid",
            gridRows=4,
            gridCols=4,
            widgets=(
                widget(
                    "Widget1",
                    "ttk::radiobutton",
                    attributes=(("text", "Pick"), ("sticky", "")),
                    geom={"row": "0", "column": "0", "sticky": "ew"},
                ),
                widget(
                    "Widget2",
                    "ttk::separator",
                    geom={"row": "1", "column": "0", "sticky": ""},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1", "Widget2"),
            ROOT,
            natural_sizes={"Widget1": (140, 32), "Widget2": (200, 8)},
        )

        ast.parse(source)
        widgets = source[source.index("Widget1 = ") : source.index("rootWidget = ")]
        rows = source[source.index("rootWidget = ") :]
        # The controls are wrapped, never given sizes they cannot take ...
        self.assertNotIn("= ft.RadioGroup(", widgets)
        self.assertNotIn("= ft.Divider(", widgets)
        # ... and the sizes sit on the grid cells that hold them.
        self.assertIn("height=32", rows)
        self.assertIn("height=8", rows)

    def test_grid_sticky_decides_which_axes_a_widget_fills(self):
        data = project(
            geom_manager="Grid",
            gridRows=3,
            gridCols=3,
            widgets=(
                widget(
                    "Widget1",
                    "ttk::entry",
                    attributes=(("sticky", ""),),
                    geom={"row": "0", "column": "0", "sticky": "ew"},
                ),
                widget(
                    "Widget2",
                    "ttk::progressbar",
                    geom={"row": "1", "column": "0", "sticky": "nsew"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1", "Widget2"),
            ROOT,
            natural_sizes={"Widget1": (180, 32), "Widget2": (200, 24)},
        )

        ast.parse(source)
        entry = source[source.index("Widget1 = ") : source.index("Widget2 = ")]
        # sticky=ew: fills across, keeps its designed height (set on the cell).
        self.assertIn("expand=True", entry)
        self.assertNotIn("height=", entry)
        rows = source[source.index("rootWidget = ") :]
        self.assertIn("height=32", rows)
        # sticky=nsew: fills the cell in both directions, no pinned height.
        self.assertIn("vertical_alignment=ft.CrossAxisAlignment.STRETCH", rows)
        self.assertNotIn("height=24", rows)

    def test_grid_row_weights_follow_the_content(self):
        """A short row must not get the same weight as a tall one."""
        data = project(
            geom_manager="Grid",
            gridRows=2,
            gridCols=2,
            widgets=(
                widget(
                    "Widget1",
                    "ttk::text",
                    geom={"row": "0", "column": "0", "sticky": "nsew"},
                ),
                widget(
                    "Widget2",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    geom={"row": "1", "column": "0", "sticky": "ew"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data,
            [ROOT, "Widget1", "Widget2"],
            ROOT,
            natural_sizes={"Widget1": (200, 200), "Widget2": (120, 32)},
        )

        ast.parse(source)
        # Each row's own weight follows "spacing=0,"; cell containers also
        # carry expand, so match the row argument specifically.
        weights = [
            int(value) for value in re.findall(r"spacing=0,\s*expand=(\d+)", source)
        ]

        self.assertEqual(len(weights), 2)
        self.assertGreater(weights[0], weights[1])  # tall row vs one line row
        # The weights follow the content (plus each cell's padding), so they
        # are proportional rather than equal.
        self.assertEqual(weights[1], 36)
        self.assertGreaterEqual(weights[0], 200)

    @unittest.skipUnless(FLET_AVAILABLE, "flet is not installed")
    def test_grid_program_with_radio_and_separator_builds(self):
        """Regression: sizes were handed to controls that cannot take them."""
        data = project(
            geom_manager="Grid",
            gridRows=6,
            gridCols=6,
            widgets=(
                widget(
                    "Widget1",
                    "ttk::radiobutton",
                    attributes=(("text", "Pick"),),
                    geom={"row": "0", "column": "0", "sticky": "ew"},
                ),
                widget(
                    "Widget2",
                    "ttk::separator",
                    geom={"row": "1", "column": "0", "sticky": ""},
                ),
                widget(
                    "Widget3",
                    "ttk::checkbutton",
                    attributes=(("text", "On"),),
                    geom={"row": "2", "column": "0", "sticky": "ew"},
                ),
                widget(
                    "Widget4",
                    "ttk::progressbar",
                    geom={"row": "3", "column": "0", "sticky": "nsew"},
                ),
                widget(
                    "Widget5",
                    "ttk::frame",
                    geom={"row": "4", "column": "0", "sticky": "nsew"},
                ),
                widget(
                    "Widget6",
                    "ttk::button",
                    parent="Widget5",
                    attributes=(("text", "in a frame"),),
                    geom={"row": "0", "column": "0", "sticky": "ew"},
                ),
            ),
        )
        order = widget_names(*[f"Widget{index}" for index in range(1, 7)])

        page = run_generated(
            flet_generator.emit_program(
                data,
                order,
                ROOT,
                natural_sizes={
                    "Widget1": (140, 32),
                    "Widget2": (200, 8),
                    "Widget3": (140, 32),
                    "Widget4": (200, 24),
                    "Widget6": (100, 32),
                },
            )
        )

        self.assertEqual(len(page.controls), 1)

    def test_font_chooser_dict_is_parsed(self):
        """The designer stores fonts as a dict, not an X11 string."""
        stored = (
            "{'family': 'Liberation\\\\ Mono', 'size': 18, 'weight': 'bold', "
            "'slant': 'italic', 'underline': 0, 'overstrike': 0}"
        )

        parsed = flet_generator.parse_font(stored)

        self.assertEqual(parsed["font_family"], "'Liberation Mono'")
        self.assertEqual(parsed["size"], "18")
        self.assertEqual(parsed["weight"], "ft.FontWeight.BOLD")
        self.assertEqual(parsed["italic"], "True")

    def test_font_size_on_a_text_field_uses_text_size(self):
        """ft.TextField has no size field; passing one is a TypeError."""
        font = (
            "{'family': 'Liberation\\\\ Mono', 'size': 18, 'weight': 'normal', "
            "'slant': 'roman', 'underline': 0, 'overstrike': 0}"
        )
        data = project(
            theme="dracula-dark",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::entry",
                    attributes=(
                        ("textvariable", "calcvar"),
                        ("font", font),
                        ("style", "primary.TEntry"),
                    ),
                    place={"x": "0", "y": "0", "width": "320", "height": "32"},
                ),
                widget(
                    "Widget2",
                    "ttk::label",
                    attributes=(("text", "Calculator"), ("font", font)),
                    place={"x": "0", "y": "40", "width": "320", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1", "Widget2"], ROOT)

        ast.parse(source)
        entry_block = source[source.index("Widget1 = ") : source.index("Widget2 = ")]
        entry_lines = [line.strip() for line in entry_block.split("\n")]
        self.assertIn("text_size=18,", entry_lines)
        self.assertNotIn("size=18,", entry_lines)  # no bare size on a field
        label = source[source.index("Widget2 = ") :]
        self.assertIn("size=18", label)
        self.assertIn("font_family='Liberation Mono'", label)

    def test_inverse_label_is_filled_by_a_container(self):
        """ft.Text paints behind its glyphs only, so a filled label needs one."""
        data = project(
            theme="cyborg",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(
                        ("text", "Given Name"),
                        ("style", "info.Inverse.TLabel"),
                        ("anchor", "w"),
                    ),
                    place={"x": "0", "y": "32", "width": "112", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("Widget1 = ft.Container(", source)
        self.assertIn("bgcolor='#9933cc'", source)  # cyborg's info colour
        self.assertIn("value='Given Name'", source)
        self.assertIn("ft.Alignment.CENTER_LEFT", source)  # ttk anchor="w"
        # The inner Text must not carry the fill, or it paints behind the text
        # only and the label loses its bar.
        inner = source[source.index("content=ft.Text(") : source.index("ft.Alignment")]
        self.assertNotIn("bgcolor=", inner)

    def test_label_with_an_explicit_background_is_filled_too(self):
        data = project(
            theme="cyborg",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(
                        ("text", "Add a New user"),
                        ("background", "#2724db"),
                        ("style", "info.Inverse.TLabel"),
                    ),
                    place={"x": "0", "y": "0", "width": "432", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("Widget1 = ft.Container(", source)
        self.assertIn("bgcolor='#2724db'", source)  # the explicit colour wins

    def test_plain_label_stays_a_text_control(self):
        data = project(
            theme="cyborg",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(("text", "Plain"), ("style", "success.TLabel")),
                    place={"x": "0", "y": "0", "width": "120", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        self.assertIn("Widget1 = ft.Text(", source)
        self.assertIn("color='#77b300'", source)

    def test_label_relief_gives_it_a_border(self):
        """The designer's relief + borderwidth is the signal, as in ttk."""
        data = project(
            theme="cyborg",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::label",
                    attributes=(
                        ("text", "Given Name"),
                        ("style", "info.Inverse.TLabel"),
                        ("relief", "solid"),
                        ("borderwidth", "1"),
                    ),
                    place={"x": "0", "y": "0", "width": "112", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("Widget1 = ft.Container(", source)
        self.assertIn("ft.BorderSide(1, '#2e2e2e')", source)  # cyborg's border

    def test_label_without_a_border_stays_flat(self):
        for attributes in (
            (("text", "L"), ("relief", "flat"), ("borderwidth", "1")),
            (("text", "L"), ("relief", "solid"), ("borderwidth", "0")),
            (("text", "L"),),
        ):
            with self.subTest(attributes=attributes):
                data = project(
                    theme="cyborg",
                    widgets=(
                        widget(
                            "Widget1",
                            "ttk::label",
                            attributes=attributes,
                            place={"x": "0", "y": "0", "width": "80", "height": "24"},
                        ),
                    ),
                )

                source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

                self.assertNotIn("ft.BorderSide", source)

    def test_frame_relief_gives_the_container_a_border(self):
        data = project(
            theme="cyborg",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::frame",
                    attributes=(("relief", "solid"), ("borderwidth", "2")),
                    place={"x": "0", "y": "0", "width": "200", "height": "100"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("Widget1 = ft.Container(", source)
        self.assertIn("ft.BorderSide(2, '#2e2e2e')", source)

    def test_labelframe_caption_follows_the_label_anchor(self):
        for anchor, expected in (
            ("n", "ft.MainAxisAlignment.CENTER"),
            ("nw", "ft.MainAxisAlignment.START"),
            ("ne", "ft.MainAxisAlignment.END"),
        ):
            with self.subTest(anchor=anchor):
                data = project(
                    theme="cyborg",
                    widgets=(
                        widget(
                            "Widget1",
                            "ttk::labelframe",
                            attributes=(
                                ("text", "Flash Card Path"),
                                ("labelanchor", anchor),
                                ("style", "primary.TLabelframe"),
                            ),
                            place={"x": "0", "y": "0", "width": "448", "height": "96"},
                        ),
                    ),
                )

                source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

                ast.parse(source)
                self.assertIn(f"alignment={expected}", source)

    def test_labelframe_caption_below_for_a_south_anchor(self):
        data = project(
            theme="cyborg",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::labelframe",
                    attributes=(
                        ("text", "Progress"),
                        ("labelanchor", "sw"),
                        ("style", "primary.TLabelframe"),
                    ),
                    place={"x": "0", "y": "0", "width": "448", "height": "96"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        column = source[source.index("ft.Column(") : source.index("spacing=2")]
        # The caption row comes after the content for a south anchor.
        self.assertGreater(column.index("ft.Text(value='Progress'"), 0)
        self.assertIn("ft.MainAxisAlignment.START", source)  # sw anchors west

    def test_labelframe_borderwidth_zero_draws_no_box(self):
        """Platypus' Camera frame: ttk draws the caption only."""
        data = project(
            theme="superhero",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::labelframe",
                    attributes=(
                        ("text", "Camera"),
                        ("labelanchor", "n"),
                        ("relief", "solid"),
                        ("borderwidth", "0"),
                        ("style", "primary.TLabelframe"),
                    ),
                    place={"x": "32", "y": "16", "width": "160", "height": "80"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("value='Camera'", source)
        self.assertNotIn("ft.Border(", source)

    def test_labelframe_borderwidth_two_widens_the_box(self):
        data = project(
            theme="superhero",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::labelframe",
                    attributes=(
                        ("text", "Flash Card Path"),
                        ("relief", "solid"),
                        ("borderwidth", "2"),
                        ("style", "primary.TLabelframe"),
                    ),
                    place={"x": "0", "y": "0", "width": "448", "height": "96"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("ft.BorderSide(2,", source)

    def test_checkbox_state_follows_onvalue_not_truthiness(self):
        """Tk selects a checkbutton when its variable equals onvalue."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::checkbutton",
                    attributes=(
                        ("text", "Checkbutton"),
                        ("variable", "flag"),
                        ("onvalue", "1"),
                        ("offvalue", "0"),
                        ("style", "warning.TCheckbutton"),
                    ),
                    place={"x": "0", "y": "0", "width": "144", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("value=str(flag) == '1'", source)
        self.assertNotIn("bool(flag)", source)
        # A fill colour would be painted while unchecked too.
        self.assertNotIn("fill_color=", source)

    def test_radio_group_follows_the_variable_not_the_widget_value(self):
        """A Tk radio is selected when the variable equals its own value."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::radiobutton",
                    attributes=(
                        ("text", "Radiobutton"),
                        ("variable", "choice"),
                        ("value", "0"),
                        ("style", "success.TRadiobutton"),
                    ),
                    place={"x": "0", "y": "0", "width": "144", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        group = source[source.index("ft.RadioGroup(") : source.index("ft.Radio(")]
        self.assertIn("value=str(choice)", group)  # follows the variable
        self.assertNotIn("value='0',", group)  # not its own identity
        self.assertIn("ft.Radio(value='0'", source)  # identity on the radio

    def test_page_theme_is_seeded_from_the_project_primary(self):
        data = project(theme="darkly")

        source = flet_generator.emit_program(data, [ROOT], ROOT)

        ast.parse(source)
        self.assertIn("page.theme = ft.Theme(color_scheme_seed='#375a7f')", source)

    @unittest.skipUnless(FLET_AVAILABLE, "flet is not installed")
    def test_unchecked_checkbox_and_unselected_radio_build_unset(self):
        """Regression: a variable holding '0.0' must not look selected."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::checkbutton",
                    attributes=(("text", "C"), ("variable", "flag"), ("onvalue", "1")),
                    place={"x": "0", "y": "0", "width": "144", "height": "32"},
                ),
                widget(
                    "Widget2",
                    "ttk::radiobutton",
                    attributes=(("text", "R"), ("variable", "choice"), ("value", "0")),
                    place={"x": "0", "y": "40", "width": "144", "height": "32"},
                ),
            ),
        )

        page = run_generated(
            flet_generator.emit_program(data, [ROOT, "Widget1", "Widget2"], ROOT)
        )

        found = {}

        def walk(control):
            for child in getattr(control, "controls", []) or []:
                walk(child)
            content = getattr(control, "content", None)
            if content is not None and not isinstance(content, str):
                walk(content)
            if isinstance(control, ft.Checkbox):
                found["checkbox"] = control
            if isinstance(control, ft.RadioGroup):
                found["radio"] = control

        for control in page.controls:
            walk(control)

        self.assertIs(found["checkbox"].value, False)
        self.assertEqual(found["radio"].value, "0.0")  # matches no radio

    def test_multiline_lines_from_a_design_height(self):
        self.assertEqual(flet_generator.multiline_lines(224), 12)
        self.assertEqual(flet_generator.multiline_lines(0), 0)
        self.assertEqual(flet_generator.multiline_lines(None), 0)
        self.assertGreaterEqual(flet_generator.multiline_lines(10), 1)

    def test_text_widget_becomes_a_sized_container_around_the_field(self):
        """A multiline field ignores height, so the box comes from a Container."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "text",
                    attributes=(
                        ("background", "#290af5"),
                        ("height", "5"),
                        ("width", "20"),
                    ),
                    place={"x": "240", "y": "80", "width": "320", "height": "224"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("Widget1 = ft.Container(", source)
        self.assertIn("clip_behavior=ft.ClipBehavior.HARD_EDGE", source)
        self.assertIn("min_lines=12", source)  # from the 224px design box
        self.assertIn("border=None", source)  # no border of its own
        self.assertIn("bgcolor='#290af5'", source)
        # The Container carries the placement, so the box is exactly the design.
        block = source[source.index("Widget1 = ") :]
        self.assertIn("height=224", block)
        self.assertIn("width=320", block)

    def test_text_styles_pin_the_weight(self):
        """Flet draws a TextStyle with no weight in bold; ttk does not."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::button",
                    attributes=(("text", "Go"), ("style", "primary.TButton")),
                    place={"x": "0", "y": "0", "width": "80", "height": "32"},
                ),
                widget(
                    "Widget2",
                    "ttk::checkbutton",
                    attributes=(("text", "C"), ("style", "primary.TCheckbutton")),
                    place={"x": "0", "y": "40", "width": "140", "height": "32"},
                ),
                widget(
                    "Widget3",
                    "ttk::radiobutton",
                    attributes=(
                        ("text", "R"),
                        ("variable", "choice"),
                        ("value", "0"),
                        ("style", "primary.TRadiobutton"),
                    ),
                    place={"x": "0", "y": "80", "width": "140", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(
            data, [ROOT, "Widget1", "Widget2", "Widget3"], ROOT
        )

        ast.parse(source)
        for style in re.findall(r"ft\.TextStyle\(([^)]*)\)", source):
            with self.subTest(style=style.strip().split(chr(10))[0]):
                self.assertIn("weight=ft.FontWeight.NORMAL", style)

    def test_notebook_is_a_panel_with_ttk_style_tabs(self):
        data = project(
            theme="tokyo-night-dark",
            widgets=(
                widget(
                    "Widget0",
                    "ttk::notebook",
                    attributes=(("style", "primary.TNotebook"),),
                    place={"x": "64", "y": "32", "width": "144", "height": "160"},
                ),
                widget("Widget1", "ttk::frame", parent="Widget0"),
                widget("Widget2", "ttk::frame", parent="Widget0"),
                widget("Widget3", "ttk::frame", parent="Widget0"),
            ),
        )
        order = widget_names("Widget0", "Widget1", "Widget2", "Widget3")

        source = flet_generator.emit_program(data, order, ROOT)

        ast.parse(source)
        # A panel of its own, so the tabs sit inside the notebook.
        self.assertIn("Widget0 = ft.Container(", source)
        self.assertIn("bgcolor='#1a1b26'", source)
        self.assertIn("ft.BorderSide(1, '#3f3f49')", source)
        # ttk style tabs: compact, left aligned, bootstyle accent.
        self.assertIn("length=3", source)
        self.assertIn("tab_alignment=ft.TabAlignment.START", source)
        self.assertIn("label_padding=ft.Padding(", source)
        self.assertIn("indicator_color='#95b5f9'", source)
        self.assertIn("unselected_label_color='#c0caf5'", source)

    def test_notebook_tab_labels_match_the_python_backend(self):
        """The designer does not save tab labels, so ttk calls them all "Tab"."""
        data = project(
            theme="darkly",
            widgets=(
                widget("Widget0", "ttk::notebook", place={"x": "0", "y": "0"}),
                widget("Widget1", "ttk::frame", parent="Widget0"),
                widget("Widget2", "ttk::frame", parent="Widget0"),
            ),
        )
        order = widget_names("Widget0", "Widget1", "Widget2")

        source = flet_generator.emit_program(data, order, ROOT)

        self.assertIn("ft.Tab(label='Tab')", source)
        self.assertNotIn("Tab 1", source)

    def test_hand_written_tab_labels_are_honoured(self):
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget0",
                    "ttk::notebook",
                    attributes=(("tab_labels", "First,Second"),),
                    place={"x": "0", "y": "0"},
                ),
                widget("Widget1", "ttk::frame", parent="Widget0"),
                widget("Widget2", "ttk::frame", parent="Widget0"),
            ),
        )
        order = widget_names("Widget0", "Widget1", "Widget2")

        source = flet_generator.emit_program(data, order, ROOT)

        self.assertIn("ft.Tab(label='First')", source)
        self.assertIn("ft.Tab(label='Second')", source)

    def test_entry_value_is_bound_and_stubs_can_reach_the_variable(self):
        """A handler assigning the variable must update the field, as in ttk."""
        data = project(
            theme="dracula-dark",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::entry",
                    attributes=(("textvariable", "calcvar"),),
                    place={"x": "0", "y": "0", "width": "320", "height": "32"},
                ),
                widget(
                    "Widget2",
                    "ttk::button",
                    attributes=(("text", "4"), ("command", "clicked_4")),
                    place={"x": "0", "y": "40", "width": "80", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1", "Widget2"], ROOT)

        ast.parse(source)
        self.assertIn("value=calcvar", source)
        # The field is bound, so set_text can put a value into it.
        self.assertIn("TEXT_BINDINGS['calcvar'] = [(Widget1, 'value')]", source)
        # And the stub can assign the module variable at all.
        self.assertIn("    global calcvar", source)
        self.assertIn("set_text('calcvar', 'new value')", source)
        self.assertIn("PAGE = page", source)

    def test_text_area_binds_the_field_inside_the_container(self):
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "text",
                    attributes=(("textvariable", "log_text"),),
                    place={"x": "0", "y": "0", "width": "200", "height": "120"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        # The Container is not the control holding the value; the field is.
        self.assertIn("Widget1_field = ft.TextField(", source)
        self.assertIn("content=Widget1_field", source)
        self.assertIn("TEXT_BINDINGS['log_text'] = [(Widget1_field, 'value')]", source)

    @unittest.skipUnless(FLET_AVAILABLE, "flet is not installed")
    def test_set_text_updates_the_field_and_the_variable(self):
        """The reported bug: a button handler could not change the display."""
        data = project(
            theme="dracula-dark",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::entry",
                    attributes=(("textvariable", "calcvar"),),
                    place={"x": "0", "y": "0", "width": "320", "height": "32"},
                ),
                widget(
                    "Widget2",
                    "ttk::button",
                    attributes=(("text", "4"), ("command", "clicked_4")),
                    place={"x": "0", "y": "40", "width": "80", "height": "32"},
                ),
            ),
        )
        source = flet_generator.emit_program(data, [ROOT, "Widget1", "Widget2"], ROOT)
        namespace, main = load_generated(source)
        page = FakePage()
        main(page)

        found = []

        def walk(control):
            for child in getattr(control, "controls", []) or []:
                walk(child)
            content = getattr(control, "content", None)
            if content is not None and not isinstance(content, str):
                walk(content)
            if isinstance(control, ft.TextField) and control.value == "0.0":
                found.append(control)

        for control in page.controls:
            walk(control)
        display = found[0]

        namespace["set_text"]("calcvar", "4")

        self.assertEqual(display.value, "4")  # the control refreshed
        self.assertEqual(namespace["calcvar"], "4")  # the variable too
        self.assertIs(namespace["PAGE"], page)

    def test_the_variable_section_explains_set_text(self):
        """The tip belongs where someone looks for the variables."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::checkbutton",
                    attributes=(("text", "On"), ("variable", "flag")),
                    place={"x": "0", "y": "0", "width": "120", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        variables_at = source.index("####### Flet variables #######")
        functions_at = source.index("####### Functions #######")
        tip = source[variables_at:functions_at]
        self.assertIn("set_text('flag', 'new value')", tip)
        self.assertIn("the widgets showing it keep the value they were built with", tip)
        # A variable with nothing bound yet still gets the helper.
        self.assertIn("def set_text(", source)
        self.assertIn("TEXT_BINDINGS = {}", source)

    def test_spinbox_and_variable_helpers_coexist(self):
        """Regression: the binding helpers once wiped the stepper helper."""
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::spinbox",
                    attributes=(
                        ("from", "0"),
                        ("to", "10"),
                        ("increment", "1"),
                        ("textvariable", "count"),
                    ),
                    place={"x": "0", "y": "0", "width": "140", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("def _step_value(", source)
        self.assertIn("def set_text(", source)

    def test_variable_starts_at_the_value_the_designer_showed(self):
        """Variables used to be '0.0' however the designer looked."""
        data = project(
            theme="dracula-dark",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::entry",
                    attributes=(
                        ("textvariable", "calcvar"),
                        ("var_value", "123"),
                    ),
                    place={"x": "0", "y": "0", "width": "320", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        ast.parse(source)
        self.assertIn("calcvar = '123'", source)
        self.assertNotIn("calcvar = '0.0'", source)

    def test_variable_without_a_captured_value_still_defaults(self):
        data = project(
            theme="darkly",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::entry",
                    attributes=(("textvariable", "calcvar"),),
                    place={"x": "0", "y": "0", "width": "320", "height": "32"},
                ),
            ),
        )

        source = flet_generator.emit_program(data, [ROOT, "Widget1"], ROOT)

        self.assertIn("calcvar = '0.0'", source)

    def test_user_edited_functions_and_variables_are_preserved(self):
        """A handler whose stub marker is gone is never overwritten."""
        earlier = '''"""Flet UI generated by PyTkQuickGui."""
import flet as ft

calcvar = '99'          # the user changed this

####### Functions #######

def clicked_4(e=None):
    global calcvar
    calcvar = '4'
    print('my own code')

def clicked_5(e=None):
    # AUTO-GENERATED STUB
    print('clicked_5')
'''
        path = os.path.join(self.temp_dir.name, "Calculator_flet.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(earlier)

        data = project(
            theme="dracula-dark",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::entry",
                    attributes=(("textvariable", "calcvar"), ("var_value", "0.0")),
                    place={"x": "0", "y": "0", "width": "320", "height": "32"},
                ),
                widget(
                    "Widget2",
                    "ttk::button",
                    attributes=(("text", "4"), ("command", "clicked_4")),
                    place={"x": "0", "y": "40", "width": "80", "height": "32"},
                ),
                widget(
                    "Widget3",
                    "ttk::button",
                    attributes=(("text", "5"), ("command", "clicked_5")),
                    place={"x": "0", "y": "80", "width": "80", "height": "32"},
                ),
            ),
        )
        order = [ROOT, "Widget1", "Widget2", "Widget3"]

        source = flet_generator.emit_program(data, order, ROOT, preserve_from=path)

        ast.parse(source)
        # The hand written handler survives, marker and all gone.
        self.assertIn("print('my own code')", source)
        self.assertNotIn("print('clicked_4')", source)
        # The untouched stub is regenerated.
        self.assertIn("# AUTO-GENERATED STUB", source)
        self.assertIn("print('clicked_5')", source)
        # And so is the user's variable value.
        self.assertIn("calcvar = '99'", source)
        self.assertNotIn("calcvar = '0.0'", source)

    def test_an_unparsable_existing_file_is_ignored(self):
        path = os.path.join(self.temp_dir.name, "broken_flet.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("this is not python(")

        data = project(theme="darkly")
        source = flet_generator.emit_program(data, [ROOT], ROOT, preserve_from=path)

        ast.parse(source)  # regenerated cleanly rather than failing
        self.assertIn("import flet as ft", source)

    @unittest.skipUnless(FLET_AVAILABLE, "flet is not installed")
    def test_generated_program_builds_real_flet_controls(self):
        data = project(
            widgets=(
                widget(
                    "Widget1",
                    "ttk::frame",
                    place={"x": "0", "y": "0", "width": "200", "height": "120"},
                ),
                widget(
                    "Widget2",
                    "ttk::label",
                    parent="Widget1",
                    attributes=(("text", "Name"), ("foreground", "#123456")),
                    place={"x": "4", "y": "4", "width": "80", "height": "24"},
                ),
                widget(
                    "Widget3",
                    "ttk::entry",
                    attributes=(("textvariable", "entry_text"), ("state", "normal")),
                    place={"x": "4", "y": "32", "width": "120", "height": "24"},
                ),
                widget(
                    "Widget4",
                    "ttk::button",
                    attributes=(("text", "Go"), ("command", "go")),
                    place={"x": "4", "y": "64", "width": "80", "height": "24"},
                ),
                widget(
                    "Widget5",
                    "ttk::combobox",
                    attributes=(("values", "(a b c)"),),
                    place={"x": "4", "y": "96", "width": "120", "height": "24"},
                ),
                widget(
                    "Widget6",
                    "ttk::checkbutton",
                    attributes=(("text", "On"), ("variable", "flag")),
                    place={"x": "140", "y": "4", "width": "60", "height": "24"},
                ),
                widget(
                    "Widget7",
                    "ttk::radiobutton",
                    attributes=(("text", "One"), ("value", "1")),
                    place={"x": "140", "y": "32", "width": "60", "height": "24"},
                ),
                widget(
                    "Widget8",
                    "ttk::scale",
                    attributes=(("from", "0"), ("to", "10"), ("value", "5")),
                    place={"x": "140", "y": "64", "width": "60", "height": "24"},
                ),
                widget(
                    "Widget9",
                    "ttk::progressbar",
                    attributes=(("value", "25"), ("maximum", "100")),
                    place={"x": "140", "y": "96", "width": "60", "height": "16"},
                ),
                widget(
                    "Widget10",
                    "ttk::separator",
                    place={"x": "0", "y": "118", "width": "200", "height": "6"},
                ),
                widget(
                    "Widget11",
                    "ttk::notebook",
                    place={"x": "220", "y": "0", "width": "200", "height": "120"},
                ),
                widget("Widget12", "ttk::frame", parent="Widget11"),
                widget("Widget13", "ttk::frame", parent="Widget11"),
            )
        )
        order = widget_names(*[f"Widget{index}" for index in range(1, 14)])

        page = run_generated(flet_generator.emit_program(data, order, ROOT))

        self.assertEqual(len(page.controls), 1)
        self.assertEqual(page.title, "test")

    @unittest.skipUnless(FLET_AVAILABLE, "flet is not installed")
    def test_grid_and_pack_programs_build_real_flet_controls(self):
        grid = project(
            geom_manager="Grid",
            gridRows=4,
            gridCols=4,
            widgets=(
                widget(
                    "Widget1",
                    "ttk::labelframe",
                    attributes=(("text", "Group"),),
                    geom={"row": "0", "column": "0", "columnspan": "2"},
                ),
                widget(
                    "Widget2",
                    "ttk::button",
                    parent="Widget1",
                    attributes=(("text", "Inner"),),
                    geom={"row": "0", "column": "0"},
                ),
                widget(
                    "Widget3",
                    "ttk::label",
                    attributes=(("text", "L"),),
                    geom={"row": "2", "column": "3", "sticky": "nesw"},
                ),
            ),
        )
        packed = project(
            geom_manager="Pack",
            widgets=(
                widget(
                    "Widget1",
                    "ttk::frame",
                    geom={"side": "top", "expand": "1", "fill": "both"},
                ),
                widget(
                    "Widget2",
                    "ttk::label",
                    parent="Widget1",
                    attributes=(("text", "L"),),
                    geom={"side": "top"},
                ),
                widget(
                    "Widget3",
                    "ttk::button",
                    attributes=(("text", "B"),),
                    geom={"side": "left"},
                ),
                widget(
                    "Widget4",
                    "ttk::button",
                    attributes=(("text", "C"),),
                    geom={"side": "right"},
                ),
                widget(
                    "Widget5",
                    "ttk::label",
                    attributes=(("text", "F"),),
                    geom={"side": "bottom"},
                ),
            ),
        )

        for data, order in (
            (grid, widget_names("Widget1", "Widget2", "Widget3")),
            (
                packed,
                widget_names("Widget1", "Widget2", "Widget3", "Widget4", "Widget5"),
            ),
        ):
            with self.subTest(layout=data["geomManager"]):
                page = run_generated(flet_generator.emit_program(data, order, ROOT))
                self.assertEqual(len(page.controls), 1)

    @unittest.skipUnless(FLET_AVAILABLE, "flet is not installed")
    def test_unsupported_widget_types_still_build(self):
        data = project(
            widgets=(
                widget("Widget1", "ttk::treeview", place={"x": "0", "y": "0"}),
                widget("Widget2", "canvas", place={"x": "0", "y": "40"}),
                widget("Widget3", "listbox", place={"x": "0", "y": "80"}),
                widget("Widget4", "text", place={"x": "0", "y": "120"}),
                widget("Widget5", "ttk::scrollbar", place={"x": "200", "y": "0"}),
            )
        )

        source = flet_generator.emit_program(
            data, widget_names(*[f"Widget{index}" for index in range(1, 6)]), ROOT
        )
        page = run_generated(source)

        self.assertEqual(len(page.controls), 1)
        self.assertIn("placeholder", source)


if __name__ == "__main__":
    unittest.main()
