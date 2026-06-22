import logging as log
import random
import tkinter as tk
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
from typing import Any

import ttkbootstrap as tboot

import editWidget as ew
import pytkguivars as myVars
import undoredo

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
    log.debug("w %s baseRoot %s",w,createWidget.baseRoot)
    if str(w) == str(createWidget.baseRoot):
        nl[PARENT] = myVars.rootWidgetName
        # remove pythonName out of any childen
        for nl1 in createWidget.widgetNameList:
            log.info("nl1 %s",nl1)
            if pythonName in nl1[CHILDREN]:
                nl1[CHILDREN].remove(pythonName)
        return
    if nl:
        # Replace the parent
        ParentName = ""
        found = False
        for nl2 in createWidget.widgetNameList:
            # print(nl)
            if nl2[WIDGET] == w:
                ParentName = nl2[NAME]
                # Check if the child is already there
                if pythonName not in nl2[CHILDREN]:
                    nl2[CHILDREN].append(pythonName)
                found = True
                break
        if not found:
            log.error("Unable to locate widget ->%s<-", str(w))
            # log.error("createWidget.widgetNameList %s", str(createWidget.widgetNameList))
        else:
            nl[PARENT] = ParentName


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
    createWidget.widgetList.remove(widget)
    createWidget.widgetNameList.remove(nl)


