import logging as log
import tkinter as tk
import tkinter.filedialog as filedialog
import webbrowser
from typing import Any

import ttkbootstrap as tboot
from PIL import ImageTk
from tkfontchooser import askfont
from ttkbootstrap import Entry, Labelframe
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog

import createWidget as cw
import pytkguivars as myVars
import undoredo

stickyVals = [" ", tk.N, tk.S, tk.E, tk.W, tk.NS, tk.EW, tk.NSEW]
borderVals = [tk.INSIDE, tk.OUTSIDE]
anchorVals = [tk.CENTER, tk.N, tk.NE, tk.E, tk.SE, tk.S, tk.SW, tk.W, tk.NW]
justifyVals = [tk.LEFT, tk.CENTER, tk.RIGHT]
reliefVals = [tk.FLAT, tk.GROOVE, tk.RAISED, tk.RIDGE, tk.SOLID, tk.SUNKEN]
compoundVals = [tk.NONE, tk.TOP, tk.BOTTOM, tk.LEFT, tk.RIGHT]
orientVals = [tk.VERTICAL, tk.HORIZONTAL]
verticalValues = [" ", "none", "LeftSide", "RightSide"]
horizontalValues = [" ", "none", "Top", "Bottom"]
scrollbars = ["vertical_scrollbar", "horizontal_scrollbar"]
cursorVals = [
    "arrow",
    "circle",
    "tcross",
    "cross",
    "exchange",
    "plus",
    "star",
    "clock",
    "mouse",
    "pirate",
    "spider",
    "target",
    "trek",
]
# these are used by scrollable widgets
scrollVals = ("xscrollcommand", "yscrollcommand")
ignoredKeys = scrollVals + (
    "class",
    "format",
    "show",
    "default",
    "takefocus",
    "state",
    "validate",
    "validatecommand",
    "xscrollincrement",
    "yscrollincrement",
    "invalidcommand",
    "labelwidget",
    "selectbackground",
    "selectforeground",
    "selectborderwidth",
    "insertborderwidth",
    "insertbackground",
    "insertontime",
    "insertofftime",
    "highlightcolor",
    "highlightbackground",
    "highlightthickness",
)

comboWidth = 10
entryWidth = 12
spinboxWidth = 9
otherWidth = 12
buttonWidth = 12


