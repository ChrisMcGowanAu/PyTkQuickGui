import unittest

import undoredo
from layout_model import GridGeometry


class FakeCreateWidget:
    pythonName = "Widget3"

    def __init__(self):
        self.applied = []

    def apply_grid_geometry(self, state):
        self.applied.append(state)


class GridMoveCommandTests(unittest.TestCase):
    def test_undo_and_redo_restore_complete_grid_state(self):
        widget = FakeCreateWidget()
        before = GridGeometry(parent="Widget1", row=2, column=3, sticky="ew")
        after = GridGeometry(
            parent="Widget2",
            row=5,
            column=6,
            columnspan=2,
            rowspan=3,
            sticky="nsew",
        )
        command = undoredo.GridMoveCommand(widget, before, after)

        command.execute()
        command.undo()

        self.assertEqual(widget.applied, [after, before])
        self.assertEqual(command.description, "reparent Widget3")


if __name__ == "__main__":
    unittest.main()
