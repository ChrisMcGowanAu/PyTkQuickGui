import logging as log
import random
import tkinter as tk
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
from typing import Any

import ttkbootstrap as ttk

import editWidget as ew
import project_format
import pytkguivars as myVars
import undoredo
from layout_model import GridGeometry

string1: Any
string2: Any
string3: Any

myVars.snapTo = 16
myVars.imageIndex = 0

# This is my enum type for list indicies
NAME: int = 0
PARENT: int = 1
WIDGET: int = 2
CHILDREN: int = 3


def leftMouseRelease(widget, event):
    log.warning(
        "Not Used? leftMouseRelease widget %s event %s", str(widget), str(event)
    )


class GridWidget:
    lastx = 0
    lasty = 0

    def __init__(self, root, widget, row, col):
        self.root = root
        self.widget = widget
        self.row = row
        self.col = col
        # self.pythonName is not defined (pylint)
        # if self.pythonName:
        #    self.widget.pythonName = self.pythonName
        self.widget.grid(row=self.row, column=self.col, sticky="WENS")

    def mouseEnter(self, event):
        log.debug(
            "Row %s Col %s Event Event %s", str(self.row), str(self.col), str(event)
        )


def snapToClosest(v: int) -> int:
    newV = int(v)
    remV = int(v) % int(myVars.snapTo)
    if remV < myVars.snapTo / 2:
        newV -= remV
    else:
        newV += myVars.snapTo - remV
    if newV < 0:
        newV = 0
    return newV


def findPythonWidgetNameFromWidget(widget) -> str:
    if str(widget) == str(createWidget.baseRoot):
        return myVars.rootWidgetName
    found: bool = False
    # [pythonName, parentName, widget, [children, ...]])
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    for nl in createWidget.widgetNameList:
        # print('Name', name, 'nl[0]', nl[NAME])
        if nl[WIDGET] == widget:
            return nl[NAME]
    if not found:
        log.error("Unable to locate widget ->%s<-", str(widget))
        log.error("createWidget.widgetNameList %s", str(createWidget.widgetNameList))
    return ""


def findPythonWidgetNameList(name: str) -> list:
    found = False
    # [pythonName, parentName, widget, [children, ...]])
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    for nl in createWidget.widgetNameList:
        # print('Name', name, 'nl[0]', nl[NAME])
        if nl[NAME] == name:
            found = True
            return nl
    if not found:
        log.error("Unable to locate pythonName ->%s<-", name)
        # log.error("createWidget.widgetNameList %s", str(createWidget.widgetNameList))
    return []


def reparentWidget(pythonName, w):
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    nl = findPythonWidgetNameList(pythonName)
    log.debug("w %s baseRoot %s", w, createWidget.baseRoot)

    # Remove this widget from its current parent's children list first.
    for nl1 in createWidget.widgetNameList:
        if pythonName in nl1[CHILDREN] and nl1[WIDGET] is not w:
            nl1[CHILDREN].remove(pythonName)

    if str(w) == str(createWidget.baseRoot):
        # Re-parenting back to the root canvas/frame
        if nl:
            nl[PARENT] = myVars.rootWidgetName
        return

    if nl:
        # Find the new parent in widgetNameList by widget object identity
        found = False
        for nl2 in createWidget.widgetNameList:
            if nl2[WIDGET] is w:
                new_parent_name = nl2[NAME]
                if pythonName not in nl2[CHILDREN]:
                    nl2[CHILDREN].append(pythonName)
                nl[PARENT] = new_parent_name
                found = True
                break
        if not found:
            # w is not a tracked widget (e.g. geomWidgetFrame itself) —
            # treat as root-level.
            log.debug(
                "reparentWidget: %s not in widgetNameList, treating as root", str(w)
            )
            nl[PARENT] = myVars.rootWidgetName


def deleteWidgetFromLists(pythonName, widget):
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    commands = []
    nl = findPythonWidgetNameList(pythonName)
    children = nl[CHILDREN]
    if children:
        for child in children:
            log.info("Deleting %s from %s children=%s", child, pythonName, children)
            childNl = findPythonWidgetNameList(child)
            if childNl:
                name = childNl[NAME]
                childWidget = childNl[WIDGET]
                commands.append([name, childWidget])
                # Dont call this here. The  deletes are saved for later
                # deleteWidgetFromLists(name, childWidget)
        for c in commands:
            deleteWidgetFromLists(c[0], c[1])

    parent = nl[PARENT]
    if parent != myVars.rootWidgetName:
        parentNl = findPythonWidgetNameList(parent)
        # Remove pythonName from the children
        parentNl[CHILDREN].remove(pythonName)
    log.info("Deleting %s and %s", str(nl), str(widget))
    try:
        createWidget.widgetList.remove(widget)
    except ValueError as e:
        log.warning("No Widget named ->%s<- %s", str(widget), e)
    try:
        createWidget.widgetNameList.remove(nl)
    except ValueError as e:
        log.warning("No Widget named ->%s<- %s", str(nl), e)


def _is_notebook_tab_type(widget):
    """Return True if *widget* is a Frame/LabelFrame — i.e. it should become a
    notebook tab via .add().  Buttons, Labels, Text widgets, etc. return False
    and should instead go *inside* the notebook's currently-selected tab frame."""
    wn = getattr(widget, "widgetName", "")
    return wn in ("ttk::frame", "ttk::labelframe", "frame", "labelframe")


def _notebook_selected_tab_frame(notebook):
    """Return the tk widget for the currently-selected tab of *notebook*, or
    None if the notebook has no tabs yet."""
    try:
        sel = notebook.select()  # returns Tk path string of selected tab
        if not sel:
            return None
        return notebook.nametowidget(sel)
    except tk.TclError:
        return None


