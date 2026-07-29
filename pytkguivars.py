import logging as log
import os
import os.path
import tkinter as tk
from tkinter import PhotoImage

import ttkbootstrap as ttk

import createWidget as cw
import project_format
from layout_model import GridGeometry

# import cdefs as C
# import io
# from io import StringIO

projectDict: dict
childNameVars: list[tk.StringVar]
imageFileNames: list[tk.StringVar]
imageTest: any
imagesUsed: list[tk.PhotoImage]
# [ 0 WIDGET 1 KEY 2 FILENAME 3 PHOTOIMAGE]
# The PHOTOIMAGE is not saved as it is unique to an instance.
# It will get generated on load project
WIDGET: int = 0
KEY: int = 1
FILENAME: int = 2
PHOTOIMAGE: int = 3

widgetImageFilenames: []
snapTo: int
imageIndex: int
backgroundColor: str
theme: str
style: ttk.Style
rootWidgetName: str
ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
createdWidgetOrder: list
alphaList = list(ascii_lowercase)
programName: str = "pytkgui"
containerWidgetsUsed = ("Frame", "Labelframe", "Panedwindow")
projectName: str = "tmp"
projectPath: str = "/tmp/tmp"
saveDirName: str = "/tmp"
# This can be used if a project is not opened
projectFileName: str = "/tmp/pytkquickgui"
fileType: str = ".json"
legacyFileType: str = ".pk1"  # kept so old saves can still be opened
lastProjectFile: str = "lastProject.txt"
defaultToolTheme: str = "defaultTheme.txt"
lastProjectSaved: str = ""
projectSaved: bool = False
# Path to the most-recently user-saved generated Python file.
# If set, buildPython() will attempt to preserve user edits from this file.
generatedPyFile: str = ""

# ---- Widgets available in the right-click palette ----------------------
widgetsUsed = (
    # ttkbootstrap widgets
    # "Frame",
    # "Labelframe",
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
    # "Panedwindow",
    # "Floodgauge",
    # "Meter",
    # "ScrolledText",  # Cannot get edit or layout
    # "ScrolledFrame", # Weird behaviour
    # Standard tk/ttk widgets
    # "tk.Button",
    # "Treeview",
    # "Scrollbar",  # needs wiring to a target widget — use Edit popup instead
    # "Sizegrip", This is Tricky, it needs to attach itself to a widget
    # Standard ttk widgets (via ttkbootstrap compatibility layer)
    # "ttk.Scale",
    # "ttk.Treeview",
    # "ttk.Combobox",
    # "ttk.Spinbox",
    # "ttk.Progressbar",
    # "ttk.Separator",
    # "ttk.Scrollbar",
)

# ---- Geometry manager ---------------------------------------------------
# Valid values: 'Place'  'Grid'  'Pack'
# Some objects use Grid and Pack internally; the root window uses Grid.
GEOM_MANAGERS = ("Place", "Grid", "Pack")
# Default
geomManager = "Grid"
# Number of rows/columns in the initial grid (Grid mode only).
# The grid auto-expands if more rows/cols are needed.
gridRows: int = 25
gridCols: int = 25
gridLineColor: str = ""
gridRowMinsize = "2.5m"  # 2.5 mm
gridColMinsize = "5m"  # 5 mm
gridRowPad = "2.5m"
gridColPad = "5m"
# ---- Widget groups (logical, not tkinter containers) --------------------
# {group_name: [widgetName, ...]}  — persisted to project JSON
groups: dict = {}

# ---- Multi-selection ----------------------------------------------------
# List of pythonName strings for currently Shift+clicked widgets
selectedWidgets: list = []

# ---- Redraw callback ----------------------------------------------------
# pytkquickgui sets this to drawGridLines() at startup so createWidget can
# trigger a redraw without a circular import.
redrawGridLines = None


# def sprintf(buf: str, fmt, *args) -> str:
#    tmpStr: str = ""
#    tmpStr.format(fmt % args)
#    # buf.write(fmt % args)
#    buf = tmpStr
#    return buf


def initVars():
    global childNameVars
    global imageIndex
    global imagesUsed
    global imageFileNames
    global snapTo
    global projectDict
    global backgroundColor
    global theme
    global rootWidgetName
    global createdWidgetOrder
    global widgetImageFilenames
    global generatedPyFile
    projectDict = {}
    childNameVars = [tk.StringVar()] * 64
    imageFileNames = [tk.StringVar()] * 64
    imagesUsed = [tk.PhotoImage]
    backgroundColor = "skyBlue3"
    # snapTo = int
    imageIndex = 0
    snapTo = 16
    theme = "default"
    rootWidgetName = "rootWidget"
    createdWidgetOrder = []
    widgetImageFilenames = []
    generatedPyFile = ""
    global groups
    global selectedWidgets
    global gridRows, gridCols, gridLineColor
    groups = {}
    selectedWidgets = []
    gridRows = 25
    gridCols = 25
    # Empty means use a readable foreground from the active tool theme.
    gridLineColor = ""