class widgetEditPopup:
    """
    This class handles the popups for editing the widget
    """

    def __init__(self, root, widget, widgetName):
        self.keys = None
        self.specialKeys = None
        self.widget = widget
        self.widgetName = widgetName
        self.root = root
        self.stringDict = {}
        self.childNameDict = {}
        # Popup-drag state (set in _popup_drag_start, used in leftMouseDrag)
        self._drag_widget = None
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_orig_x = 300
        self._drag_orig_y = 10

    # def addToChildNamesDict(self, key, val):
    #    self.childNameDict.update({key + ':', val})

    def addToStringDict(self, key, val):
        """
        Add a new or update an existing entry in the dictionary
        :param key: widget key
        :param val: value to store
        """
        log.debug("key is ->%s<- val is ->%s<-", key, str(val))
        self.stringDict[key] = val

    def fontChange(self, key):
        """
        Choose a new font
        :param key:
        """
        # existingFont = self.stringDict.get(key)
        # ttkbootstrap font dialog has issues
        font: dict = {}
        font = askfont(self.root)
        font_str = myVars.checkFontDict(font)
        if font_str != "":
            log.debug("Font is %s", str(font_str))
            self.addToStringDict(key, font_str)

    def popupCallback(self, key) -> bool:
        """
        This is attached to a lot of combo and other widgets. Used to set new values for
        the widget,  which are stored in a dict
        :param key:
        :return:
        """
        popupWidget: str = ""
        widgetKey = key + "Widget"
        popupWidget = self.stringDict.get(widgetKey)
        log.debug(
            "popupCallback widgetKey %s val %s key %s", widgetKey, popupWidget, key
        )
        val: str = ""
        val = popupWidget.get()
        self.addToStringDict(key, val)
        # This is needed to keep the validatecommand going
        return True

    def changeColour(self, key, swatch_btn=None):
        """
        Choose a Colour and immediately apply it to the live widget.
        :param key: Widget attribute key (e.g. 'bg', 'fg', 'background', 'foreground')
        :param swatch_btn: optional tboot.Button whose background will be updated
                           to show the chosen colour as a preview swatch.
        """
        colorDialog = ColorChooserDialog()
        currentVal = self.stringDict.get(key)
        if currentVal:
            try:
                colorDialog.initialcolor = currentVal
            except Exception:  # pylint: disable=broad-except
                pass
        colorDialog.show()
        colors = colorDialog.result
        if colors is None:
            log.warning("Color Chooser returned None for key %s", key)
            return
        # colors is a namedtuple (rgb, hsl, hex); use the hex value (index 2)
        hex_val = colors[2] if colors[2] else ""
        if hex_val:
            self.addToStringDict(key, hex_val)
            # Immediately apply to the live widget so the change is visible
            # without needing to hit "Apply".
            try:
                self.widget.configure(**{key: hex_val})
                log.info("changeColour: applied %s=%s to %s", key, hex_val, self.widget)
            except tk.TclError as e:
                log.warning("changeColour configure %s=%s: %s", key, hex_val, e)
            # Update the swatch button background to preview the chosen colour
            if swatch_btn is not None:
                try:
                    swatch_btn.configure(background=hex_val)
                except tk.TclError:
                    pass
        else:
            log.warning("Color Chooser did not return a hex value for key %s", key)

    def leftMouseDragResize(self, event):
        """
        Lower right drag box
        :param event:
        """
        widget = event.widget.master
        x = int(widget.place_info().get("x"))
        y = int(widget.place_info().get("y"))
        moveX = event.x
        moveY = event.y
        width = widget.winfo_width()
        height = widget.winfo_height()

        # newHeight = height + event.y
        # newWidth = width + event.x
        # widget.place(height=newHeight, width=newWidth)
        log.info(
            "Resize height %s width %s event.x %s \
                  event.y %s x_root %s y_root %s x %s y %s",
            str(height),
            str(width),
            str(event.x),
            str(event.y),
            str(event.x_root),
            str(event.y_root),
            str(x),
            str(y),
        )
        newX = x + moveX
        newY = y + moveY
        widget.place(x=newX, y=newY)

    def _popup_drag_start(self, event):
        """Record the starting position for a popup drag."""
        widget = event.widget
        # Walk up to the Labelframe root of the popup
        while widget is not None:
            try:
                if isinstance(widget, Labelframe):
                    break
                widget = widget.master
            except AttributeError:
                break
        self._drag_widget = widget
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        pi = widget.place_info()
        self._drag_orig_x = int(pi.get("x", 300))
        self._drag_orig_y = int(pi.get("y", 10))

    def leftMouseDrag(self, event):
        """
        Callback to allow a user to drag the popup frame.
        Bound to both the yellow triangle and the whole header row.
        Uses absolute screen coords (event.x_root/y_root) for reliable
        movement regardless of which child widget the event fired on.
        """
        widget = getattr(self, "_drag_widget", None)
        if widget is None:
            # fallback: walk up from the event source
            widget = event.widget
            while widget is not None:
                try:
                    if isinstance(widget, Labelframe):
                        break
                    widget = widget.master
                except AttributeError:
                    break
        dx = event.x_root - getattr(self, "_drag_start_x", event.x_root)
        dy = event.y_root - getattr(self, "_drag_start_y", event.y_root)
        newX = getattr(self, "_drag_orig_x", 300) + dx
        newY = getattr(self, "_drag_orig_y", 10) + dy
        newX = max(0, newX)
        newY = max(0, newY)
        log.debug("popup drag dx %s dy %s -> %s %s", dx, dy, newX, newY)
        widget.place(x=newX, y=newY)

    def leftMouseRelease(self, event):
        """
        Left Mouse released
        :param event:
        """
        log.debug("leftMouseRelease event %s %s", str(event), self.widget)

    def selectImage(self, key):
        """
        Select an image to load into the widget
        :param key: Name of key or attribute
        """
        # Need to convert this file to image (or other package. PIL has issues with github pylint)
        # log.warning("selectImage is Expermental")
        # return
        f_types = [("Png Files", "*.png"), ("Jpg kFiles", "*.jpg")]
        filename = filedialog.askopenfilename(filetypes=f_types)
        myVars.imageTest = ImageTk.PhotoImage(file=filename)
        imageTk = myVars.imageTest
        log.info("image %s", str(imageTk))
        filePath = key + "filename"
        self.addToStringDict(key, imageTk)
        self.addToStringDict(filePath, filename)
        self.widget.configure(image=imageTk)
        # [ 0 WIDGET 1 KEY 2 FILENAME 3 PHOTOIMAGE]
        # Check to see if it is new
        found = False
        # if myVars.widgetImageFilenames is None:
        for f in myVars.widgetImageFilenames:
            if f[myVars.WIDGET] == self.widgetName:
                if f[myVars.KEY] == key:
                    f[myVars.FILENAME] = filename
                    f[myVars.PHOTOIMAGE] = myVars.imageTest
                    found = True
        if found is False:
            f = [self.widgetName, key, filename, myVars.imageTest]
            log.debug("Adding f %s", str(f))
            myVars.widgetImageFilenames.append(f)

    def applyLayoutSettings(self) -> None:
        """
        Apply changed layout for the Widget.
        Place mode: updates x, y, width, height.
        Grid mode:  updates row, column, sticky, padx, pady.
        """
        logString = "Layout %s new value %s"
        log.debug("Apply Layout settings (geomManager=%s)", myVars.geomManager)

        if myVars.geomManager == "Grid":
            cwo = cw.findCreateWidgetObject(self.widgetName)
            try:
                row = int(self.stringDict.get("row", 0))
                col = int(self.stringDict.get("column", 0))
                columnspan = max(1, int(self.stringDict.get("columnspan", 1)))
                rowspan = max(1, int(self.stringDict.get("rowspan", 1)))
                padx = int(self.stringDict.get("padx", 2))
                pady = int(self.stringDict.get("pady", 2))
                ipadx = int(self.stringDict.get("ipadx", 0))
                ipady = int(self.stringDict.get("ipady", 0))
                sticky = str(self.stringDict.get("sticky", "nsew"))
                self.widget.grid(
                    row=row,
                    column=col,
                    columnspan=columnspan,
                    rowspan=rowspan,
                    padx=padx,
                    pady=pady,
                    ipadx=ipadx,
                    ipady=ipady,
                    sticky=sticky,
                )
                if cwo:
                    cwo.row = row
                    cwo.col = col
                    cwo.columnspan = columnspan
                    cwo.rowspan = rowspan
                    cwo.sticky = sticky
                    cwo.padx = padx
                    cwo.pady = pady
                    cwo.ipadx = ipadx
                    cwo.ipady = ipady
                log.debug(
                    logString,
                    "grid",
                    f"row={row} col={col} cspan={columnspan} rspan={rowspan} sticky={sticky}",
                )
            except (tk.TclError, ValueError) as e:
                log.error("applyLayoutSettings Grid: %s", e)
            return

        if myVars.geomManager == "Pack":
            cwo = cw.findCreateWidgetObject(self.widgetName)
            try:
                side = str(self.stringDict.get("side", "top"))
                fill = str(self.stringDict.get("fill", "none"))
                expand = int(self.stringDict.get("expand", 0))
                padx = int(self.stringDict.get("padx", 4))
                pady = int(self.stringDict.get("pady", 4))
                anchor = str(self.stringDict.get("anchor", "center"))
                self.widget.pack(
                    side=side,
                    fill=fill,
                    expand=expand,
                    padx=padx,
                    pady=pady,
                    anchor=anchor,
                )
                if cwo:
                    cwo.pack_side = side
                    cwo.pack_fill = fill
                    cwo.pack_expand = expand
                    cwo.pack_padx = padx
                    cwo.pack_pady = pady
                    cwo.pack_anchor = anchor
                log.debug(
                    logString,
                    "pack",
                    f"side={side} fill={fill} expand={expand} anchor={anchor}",
                )
            except (tk.TclError, ValueError) as e:
                log.error("applyLayoutSettings Pack: %s", e)
            return

        onlyThese = ["x", "y", "width", "height"]
        for p in onlyThese:
            origName = str(p) + "Orig"
            oldVal = self.stringDict.get(origName)
            newVal = self.stringDict.get(p)
            if newVal == "None" or newVal is None:
                newVal = ""
            if oldVal != newVal:
                log.debug(
                    "Widget %s Layout %s old ->%s<- new ->%s<-",
                    self.widget,
                    p,
                    oldVal,
                    newVal,
                )
                try:
                    log.debug(logString, str(p), str(newVal))
                    self.widget.place(**{p: newVal})
                except tk.TclError as e:
                    log.error(e)
                    log.warning("k %s val %s", str(p), str(newVal))

    def applyEditSettings(self) -> None:
        """
        Apply any changes settings for the Widget
        """
        keys = self.widget.keys()
        logString = "key %s new value %s"
        log.debug("Apply edit settings")
        for key in keys:
            # row += 1
            if isinstance(key, tuple):
                # childW = key[0]
                k = key[1]  # child_widget = getattr(self.widget, childW)
            else:
                k = key
            if k:
                if k is None:
                    continue
                if k in ignoredKeys:
                    continue
                oldVal = self.widget.cget(k)
                newVal = self.stringDict.get(k)
                if newVal == "None" or newVal is None:
                    newVal = ""
                if oldVal != newVal:
                    log.debug(
                        "Widget %s Key %s old ->%s<- new ->%s<-",
                        self.widget,
                        k,
                        oldVal,
                        newVal,
                    )
                if k in ignoredKeys:
                    continue  # log.warning("Ignore %s", k)
                elif k == "image":
                    newVal = self.stringDict.get(k)
                    log.info(logString, str(k), str(newVal))
                    # self.widget.configure(image=newVal)
                elif k == "values":
                    values = self.reformatValues(newVal)
                    log.debug(logString, str(k), str(values))
                    # This seems to be the way to add values
                    self.widget["values"] = values
                elif k == "style" or k == "bootstyle":
                    log.debug(logString, str(k), str(oldVal))
                    newVal = self.stringDict.get(k)
                    log.debug(logString, str(k), str(newVal))
                    # Don't do this .... self.widget.configure(style=newVal)
                    # or this ... newVal = newVal + '-round'
                    self.widget.configure(bootstyle=newVal)
                else:
                    log.debug(logString, str(k), str(newVal))
                    # self.addToStringDict(k, val)
                    if oldVal != newVal:
                        try:
                            log.info(logString, str(k), str(newVal))
                            self.widget.configure(**{k: newVal})
                            # Record the attribute change for undo
                            undoredo.stack.push_done(
                                undoredo.EditAttributeCommand(
                                    self.widget, k, str(oldVal), str(newVal)
                                )
                            )
                        except tk.TclError as e:
                            log.error(e)
                            log.warning("k %s val %s", str(k), str(newVal))
        wName = myVars.fixWidgetName(self.widget.widgetName)
        # Scrollbar wiring works in both Grid and Place geometry manager modes.
        if wName in ("canvas", "listbox", "treeview", "text"):
            # scrollbars = ['vertical_scrollbar', 'horizontal_scrollbar']
            for k in scrollbars:
                # verticalValues = [' ', 'none', 'LeftSide', 'RightSide']
                # horizontalValues = [' ', 'none', 'Top', 'Bottom']
                newVal = self.stringDict.get(k)
                log.info("scrollbar %s value %s", k, newVal)
                if k == "vertical_scrollbar":
                    if newVal in ("LeftSide", "RightSide"):
                        sb = tboot.Scrollbar(
                            self.root, orient="vertical", style="info round"
                        )
                        cw.createWidget(self.root, sb)
                        cw.changeParentOfTo(sb, self.widget)
                        self.widget.configure(yscrollcommand=sb.set)
                        sb.config(command=self.widget.yview)
                        if myVars.geomManager == "Place":
                            # In Place mode: position the scrollbar to the
                            # right (or left) edge of the target widget using
                            # place with relx/rely so it resizes with the widget.
                            sb.place_forget()
                            if newVal == "RightSide":
                                sb.place(
                                    in_=self.widget,
                                    relx=1.0, rely=0.0,
                                    relheight=1.0, width=16,
                                    anchor="ne",
                                )
                            else:  # LeftSide
                                sb.place(
                                    in_=self.widget,
                                    relx=0.0, rely=0.0,
                                    relheight=1.0, width=16,
                                    anchor="nw",
                                )
                        else:
                            # Grid / Pack mode: use pack() for natural flow
                            sbSide = "left" if newVal == "LeftSide" else "right"
                            sb.place_forget()
                            sb.pack(side=sbSide, fill="y")
                elif k == "horizontal_scrollbar":
                    if newVal in ("Top", "Bottom"):
                        sb = tboot.Scrollbar(
                            self.widget, orient="horizontal", style="info"
                        )
                        cw.createWidget(self.widget, sb)
                        cw.changeParentOfTo(sb, self.widget)
                        self.widget.configure(xscrollcommand=sb.set)
                        sb.config(command=self.widget.xview)
                        if myVars.geomManager == "Place":
                            sb.place_forget()
                            if newVal == "Bottom":
                                sb.place(
                                    in_=self.widget,
                                    relx=0.0, rely=1.0,
                                    relwidth=1.0, height=16,
                                    anchor="sw",
                                )
                            else:  # Top
                                sb.place(
                                    in_=self.widget,
                                    relx=0.0, rely=0.0,
                                    relwidth=1.0, height=16,
                                    anchor="nw",
                                )
                        else:
                            sbSide = "top" if newVal == "Top" else "bottom"
                            sb.pack(side=sbSide, fill="x")
        if wName in ("notebook"):
            # ---- Notebook tab sync (works in Place and Grid mode) ---------
            # Goal: make the notebook have exactly n_tabs tabs with the
            # requested labels.  We must NOT blindly add every time Apply is
            # pressed — that would duplicate tabs on every edit.
            key = "tab_count"
            newVal = self.stringDict.get(key)
            if newVal is None or newVal == "":
                newVal = "0"
            try:
                n_tabs = int(newVal)
            except ValueError:
                n_tabs = 0
            # Build target label list (fallback to "Tab0", "Tab1", …)
            labels_raw = self.stringDict.get("tab_labels", "") or ""
            label_parts = [lbl.strip() for lbl in labels_raw.split(",") if lbl.strip()]
            def _tab_label(idx):
                return label_parts[idx] if idx < len(label_parts) else "Tab" + str(idx)

            # How many tabs exist right now?
            existing_tabs = list(self.widget.tabs())   # list of tab IDs
            existing_count = len(existing_tabs)

            # 1. Rename / relabel existing tabs to match the new label list
            for idx, tab_id in enumerate(existing_tabs):
                self.widget.tab(tab_id, text=_tab_label(idx))

            # 2. Add new tabs for any slots beyond the current count
            for n in range(existing_count, n_tabs):
                frame = tboot.Frame(self.widget, borderwidth=1, style="info")
                cw.createWidget(self.widget, frame)
                cw.changeParentOfTo(frame, self.widget)
                self.widget.add(frame, text=_tab_label(n))

            # 3. Remove excess tabs (from the end) if n_tabs shrank
            for tab_id in reversed(existing_tabs[n_tabs:]):
                try:
                    self.widget.forget(tab_id)
                except tk.TclError as _te:
                    log.warning("notebook forget tab %s: %s", tab_id, _te)

        # Any Apply press means the project has unsaved changes
        myVars.projectSaved = False

    def reformatValues(self, values) -> str | list[Any]:
        """
        This fixes the values used in combo boxes
        :param values: list of values
        :return: a list of the reformatted values
        """
        v = str(values)
        log.info("Values " + v)
        # There is possibly a better way to do this
        # configure does not work for lists. change directly ...
        # It needs a string list like this .
        # self.widget['values'] = "1 2 3 4 5"
        try:
            val = v.replace("(", "")
            newVal = val.replace(")", "")
            val = newVal
            newVal = val.replace(", ", " ")
            val = newVal
            newVal: str = val.replace("'", "")
            return newVal
        except tk.TclError as e:
            log.error("reformartValues values=%s exception %s", str(values), str(e))
            return []

    def createDragPoint(self, rootFrame, dragType) -> None:
        """
        Creates the drag handle row at the top of a popup.
        The entire header row (including a spacer label) is draggable,
        not just the small yellow triangle.
        :param rootFrame: the Labelframe popup
        :param dragType: 'triangle' or 'dot'
        """
        # Header row: yellow handle + spacer label (both draggable)
        headerRow = tboot.Frame(rootFrame)
        headerRow.grid(row=0, column=0, columnspan=10, sticky="EW")
        clickCanvas = tboot.Canvas(
            headerRow,
            width=20,
            height=20,
        )
        clickCanvas.pack(side=tk.LEFT)
        if dragType == "triangle":
            points = [0, 20, 0, 0, 20, 0]
            clickCanvas.create_polygon(points, fill="yellow")
        else:
            clickCanvas.create_oval(1, 1, 20, 20, fill="yellow")
        # Spacer label fills the rest of the header — also draggable
        spacer = tboot.Label(
            headerRow,
            text="  drag here  ",
            foreground="#888",
            font=("TkDefaultFont", 8),
        )
        spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Bind drag on all header children
        for w in (clickCanvas, spacer, headerRow):
            w.bind("<ButtonPress-1>", self._popup_drag_start)
            w.bind("<B1-Motion>", self.leftMouseDrag)

    def createLayoutPopup(self):
        """
        Widget layout popup.
        Place mode: x, y, width, height spinboxes.
        Grid mode:  row, column, sticky, padx, pady spinboxes.
        The popup is parented to the top-level window so it always appears
        on top, regardless of whether the widget lives in geomWidgetFrame.
        """
        # Always parent to the real top-level window, not self.root
        # (self.root may be geomWidgetFrame which is inside a canvas window)
        topWin = self.widget.winfo_toplevel()
        gridRow = 0
        wName = myVars.fixWidgetName(self.widget.widgetName)
        log.debug("Widget %s name %s", self.widget, wName)
        label = "Edit layout for " + wName
        layoutPopupFrame = Labelframe(
            topWin,
            text=label,
            labelanchor="n",
            padding=2,
            borderwidth=1,
            relief="solid",
        )
        layoutPopupFrame.place(x=300, y=10)
        self.createDragPoint(layoutPopupFrame, "triangle")

        if myVars.geomManager == "Grid":
            # ---- Grid layout fields -----------------------------------
            # Read stored GeomData from our helper dict, or fall back to
            # the widget's actual grid_info()
            try:
                gi = self.widget.grid_info()
            except tk.TclError:
                gi = {}
            # Try to find the createWidget object to read row/col
            cwo = cw.findCreateWidgetObject(self.widgetName)

            # cwo fields are the authoritative user-set values; gi is a fallback
            # only when there is no cwo (e.g. non-tracked widgets).
            def _gi_int(key, cwo_val, default=0):
                if cwo_val is not None:
                    return cwo_val
                raw = gi.get(key)
                if raw is None:
                    return default
                return int(str(raw).split()[0])

            grid_fields = [
                ("row", _gi_int("row", cwo.row if cwo else None, 0), 0, 31, 1),
                ("column", _gi_int("column", cwo.col if cwo else None, 0), 0, 31, 1),
                (
                    "columnspan",
                    _gi_int("columnspan", cwo.columnspan if cwo else None, 1),
                    1,
                    32,
                    1,
                ),
                (
                    "rowspan",
                    _gi_int("rowspan", cwo.rowspan if cwo else None, 1),
                    1,
                    32,
                    1,
                ),
                ("padx", _gi_int("padx", cwo.padx if cwo else None, 2), 0, 50, 1),
                ("pady", _gi_int("pady", cwo.pady if cwo else None, 2), 0, 50, 1),
                ("ipadx", _gi_int("ipadx", cwo.ipadx if cwo else None, 0), 0, 500, 1),
                ("ipady", _gi_int("ipady", cwo.ipady if cwo else None, 0), 0, 500, 1),
            ]
            # sticky: prefer cwo.sticky (user-set), fall back to gi, then "ew"
            sticky_val = (
                (cwo.sticky if cwo and hasattr(cwo, "sticky") else None)
                or str(gi.get("sticky", ""))
                or "nsew"
            )
            for p, val, frm, to, inc in grid_fields:
                gridRow += 1
                lab1 = tboot.Label(layoutPopupFrame, text=p)
                origName = p + "Orig"
                self.addToStringDict(origName, str(val))
                self.addToStringDict(p, str(val))
                uniqueName = p + str(gridRow)
                w = tboot.Spinbox(
                    layoutPopupFrame,
                    width=5,
                    name=uniqueName,
                    from_=frm,
                    to=to,
                    increment=inc,
                    validate="focusout",
                    validatecommand=lambda pp=p: self.popupCallback(pp),
                )
                widgetKey = p + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                lab1.grid(row=gridRow, column=0, sticky=tk.NE)
                w.grid(row=gridRow, column=3, sticky=tk.SW)
            # sticky combobox
            gridRow += 1
            lab1 = tboot.Label(layoutPopupFrame, text="sticky")
            stickyCombo = tboot.Combobox(
                layoutPopupFrame,
                values=[
                    "ew",
                    "ns",
                    "nsew",
                    "n",
                    "s",
                    "e",
                    "w",
                    "ne",
                    "nw",
                    "se",
                    "sw",
                ],
                width=6,
                height=11,  # should be len(values) ?
                validate="focusout",
                validatecommand=lambda: self.popupCallback("sticky"),
            )
            self.addToStringDict("sticky", sticky_val)
            self.addToStringDict("stickyOrig", sticky_val)
            self.addToStringDict("stickyWidget", stickyCombo)
            stickyCombo.set(sticky_val)
            lab1.grid(row=gridRow, column=0, sticky=tk.NE)
            stickyCombo.grid(row=gridRow, column=3, sticky=tk.SW)
        elif myVars.geomManager == "Pack":
            # ---- Pack layout fields -----------------------------------
            cwo = cw.findCreateWidgetObject(self.widgetName)
            try:
                pi = self.widget.pack_info()
            except tk.TclError:
                pi = {}

            def _pi(key, cwo_val, default):
                if cwo_val is not None:
                    return cwo_val
                return pi.get(key, default)

            side_val = _pi("side", cwo.pack_side if cwo else None, "top")
            fill_val = _pi("fill", cwo.pack_fill if cwo else None, "none")
            expand_val = int(_pi("expand", cwo.pack_expand if cwo else None, 0))
            padx_val = int(_pi("padx", cwo.pack_padx if cwo else None, 4))
            pady_val = int(_pi("pady", cwo.pack_pady if cwo else None, 4))
            # side combobox
            gridRow += 1
            tboot.Label(layoutPopupFrame, text="side").grid(
                row=gridRow, column=0, sticky=tk.NSEW
            )
            sideCombo = tboot.Combobox(
                layoutPopupFrame,
                values=["top", "bottom", "left", "right"],
                width=6,
                validate="focusout",
                validatecommand=lambda: self.popupCallback("side"),
            )
            self.addToStringDict("side", side_val)
            self.addToStringDict("sideOrig", side_val)
            self.addToStringDict("sideWidget", sideCombo)
            sideCombo.set(side_val)
            sideCombo.grid(row=gridRow, column=3, sticky=tk.SW)
            # fill combobox
            gridRow += 1
            tboot.Label(layoutPopupFrame, text="fill").grid(
                row=gridRow, column=0, sticky=tk.NE
            )
            fillCombo = tboot.Combobox(
                layoutPopupFrame,
                values=["none", "x", "y", "both"],
                width=6,
                validate="focusout",
                validatecommand=lambda: self.popupCallback("fill"),
            )
            self.addToStringDict("fill", fill_val)
            self.addToStringDict("fillOrig", fill_val)
            self.addToStringDict("fillWidget", fillCombo)
            fillCombo.set(fill_val)
            fillCombo.grid(row=gridRow, column=3, sticky=tk.SW)
            # expand spinbox
            gridRow += 1
            tboot.Label(layoutPopupFrame, text="expand").grid(
                row=gridRow, column=0, sticky=tk.NE
            )
            expandSpin = tboot.Spinbox(
                layoutPopupFrame,
                width=5,
                from_=0,
                to=1,
                increment=1,
                validate="focusout",
                validatecommand=lambda: self.popupCallback("expand"),
            )
            self.addToStringDict("expand", str(expand_val))
            self.addToStringDict("expandOrig", str(expand_val))
            self.addToStringDict("expandWidget", expandSpin)
            expandSpin.set(expand_val)
            expandSpin.grid(row=gridRow, column=3, sticky=tk.SW)
            # padx / pady spinboxes
            for pname, pval in (("padx", padx_val), ("pady", pady_val)):
                gridRow += 1
                tboot.Label(layoutPopupFrame, text=pname).grid(
                    row=gridRow, column=0, sticky=tk.NE
                )
                pspin = tboot.Spinbox(
                    layoutPopupFrame,
                    width=5,
                    from_=0,
                    to=50,
                    increment=1,
                    validate="focusout",
                    validatecommand=lambda pp=pname: self.popupCallback(pp),
                )
                self.addToStringDict(pname, str(pval))
                self.addToStringDict(pname + "Orig", str(pval))
                self.addToStringDict(pname + "Widget", pspin)
                pspin.set(pval)
                pspin.grid(row=gridRow, column=3, sticky=tk.SW)
            # anchor combobox
            anchor_val = _pi("anchor", cwo.pack_anchor if cwo else None, "center")
            gridRow += 1
            tboot.Label(layoutPopupFrame, text="anchor").grid(
                row=gridRow, column=0, sticky=tk.NE
            )
            anchorCombo = tboot.Combobox(
                layoutPopupFrame,
                values=["center", "n", "ne", "e", "se", "s", "sw", "w", "nw"],
                width=6,
                validate="focusout",
                validatecommand=lambda: self.popupCallback("anchor"),
            )
            self.addToStringDict("anchor", anchor_val)
            self.addToStringDict("anchorOrig", anchor_val)
            self.addToStringDict("anchorWidget", anchorCombo)
            anchorCombo.set(anchor_val)
            anchorCombo.grid(row=gridRow, column=3, sticky=tk.SW)
        else:
            # ---- Place layout fields ----------------------------------
            place = self.widget.place_info()
            for p in place:
                onlyThese = ["x", "y", "width", "height"]
                if p not in onlyThese:
                    continue
                gridRow += 1
                lab1 = tboot.Label(layoutPopupFrame, text=p)
                val = place[p]
                origName = str(p) + "Orig"
                self.addToStringDict(origName, val)
                self.addToStringDict(p, val)
                uniqueName = p + str(gridRow)
                w = tboot.Spinbox(
                    layoutPopupFrame,
                    width=5,
                    name=uniqueName,
                    from_=0,
                    to=9999,
                    increment=1,
                    validate="focusout",
                    validatecommand=lambda pp=p: self.popupCallback(pp),
                )
                widgetKey = p + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                lab1.grid(row=gridRow, column=0, sticky=tk.NE)
                w.grid(row=gridRow, column=3, sticky=tk.SW)

        # blank spacer
        gridRow += 1
        lab2 = tboot.Label(layoutPopupFrame, text="  ")
        lab2.grid(row=gridRow, column=2)
        gridRow += 1
        b1 = tboot.Button(
            layoutPopupFrame,
            style="warning",
            width=5,
            text="Close",
            command=layoutPopupFrame.destroy,
        )
        b2 = tboot.Button(
            layoutPopupFrame,
            style="success",
            width=5,
            text="Apply",
            command=self.applyLayoutSettings,
        )

        b1.grid(row=gridRow, column=0)
        b2.grid(row=gridRow, column=3)

    # Map each widget's lower-case tcl name (after fixWidgetName) to the best
    # available docs URL.  ttkbootstrap widgets go to the ttkbootstrap API docs;
    # plain tk widgets go to the standard tkinter reference.
    _HELP_URLS: dict = {
        # ttkbootstrap widgets
        "label": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/label/",
        "button": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/button/",
        "entry": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/entry/",
        "combobox": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/combobox/",
        "spinbox": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/spinbox/",
        "checkbutton": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/checkbutton/",
        "radiobutton": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/radiobutton/",
        "progressbar": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/progressbar/",
        "scale": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/scale/",
        "scrollbar": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/scrollbar/",
        "separator": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/separator/",
        "sizegrip": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/sizegrip/",
        "notebook": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/notebook/",
        "treeview": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/treeview/",
        "frame": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/frame/",
        "labelframe": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/labelframe/",
        "panedwindow": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/panedwindow/",
        "scrolledtext": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/scrolledtext/",
        "floodgauge": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/floodgauge/",
        "meter": "https://ttkbootstrap.readthedocs.io/en/latest/api/widgets/meter/",
        # Standard tk widgets (no ttkbootstrap page)
        "canvas": "https://docs.python.org/3/library/tkinter.html#tkinter.Canvas",
        "text": "https://docs.python.org/3/library/tkinter.html#tkinter.Text",
        "listbox": "https://docs.python.org/3/library/tkinter.html#tkinter.Listbox",
    }

    def getHelp(self):
        """
        Open the documentation page for the current widget type in the browser.
        :return: None
        """
        try:
            wName = myVars.fixWidgetName(self.widget.widgetName).lower()
            url = self._HELP_URLS.get(
                wName,
                "https://ttkbootstrap.readthedocs.io/en/latest/",
            )
            log.info("getHelp: widget=%s url=%s", wName, url)
            webbrowser.open(url)
        except Exception as e:  # pylint: disable=broad-except
            log.error("getHelp got an exception %s", str(e))

    def createEditPopup(self) -> None:
        """
        Popup to edit the tags/attributes for the Widget.
        Content rows live in a scrollable inner frame so that widgets with
        many attributes (e.g. tk.Button) don't push the Apply/Close buttons
        off the screen.
        """
        row = 0
        gridRow = 0
        wName = myVars.fixWidgetName(self.widget.widgetName)
        log.debug("Widget %s name %s", self.widget, wName)
        label = "Edit attributes for " + wName
        # Always parent to the real top-level window (not geomWidgetFrame)
        topWin = self.widget.winfo_toplevel()
        topWin.resizable(True, True)
        editPopupFrame = Labelframe(
            topWin,
            text=label,
            labelanchor="n",
            padding=2,
            borderwidth=1,
            relief="solid",
        )
        editPopupFrame.place(x=300, y=10)
        self.createDragPoint(editPopupFrame, "triangle")

        # ---- Scrollable content area ------------------------------------
        # Height is computed from the number of attribute rows so there is
        # no wasted gap at the bottom.  A vertical scrollbar is shown only
        # when the content is taller than the maximum visible height.
        _ROW_PX = 26  # approximate pixels per attribute row
        _MAX_H = 480  # maximum visible height before scrolling starts
        _scroll_w = 320

        # Estimate row count: widget keys + any child-widget extra keys.
        # A precise count comes later but this is close enough for sizing.
        _est_keys = self.widget.keys()
        _est_rows = max(4, len(_est_keys) + 2)  # +2 for padding / children header
        _content_h = _est_rows * _ROW_PX
        _scroll_h = min(_content_h, _MAX_H)  # clip to maximum

        scrollCanvas = tk.Canvas(
            editPopupFrame,
            width=_scroll_w,
            height=_scroll_h,
            highlightthickness=0,
            bd=0,
        )
        # Show scrollbar only when content is taller than the visible area
        _need_scroll = _content_h > _MAX_H
        vscroll = tboot.Scrollbar(
            editPopupFrame, orient="vertical", command=scrollCanvas.yview
        )
        scrollCanvas.configure(yscrollcommand=vscroll.set)
        scrollCanvas.grid(row=1, column=0, columnspan=6, sticky="nsew")
        if _need_scroll:
            vscroll.grid(row=1, column=6, sticky="ns")
        scrollContent = tboot.Frame(scrollCanvas)
        _win_id = scrollCanvas.create_window((0, 0), window=scrollContent, anchor="nw")

        def _on_frame_configure(_evt):
            scrollCanvas.configure(scrollregion=scrollCanvas.bbox("all"))
            # Resize inner frame to fill canvas width
            scrollCanvas.itemconfig(_win_id, width=scrollCanvas.winfo_width())
            # Dynamically show/hide scrollbar based on actual content height
            content_h = scrollContent.winfo_reqheight()
            canvas_h = scrollCanvas.winfo_height()
            if content_h > canvas_h:
                vscroll.grid(row=1, column=6, sticky="ns")
                scrollCanvas.configure(yscrollcommand=vscroll.set)
            else:
                vscroll.grid_remove()
                scrollCanvas.configure(height=content_h)

        scrollContent.bind("<Configure>", _on_frame_configure)

        # Mouse-wheel scrolling
        def _on_mousewheel(evt):
            scrollCanvas.yview_scroll(int(-1 * (evt.delta / 120)), "units")

        scrollCanvas.bind("<MouseWheel>", _on_mousewheel)
        scrollContent.bind("<MouseWheel>", _on_mousewheel)
        # -------------------------------------------------------------------
        gridRow += 1
        keys = self.widget.keys()
        if keys == {}:
            editPopupFrame.destroy()
            return
        log.debug("Keys %s", str(keys))
        self.keys = keys
        labelCol = 0
        controlCol = 3
        val: str = ""
        # Some widgets will need extra 'keys'
        if wName == "notebook":
            # self.specialKeys("Tabs")
            log.warning("TBD -- Adding Tabs for notebook")
        for key in self.keys:
            row += 1
            gridRow += 1
            k = key
            childW = ""
            if isinstance(key, tuple):
                childW = key[0]
                k = key[1]
                child_widget = getattr(self.widget, childW)
                val = child_widget.cget(k)
            else:
                val = self.widget.cget(k)
            l1 = tboot.Label(scrollContent, text=k)
            uniqueName = k + str(row)
            if k in ignoredKeys:
                continue
            ###############################
            # Special cases. Most will default to an entry widget
            ###############################
            elif k == "font":
                self.addToStringDict(k, val)
                w = tboot.Button(
                    scrollContent,
                    name=uniqueName,
                    text="Select a Font",
                    width=buttonWidth,
                    command=lambda kk=k: self.fontChange(kk),
                )
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            ###############################
            # spinbox integer tags
            ###############################
            elif k in (
                "height",
                "columns",
                "width",
                "borderwidth",
                "displaycolumns",
                "padding",
            ):
                self.addToStringDict(k, val)
                w = tboot.Spinbox(
                    scrollContent,
                    width=spinboxWidth,
                    name=uniqueName,
                    from_=0,
                    to=299,
                    increment=1,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
                w.set(val)
            ###############################
            # Combobox fields
            ###############################
            elif k == "anchor" or k == "labelanchor":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    scrollContent,
                    values=anchorVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            elif k == "justify":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    scrollContent,
                    values=justifyVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            elif k == "relief":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    scrollContent,
                    values=reliefVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            elif k == "compound":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    scrollContent,
                    values=compoundVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            elif k == "cursor":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    scrollContent,
                    values=cursorVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            elif k == "orient":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    scrollContent,
                    values=orientVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            ###############################
            # Style is tricky -- using ttkbootstrap
            ###############################
            elif k == "style":
                self.addToStringDict(k, val)
                # varName = self.stringDict.get(k)
                style = tboot.Style()
                colours = []
                # if self.widget.widgetName == 'ttk::button':
                # largest range ,  bur does not seem to work
                # for color_label in style.colors.label_iter():
                # for color_label in style.colors.selectfg:
                #     log.info("colour label " + color_label)
                altList = []
                if self.widget.widgetName == "ttk::button":
                    altList = ["Outline", "Link"]
                elif self.widget.widgetName == "ttk::label":
                    altList = ["Inverse"]
                elif self.widget.widgetName == "ttk::checkbutton":
                    # altList = ['Outline',  'Roundtoggle',  'Squaretoggle'] # according to Docs
                    altList = ["Roundtoggle", "Squaretoggle"]

                for color_label in style.colors:
                    colours.append(color_label)
                    if altList:
                        for alt in altList:
                            colours.append(color_label + "." + alt)
                w = tboot.Combobox(
                    scrollContent,
                    values=colours,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.insert(tk.END, val)
                # python or tk change the format to 'name.wiget-type'
                # bval = self.widget.cget('bootstyle') # This does not work
                try:
                    bval = self.widget.cget("style")
                    bvalList = bval.split(".")
                    if bvalList[0] not in colours:
                        val = ""
                    else:
                        val = bvalList[0]
                except tk.TclError as e:
                    log.error("Style parsing val %s got Exception %s", str(val), str(e))
                # self.addToStringDict(k, val)
                self.addToStringDict("bootstyle", val)
                w.set(val)
                w.grid(row=gridRow, column=controlCol, columnspan=4, sticky=tk.SW)
            ###############################
            # Image need work TBD Does not get saved correctly
            ###############################
            elif k == "image":
                # thisRow1 = row
                self.addToStringDict(k, val)
                w = tboot.Button(
                    scrollContent,
                    name=uniqueName,
                    text="Select Image",
                    width=buttonWidth,
                    command=lambda kk=k: self.selectImage(kk),
                )
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            ###############################
            # Colour selection possibly a canvas with the colour
            ###############################
            elif k == "fg" or k == "bg" or k == "foreground" or k == "background":
                self.addToStringDict(k, val)
                w = tboot.Button(
                    scrollContent,
                    name=uniqueName,
                    text="Select Color",
                    width=buttonWidth,
                )
                # Pre-fill the button background with the current colour so it
                # acts as a live preview swatch.  Wrap in try in case
                # ttkbootstrap rejects the colour (e.g. empty string).
                if val:
                    try:
                        w.configure(background=val)
                    except tk.TclError:
                        pass
                w.configure(command=lambda kk=k, sw=w: self.changeColour(kk, sw))
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            ###############################
            # The Default --- use and entry widget for all other tags
            ###############################
            else:
                self.addToStringDict(k, val)
                w = Entry(
                    scrollContent,
                    name=uniqueName,
                    width=entryWidth,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.insert(tk.END, val)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)

            # if stringUsed[row]:
            l1.grid(row=gridRow, column=labelCol, columnspan=3, sticky=tk.E)

        # Some widgets have 'children'
        # Filter out internal Tk children that are not user-created widgets:
        # - widgets without a widgetName attribute (Tk internal objects)
        # - notebook tab-bar menus ("menu") — Tk creates these internally
        # - scrollbar/grip helper widgets injected by ttkbootstrap
        _INTERNAL_WIDGET_NAMES = ("menu",)
        kids = self.widget.children
        if kids:
            # for k in kids:
            for k in kids.values():
                try:
                    widgetName = k.widgetName
                except AttributeError as e:
                    log.warning("child widget ->%s<- got exception %s (skipped)", str(k), str(e))
                    continue
                # Skip internal Tk children that are not user widgets
                if widgetName in _INTERNAL_WIDGET_NAMES:
                    log.debug("createEditPopup: skipping internal child %s", widgetName)
                    continue
                log.debug(widgetName)
                l0 = tboot.Label()
                try:
                    l0 = tboot.Label(
                        scrollContent,
                        text=widgetName,
                        borderwidth=1,
                        # border=tk.SOLID,
                        justify=tk.CENTER,
                    )
                    l0.grid(row=gridRow, column=1, columnspan=5, sticky=tk.EW)
                except tk.TclError as e:
                    log.error("widget ->%s<- got exception %s", str(l0), str(e))

                row += 1
                gridRow += 1
                if widgetName == "ttk::notebook":
                    log.info(widgetName)
                    # Need a Tabs button
                    keys.append(tuple(("Tabs", "Tabs")))
                elif widgetName == "ttk::labelframe":
                    keys1 = self.widget.label.keys()
                    keys2 = self.widget.scale.keys()
                    for k1 in keys1:
                        keys.append(tuple(("label", k1)))
                    for k2 in keys2:
                        keys.append(tuple(("scale", k2)))
                    log.debug(keys)
                else:
                    log.debug("unhandled child %s", widgetName)
        # If a scrollable widget, add scrollbar placement controls.
        # These work in both Grid and Place geometry manager modes.
        wName = myVars.fixWidgetName(self.widget.widgetName)
        log.debug("wName ->%s<-", wName)
        if wName in ("canvas", "listbox", "treeview", "text"):
            log.info("Creating scrollbar stuff for %s", wName)
            for k in scrollbars:
                gridRow += 1
                sb = tboot.Label(scrollContent, text=k)
                sb.grid(row=gridRow, column=labelCol, columnspan=3, sticky=tk.E)
                self.addToStringDict(k, val)
                if k == "vertical_scrollbar":
                    w = tboot.Combobox(
                        scrollContent,
                        values=verticalValues,
                        width=comboWidth,
                        validate="focusout",
                        validatecommand=lambda kk=k: self.popupCallback(kk),
                    )
                else:
                    w = tboot.Combobox(
                        scrollContent,
                        values=horizontalValues,
                        width=comboWidth,
                        validate="focusout",
                        validatecommand=lambda kk=k: self.popupCallback(kk),
                    )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            gridRow += 1
        if wName in ("notebook"):
            # ---- tab_count spinbox (works in both Place and Grid mode) ----
            gridRow += 1
            key = "tab_count"
            val = self.stringDict.get(key)
            # Pre-populate from the live notebook's actual tab count so the
            # spinbox reflects reality when reopening the editor on an existing
            # notebook (rather than showing 0 every time).
            if val is None or val == "":
                try:
                    val = str(len(self.widget.tabs()))
                except tk.TclError:
                    val = "0"
            sb = tboot.Label(scrollContent, text="tab_count")
            sb.grid(row=gridRow, column=labelCol, columnspan=3, sticky=tk.E)
            self.addToStringDict(key, val)
            tc_spin = tboot.Spinbox(
                scrollContent,
                width=spinboxWidth,
                from_=0,
                to=16,
                increment=1,
                validate="focusout",
                validatecommand=lambda kk=key: self.popupCallback(kk),
            )
            widgetKey = key + "Widget"
            self.addToStringDict(widgetKey, tc_spin)
            tc_spin.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            tc_spin.set(val)
            # ---- tab_labels entry -----------------------------------------
            # Comma-separated list of tab labels, e.g. "Home,Config,About"
            gridRow += 1
            key2 = "tab_labels"
            val2 = self.stringDict.get(key2, "")
            # Pre-populate from the live notebook tab texts if no value stored
            if not val2:
                try:
                    _live_labels = [
                        self.widget.tab(tid, "text") for tid in self.widget.tabs()
                    ]
                    val2 = ",".join(_live_labels)
                except tk.TclError:
                    val2 = ""
            if val2 is None:
                val2 = ""
            sb2 = tboot.Label(scrollContent, text="tab_labels")
            sb2.grid(row=gridRow, column=labelCol, columnspan=3, sticky=tk.E)
            self.addToStringDict(key2, val2)
            tl_entry = Entry(
                scrollContent,
                width=entryWidth,
                validate="focusout",
                validatecommand=lambda kk=key2: self.popupCallback(kk),
            )
            widgetKey2 = key2 + "Widget"
            self.addToStringDict(widgetKey2, tl_entry)
            tl_entry.insert(tk.END, val2)
            tl_entry.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)

        gridRow += 1

        b1 = tboot.Button(
            editPopupFrame,
            style="warning",
            width=5,
            text="Close",
            command=editPopupFrame.destroy,
        )
        b2 = tboot.Button(
            editPopupFrame, style="info", width=5, text="Help", command=self.getHelp
        )
        b3 = tboot.Button(
            editPopupFrame,
            style="success",
            width=5,
            text="Apply",
            command=self.applyEditSettings,
        )

        # blank Label to make the layout better
        lab2 = tboot.Label(editPopupFrame, text="   ")
        lab2.grid(row=gridRow, column=2)

        gridRow += 1
        b1.grid(row=gridRow, column=0, columnspan=2, sticky="EW")
        b2.grid(row=gridRow, column=2, columnspan=2, sticky="EW")
        b3.grid(row=gridRow, column=4, columnspan=2, sticky="EW")