def changeParentOfTo(widget, newParentWidget):
    """Re-parent *widget* into *newParentWidget* using the active geometry manager."""
    # ------------------------------------------------------------------
    # Notebook handling — two cases:
    #   1. widget IS a Frame/LabelFrame → add it as a new tab (.add())
    #   2. widget is any other type    → place it INSIDE the currently-
    #      selected tab frame, not as a new tab
    # ------------------------------------------------------------------
    parent_wn = getattr(newParentWidget, "widgetName", "")
    if parent_wn == "ttk::notebook":
        if _is_notebook_tab_type(widget):
            # Frame/LabelFrame: register as a tab page
            existing_tabs = list(newParentWidget.tabs())
            if str(widget) not in existing_tabs:
                try:
                    newParentWidget.add(widget, text="Tab")
                    log.info("changeParentOfTo: added %s as notebook tab", widget)
                except tk.TclError as _te:
                    log.warning("notebook.add: %s", _te)
            pythonName = findPythonWidgetNameFromWidget(widget)
            if pythonName:
                reparentWidget(pythonName, newParentWidget)
                # Lock drag/resize — tab frames are sized by the notebook
                cwo = findCreateWidgetObject(pythonName)
                if cwo is not None:
                    cwo.lock_as_tab_frame()
            widget.parent = newParentWidget
            newParentWidget.update()
            return
        else:
            # Non-frame widget: route into the currently-selected tab frame
            tab_frame = _notebook_selected_tab_frame(newParentWidget)
            if tab_frame is not None:
                log.info(
                    "changeParentOfTo: routing non-frame %s into tab frame %s",
                    widget,
                    tab_frame,
                )
                # Recurse with the tab frame as the real parent
                changeParentOfTo(widget, tab_frame)
                return
            else:
                log.warning(
                    "changeParentOfTo: notebook has no selected tab; "
                    "falling through to place %s in notebook directly",
                    widget,
                )

    mgr = myVars.geomManager
    if mgr == "Grid":
        py_name = findPythonWidgetNameFromWidget(widget)
        cwo = findCreateWidgetObject(py_name) if py_name else None
        if cwo is not None:
            state = cwo.capture_grid_geometry()
            parent_name = findPythonWidgetNameFromWidget(newParentWidget)
            if not parent_name:
                parent_name = myVars.rootWidgetName
            cwo.apply_grid_geometry(
                state.updated(parent=parent_name),
                parent_widget=newParentWidget,
            )
            return
        # Untracked helper widgets are uncommon; preserve their live settings.
        try:
            grid_info = widget.grid_info()
        except tk.TclError:
            grid_info = {}
        widget.grid(
            in_=newParentWidget,
            row=int(grid_info.get("row", 0)),
            column=int(grid_info.get("column", 0)),
            columnspan=max(1, int(grid_info.get("columnspan", 1))),
            rowspan=max(1, int(grid_info.get("rowspan", 1))),
            padx=int(grid_info.get("padx", 2)),
            pady=int(grid_info.get("pady", 2)),
            ipadx=int(grid_info.get("ipadx", 0)),
            ipady=int(grid_info.get("ipady", 0)),
            sticky=str(grid_info.get("sticky", "nsew")),
        )
    elif mgr == "Pack":
        widget.pack(in_=newParentWidget, padx=4, pady=4, anchor="nw")
    else:
        # Place mode (default)
        widget.place(in_=newParentWidget)
    pythonName = findPythonWidgetNameFromWidget(widget)
    if pythonName is None:
        return
    reparentWidget(pythonName, newParentWidget)
    widget.parent = newParentWidget
    tk.Misc.lift(widget, aboveThis=None)
    widget.update()
    newParentWidget.update()


def raiseChildren(pythonName):
    # [pythonName, parentName, widget, [children, ...]])
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    nl = findPythonWidgetNameList(pythonName)
    if nl:
        children = nl[CHILDREN]
        if children:
            for child in children:
                childNl = findPythonWidgetNameList(child)
                if childNl:
                    w = childNl[WIDGET]
                    try:
                        tk.Misc.lift(w, aboveThis=None)
                        log.debug("Widget ->%s<- Lifted", w)
                    except AttributeError as e:
                        log.error("Widget ->%s<- got Exception %s", w, str(e))
                    childName = childNl[NAME]
                    raiseChildren(childName)
    else:
        log.warning("Failed to find %s", pythonName)


# def findCreateWidgetObject(pythonName) -> createWidget:
def findCreateWidgetObject(pythonName):
    for obj in createWidget.widgetObjectList:
        if obj.pythonName == pythonName:
            return obj
    return None