# Common Procs
def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res


def checkFontDict(font: dict) -> str:
    font_str: str = ""
    if font:
        # spaces in the family name need to be escaped
        family = font["family"]
        family_str = family.replace(" ", "\\ ")
        font["family"] = family_str
        font_str = f"{font['family']} {font['size']} {font['weight']} {font['slant']}"
        if font["underline"]:
            font_str += " underline"
        if font["overstrike"]:
            font_str += " overstrike"
            log.debug("Font is %s", str(font_str))
    return font_str


def getWidgetNameDetails(w) -> list:
    # NAME 0 PARENT 1 WIDGET 2 CHILDREN 3
    for nl in cw.createWidget.widgetNameList:
        widget = nl[cw.WIDGET]
        if w == widget:
            return nl
    log.error("Unable to find widget %s", w)
    return []


def getWidgetNameDetailsFromName(widgetName) -> list:
    # NAME 0 PARENT 1 WIDGET 2 CHILDREN 3
    for nl in cw.createWidget.widgetNameList:
        name = nl[cw.NAME]
        if name == widgetName:
            return nl
    log.error("Unable to find widget ->%s<-", widgetName)
    return []


def saveWidgetAsDict(widgetName) -> dict:
    """
    Save a Widget info as a dictonary
    :param widgetName: string
    :return: Dict()
    """
    keyCount = 0
    widgetDict = {}
    widgetDetails = getWidgetNameDetailsFromName(widgetName)
    if widgetDetails:
        w = widgetDetails[cw.WIDGET]
        widgetParent = widgetDetails[cw.PARENT]
        # w.update()
        log.debug("widgetName %s", w.widgetName)
        # Remove 'in' from place.
        # For Grid/Pack managed widgets place_info() returns {} — that is fine,
        # we just store an empty dict and rely on GeomData instead.
        place = {}
        try:
            place = w.place_info()
            place.pop("in", None)  # remove quietly; may not be present
        except tk.TclError as ex:
            # Pack/Grid widgets are not in .place() — place_info() may raise
            # TclError if the widget path is stale.  Log and continue; geomData
            # will capture the real geometry below.
            log.warning("place_info() on ->%s<- raised %s (ignored)", str(w), str(ex))
        # Capture geometry info for all supported managers
        geomData = {}
        try:
            if geomManager == "Grid":
                cwo = cw.findCreateWidgetObject(widgetName)
                if cwo is not None:
                    geomData = cwo.capture_grid_geometry().to_json()
                else:
                    # Compatibility fallback for untracked helper widgets.
                    gi = w.grid_info()

                    geomData = GridGeometry.from_mapping(gi).to_json()
            elif geomManager == "Pack":
                pi = w.pack_info()
                geomData = {
                    "side": str(pi.get("side", "top")),
                    "fill": str(pi.get("fill", "none")),
                    "expand": str(pi.get("expand", 0)),
                    "padx": str(pi.get("padx", 2)),
                    "pady": str(pi.get("pady", 2)),
                    "anchor": str(pi.get("anchor", "center")),
                }
        except tk.TclError:
            pass

        widgetDict = {
            "WidgetName": w.widgetName,
            "WidgetParent": widgetParent,
            "Place": place,
            "GeomData": geomData,
        }
        keyCount = 0
        # Guard against stale / already-destroyed widget paths.  This can
        # happen when an undo snapshot is taken for a child widget whose parent
        # was destroyed first, making the Tk path invalid.
        try:
            keys = w.keys()
        except tk.TclError as _ke:
            log.warning(
                "saveWidgetAsDict: w.keys() failed for %s: %s (skipping attributes)",
                widgetName,
                _ke,
            )
            return {widgetName: widgetDict}
        # Keys whose values are bound Python callables (e.g. scrollbar.set,
        # canvas.yview).  Tkinter returns them as strings like
        # "140234567890set" or "140234567890yview" — a raw memory address
        # concatenated with the method name.  These are meaningless on reload
        # and must never be passed back to widget.configure().  We skip them
        # here and re-wire them in loadProject() instead.
        #
        # EXCEPTION: command/postcommand/textvariable/variable may hold a
        # plain user-supplied Python name (e.g. "my_button_click").  When set
        # via widget.configure() Tkinter wraps these in Tcl references, making
        # widget["command"] return a mangled string.  editWidget.py saves the
        # raw user string in widget._user_attrs so we can recover it here.
        _CALLABLE_KEYS = project_format.RUNTIME_CALLABLE_KEYS
        # Keep all Python callback and Tk-variable names in explicit design
        # metadata. This avoids depending on Tk's internal Tcl representation
        # and gives every save/load/duplicate path the same source of truth.
        _USER_STRING_KEYS = project_format.PRESERVED_STRING_KEYS
        # Emit preserved design strings before reading live Tk attributes.
        _user_attrs = getattr(w, "_user_attrs", {})
        if not isinstance(_user_attrs, dict):
            _user_attrs = {}
        for _ukey in _USER_STRING_KEYS:
            _uval = _user_attrs.get(_ukey, "")
            if not _uval:
                # Compatibility path for widgets created before explicit raw
                # metadata was introduced. Plain identifiers are safe design
                # names; Tcl-generated callback handles start with digits.
                try:
                    live_value = str(w[_ukey])
                except (KeyError, tk.TclError):
                    live_value = ""
                if project_format.valid_python_name(live_value):
                    _uval = live_value
                    project_format.remember_widget_value(w, _ukey, live_value)
            if _uval:
                attrId = "Attribute" + str(keyCount)
                widgetAttribute = {attrId: {"Key": _ukey, "Value": str(_uval)}}
                newWidget = Merge(widgetDict, widgetAttribute)
                widgetDict = newWidget
                keyCount += 1
                log.debug("saveWidgetAsDict: user_attr %s=%s", _ukey, _uval)
        if keys:
            for key in keys:
                log.debug("Key->%s<-", key)
                if key != "in":
                    # Skip scroll-command callables — always raw Tcl addresses.
                    if key in _CALLABLE_KEYS:
                        log.debug("saveWidgetAsDict: skipping callable key %s", key)
                        continue
                    # Skip preserved strings — already emitted from _user_attrs.
                    if key in _USER_STRING_KEYS:
                        log.debug("saveWidgetAsDict: skipping (in _user_attrs) %s", key)
                        continue
                    value = w[key]
                    if key == "image":
                        if value:
                            # The value is w.widgetName + key
                            value = widgetName + key
                    # Tkinter sometimes returns tuple/list objects for attributes
                    # like Treeview 'show', 'columns', 'displaycolumns'.
                    # Convert to a plain space-separated string so buildAWidget
                    # can serialise and re-eval them without hitting the '<' guard.
                    if isinstance(value, (tuple, list)):
                        # Each element may be an index object; str() gives the name
                        value = " ".join(str(v) for v in value)
                    log.debug("Value->%s<-", str(value))
                    attrId = "Attribute" + str(keyCount)
                    # Ignore empty values
                    if (value is not None) and (len(str(value)) > -1):
                        widgetAttribute = {attrId: {"Key": key, "Value": str(value)}}
                        newWidget = Merge(widgetDict, widgetAttribute)
                        widgetDict = newWidget
                        keyCount += 1
    widgetKeys = widgetName + "-KeyCount"
    tmpDict = Merge(widgetDict, {widgetKeys: keyCount})
    newWidget = {widgetName: tmpDict}
    return newWidget


