import ast
import contextlib
import io
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
        self.assertIn("ft.Tab(label='Tab 1')", source)

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
        self.assertIn("Widget1 = ft.ListView(", source)
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

    def test_grid_absolute_mode_places_widgets_by_pixels(self):
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
                    geom={
                        "row": "0",
                        "column": "0",
                        "columnspan": "2",
                        "padx": "0",
                        "pady": "0",
                    },
                ),
                widget(
                    "Widget2",
                    "ttk::label",
                    attributes=(("text", "M"),),
                    geom={
                        "row": "1",
                        "column": "1",
                        "columnspan": "1",
                        "padx": "0",
                        "pady": "0",
                    },
                ),
                widget(
                    "Widget3",
                    "ttk::label",
                    attributes=(("text", "N"),),
                    geom={
                        "row": "2",
                        "column": "0",
                        "columnspan": "1",
                        "rowspan": "2",
                        "padx": "0",
                        "pady": "0",
                    },
                ),
            ),
        )

        source = flet_generator.emit_program(
            data,
            widget_names("Widget1", "Widget2", "Widget3"),
            ROOT,
            grid_mode="absolute",
        )

        ast.parse(source)
        self.assertIn("rootWidget = ft.Stack(", source)
        self.assertIn("left=0", source)
        self.assertIn("top=0", source)
        self.assertIn("width=20", source)  # two 10px columns
        start = source.index("Widget2 = ")
        end = source.index("Widget3 = ", start)
        widget2 = source[start:end]
        self.assertIn("left=10", widget2)
        self.assertIn("top=10", widget2)
        widget3 = source[source.index("Widget3 = "):]
        self.assertIn("height=20", widget3)  # rowspan of two rows
        self.assertNotIn("rowspan", source)

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
        self.assertIn("color='#000000'", source)          # ink on a light fill
        self.assertIn("bgcolor='#1a1b26'", source)        # outline keeps the surface
        self.assertIn("ft.BorderSide(1, '#c9aef9')", source)
        self.assertIn("bgcolor='#1f202d'", source)        # entry surface
        self.assertIn("border_color='#3f3f49'", source)   # theme border, not bootstyle
        self.assertIn("color='#c0caf5'", source)          # entry text

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
        self.assertEqual(ink("#b1d888"), "#000000")   # light fill -> black
        self.assertEqual(ink("#375a7f"), "#ffffff")   # dark fill -> white
        self.assertEqual(ink(""), "#c0caf5")          # falls back to theme fg

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

    def test_labelframe_caption_uses_the_theme_text_colour(self):
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
        self.assertIn("ft.Text(value='Group', color='#ffffff'", source)
        self.assertIn("ft.BorderSide(1, '#375a7f')", source)

    def test_report_names_the_theme(self):
        data = project(theme="darkly")
        report = flet_generator.compatibility_report(data, [ROOT], ROOT)
        self.assertIn("Theme   : darkly", report)
        report = flet_generator.compatibility_report(
            project(theme="nope"), [ROOT], ROOT
        )
        self.assertIn("no theme palette", report)

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
