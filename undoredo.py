"""
undoredo.py  –  Command-pattern undo/redo stack for PyTkQuickGui
================================================================

Every user action that changes the canvas is wrapped in a Command subclass.
Commands are pushed onto an UndoStack; Ctrl+Z pops and reverses them,
Ctrl+Y (or Ctrl+Shift+Z) re-applies them.

Public API
----------
    stack = UndoStack(max_depth=100)

    stack.push(cmd)          # execute + remember
    stack.undo()             # undo last action
    stack.redo()             # redo last undone action
    stack.clear()            # wipe both stacks (e.g. on project load)
    stack.can_undo -> bool
    stack.can_redo -> bool
    stack.describe() -> str  # human-readable top of undo stack

Command classes (all importable from this module)
--------------------------------------------------
    MoveCommand(cw_obj, old_x, old_y, old_w, old_h,
                         new_x, new_y, new_w, new_h)
    ResizeCommand          – alias, same signature as MoveCommand
    CreateCommand(cw_obj, widget_snapshot)
    DeleteCommand(parent_widget, widget_snapshot,
                  name_list_entry, geom_mgr)
    EditAttributeCommand(widget, key, old_val, new_val)
    ReparentCommand(cw_obj, old_parent_name, new_parent_name)
    GroupCommand(group_name, member_names)
    UngroupCommand(group_name, member_names)
    MoveManyCommand(moves)   – list of (cw_obj, ox,oy,ow,oh, nx,ny,nw,nh)

Internal helpers
----------------
    snapshot_widget(widgetName)  -> dict   (calls myVars.saveWidgetAsDict)
    restore_widget(snapshot)              (re-creates & places a widget)
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import Any

# import ttkbootstrap as tboot

log = logging.getLogger("mylogger")

# pytkguivars and createWidget are imported lazily (inside functions) to avoid
# a circular-import deadlock:  createWidget → undoredo → createWidget.
# pylint: disable=import-outside-toplevel


# ---------------------------------------------------------------------------
# Snapshot / restore helpers
# ---------------------------------------------------------------------------


def snapshot_widget(widgetName: str) -> dict:
    """Return a complete serialisable snapshot of *widgetName*.

    Uses the existing myVars.saveWidgetAsDict() machinery so the snapshot
    format is identical to what gets saved to the project JSON.
    """
    import pytkguivars as myVars  # local import to avoid circular deps

    snap = myVars.saveWidgetAsDict(widgetName)
    # saveWidgetAsDict returns  {widgetName: {...data...}}
    # Unwrap to  {widgetName: widgetName, data: {...}}  so we can recover the name.
    return {"widgetName": widgetName, "data": snap}


def restore_widget(snapshot: dict, mainFrame) -> Any | None:
    """Re-create a widget from a *snapshot* produced by snapshot_widget().

    Returns the new createWidget object, or None on failure.
    """
    import createWidget as cw
    import pytkguivars as myVars

    widgetName = snapshot.get("widgetName")
    data = snapshot.get("data", {})
    wDict = data.get(widgetName, data)  # handle both wrapped and bare forms

    if not wDict:
        log.error("restore_widget: empty snapshot for %s", widgetName)
        return None

    # Parse the numeric id from the name so buildAWidget gets the right key prefix
    try:
        wId = int(widgetName.replace("Widget", ""))
    except ValueError:
        wId = cw.createWidget.widgetId

    widgetDef = myVars.buildAWidget(wId, wDict)
    if not widgetDef:
        log.error("restore_widget: buildAWidget returned empty for %s", widgetName)
        return None

    try:
        widget = eval(widgetDef)  # noqa: S307
    except Exception as e:
        log.error("restore_widget: eval failed for %s: %s", widgetName, e)
        return None

    w = cw.createWidget(mainFrame, widget)

    mgr = myVars.geomManager
    if mgr == "Place":
        place = wDict.get("Place") or {}
        if place:
            w.addPlace(place)
    elif mgr == "Grid":
        gd = wDict.get("GeomData") or {}
        widget.grid(
            row=int(gd.get("row", 0)),
            column=int(gd.get("column", 0)),
            sticky=gd.get("sticky", "WE"),
            padx=int(gd.get("padx", 2)),
            pady=int(gd.get("pady", 2)),
        )
    elif mgr == "Pack":
        gd = wDict.get("GeomData") or {}
        widget.pack(
            side=gd.get("side", "top"),
            fill=gd.get("fill", "none"),
            expand=int(gd.get("expand", 0)),
            padx=int(gd.get("padx", 4)),
            pady=int(gd.get("pady", 4)),
        )

    # Restore parent relationship
    parentName = wDict.get("WidgetParent", "")
    if parentName and parentName != myVars.rootWidgetName:
        try:
            parentNl = cw.findPythonWidgetNameList(parentName)
            if parentNl:
                parentWidget = parentNl[cw.WIDGET]
                cw.changeParentOfTo(widget, parentWidget)
        except Exception as e:
            log.warning(
                "restore_widget: could not restore parent %s: %s", parentName, e
            )

    log.info("restore_widget: restored %s", widgetName)
    return w


# ---------------------------------------------------------------------------
# Base Command
# ---------------------------------------------------------------------------


class Command:
    """Abstract base for all undoable actions."""

    description: str = "action"

    def execute(self) -> None:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.description}>"


# ---------------------------------------------------------------------------
# Move / Resize  (same data, different label)
# ---------------------------------------------------------------------------


class MoveCommand(Command):
    """Record a widget position/size change (move or resize)."""

    def __init__(self, cw_obj, ox, oy, ow, oh, nx, ny, nw, nh):
        self.cw_obj = cw_obj
        self.old = (int(ox), int(oy), int(ow), int(oh))
        self.new = (int(nx), int(ny), int(nw), int(nh))
        self.description = f"move {cw_obj.pythonName}"

    def _apply(self, x, y, w, h):
        import pytkguivars as myVars

        mgr = myVars.geomManager
        obj = self.cw_obj
        obj.x, obj.y, obj.width, obj.height = x, y, w, h
        if mgr == "Place":
            obj.widget.place(x=x, y=y, width=w, height=h)
        elif mgr == "Grid":
            obj.widget.grid(row=obj.row, column=obj.col, padx=2, pady=2, sticky="WE")
        elif mgr == "Pack":
            obj.widget.pack(padx=4, pady=4, anchor="nw")

    def execute(self):
        self._apply(*self.new)

    def undo(self):
        self._apply(*self.old)


ResizeCommand = MoveCommand  # same data, semantic alias


# ---------------------------------------------------------------------------
# Move many (group move)
# ---------------------------------------------------------------------------


class MoveManyCommand(Command):
    """Move multiple widgets in one undoable step (group move)."""

    def __init__(self, moves: list[tuple]):
        """moves: list of (cw_obj, ox, oy, ow, oh, nx, ny, nw, nh)"""
        self._cmds = [MoveCommand(*m) for m in moves]
        n = len(moves)
        self.description = f"move {n} widget{'s' if n != 1 else ''}"

    def execute(self):
        for c in self._cmds:
            c.execute()

    def undo(self):
        for c in reversed(self._cmds):
            c.undo()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class CreateCommand(Command):
    """Record the creation of a new widget."""

    def __init__(self, cw_obj, main_frame):
        self.pythonName = cw_obj.pythonName
        self.main_frame = main_frame
        self.snapshot = snapshot_widget(cw_obj.pythonName)
        self.description = f"create {cw_obj.widget.widgetName} ({self.pythonName})"

    def execute(self):
        # Already done by the normal creation path; nothing to repeat.
        pass

    def undo(self):
        import createWidget as cw

        nl = cw.findPythonWidgetNameList(self.pythonName)
        if nl:
            widget = nl[cw.WIDGET]
            cw.deleteWidgetFromLists(self.pythonName, widget)
            widget.destroy()
            log.info("CreateCommand.undo: destroyed %s", self.pythonName)
        else:
            log.warning("CreateCommand.undo: %s not found", self.pythonName)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class DeleteCommand(Command):
    """Record the deletion of a widget (so it can be restored)."""

    def __init__(self, cw_obj, main_frame):
        self.pythonName = cw_obj.pythonName
        self.main_frame = main_frame
        # Take a full snapshot BEFORE the delete happens
        self.snapshot = snapshot_widget(cw_obj.pythonName)
        # Also save the name-list entry for parent/children info
        import createWidget as cw

        nl = cw.findPythonWidgetNameList(self.pythonName)
        self.nl_copy = list(nl) if nl else []
        self.description = f"delete {self.pythonName}"

    def execute(self):
        import createWidget as cw

        nl = cw.findPythonWidgetNameList(self.pythonName)
        if nl:
            widget = nl[cw.WIDGET]
            cw.deleteWidgetFromLists(self.pythonName, widget)
            widget.destroy()

    def undo(self):
        restore_widget(self.snapshot, self.main_frame)
        log.info("DeleteCommand.undo: restored %s", self.pythonName)


# ---------------------------------------------------------------------------
# Edit attribute
# ---------------------------------------------------------------------------


class EditAttributeCommand(Command):
    """Record a single attribute change on a widget."""

    def __init__(self, widget, key: str, old_val: str, new_val: str):
        self.widget = widget
        self.key = key
        self.old_val = old_val
        self.new_val = new_val
        self.description = f"edit {key} on {getattr(widget, 'widgetName', str(widget))}"

    def _apply(self, val: str):
        if not val:
            return
        try:
            self.widget.configure(**{self.key: val})
        except tk.TclError as e:
            log.warning(
                "EditAttributeCommand: configure %s=%s failed: %s", self.key, val, e
            )

    def execute(self):
        self._apply(self.new_val)

    def undo(self):
        self._apply(self.old_val)


# ---------------------------------------------------------------------------
# Re-parent
# ---------------------------------------------------------------------------


class ReparentCommand(Command):
    """Record a widget being moved to a different parent container."""

    def __init__(self, cw_obj, old_parent_name: str, new_parent_name: str, main_frame):
        self.pythonName = cw_obj.pythonName
        self.old_parent = old_parent_name
        self.new_parent = new_parent_name
        self.main_frame = main_frame
        self.description = (
            f"reparent {self.pythonName} " f"{old_parent_name} → {new_parent_name}"
        )

    def _reparent_to(self, target_name: str):
        import createWidget as cw
        import pytkguivars as myVars

        nl = cw.findPythonWidgetNameList(self.pythonName)
        if not nl:
            log.warning("ReparentCommand: %s not found", self.pythonName)
            return
        widget = nl[cw.WIDGET]
        if target_name == myVars.rootWidgetName:
            parent_widget = self.main_frame
        else:
            pnl = cw.findPythonWidgetNameList(target_name)
            if not pnl:
                log.warning("ReparentCommand: parent %s not found", target_name)
                return
            parent_widget = pnl[cw.WIDGET]
        cw.changeParentOfTo(widget, parent_widget)

    def execute(self):
        self._reparent_to(self.new_parent)

    def undo(self):
        self._reparent_to(self.old_parent)


# ---------------------------------------------------------------------------
# Group / Ungroup
# ---------------------------------------------------------------------------


class GroupCommand(Command):
    """Create a named logical group from a list of widget names."""

    def __init__(self, group_name: str, member_names: list[str]):
        self.group_name = group_name
        self.member_names = list(member_names)
        self.description = f"group '{group_name}' ({len(member_names)} widgets)"

    def execute(self):
        import pytkguivars as myVars

        myVars.groups[self.group_name] = list(self.member_names)
        log.info(
            "GroupCommand: created group '%s' %s", self.group_name, self.member_names
        )

    def undo(self):
        import pytkguivars as myVars

        myVars.groups.pop(self.group_name, None)
        log.info("GroupCommand.undo: removed group '%s'", self.group_name)


class UngroupCommand(Command):
    """Dissolve a named logical group."""

    def __init__(self, group_name: str):
        import pytkguivars as myVars

        self.group_name = group_name
        self.member_names = list(myVars.groups.get(group_name, []))
        self.description = f"ungroup '{group_name}'"

    def execute(self):
        import pytkguivars as myVars

        myVars.groups.pop(self.group_name, None)

    def undo(self):
        import pytkguivars as myVars

        myVars.groups[self.group_name] = list(self.member_names)


# ---------------------------------------------------------------------------
# Compound command  (batch several commands into one undo step)
# ---------------------------------------------------------------------------


class CompoundCommand(Command):
    """Wrap several commands so they undo/redo as a single step."""

    def __init__(self, commands: list[Command], description: str = "compound"):
        self.commands = list(commands)
        self.description = description

    def execute(self):
        for c in self.commands:
            c.execute()

    def undo(self):
        for c in reversed(self.commands):
            c.undo()


# ---------------------------------------------------------------------------
# Undo Stack
# ---------------------------------------------------------------------------


class UndoStack:
    """Central undo/redo manager.

    Usage::

        from undoredo import UndoStack, MoveCommand
        stack = UndoStack()

        # Record a move (BEFORE applying it)
        cmd = MoveCommand(cw_obj, old_x, old_y, old_w, old_h,
                                   new_x, new_y, new_w, new_h)
        stack.push(cmd)   # calls cmd.execute() then stores it

    Keyboard bindings are set up externally (see pytkquickgui.py).
    """

    def __init__(self, max_depth: int = 100):
        self._undo: list[Command] = []
        self._redo: list[Command] = []
        self._max = max_depth
        # Optional callback: called after every undo/redo/push so the UI
        # can refresh status labels etc.
        self.on_change: Any = None

    # ------------------------------------------------------------------
    def push(self, cmd: Command) -> None:
        """Execute *cmd* and push it onto the undo stack."""
        cmd.execute()
        self._undo.append(cmd)
        if len(self._undo) > self._max:
            self._undo.pop(0)
        self._redo.clear()  # any new action wipes the redo stack
        log.debug("UndoStack.push: %s  (depth=%d)", cmd, len(self._undo))
        self._notify()

    def push_done(self, cmd: Command) -> None:
        """Push *cmd* without calling execute() — the action already happened.

        Use this when the action was performed by the normal interaction code
        and you just want to record it for undoing later.
        """
        self._undo.append(cmd)
        if len(self._undo) > self._max:
            self._undo.pop(0)
        self._redo.clear()
        log.debug("UndoStack.push_done: %s  (depth=%d)", cmd, len(self._undo))
        self._notify()

    def undo(self) -> None:
        if not self._undo:
            log.info("UndoStack.undo: nothing to undo")
            return
        cmd = self._undo.pop()
        log.info("UndoStack.undo: %s", cmd)
        try:
            cmd.undo()
        except Exception as e:
            log.error("UndoStack.undo: exception in %s: %s", cmd, e)
        self._redo.append(cmd)
        self._notify()

    def redo(self) -> None:
        if not self._redo:
            log.info("UndoStack.redo: nothing to redo")
            return
        cmd = self._redo.pop()
        log.info("UndoStack.redo: %s", cmd)
        try:
            cmd.execute()
        except Exception as e:
            log.error("UndoStack.redo: exception in %s: %s", cmd, e)
        self._undo.append(cmd)
        self._notify()

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._notify()

    # ------------------------------------------------------------------
    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def describe(self) -> str:
        """One-line summary of the top of each stack (for status bars)."""
        u = f"Undo: {self._undo[-1].description}" if self._undo else "Nothing to undo"
        r = f"Redo: {self._redo[-1].description}" if self._redo else ""
        return f"{u}   {r}".strip()

    def _notify(self):
        if callable(self.on_change):
            try:
                self.on_change()
            except Exception as e:
                log.warning("UndoStack.on_change callback raised: %s", e)


# ---------------------------------------------------------------------------
# Module-level singleton  (imported by createWidget and pytkquickgui)
# ---------------------------------------------------------------------------

stack = UndoStack(max_depth=100)