def buildAWidget(widgetId: object, wDictOrig: dict) -> str:
    """
    generate python code to display a widget
    :param widgetId:
    :param wDictOrig:
    :return: The python commands string to build this widget
    """
    # testDict =
    widgetName = "Widget" + str(widgetId)
    try:
        testDict = wDictOrig.get(widgetName)
    except AttributeError as e:
        log.error("Cannot find %s Exception %s", widgetName, str(e))
        testDict = None
    if testDict is not None:
        wDict = testDict
    else:
        wDict = wDictOrig
    log.debug(
        "buildAWidget widgetName %s widgetId %d wDict->%s<-",
        widgetName,
        widgetId,
        wDict,
    )
    try:
        wType = wDict.get("WidgetName")
    except AttributeError as e:
        log.error("Cannot find %s Exception %s", "WidgetName", str(e))
        print("wDictOrig", wDictOrig)
        return ""
    t = fixWidgetTypeName(wType)
    wType = t
    keyCount = widgetName + "-KeyCount"

    nKeys = 0

    try:
        nKeys = wDict[keyCount]
    except KeyError as e:
        log.error("KeyError in json? ->%s<- ->%s<- %s", keyCount, str(nKeys), e)

    widgetDef = wType + "(mainFrame"
    for a in range(nKeys):
        attribute = "Attribute" + str(a)
        aDict = wDict[attribute]
        key = aDict["Key"]
        val = aDict["Value"]
        useValQuotes = True
        if key == "image":
            if val:
                # The problem here is the ID is for the original widget.
                # Create widget keeps the count. Use the next one that will get created
                # As this is a clone, find the original amd make a new entry
                newWidgetName = "Widget" + str(cw.createWidget.widgetId)
                if widgetImageFilenames is None:
                    continue
                for f in widgetImageFilenames:
                    if f[WIDGET] == widgetName:
                        if f[KEY] == key:
                            filename = f[FILENAME]
                            if os.path.isfile(filename):
                                newImage = tk.PhotoImage(file=filename)
                                n = [newWidgetName, key, filename, newImage]
                                widgetImageFilenames.append(n)
                                log.info(
                                    "New image for newWidgetName %s %s",
                                    newWidgetName,
                                    n,
                                )
                                break
                val = "myVars.getPhotoImage('" + newWidgetName + "','" + key + "')"
        # like 'to' 'from' needs to have an underscore
        if key == "from":
            key = "from_"
        # j(' is in lists for combo boxes
        if val.find("<") > -1:
            log.warning(
                "key ->%s<- value ->%s<-has a weird value dict  ->%s<- ",
                key,
                val,
                aDict,
            )
            # Typically, this a TK object that is in < xxx > format
            continue
        if key != "image" and val.find("(") > -1:
            # The 'values' key has this saved format. This might be a tk thing.
            # It needs to be converted to a list
            newVal = fixComboValues(key, val)
            val = newVal
            useValQuotes = False
        if key == "image":
            useValQuotes = False
        if len(val) > 0:
            tmpWidgetDef: str = ""
            if useValQuotes:
                tmpWidgetDef = f"{widgetDef},{key}={val!r}"
                # tmpWidgetDef = C.sprintf(widgetDef,"%s,%s='%s'",widgetDef,key,val)
            else:
                tmpWidgetDef = f"{widgetDef},{key}={val}"
                # tmpWidgetDef = C.sprintf(widgetDef,"%s,%s=%s",widgetDef,key,val)
            widgetDef = tmpWidgetDef
    tmp = widgetDef + ")"
    widgetDef = tmp
    return widgetDef