class createWidget:
    # This just a list of widgets in the order they are created
    widgetList = []
    # A list of created objects
    widgetObjectList = []
    # Widget Name list will have child lists in the form
    # This just a list of widgets in the order they are created
    # [widgetName,  parentName ,  widget,  childList]
    widgetNameList = []
    widgetId = 0
    baseRoot = any
    lastCreated = None
    dragType = ["move", "dragEast", "dragWest", "dragNorth", "dragSouth"]

    @classmethod
    def _allocate_identity(cls, python_name: str | None = None) -> tuple[int, str]:
        """Allocate a new ID or reserve an exact persisted ``WidgetN`` name."""
        if python_name is None:
            widget_id = cls.widgetId
            cls.widgetId += 1
            return widget_id, "Widget" + str(widget_id)
        if not python_name.startswith("Widget") or not python_name[6:].isdigit():
            raise ValueError(f"invalid saved widget name: {python_name!r}")
        if any(nl[NAME] == python_name for nl in cls.widgetNameList):
            raise ValueError(f"duplicate saved widget name: {python_name}")
        widget_id = int(python_name[6:])
        cls.widgetId = max(cls.widgetId, widget_id + 1)
        return widget_id, python_name

    def __init__(self, root, widget, python_name: str | None = None):
        self.bordermode = None
        self.parentX = 0
        self.parentY = 0
        self.cornerX = 0
        self.cornerY = 0
        self.lastX = 0
        self.lastY = 0
        self.root = root
        self.widget = widget
        self.popup = any
        self.startX = 0
        self.startY = 0
        log.debug(self.widget.widgetName)
        #######################
        # Notebook is a funny case,  just 'raw' it does not display
        # if self.widget.widgetName == 'ttk::notebook':
        #    log.warning('Notebook is not yet done correctly')
        self.x = random.randint(50, 50)
        self.y = random.randint(50, 50)
        # log.debug(random.randint(3,  9))
        self.row = 4
        self.col = 4
        grid_defaults = myVars.gridDefaultsForWidget(self.widget.widgetName)
        self.columnspan = grid_defaults["columnspan"]
        self.rowspan = grid_defaults["rowspan"]
        self.sticky = grid_defaults["sticky"]
        self.padx = grid_defaults["padx"]
        self.pady = grid_defaults["pady"]
        self.ipadx = grid_defaults["ipadx"]
        self.ipady = grid_defaults["ipady"]
        # Pack geometry fields — authoritative user-set values
        self.pack_side = "top"  # pack side
        self.pack_fill = "none"  # pack fill
        self.pack_expand = 0  # pack expand (0 or 1)
        self.pack_padx = 4  # pack padx
        self.pack_pady = 4  # pack pady
        self.pack_anchor = "center"  # pack anchor
        self.x_root = self.x
        self.y_root = self.y
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
        self._pre_drag = (self.x, self.y, 0, 0)  # set properly in leftMouseDown
        self._last_drag_type = ""  # set in leftMouseRelease
        self._span_drag_origin = (
            self.col,
            self.row,
            self.columnspan,
            self.rowspan,
            self.x,
            self.y,
            0,
            0,
        )

        log.debug(self.widget.widgetName)
        self.widgetId, self.pythonName = createWidget._allocate_identity(python_name)
        # Stamp pythonName onto the tk widget itself so editWidget.py can
        # look up the createWidget object via findCreateWidgetObject().
        self.widget.pythonName = self.pythonName
        log.debug("Widget ID %s", str(self.widgetId))
        createWidget.widgetList.append(self.widget)
        createWidget.widgetNameList.append(
            [self.pythonName, myVars.rootWidgetName, self.widget, []]
        )
        #  K_UP,  K_DOWN,  K_LEFT,  and K_RIGHT
        self.widget.bind("<Button-3>", self.rightMouseDown)
        self.widget.bind("<Button-1>", self.leftMouseDown)
        self.widget.bind("<B1-Motion>", self.leftMouseDrag)
        self.widget.bind("<ButtonRelease-1>", self.leftMouseRelease)
        if myVars.geomManager == "Grid":
            self.widget.grid(
                row=self.row,
                column=self.col,
                columnspan=self.columnspan,
                rowspan=self.rowspan,
                padx=self.padx,
                pady=self.pady,
                ipadx=self.ipadx,
                ipady=self.ipady,
                sticky=self.sticky,
            )
        elif myVars.geomManager == "Place":
            self.widget.place(x=self.x, y=self.y)
        elif myVars.geomManager == "Pack":
            self.widget.pack(
                side=self.pack_side,
                fill=self.pack_fill,
                expand=self.pack_expand,
                padx=self.pack_padx,
                pady=self.pack_pady,
                anchor=self.pack_anchor,
            )
        else:
            log.error("Geometry Manager %s is TBD", myVars.geomManager)

        self.widget.update()
        self.width = self.widget.winfo_width()
        self.height = self.widget.winfo_height()
        if myVars.geomManager == "Place":
            # The second place is needed after the 'update()'
            self.widget.place(x=self.x, y=self.y, width=self.width, height=self.height)
        log.debug(
            "New %s WidgetId %d Width %d Height %d",
            self.widget.widgetName,
            self.widgetId,
            self.width,
            self.height,
        )
        createWidget.lastCreated = self
        createWidget.widgetObjectList.append(self)
        # Mark project as having unsaved changes
        myVars.projectSaved = False
        # Record creation for undo (push_done: the widget is already on screen)
        undoredo.stack.push_done(undoredo.CreateCommand(self, self.root))

    def setRoot(self, root):
        createWidget.baseRoot = root

    def _design_root(self):
        """Return the root geometry container used by designer widgets."""
        root = createWidget.baseRoot
        if root is any or root is None:
            return self.root
        return root

    def grid_parent_name(self) -> str:
        nl = findPythonWidgetNameList(self.pythonName)
        if nl and nl[PARENT]:
            return nl[PARENT]
        return myVars.rootWidgetName

    def grid_parent_widget(self):
        parent_name = self.grid_parent_name()
        if parent_name != myVars.rootWidgetName:
            parent_nl = findPythonWidgetNameList(parent_name)
            if parent_nl:
                return parent_nl[WIDGET]
        return self._design_root()

    def capture_grid_geometry(self) -> GridGeometry:
        """Return the authoritative Grid geometry for this widget."""
        return GridGeometry(
            parent=self.grid_parent_name(),
            row=max(0, int(self.row)),
            column=max(0, int(self.col)),
            columnspan=max(1, int(self.columnspan)),
            rowspan=max(1, int(self.rowspan)),
            sticky=str(self.sticky),
            padx=max(0, int(self.padx)),
            pady=max(0, int(self.pady)),
            ipadx=max(0, int(self.ipadx)),
            ipady=max(0, int(self.ipady)),
        )

    @staticmethod
    def _configure_grid_extent(parent_widget, state: GridGeometry) -> None:
        """Ensure newly addressed cells have useful size and resize weight."""
        is_root_grid = parent_widget is createWidget.baseRoot
        column_minsize = myVars.gridColMinsize if is_root_grid else 40
        row_minsize = myVars.gridRowMinsize if is_root_grid else 24
        column_pad = myVars.gridColPad if is_root_grid else 0
        row_pad = myVars.gridRowPad if is_root_grid else 0
        try:
            for col in range(state.column, state.column + state.columnspan):
                info = parent_widget.columnconfigure(col)
                minsize = str(info.get("minsize", "0"))
                if minsize in ("", "0", "0.0"):
                    parent_widget.columnconfigure(
                        col,
                        weight=1,
                        minsize=column_minsize,
                        pad=column_pad,
                    )
            for row in range(state.row, state.row + state.rowspan):
                info = parent_widget.rowconfigure(row)
                minsize = str(info.get("minsize", "0"))
                if minsize in ("", "0", "0.0"):
                    parent_widget.rowconfigure(
                        row,
                        weight=1,
                        minsize=row_minsize,
                        pad=row_pad,
                    )
        except (tk.TclError, TypeError, ValueError):
            # Notebook tab frames and a few ttkbootstrap helper widgets do not
            # expose a configurable grid.  The grid() call below will report a
            # useful error if the target genuinely cannot manage the widget.
            pass

    def apply_grid_geometry(
        self,
        state: GridGeometry,
        parent_widget=None,
        update_hierarchy: bool = True,
    ) -> None:
        """Apply one complete Grid state and keep every representation in sync."""
        if not isinstance(state, GridGeometry):
            raise TypeError("state must be a GridGeometry")

        if parent_widget is None:
            if state.parent != myVars.rootWidgetName:
                parent_nl = findPythonWidgetNameList(state.parent)
                parent_widget = parent_nl[WIDGET] if parent_nl else None
            if parent_widget is None:
                parent_widget = self._design_root()

        self.row = state.row
        self.col = state.column
        self.columnspan = state.columnspan
        self.rowspan = state.rowspan
        self.sticky = state.sticky
        self.padx = state.padx
        self.pady = state.pady
        self.ipadx = state.ipadx
        self.ipady = state.ipady

        try:
            self.widget.place_forget()
        except tk.TclError:
            pass
        self._configure_grid_extent(parent_widget, state)
        self.widget.grid(
            in_=parent_widget,
            row=state.row,
            column=state.column,
            columnspan=state.columnspan,
            rowspan=state.rowspan,
            padx=state.padx,
            pady=state.pady,
            ipadx=state.ipadx,
            ipady=state.ipady,
            sticky=state.sticky,
        )
        if update_hierarchy:
            reparentWidget(self.pythonName, parent_widget)
        self.widget.parent = parent_widget
        try:
            tk.Misc.lift(self.widget, aboveThis=None)
            parent_widget.update_idletasks()
        except tk.TclError:
            pass

    def _is_descendant_name(self, candidate_name: str) -> bool:
        """Return True when *candidate_name* is below this widget in the tree."""
        current = candidate_name
        visited: set[str] = set()
        while current and current != myVars.rootWidgetName and current not in visited:
            if current == self.pythonName:
                return True
            visited.add(current)
            nl = findPythonWidgetNameList(current)
            if not nl:
                break
            current = nl[PARENT]
        return False

    def _find_grid_container_at(self, x_root: int, y_root: int):
        """Return the smallest valid container containing a screen position."""
        best = None
        best_area = float("inf")
        for nl in createWidget.widgetNameList:
            candidate_name = nl[NAME]
            candidate = nl[WIDGET]
            if candidate is self.widget or self._is_descendant_name(candidate_name):
                continue
            if not hasattr(candidate, "widgetName"):
                continue
            widget_name = myVars.fixWidgetName(candidate.widgetName).lower()
            if widget_name not in ("frame", "labelframe", "panedwindow"):
                continue
            try:
                rx = candidate.winfo_rootx()
                ry = candidate.winfo_rooty()
                width = candidate.winfo_width()
                height = candidate.winfo_height()
            except tk.TclError:
                continue
            if width < 4 or height < 4:
                continue
            if rx <= x_root <= rx + width and ry <= y_root <= ry + height:
                area = width * height
                if area < best_area:
                    best = candidate
                    best_area = area
        return best

    @staticmethod
    def _grid_location(parent_widget, x_root: int, y_root: int) -> tuple[int, int]:
        """Convert screen coordinates to a non-negative cell in *parent_widget*."""
        local_x = max(0, int(x_root) - parent_widget.winfo_rootx())
        local_y = max(0, int(y_root) - parent_widget.winfo_rooty())
        try:
            col, row = parent_widget.grid_location(local_x, local_y)
        except tk.TclError:
            col = local_x // 60
            row = local_y // 30
        return max(0, int(col)), max(0, int(row))

    def lock_as_tab_frame(self):
        """Called when this widget has been added to a notebook as a tab frame.
        Unbinds drag/resize mouse events so the user cannot accidentally move
        or resize the frame (it is sized and positioned by the notebook).
        Right-click (edit popup) is kept so the tab can still be configured."""
        self.widget.unbind("<Button-1>")
        self.widget.unbind("<B1-Motion>")
        self.widget.unbind("<ButtonRelease-1>")
        log.info("lock_as_tab_frame: %s mouse drag disabled", self.pythonName)

    def unlock_as_tab_frame(self):
        """Restore normal drag/resize bindings (e.g. if tab frame is later
        removed from the notebook and reparented elsewhere)."""
        self.widget.bind("<Button-1>", self.leftMouseDown)
        self.widget.bind("<B1-Motion>", self.leftMouseDrag)
        self.widget.bind("<ButtonRelease-1>", self.leftMouseRelease)
        log.info("unlock_as_tab_frame: %s mouse drag restored", self.pythonName)

    def addPlace(self, placeDict):
        log.debug(placeDict)
        self.x = int(placeDict.get("x"))
        self.y = int(placeDict.get("y"))
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
        width = placeDict.get("width")
        height = placeDict.get("height")
        if width == "" or height == "":
            self.widget.place(x=self.x, y=self.y)
        else:
            self.width = int(width)
            self.height = int(height)
            self.widget.place(x=self.x, y=self.y, width=self.width, height=self.height)

    def editPlacePopup(self):
        popup = ew.widgetEditPopup(self.root, self.widget, self.pythonName)
        popup.createLayoutPopup()

    def editTtkPopup(self):
        popup = ew.widgetEditPopup(self.root, self.widget, self.pythonName)
        popup.createEditPopup()

    def findParentObject(self, parent):
        for w in createWidget.widgetList:
            if w is not None and w != self.widget:
                if w.widget == parent:
                    return w
        return None

    def findParentWidget(self, widget):
        parent = widget.place_info().get("in")
        log.debug("Parent %s self.root %s", str(parent), str(self.root))
        if self.root == parent:
            return parent
        else:
            for w in createWidget.widgetList:
                if w is not None and w != self.widget:
                    # wName = w.widgetName
                    if w == parent:
                        return w
        return self.root

    def _find_grid_container(self):
        """Return the smallest container sibling whose screen bbox encloses this
        widget's centre, or None if no container qualifies.

        Used by reParent() in Grid/Pack mode to auto-detect the target parent
        when the user clicks Re-Parent without specifying one explicitly.
        """
        cx = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        cy = self.widget.winfo_rooty() + self.widget.winfo_height() // 2
        return self._find_grid_container_at(cx, cy)

    def reParent(self, parentWidget):
        """Re-parent this widget.

        In Place mode the widget is auto-contained into whichever sibling it
        physically overlaps (pixel bounding-box test).
        In Grid/Pack mode we find the smallest container Frame/Labelframe whose
        screen bbox contains this widget's centre point; if none qualifies we
        re-parent back to the root frame.
        """
        # Record old parent name before reparenting
        nl = findPythonWidgetNameList(self.pythonName)
        old_parent_name = nl[PARENT] if nl else myVars.rootWidgetName

        if myVars.geomManager == "Grid":
            old_state = self.capture_grid_geometry()
            target = parentWidget or self._find_grid_container()
            if target is None:
                target = self._design_root()
            target_name = findPythonWidgetNameFromWidget(target)
            if not target_name:
                target_name = myVars.rootWidgetName
            col, row = self._grid_location(
                target,
                self.widget.winfo_rootx(),
                self.widget.winfo_rooty(),
            )
            new_state = old_state.updated(
                parent=target_name,
                row=row,
                column=col,
            )
            self.apply_grid_geometry(new_state, parent_widget=target)
            if new_state != old_state:
                undoredo.stack.push_done(
                    undoredo.GridMoveCommand(self, old_state, new_state)
                )
                myVars.projectSaved = False
            return

        if parentWidget is not None:
            # Caller supplied an explicit target — use it directly.
            changeParentOfTo(self.widget, parentWidget)
        elif myVars.geomManager == "Pack":
            # Auto-detect: find the innermost container that encloses this widget.
            target = self._find_grid_container()
            if target is not None:
                changeParentOfTo(self.widget, target)
                parentWidget = target
            else:
                # No container found — re-parent to geomWidgetFrame (root frame).
                # changeParentOfTo handles None → self.root case; pass root here.
                changeParentOfTo(self.widget, self.root)
                parentWidget = self.root
        else:
            changeParentOfTo(self.widget, self.root)
            parentWidget = self.root

        # Record undo
        nl2 = findPythonWidgetNameList(self.pythonName)
        new_parent_name = nl2[PARENT] if nl2 else myVars.rootWidgetName
        if old_parent_name != new_parent_name:
            undoredo.stack.push_done(
                undoredo.ReparentCommand(
                    self, old_parent_name, new_parent_name, self.root
                )
            )

        # Place mode only: also auto-contain into the first sibling that encloses us.
        if myVars.geomManager != "Place":
            return

        try:
            if not self.widget.winfo_exists():
                log.debug(
                    "reParent: %s no longer exists; request ignored",
                    self.pythonName,
                )
                return
            place = self.widget.place_info()
        except tk.TclError as exc:
            log.debug(
                "reParent: %s is no longer available (%s); request ignored",
                self.pythonName,
                exc,
            )
            return
        x_str = place.get("x")
        y_str = place.get("y")
        w_str = place.get("width")
        h_str = place.get("height")
        if None in (x_str, y_str, w_str, h_str):
            # Widget is not placed yet — nothing to auto-contain
            return
        try:
            x1 = int(x_str)
            y1 = int(y_str)
            w = int(w_str)
            h = int(h_str)
        except (ValueError, TypeError) as e:
            log.warning("reParent: could not parse place_info: %s", e)
            return
        x2 = x1 + w
        y2 = y1 + h
        name0 = self.widget.widgetName
        for sib in createWidget.widgetList:
            if sib is None or sib is self.widget:
                continue
            try:
                if not sib.winfo_exists():
                    log.debug("reParent: skipping destroyed sibling %s", sib)
                    continue
                sib_place = sib.place_info()
            except tk.TclError as exc:
                log.debug(
                    "reParent: skipping unavailable sibling %s (%s)",
                    sib,
                    exc,
                )
                continue
            wx_str = sib_place.get("x")
            wy_str = sib_place.get("y")
            if wx_str is None or wy_str is None:
                continue
            try:
                wx1 = int(wx_str)
                wy1 = int(wy_str)
                width = int(sib_place.get("width", 10))
                height = int(sib_place.get("height", 10))
            except (ValueError, TypeError) as e:
                log.error("reParent sibling parse error: %s", e)
                continue
            wx2 = wx1 + width
            wy2 = wy1 + height
            if x1 >= wx1 and y1 >= wy1 and x2 <= wx2 and y2 <= wy2:
                log.debug("Match Name %s fits inside %s", name0, sib.widgetName)
                changeParentOfTo(self.widget, sib)
                self.widget.place(x=x1 - wx1, y=y1 - wy1)

    def duplicate(self, offsetx, offsety, into_parent=None):
        """Clone this single widget.

        *into_parent* – if supplied, place/grid the duplicate into this tk widget
        instead of the original's saved parent.  Used by deepClone() so each
        duplicated child ends up inside the duplicated parent, not the original parent.

        Returns the new createWidget object.
        """
        # Loaded projects may contain non-contiguous IDs. ``pythonName`` is
        # corrected to the saved ID during load, while the historical numeric
        # ``widgetId`` field still reflects construction order.
        originalName = self.pythonName
        try:
            source_id = int(originalName.removeprefix("Widget"))
        except ValueError:
            source_id = self.widgetId
        origWidgetDict = myVars.saveWidgetAsDict(originalName)
        useDict = origWidgetDict[originalName]
        log.debug("duplicate useDict: %s", useDict)

        # Resolve the target parent BEFORE eval so we can inject it as
        # 'mainFrame' — buildAWidget always emits "WidgetType(mainFrame, ...)".
        if into_parent is not None:
            target_parent = into_parent
        else:
            widgetParent = useDict.get("WidgetParent", myVars.rootWidgetName)
            if myVars.rootWidgetName != widgetParent:
                nameDetails = findPythonWidgetNameList(widgetParent)
                target_parent = nameDetails[WIDGET] if nameDetails else self.root
            else:
                target_parent = self.root

        widgetDef = myVars.buildAWidget(source_id, useDict)
        log.debug("duplicate widgetDef %s", widgetDef)
        # Designer widgets share one Tk master and use the geometry manager's
        # in_= target for logical containment.  Keeping that invariant allows
        # a cloned child to be dragged back out of its current container.
        construction_parent = createWidget.baseRoot
        if construction_parent is any or construction_parent is None:
            construction_parent = self.root
        widget = eval(  # pylint: disable=eval-used
            widgetDef, globals(), {"mainFrame": construction_parent}
        )

        newW = createWidget(construction_parent, widget)
        project_format.remember_preserved_attributes(newW.widget, originalName, useDict)

        # Apply geometry appropriate to the current manager
        mgr = myVars.geomManager
        if mgr == "Place":
            place = useDict.get("Place", {})
            width = place.get("width", str(self.width))
            height = place.get("height", str(self.height))
            newW.widget.place(
                in_=target_parent,
                x=self.x + offsetx,
                y=self.y + offsety,
                width=width,
                height=height,
            )
            newW.x = self.x + offsetx
            newW.y = self.y + offsety
        elif mgr == "Grid":
            # Place the duplicate in the next available cell after this widget's cell
            new_col = max(0, self.col + offsetx)  # offsetx/y are cell offsets in Grid
            new_row = max(0, self.row + offsety)
            target_name = findPythonWidgetNameFromWidget(target_parent)
            if not target_name:
                target_name = myVars.rootWidgetName
            state = self.capture_grid_geometry().updated(
                parent=target_name,
                row=new_row,
                column=new_col,
            )
            newW.apply_grid_geometry(state, parent_widget=target_parent)
        else:
            # Pack or unknown — fall back to pack
            newW.widget.pack(in_=target_parent, padx=4, pady=4)

        # Sync widgetNameList so the clone's parent is recorded correctly
        reparentWidget(newW.pythonName, target_parent)
        return newW

    def _deepClone_recursive(self, new_parent_widget):
        """Internal helper: clone all CHILDREN of self into *new_parent_widget*,
        then recurse for grandchildren."""
        nl = findPythonWidgetNameList(self.pythonName)
        if not nl:
            return
        for child_name in nl[CHILDREN]:
            if not child_name:
                continue
            child_obj = findCreateWidgetObject(child_name)
            if child_obj is None:
                continue
            # Clone with cell offset 0 (same cell) so it lands inside the new parent
            new_child = child_obj.duplicate(0, 0, into_parent=new_parent_widget)
            # Recurse: duplicate the child's own children into the new child widget
            child_obj._deepClone_recursive(new_child.widget)

    def deepClone(self):
        """Clone this widget AND all its descendants, preserving the full tree.

        In Place mode the clone group is offset by 32px down.
        In Grid mode the duplicate is placed one row below the original.
        """
        # Determine offset so duplicate doesn't land on top of the original
        if myVars.geomManager == "Grid":
            offset = (0, 1)  # (col_offset, row_offset)
        else:
            offset = (0, 32)  # (x_offset, y_offset) in pixels

        newW = self.duplicate(offset[0], offset[1])  # duplicate the root widget
        # Recursively clone all children into the new root widget
        self._deepClone_recursive(newW.widget)
        return newW

    def deleteWidget(self):
        # Record deletion BEFORE destroying so snapshot can still be taken
        undoredo.stack.push_done(undoredo.DeleteCommand(self, self.root))
        deleteWidgetFromLists(self.pythonName, self.widget)
        self.widget.destroy()
        myVars.projectSaved = False

    def _highlight(self, on: bool):
        """Toggle a visual highlight to show multi-selection."""
        try:
            if on:
                self.widget.configure(relief="solid")
            else:
                self.widget.configure(relief="flat")
        except tk.TclError:
            pass  # widget may not support 'relief'

    def makePopup(self):
        # Add Menu
        self.popup = ttk.Menu(self.root, tearoff=0)

        # Adding Menu Items
        self.popup.add_command(label="Edit", command=self.editTtkPopup)
        self.popup.add_command(label="Layout", command=self.editPlacePopup)
        self.popup.add_command(label="Duplicate", command=lambda: self.duplicate(0, 0))
        self.popup.add_command(label="Clone", command=self.deepClone)
        self.popup.add_command(label="Re-Parent", command=lambda: self.reParent(None))
        self.popup.add_command(label="Delete", command=self.deleteWidget)
        self.popup.add_separator()
        # Multi-select / Group
        self.popup.add_command(label="Add to Selection", command=self._addToSelection)
        self.popup.add_command(label="Group Selected", command=self._groupFromPopup)
        self.popup.add_separator()
        self.popup.add_command(label="Close", command=self.popup.destroy)

    def _addToSelection(self):
        """Add this widget to the multi-selection."""
        if self.pythonName not in myVars.selectedWidgets:
            myVars.selectedWidgets.append(self.pythonName)
            self._highlight(True)
            log.info(
                "Added %s to selection: %s", self.pythonName, myVars.selectedWidgets
            )

    def _groupFromPopup(self):
        """Prompt for a group name and group all selected widgets."""
        sel = myVars.selectedWidgets
        if len(sel) < 2:
            mb.showinfo("Group", "Select two or more widgets first.")
            return
        name = sd.askstring(
            "Create Group",
            "Group name:",
            initialvalue=f"group{len(myVars.groups) + 1}",
        )
        if name:
            undoredo.stack.push(undoredo.GroupCommand(name, list(sel)))
            log.info("Grouped %s as '%s'", sel, name)

    def menuPopup(self, event):
        # display the popup menu
        try:
            self.popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            # Release the grab
            self.popup.grab_release()
            # self.widget.unbind("<Button-3>")

    def rightMouseDown(self, event):
        # popup a menu for the type of object
        log.debug(self.widget.widgetName)
        # log.debug(event)
        # log.debug(createWidget.widgetList[self.widgetId].widgetName)
        # self.widget.destroy()
        self.makePopup()
        self.menuPopup(event)

    def leftMouseInfo(self, widget, event):
        # Dump out widget geometry info and
        # recurse up the parent tree
        if str(widget) == "None":
            return
        log.info("-----------------")
        log.info("Widget Info -->%s<--", widget)
        width = widget.winfo_width()
        height = widget.winfo_height()
        rootx = widget.winfo_rootx()
        rooty = widget.winfo_rooty()
        placex = widget.place_info().get("x")
        placey = widget.place_info().get("y")
        p = widget.place_info().get("in")
        x = widget.winfo_x()
        y = widget.winfo_y()
        # g = widget.winfo_geometry()
        # p0 = widget.winfo_parent()
        ptrx = widget.winfo_pointerx()
        ptry = widget.winfo_pointery()
        log.info("event x,y %s,%s", event.x, event.y)
        log.info("pointer x,y %s,%s", ptrx, ptry)
        log.info("root x,y %s,%s", rootx, rooty)
        log.info("pos x,y %s,%s width %s height %s", x, y, width, height)
        log.info("place x,y %s %s", placex, placey)
        # log.info("geometry %s",str(g))
        log.info("widget %s parent %s", str(widget), str(p))
        if p != ".":
            self.leftMouseInfo(p, event)

    def leftMouseDown(self, event):
        # Call this if needed -- leave in for idiots like me
        # self.leftMouseInfo(self.widget,event)

        # Multi-select: Shift+click toggles this widget in selectedWidgets
        if event.state & 0x0001:  # Shift key held
            if self.pythonName in myVars.selectedWidgets:
                myVars.selectedWidgets.remove(self.pythonName)
                self._highlight(False)
            else:
                myVars.selectedWidgets.append(self.pythonName)
                self._highlight(True)
            return  # don't start a drag when Shift-clicking
        else:
            # Normal click: clear multi-selection and highlight only this widget
            for name in list(myVars.selectedWidgets):
                obj = findCreateWidgetObject(name)
                if obj:
                    obj._highlight(False)
            myVars.selectedWidgets.clear()

        self.startX = event.x
        self.startY = event.y
        self.dragType = ""
        self.parentX = int(0)
        self.parentY = int(0)

        self.startX = event.x + self.parentX
        self.startY = event.y + self.parentY

        x = self.widget.winfo_x() + event.x - self.startX
        y = self.widget.winfo_y() + event.y - self.startY
        self.x = x
        self.y = y

        # Is the stuff above all crap?
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        # Save pre-drag state so leftMouseRelease can record undo
        self._pre_drag = (self.x, self.y, width, height)
        if myVars.geomManager == "Grid":
            design_root = self._design_root()
            self._pre_grid_geometry = self.capture_grid_geometry()
            self._grid_drag_active = False
            self._grid_drag_origin_px = (
                self.widget.winfo_rootx() - design_root.winfo_rootx(),
                self.widget.winfo_rooty() - design_root.winfo_rooty(),
                width,
                height,
            )
        # This should be a configuration param
        jiffyW = 8
        jiffyH = 8
        if width < (jiffyW * 4):
            jiffyW = width / 4
        if height < (jiffyH * 4):
            jiffyH = height / 4
        self.x = self.widget.winfo_x()
        self.y = self.widget.winfo_y()
        # For Grid span-drags: remember anchor cell, original span, and
        # ACTUAL pixel position (captured after winfo_x/y update above)
        self._span_drag_origin = (
            self.col,
            self.row,
            self.columnspan,
            self.rowspan,
            self.x,
            self.y,
            width,
            height,
        )
        self.cornerY = self.y + height
        self.cornerX = self.x + width
        log.debug(
            "Left Mouse Down --  self.x %s self.y %s Width %s Height %s",
            str(self.x),
            str(self.y),
            str(width),
            str(height),
        )
        if event.x > (width - jiffyW):
            self.dragType = "dragEast"
            log.debug("Drag right Side")
        elif event.x < jiffyW:
            self.dragType = "dragWest"
            log.debug("Drag left Side")
        if event.y > (height - jiffyH):
            self.dragType = "dragSouth"
            log.debug("Drag bottom Side")
        elif event.y < jiffyH:
            self.dragType = "dragNorth"
            log.debug("Drag top Side")  # log.info(event)
        # Make sure any children are on top.
        try:
            parentType = self.widget.master.widgetName
            log.debug(
                "self.widget %s lift parent %s", str(self.widget), str(parentType)
            )
            if parentType == "canvas":
                log.debug("Trying tag_raise for %s", self.widget)
                # This should work. but is buggy :-(
                # self.widget.master.tag_raise(self.widget)
                tk.Misc.lift(self.widget, aboveThis=None)
            else:
                log.debug("Trying tk.Misc.liftc for %s", self.widget)
                tk.Misc.lift(self.widget, aboveThis=None)
        except tk.TclError as e:
            log.warning(
                "self.widget lift %s Failed with exception %s", str(self.widget), str(e)
            )
        raiseChildren(self.pythonName)
        log.debug(
            "Left Mouse Down --  self.x %s self.y %s Width %s Height %s self.dragType %s",
            str(self.x),
            str(self.y),
            str(width),
            str(height),
            self.dragType,
        )
        self.lastX = self.x
        self.lastY = self.y

    def leftMouseDrag(self, event):
        x0 = self.widget.winfo_x() - self.startX
        y0 = self.widget.winfo_y() - self.startY
        x = x0 + event.x
        y = y0 + event.y
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()

        deltaX = x - self.lastX
        deltaY = y - self.lastY

        # Grid mode: edge-drags resize the span; centre-drag moves the widget.
        if myVars.geomManager == "Grid":
            self._grid_drag_active = True
            design_root = self._design_root()
            origin_x, origin_y, origin_w, origin_h = getattr(
                self,
                "_grid_drag_origin_px",
                (
                    self.widget.winfo_rootx() - design_root.winfo_rootx(),
                    self.widget.winfo_rooty() - design_root.winfo_rooty(),
                    width,
                    height,
                ),
            )
            pointer_x = event.x_root - design_root.winfo_rootx()
            pointer_y = event.y_root - design_root.winfo_rooty()
            if self.dragType == "dragEast":
                new_x = origin_x
                new_y = origin_y
                new_w = max(16, pointer_x - origin_x)
                new_h = origin_h
            elif self.dragType == "dragSouth":
                new_x = origin_x
                new_y = origin_y
                new_w = origin_w
                new_h = max(16, pointer_y - origin_y)
            elif self.dragType == "dragWest":
                right_edge = origin_x + origin_w
                new_x = min(max(0, pointer_x), right_edge - 16)
                new_y = origin_y
                new_w = max(16, right_edge - new_x)
                new_h = origin_h
            elif self.dragType == "dragNorth":
                bottom_edge = origin_y + origin_h
                new_x = origin_x
                new_y = min(max(0, pointer_y), bottom_edge - 16)
                new_w = origin_w
                new_h = max(16, bottom_edge - new_y)
            else:
                # Float relative to the design root, not the logical parent.
                # This lets a widget cross container boundaries without its
                # coordinates jumping between unrelated grids.
                new_x = max(0, pointer_x - self.startX)
                new_y = max(0, pointer_y - self.startY)
                new_w = origin_w
                new_h = origin_h
            self.x = new_x
            self.y = new_y
            self.width = new_w
            self.height = new_h
            self.widget.place(
                in_=design_root,
                x=new_x,
                y=new_y,
                width=new_w,
                height=new_h,
            )
            self.lastX = x
            self.lastY = y
            return
        if myVars.geomManager == "Pack":
            # Float the widget visually so the user can see where it is going.
            # Actual pack order is updated on mouse-release.
            newX = self.widget.winfo_x() + int(deltaX)
            newY = self.widget.winfo_y() + int(deltaY)
            self.x = max(0, newX)
            self.y = max(0, newY)
            try:
                self.widget.pack_forget()
            except tk.TclError:
                pass
            self.widget.place(
                x=self.x,
                y=self.y,
                width=self.widget.winfo_width(),
                height=self.widget.winfo_height(),
            )
            self.lastX = x
            self.lastY = y
            return

        placex = self.widget.place_info().get("x", self.x)
        placey = self.widget.place_info().get("y", self.y)
        if placex is None:
            placex = self.x
        if placey is None:
            placey = self.y

        # Doing this correctly has done my head in. I think it now works ok
        if self.dragType == "dragEast":
            width = width + deltaX
            self.x = placex
            self.y = placey
        elif self.dragType == "dragSouth":
            height = height + deltaY
            self.x = placex
            self.y = placey
        elif self.dragType == "dragWest":
            width = width - deltaX
            self.x = int(placex) + int(deltaX)
            self.y = placey
        elif self.dragType == "dragNorth":
            height = height - deltaY
            self.x = placex
            self.y = int(placey) + int(deltaY)
        else:
            self.x = int(placex) + int(deltaX)
            self.y = int(placey) + int(deltaY)

        self.widget.place(x=self.x, y=self.y, width=width, height=height)
        log.debug(
            "self.dragType %s x = %s y = %s self.x %s y=self.y %s width %s height %s self.startX %s self.startY %s",
            self.dragType,
            x,
            y,
            self.x,
            self.y,
            width,
            height,
            self.startX,
            self.startY,
        )
        self.lastX = x
        self.lastY = y

    def leftMouseRelease(self, _event):
        # Capture pre-drag state (set in leftMouseDown)
        pre = getattr(self, "_pre_drag", (self.x, self.y, self.width, self.height))
        ox, oy, ow, oh = pre

        self._last_drag_type = self.dragType  # read before clearing
        self.dragType = ""
        if myVars.geomManager == "Grid":
            if not getattr(self, "_grid_drag_active", False):
                self.x, self.y, self.width, self.height = getattr(
                    self,
                    "_grid_drag_origin_px",
                    (self.x, self.y, self.width, self.height),
                )
            newX = int(self.x)
            newY = int(self.y)
            newWidth = int(self.width)
            newHeight = int(self.height)
        else:
            newX = snapToClosest(self.x)
            newY = snapToClosest(self.y)
            newWidth = snapToClosest(self.widget.winfo_width())
            newHeight = snapToClosest(self.widget.winfo_height())
        self.x = newX
        self.y = newY
        if newWidth < 16:
            newWidth = 16
        if newHeight < 16:
            newHeight = 16
        self.height = newHeight
        self.width = newWidth
        if myVars.geomManager == "Place":
            self.widget.place(x=self.x, y=self.y, height=self.height, width=self.width)
        elif myVars.geomManager == "Grid":
            drag_type = getattr(self, "_last_drag_type", "")
            drag_active = getattr(self, "_grid_drag_active", False)
            old_state = getattr(
                self, "_pre_grid_geometry", self.capture_grid_geometry()
            )
            design_root = self._design_root()
            root_x = design_root.winfo_rootx()
            root_y = design_root.winfo_rooty()
            left_root = root_x + self.x
            top_root = root_y + self.y
            right_root = left_root + max(1, self.width) - 1
            bottom_root = top_root + max(1, self.height) - 1

            # Resizing stays in the current parent. A centre drag may cross a
            # container boundary and is automatically re-parented on release.
            if drag_type or not drag_active:
                target = self.grid_parent_widget()
                target_name = old_state.parent
            else:
                centre_x = left_root + max(1, self.width) // 2
                centre_y = top_root + max(1, self.height) // 2
                target = self._find_grid_container_at(centre_x, centre_y)
                if target is None:
                    target = design_root
                target_name = findPythonWidgetNameFromWidget(target)
                if not target_name:
                    target_name = myVars.rootWidgetName

            start_col, start_row = self._grid_location(target, left_root, top_root)
            end_col, end_row = self._grid_location(target, right_root, bottom_root)

            if not drag_active:
                new_state = old_state
            elif drag_type == "dragEast":
                new_state = old_state.updated(
                    parent=target_name,
                    columnspan=max(1, end_col - old_state.column + 1),
                )
            elif drag_type == "dragSouth":
                new_state = old_state.updated(
                    parent=target_name,
                    rowspan=max(1, end_row - old_state.row + 1),
                )
            elif drag_type == "dragWest":
                right_col = old_state.column + old_state.columnspan - 1
                new_col = min(start_col, right_col)
                new_state = old_state.updated(
                    parent=target_name,
                    column=new_col,
                    columnspan=max(1, right_col - new_col + 1),
                )
            elif drag_type == "dragNorth":
                bottom_row = old_state.row + old_state.rowspan - 1
                new_row = min(start_row, bottom_row)
                new_state = old_state.updated(
                    parent=target_name,
                    row=new_row,
                    rowspan=max(1, bottom_row - new_row + 1),
                )
            else:
                new_state = old_state.updated(
                    parent=target_name,
                    row=start_row,
                    column=start_col,
                )

            self.apply_grid_geometry(new_state, parent_widget=target)
            log.debug(
                "Grid release %s: %s -> %s",
                self.pythonName,
                old_state,
                new_state,
            )
            if myVars.redrawGridLines is not None:
                self.widget.after_idle(myVars.redrawGridLines)
        elif myVars.geomManager == "Pack":
            # Remove the temporary place() used during drag, then re-insert
            # into pack order at the position nearest to the drop point.
            try:
                self.widget.place_forget()
            except tk.TclError:
                pass
            # Find the pack slave whose midpoint is closest to the drop Y
            # and insert before/after it accordingly.
            parent = self.root
            slaves = parent.pack_slaves()
            # Remove self from the slave list (it was pack_forgotten during drag)
            other_slaves = [s for s in slaves if s is not self.widget]
            insert_after = None  # None means insert at the front
            for sib in other_slaves:
                sib_mid = sib.winfo_y() + sib.winfo_height() // 2
                if self.y > sib_mid:
                    insert_after = sib
            try:
                if insert_after is None:
                    self.widget.pack(
                        side=self.pack_side,
                        fill=self.pack_fill,
                        expand=self.pack_expand,
                        padx=self.pack_padx,
                        pady=self.pack_pady,
                        anchor=self.pack_anchor,
                        before=other_slaves[0] if other_slaves else None,
                    )
                else:
                    self.widget.pack(
                        side=self.pack_side,
                        fill=self.pack_fill,
                        expand=self.pack_expand,
                        padx=self.pack_padx,
                        pady=self.pack_pady,
                        anchor=self.pack_anchor,
                        after=insert_after,
                    )
            except (tk.TclError, IndexError):
                self.widget.pack(
                    side=self.pack_side,
                    fill=self.pack_fill,
                    expand=self.pack_expand,
                    padx=self.pack_padx,
                    pady=self.pack_pady,
                    anchor=self.pack_anchor,
                )
        else:
            log.error("Geometry Manager %s is TBD", myVars.geomManager)
        raiseChildren(self.pythonName)

        # Record the move/resize as an undoable action.
        if myVars.geomManager == "Grid":
            if old_state != new_state:
                undoredo.stack.push_done(
                    undoredo.GridMoveCommand(self, old_state, new_state)
                )
                myVars.projectSaved = False
        else:
            nx, ny, nw, nh = self.x, self.y, self.width, self.height
            if (ox, oy, ow, oh) == (nx, ny, nw, nh):
                return
            undoredo.stack.push_done(
                undoredo.MoveCommand(self, ox, oy, ow, oh, nx, ny, nw, nh)
            )
            myVars.projectSaved = False
