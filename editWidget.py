import logging as log
import tkinter as tk
import tkinter.filedialog as filedialog

# import urllib.request
import webbrowser

import ttkbootstrap as tboot
from PIL import ImageTk
from tkfontchooser import askfont
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog

# from ttkbootstrap.dialogs.dialogs import FontDialog
from ttkbootstrap.widgets import Entry, LabelFrame

import createWidget as cw
import pytkguivars as myVars

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
        # clickCanvas.bind('<B1-Motion>', leftMouseDrag)  # clickCanvas2.bind('<B1-Motion>', leftMouseDragResize)
        self.childNameDict = {}

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

    def changeColour(self, key):
        """
        Choose a Colour
        :param key: Widgets key name
        """
        colorDialog = ColorChooserDialog()
        currentVal = self.stringDict.get(key)
        if currentVal is not None:
            colorDialog.initialcolor = currentVal
        colorDialog.show()
        colors = colorDialog.result
        if colors[2] != "":
            self.addToStringDict(key, colors[2])
        else:
            log.warning("Color Chooser did not return anything")

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

    def leftMouseDrag(self, event):
        """
        Callback to allow a user to drag the widget
        :param event:
        """
        # This is a weird algorithm
        # it is a hack to get around using event.x_root and event.y_root
        # which seems tricky. However,  it does work (sort of)
        # The yellow dot/triangle on the popup is uses as a selection point
        widget = event.widget.master
        x = int(widget.place_info().get("x"))
        y = int(widget.place_info().get("y"))
        moveX = event.x
        moveY = event.y
        threshold = 8 
        if abs(event.x) > threshold:
            if event.x > 0:
                moveX = threshold
            else:
                moveX = -1 * threshold
        if abs(event.y) > threshold:
            if event.y > 0:
                moveY = threshold
            else:
                moveY = -1 * threshold

        log.debug("x %s event.x %s moveX %s",x,event.x,moveX) 
        log.debug("y %s event.y %s moveY %s",y,event.y,moveY) 
        newX = x + moveX
        newY = y + moveY
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
        log.info("image %s",str(imageTk))
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
                if [myVars.KEY] == key:
                    f[myVars.FILENAME] = filename
                    f[myVars.PHOTOIMAGE] = myVars.imageTest
                    found = True
        if found is False: 
            f = [self.widgetName,key,filename,myVars.imageTest]
            log.debug("Adding f %s",str(f))
            myVars.widgetImageFilenames.append(f)


    def applyLayoutSettings(self) -> None:
        """
        Apply changed layout for the Widget
        """
        logString = "Layout %s new value %s"
        log.debug("Apply Layout settings")
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
                    self.widget["values"] = newVal
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
                        except tk.TclError as e:
                            log.error(e)
                            log.warning("k %s val %s", str(k), str(newVal))
        wName = myVars.fixWidgetName(self.widget.widgetName)
        # if wName in ('canvas', 'listbox', 'text', 'treeview'):
        # scrollbars are very hard when using place.
        if myVars.geomManager == "Grid" and wName in ("canvas", "listbox", "treeview"):
            # scrollbars = ['vertical_scrollbar', 'horizontal_scrollbar']
            for k in scrollbars:
                # verticalValues = [' ', 'none', 'LeftSide', 'RightSide']
                # horizontalValues = [' ', 'none', 'Top', 'Bottom']
                newVal = self.stringDict.get(k)
                log.info("scrollbar %s value %s", k, newVal)
                if k == "vertical_scrollbar":
                    if newVal == "LeftSide" or newVal == "RightSide":
                        sbSide = "right"
                        if newVal == "LeftSide":
                            sbSide = "left"
                        # sb = tboot.Scrollbar(self.widget, orient="vertical", style='info round')
                        sb = tboot.Scrollbar(
                            self.root, orient="vertical", style="info round"
                        )
                        cw.createWidget(self.root, sb)
                        cw.changeParentOfTo(sb, self.widget)
                        self.widget.configure(yscrollcommand=sb.set)
                        sb.config(command=self.widget.yview)
                        sb.place_forget()
                        sb.pack(side=sbSide, fill="y")
                        # sb.place(relx=1,  rely=0,  relheight=1,  anchor='ne')
                elif k == "horizontal_scrollbar":
                    if newVal == "Top" or newVal == "Bottom":
                        sbSide = "top"
                        if newVal == "Bottom":
                            sbSide = "bottom"
                        sb = tboot.Scrollbar(
                            self.widget, orient="horizontal", style="info"
                        )
                        cw.createWidget(self.widget, sb)
                        cw.changeParentOfTo(sb, self.widget)
                        self.widget.configure(xscrollcommand=sb.set)
                        sb.config(command=self.widget.xview)
                        sb.pack(side=sbSide, fill="x")
                        # self.widget.configure(xscrollcommand=sb.set)
        if myVars.geomManager == "Grid" and wName in ("notebook"):
            key = "tab_count"
            newVal = self.stringDict.get(key)
            if newVal is None or newVal == "":
                newVal = "0"
            # Get the number of tabs.
            for n in range(int(newVal)):
                frame = tboot.Frame(self.widget, borderwidth=1, style="info")
                cw.createWidget(self.widget, frame)
                cw.changeParentOfTo(frame, self.widget)
                self.widget.add(frame, text="Tab" + str(n))
                # frame.pack(fill='both',  expand=True)

    def reformatValues(self, values) -> list:
        """
        This fixes the values used in combo boxes
        :param values: list of values
        :return: a list of the reformatted values
        """
        # There is possibly a better way to do this
        # configure does not work for lists. change directly ...
        # It needs a string list like this .
        # self.widget['values'] = "1 2 3 4 5"
        try:
            val = values.replace("(", "")
            newVal = val.replace(")", "")
            val = newVal
            newVal = val.replace(", ", " ")
            val = newVal
            newVal = val.replace("'", "")
            return newVal
        except tk.TclError as e:
            log.error("reformartValues %s", str(e))
            return []

    def createDragPoint(self, rootFrame, dragType) -> None:
        """
        Creates a small drag able point to move the popup
        :param rootFrame:
        :param dragType:
        """
        # This creates a yellow dot which can be used to drag the Frame
        clickCanvas = tboot.Canvas(
            rootFrame,
            width=20,
            height=20,
        )
        clickCanvas.grid(row=0, column=0, sticky="NW")
        if dragType == "triangle":
            points = [0, 20, 0, 0, 20, 0]
            clickCanvas.create_polygon(points, fill="yellow")
        else:
            clickCanvas.create_oval(1, 1, 20, 20, fill="yellow")
        clickCanvas.bind("<B1-Motion>", self.leftMouseDrag)

    def createLayoutPopup(self):
        """
        Widget layout ( x, y, width, height)
        """
        gridRow = 0
        wName = myVars.fixWidgetName(self.widget.widgetName)
        log.debug("Widget %s name %s", self.widget, wName)
        label = "Edit layout for " + wName
        layoutPopupFrame = LabelFrame(
            self.root,
            text=label,
            labelanchor="n",
            padding=2,
            borderwidth=1,
            relief="solid",
        )
        layoutPopupFrame.place(x=300, y=10)
        self.createDragPoint(layoutPopupFrame, "triangle")
        w = tboot.Label(layoutPopupFrame, text=" ")
        w.grid(row=gridRow, column=1, columnspan=3, sticky=tk.NS)
        place = self.widget.place_info()
        # layoutPopupFrame.title("Edit Widget Layout")
        for p in place:
            onlyThese = ["x", "y", "width", "height"]
            if p not in onlyThese:
                continue
            gridRow += 1
            lab1 = tboot.Label(layoutPopupFrame, text=p)
            ###############################
            # Spinbox fields
            ###############################
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
                to=299,
                increment=1,
                validate="focusout",
                validatecommand=lambda pp=p: self.popupCallback(pp),
            )
            widgetKey = p + "Widget"
            self.addToStringDict(widgetKey, w)
            w.set(val)
            lab1.grid(row=gridRow, column=0, sticky=tk.NE)
            w.grid(row=gridRow, column=3, sticky=tk.SW)
        # blank Label to make the layout better
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

    def getHelp(self):
        """
        should take a user to the documentation for the widget
        :return: None
        """
        try:
            wName = myVars.fixWidgetName(self.widget.widgetName)
            if wName == "label":
                webbrowser.open(
                    "https://docs.python.org/3/library/tkinter.tboot.html#label-options"
                )
            else:
                webbrowser.open(
                    "https://docs.python.org/3/library/tkinter.tboot.html#ttk-widgets"
                )
            print(wName)
        except tk.TclError as e:
            log.error("getHelp got am exception %s", str(e))

    def createEditPopup(self) -> None:
        """
        Popup to edit the tags/attributes for the Widget
        """
        row = 0
        gridRow = 0
        wName = myVars.fixWidgetName(self.widget.widgetName)
        log.debug("Widget %s name %s", self.widget, wName)
        label = "Edit attributes for " + wName
        editPopupFrame = LabelFrame(
            self.root,
            text=label,
            labelanchor="n",
            padding=2,
            borderwidth=1,
            relief="solid",
        )
        editPopupFrame.place(x=300, y=10)
        self.createDragPoint(editPopupFrame, "triangle")
        # w = tboot.Label(editPopupFrame, text='Edit ' + wName, justify=tk.CENTER, anchor=tk.CENTER)
        # w.grid(row=gridRow, column=1, columnspan=3, sticky=tk.NS)
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
            l1 = tboot.Label(editPopupFrame, text=k)
            uniqueName = k + str(row)
            if k in ignoredKeys:
                continue
            ###############################
            # Special cases. Most will default to an entry widget
            ###############################
            elif k == "font":
                self.addToStringDict(k, val)
                w = tboot.Button(
                    editPopupFrame,
                    name=uniqueName,
                    text="Select a Font",
                    width=buttonWidth,
                    command=lambda kk=k: self.fontChange(kk),
                )
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
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
                    editPopupFrame,
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
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
                w.set(val)
            ###############################
            # Combobox fields
            ###############################
            elif k == "anchor" or k == "labelanchor":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    editPopupFrame,
                    values=anchorVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            elif k == "justify":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    editPopupFrame,
                    values=justifyVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            elif k == "relief":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    editPopupFrame,
                    values=reliefVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            elif k == "compound":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    editPopupFrame,
                    values=compoundVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            elif k == "cursor":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    editPopupFrame,
                    values=cursorVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            elif k == "orient":
                self.addToStringDict(k, val)
                w = tboot.Combobox(
                    editPopupFrame,
                    values=orientVals,
                    width=comboWidth,
                    name=uniqueName,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.set(val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
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
                    editPopupFrame,
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
                    log.error("Style parsing val %s got Exception %s",
                              str(val), str(e))
                # self.addToStringDict(k, val)
                self.addToStringDict("bootstyle", val)
                w.set(val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=4, sticky=tk.SW)
            ###############################
            # Image need work TBD Does not get saved correctly
            ###############################
            elif k == "image":
                # thisRow1 = row
                self.addToStringDict(k, val)
                w = tboot.Button(
                    editPopupFrame,
                    name=uniqueName,
                    text="Select Image",
                    width=buttonWidth,
                    command=lambda kk=k: self.selectImage(kk),
                )
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            ###############################
            # Colour selection possibly a canvas with the colour
            ###############################
            elif k == "fg" or k == "bg" or k == "foreground" or k == "background":
                self.addToStringDict(k, val)
                w = tboot.Button(
                    editPopupFrame,
                    name=uniqueName,
                    text="Select Color",
                    width=buttonWidth,
                    command=lambda kk=k: self.changeColour(kk),
                )
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            ###############################
            # The Default --- use and entry widget for all other tags
            ###############################
            else:
                self.addToStringDict(k, val)
                w = Entry(
                    editPopupFrame,
                    name=uniqueName,
                    width=entryWidth,
                    validate="focusout",
                    validatecommand=lambda kk=k: self.popupCallback(kk),
                )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.insert(tk.END, val)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)

            # if stringUsed[row]:
            l1.grid(row=gridRow, column=labelCol, columnspan=3, sticky=tk.E)

        # Some widgets have 'children'
        kids = self.widget.children
        if kids:
            for k in kids:
                try:
                    widgetName = k.widgetName
                except AttributeError as e:
                    log.warning(
                        "child widget ->%s<- got exception %s", str(k), str(e))
                    continue
                log.debug(widgetName)
                l0 = tboot.Label(
                    editPopupFrame,
                    text=widgetName,
                    borderwidth=1,
                    border=tk.SOLID,
                    justify=tk.CENTER,
                )
                l0.grid(row=gridRow, column=1, columnspan=5, sticky=tk.EW)
                row += 1
                gridRow += 1
                if widgetName == "ttk::notebook":
                    log.info(widgetName)
                    # Need a Tabs button
                    keys.append(tuple(("Tabs", "Tabs")))
                elif widgetName == "ttk::labelframe":
                    keys1 = self.widget.label.keys()
                    for k1 in keys1:
                        keys.append(tuple(("label", k1)))
                        keys2 = self.widget.scale.keys()
                    for k2 in keys2:
                        keys.append(tuple(("scale", k2)))
                    log.debug(keys)
                else:
                    log.debug("unhandled child %s", widgetName)
        # If a frame,  add button(s) for scrollbar
        wName = myVars.fixWidgetName(self.widget.widgetName)
        log.debug("wName ->%s<-", wName)
        if myVars.geomManager == "Grid" and wName in ("canvas", "listbox", "treeview"):
            # if wName in ('frame', 'labelframe', 'panedwindow'):
            log.info("Creating scrollbar stuff for %s", wName)
            for k in scrollbars:
                gridRow += 1
                sb = tboot.Label(editPopupFrame, text=k)
                sb.grid(row=gridRow, column=labelCol,
                        columnspan=3, sticky=tk.E)
                self.addToStringDict(k, val)
                if k == "vertical_scrollbar":
                    w = tboot.Combobox(
                        editPopupFrame,
                        values=verticalValues,
                        width=comboWidth,
                        validate="focusout",
                        validatecommand=lambda kk=k: self.popupCallback(kk),
                    )
                else:
                    w = tboot.Combobox(
                        editPopupFrame,
                        values=horizontalValues,
                        width=comboWidth,
                        validate="focusout",
                        validatecommand=lambda kk=k: self.popupCallback(kk),
                    )
                widgetKey = k + "Widget"
                self.addToStringDict(widgetKey, w)
                w.grid(row=gridRow, column=controlCol,
                       columnspan=3, sticky=tk.SW)
            gridRow += 1
        if myVars.geomManager == "Grid" and wName in ("notebook"):
            gridRow += 1
            key = "tab_count"
            val = self.stringDict.get(key)
            if val is None or val == "":
                val = "0"
            sb = tboot.Label(editPopupFrame, text=key)
            sb.grid(row=gridRow, column=labelCol, columnspan=3, sticky=tk.E)
            self.addToStringDict(key, val)
            w = tboot.Spinbox(
                editPopupFrame,
                width=spinboxWidth,
                name=uniqueName,
                from_=0,
                to=16,
                increment=1,
                validate="focusout",
                validatecommand=lambda kk=key: self.popupCallback(kk),
            )
            widgetKey = key + "Widget"
            self.addToStringDict(widgetKey, w)
            w.grid(row=gridRow, column=controlCol, columnspan=3, sticky=tk.SW)
            w.set(val)

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
            style="sucess",
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