def fixComboValues(key, val) -> list:
    # The 'values' key has this saved format. This might be a tk thing.
    # It needs to be converted to a list
    log.debug("key %s ->%s<-has a weird value", key, val)
    newVal = val.replace("(", "[")
    val = newVal
    newVal = val.replace(")", "]")
    val = newVal
    log.debug("key %s ->%s<-converted to list", key, val)
    return val


def fixWidgetName(wType) -> str:
    t = wType.replace("ttk::", "")
    wType = t
    t = wType.replace("tk::", "")
    return t


def fixWidgetTypeName(wType) -> str:
    """
    reformat a widget name to be used in code
    :param wType:
    :return: the basic str
    """
    # "ttk." prefix names (palette widgets like "ttk.Scale") — capitalise class.
    # These also resolve to ttkbootstrap widgets since we import ttkbootstrap as ttk.
    if wType.startswith("ttk."):
        parts = wType.split(".", 1)
        cls = parts[1][0].upper() + parts[1][1:] if len(parts) > 1 else parts[0]
        return "ttk." + cls
    # "ttk::" is Tk's internal class prefix (e.g. "ttk::button" → "ttk.Button").
    # Maps to ttkbootstrap widgets because we import ttkbootstrap as ttk.
    t = wType.replace("ttk::", "ttk.")
    wType = t
    idx = wType.find(".")
    if idx == -1:  # Plain tk widget (no namespace prefix)
        t = "tk." + wType
        wType = t
    for ch in alphaList:
        t = wType.replace("." + ch, "." + ch.upper())
        wType = t
    return wType


def getPhotoImage(widgetName, key) -> PhotoImage | None:
    # the 'image=' part of tkinter widget parameters is tricky to save and restore.
    # The imageName and path to file is in myVars.widgetImageFilenames
    count = -1
    for w in widgetImageFilenames:
        count += 1
        if widgetName == w[WIDGET]:
            if key == w[KEY]:
                log.info("getPhotoImage %s", str(w))
                fileName = w[FILENAME]
                try:
                    if os.path.isfile(fileName):
                        newImage = tk.PhotoImage(file=fileName)
                        n = [widgetName, key, fileName, newImage]
                        widgetImageFilenames[count] = n
                        return newImage
                except IndexError:
                    log.error("IndexError in %s", str(w))
                    return None
    return None