def changeParentOfTo(widget, newParentWidget):
    widget.place(in_=newParentWidget)
    pythonName = findPythonWidgetNameFromWidget(widget)
    if pythonName is None:
        return
    reparentWidget(pythonName, newParentWidget)
    widget.parent = newParentWidget
    # This might be the cause of the parent not clipping the child
    # .... need more info
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

    def __init__(self, root, widget):
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
        self.columnspan = 1   # number of grid columns this widget spans
        self.rowspan    = 1   # number of grid rows    this widget spans
        self.x_root = self.x
        self.y_root = self.y
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
        self._pre_drag = (self.x, self.y, 0, 0)        # set properly in leftMouseDown
        self._last_drag_type   = ""                     # set in leftMouseRelease
        self._span_drag_origin = (self.col, self.row,   # set in leftMouseDown
                                  self.columnspan, self.rowspan,
                                  self.x, self.y, 0, 0)

        log.debug(self.widget.widgetName)
        self.pythonName = "Widget" + str(createWidget.widgetId)
        log.debug("Widget ID %s", str(createWidget.widgetId))
        createWidget.widgetList.append(self.widget)
        createWidget.widgetNameList.append(
            [self.pythonName, myVars.rootWidgetName, self.widget, []]
        )
        self.widgetId = createWidget.widgetId
        createWidget.widgetId += 1
        #  K_UP,  K_DOWN,  K_LEFT,  and K_RIGHT
        self.widget.bind("<Button-3>", self.rightMouseDown)
        self.widget.bind("<Button-1>", self.leftMouseDown)
        self.widget.bind("<B1-Motion>", self.leftMouseDrag)
        self.widget.bind("<ButtonRelease-1>", self.leftMouseRelease)
        if myVars.geomManager == "Grid":
            self.widget.grid(row=self.row, column=self.col,
                             columnspan=self.columnspan, rowspan=self.rowspan,
                             padx=2, pady=2, sticky="WE")
        elif myVars.geomManager == "Place":
            self.widget.place(x=self.x, y=self.y)
        elif myVars.geomManager == "Pack":
            self.widget.pack(padx=4, pady=4, anchor="nw")
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
        # Record creation for undo (push_done: the widget is already on screen)
        undoredo.stack.push_done(
            undoredo.CreateCommand(self, self.root)
        )

    def setRoot(self, root):
        createWidget.baseRoot = root

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

    def findParentObject(self,parent):
        for w in createWidget.widgetList:
            if w is not None and w != self.widget:
                if w.widget == parent:
                    return w
        return None

    def findParentWidget(self,widget):
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

    def reParent(self, parentWidget):
        name0 = self.widget.widgetName
        place = self.widget.place_info()
        # Record old parent name before reparenting
        nl = findPythonWidgetNameList(self.pythonName)
        old_parent_name = nl[PARENT] if nl else myVars.rootWidgetName
        if parentWidget is not None:
            changeParentOfTo(self.widget, parentWidget)
        else:
            changeParentOfTo(self.widget, self.root)
            parentWidget = self.root
        # Determine new parent name after reparenting
        nl2 = findPythonWidgetNameList(self.pythonName)
        new_parent_name = nl2[PARENT] if nl2 else myVars.rootWidgetName
        if old_parent_name != new_parent_name:
            undoredo.stack.push_done(
                undoredo.ReparentCommand(
                    self, old_parent_name, new_parent_name, self.root
                )
            )
        x1 = int(place.get("x"))
        y1 = int(place.get("y"))
        w = int(place.get("width"))
        h = int(place.get("height"))
        x2 = x1 + w
        y2 = y1 + h
        for w in createWidget.widgetList:
            if w is not None and w != self.widget:
                name = w.widgetName
                place = w.place_info()
                wx1 = int(place.get("x"))
                wy1 = int(place.get("y"))
                try:
                    width = int(place.get("width"))
                    height = int(place.get("height"))
                except ValueError as e:
                    log.error(e)
                    width = 10
                    height = 10
                wx2 = wx1 + width
                wy2 = wy1 + height
                if x1 >= wx1 and y1 >= wy1 and x2 <= wx2 and y2 <= wy2:
                    log.debug("Match Name %s fits inside %s", name0, name)
                    newX = x1 - wx1
                    newY = y1 - wy1
                    changeParentOfTo(self.widget, w)
                    self.widget.place(x=newX, y=newY)

    def clone(self,offsetx,offsety):
        mainFrame = self.root
        mainCanvas = self.root
        # widgetId = createWidget.widgetId
        useDict: dict = {}
        origWidgetDict: dict = {}
        originalName = "Widget" + str(self.widgetId)
        origWidgetDict = myVars.saveWidgetAsDict(originalName)
        log.debug("origWidgetDict: %s", origWidgetDict)
        # useDict = origWidgetDict.get(originalName)
        useDict = origWidgetDict[originalName]
        log.debug(
            "mainFrame %s mainCanvas %s useDict %s",
            str(mainFrame),
            str(mainCanvas),
            useDict,
        )
        widgetDef = myVars.buildAWidget(self.widgetId, useDict)
        log.debug("widgetDef %s", widgetDef)
        # widget = ast.literal_eval(widgetDef)
        widget = eval(widgetDef)
        place: dict = {}
        place = useDict["Place"]
        widgetParent = useDict["WidgetParent"]
        width = place.get("width")
        height = place.get("height")
        newW = createWidget(mainCanvas, widget)
        # newW : createWidget
        # newW = createWidget.lastCreated
        if myVars.rootWidgetName != widgetParent:
            nameDetails = findPythonWidgetNameList(widgetParent)
            log.info("widgetParent: %s", widgetParent)
            log.info("nameDetails: %s", nameDetails)
            try:
                w = nameDetails[WIDGET]
                changeParentOfTo(newW.widget, w)
            except tk.TclError as e:
                log.error("self.widget ->%s<- nameDetails ->%s<-",self.widget, str(nameDetails[WIDGET]))
                log.error("Exception %s", str(e))
        newW.widget.place(x=self.x + offsetx, y=self.y + offsety, width=width, height=height)
        return newW

    def deepClone(self):
        newW = self.clone(0,32) # The main widget
        # clonedParent = "Widget" + str(self.widgetId)
        # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
        for w in createWidget.widgetNameList:
            log.info("w %s self %s",str(w[NAME]),str(self.pythonName))
            if  self.pythonName == w[NAME]:
                children = w[CHILDREN]
                for c in children:
                    log.info("child %s",str(c))
                    if c:
                        obj = findCreateWidgetObject(c)
                        if obj is not None:
                            newObj = obj.clone(0,0)
                            changeParentOfTo(newObj.widget, newW.widget)


        # Like cone bt create clild widgets of self

    def deleteWidget(self):
        # Record deletion BEFORE destroying so snapshot can still be taken
        undoredo.stack.push_done(
            undoredo.DeleteCommand(self, self.root)
        )
        deleteWidgetFromLists(self.pythonName, self.widget)
        self.widget.destroy()

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
        self.popup = tboot.Menu(self.root, tearoff=0)

        # Adding Menu Items
        self.popup.add_command(label="Edit", command=self.editTtkPopup)
        self.popup.add_command(label="Layout", command=self.editPlacePopup)
        self.popup.add_command(label="Clone", command=lambda: self.clone(0,0))
        self.popup.add_command(label="DeepClone", command=self.deepClone)
        self.popup.add_command(label="Re-Parent", command=lambda: self.reParent(None))
        self.popup.add_command(label="Delete", command=self.deleteWidget)
        self.popup.add_separator()
        # Multi-select / Group
        self.popup.add_command(
            label="Add to Selection",
            command=self._addToSelection
        )
        self.popup.add_command(
            label="Group Selected",
            command=self._groupFromPopup
        )
        self.popup.add_separator()
        self.popup.add_command(label="Close", command=self.popup.destroy)

    def _addToSelection(self):
        """Add this widget to the multi-selection."""
        if self.pythonName not in myVars.selectedWidgets:
            myVars.selectedWidgets.append(self.pythonName)
            self._highlight(True)
            log.info("Added %s to selection: %s", self.pythonName, myVars.selectedWidgets)

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
        log.info("Widget Info -->%s<--",widget)
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
        log.info("event x,y %s,%s",event.x,event.y)
        log.info("pointer x,y %s,%s",ptrx,ptry)
        log.info("root x,y %s,%s",rootx,rooty)
        log.info("pos x,y %s,%s width %s height %s",x,y,width,height)
        log.info("place x,y %s %s",placex,placey)
        # log.info("geometry %s",str(g))
        log.info("widget %s parent %s",str(widget),str(p))
        if p != ".":
            self.leftMouseInfo(p,event)

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
        # For Grid span-drags: remember the anchor cell and original span
        self._span_drag_origin = (
            self.col, self.row,
            self.columnspan, self.rowspan,
            self.x, self.y, width, height,
        )
        # This should be a configuration param
        jiffyW = 8
        jiffyH = 8
        if width < (jiffyW * 4):
            jiffyW = width/4
        if height < (jiffyH * 4):
            jiffyH = height/4
        self.x = self.widget.winfo_x()
        self.y = self.widget.winfo_y()
        self.cornerY = self.y + height
        self.cornerX = self.x + width
        log.debug("Left Mouse Down --  self.x %s self.y %s Width %s Height %s", str(self.x) , str(self.y), str(width), str(height))
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
        log.debug("Left Mouse Down --  self.x %s self.y %s Width %s Height %s self.dragType %s", str(self.x) , str(self.y), str(width), str(height),self.dragType)
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
            origin = getattr(self, "_span_drag_origin",
                             (self.col, self.row, self.columnspan, self.rowspan,
                              self.x, self.y, width, height))
            _oc, _or, _ocs, _ors, ox, oy, ow, oh = origin
            if self.dragType == "dragEast":
                # Stretch right edge rightward; left anchor stays fixed at ox
                cur_right = self.widget.winfo_x() + width + int(deltaX)
                new_w = max(16, cur_right - ox)
                self.widget.place(x=ox, y=oy, width=new_w, height=oh)
            elif self.dragType == "dragSouth":
                # Stretch bottom edge downward; top anchor stays fixed at oy
                cur_bottom = self.widget.winfo_y() + height + int(deltaY)
                new_h = max(16, cur_bottom - oy)
                self.widget.place(x=ox, y=oy, width=ow, height=new_h)
            elif self.dragType == "dragWest":
                # Stretch left edge leftward; right anchor stays fixed at ox+ow
                right_edge = ox + ow
                cur_left  = self.widget.winfo_x() + int(deltaX)
                new_x = min(max(0, cur_left), right_edge - 16)
                new_w = max(16, right_edge - new_x)
                self.widget.place(x=new_x, y=oy, width=new_w, height=oh)
            elif self.dragType == "dragNorth":
                # Stretch top edge upward; bottom anchor stays fixed at oy+oh
                bottom_edge = oy + oh
                cur_top = self.widget.winfo_y() + int(deltaY)
                new_y = min(max(0, cur_top), bottom_edge - 16)
                new_h = max(16, bottom_edge - new_y)
                self.widget.place(x=ox, y=new_y, width=ow, height=new_h)
            else:
                # Centre-drag: float the whole widget
                newX = self.widget.winfo_x() + int(deltaX)
                newY = self.widget.winfo_y() + int(deltaY)
                self.x = max(0, newX)
                self.y = max(0, newY)
                self.widget.place(x=self.x, y=self.y,
                                  width=self.widget.winfo_width(),
                                  height=self.widget.winfo_height())
            self.lastX = x
            self.lastY = y
            return
        if myVars.geomManager == "Pack":
            # Pack order can't be dragged visually; just update tracking
            self.x = self.widget.winfo_x() + int(deltaX)
            self.y = self.widget.winfo_y() + int(deltaY)
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
        log.debug("self.dragType %s x = %s y = %s self.x %s y=self.y %s width %s height %s self.startX %s self.startY %s",self.dragType,x,y,self.x,self.y,width,height,self.startX,self.startY)
        self.lastX = x
        self.lastY = y

    def leftMouseRelease(self, event):
        # Capture pre-drag state (set in leftMouseDown)
        pre = getattr(self, "_pre_drag", (self.x, self.y, self.width, self.height))
        ox, oy, ow, oh = pre

        self._last_drag_type = self.dragType   # read before clearing
        self.dragType = ""
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
            # Widget may be floating via .place() from drag — snap back to grid.
            drag_type = getattr(self, "_last_drag_type", "")
            origin = getattr(self, "_span_drag_origin",
                             (self.col, self.row, self.columnspan, self.rowspan,
                              self.x, self.y, self.width, self.height))
            anc_col, anc_row, _ocs, _ors, _ox, _oy, _ow, _oh = origin
            try:
                self.widget.place_forget()
            except tk.TclError:
                pass
            try:
                if drag_type == "dragEast":
                    # Right edge dragged: anchor col unchanged, span = cols crossed
                    right_x = self.widget.winfo_x() + self.widget.winfo_width()
                    z_end = self.root.grid_location(right_x - 1, self.widget.winfo_y())
                    end_col = max(anc_col, int(z_end[0]))
                    self.col = anc_col
                    self.columnspan = max(1, end_col - anc_col + 1)
                    self.row = anc_row
                    self.rowspan = _ors
                elif drag_type == "dragSouth":
                    # Bottom edge dragged: anchor row unchanged, span = rows crossed
                    bot_y = self.widget.winfo_y() + self.widget.winfo_height()
                    z_end = self.root.grid_location(self.widget.winfo_x(), bot_y - 1)
                    end_row = max(anc_row, int(z_end[1]))
                    self.row = anc_row
                    self.rowspan = max(1, end_row - anc_row + 1)
                    self.col = anc_col
                    self.columnspan = _ocs
                elif drag_type == "dragWest":
                    # Left edge dragged: right col fixed, new start col moves left
                    right_col = anc_col + _ocs - 1
                    z_start = self.root.grid_location(
                        self.widget.winfo_x(), self.widget.winfo_y())
                    new_col = min(max(0, int(z_start[0])), right_col)
                    self.col = new_col
                    self.columnspan = max(1, right_col - new_col + 1)
                    self.row = anc_row
                    self.rowspan = _ors
                elif drag_type == "dragNorth":
                    # Top edge dragged: bottom row fixed, new start row moves up
                    bot_row = anc_row + _ors - 1
                    z_start = self.root.grid_location(
                        self.widget.winfo_x(), self.widget.winfo_y())
                    new_row = min(max(0, int(z_start[1])), bot_row)
                    self.row = new_row
                    self.rowspan = max(1, bot_row - new_row + 1)
                    self.col = anc_col
                    self.columnspan = _ocs
                else:
                    # Centre-drag: move to the cell under the widget's top-left
                    z = self.root.grid_location(self.x, self.y)
                    self.row = max(0, int(z[1]))
                    self.col = max(0, int(z[0]))
            except (tk.TclError, TypeError, ValueError):
                pass
            self.widget.grid(row=self.row, column=self.col,
                             columnspan=self.columnspan, rowspan=self.rowspan,
                             padx=2, pady=2, sticky="WE")
            log.debug("Left Mouse Release -- col=%s row=%s cspan=%s rspan=%s",
                      self.col, self.row, self.columnspan, self.rowspan)
        elif myVars.geomManager == "Pack":
            self.widget.pack(padx=4, pady=4, anchor="nw")
        else:
            log.error("Geometry Manager %s is TBD", myVars.geomManager)
        raiseChildren(self.pythonName)

        # Record the move/resize as an undoable action (only if something changed)
        nx, ny, nw, nh = self.x, self.y, self.width, self.height
        if (ox, oy, ow, oh) != (nx, ny, nw, nh):
            undoredo.stack.push_done(
                undoredo.MoveCommand(self, ox, oy, ow, oh, nx, ny, nw, nh)
            )

