import logging as log
import tkinter as tk
import ttkbootstrap as tboot
import createWidget as cw
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
style: tboot.Style
rootWidgetName: str
ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
createdWidgetOrder: list
alphaList = list(ascii_lowercase)
programName: str = "pytkgui"
containerWidgetsUsed = ("Frame", "Labelframe", "Panedwindow")
projectName: str = "tmp"
projectPath: str = "/tmp/tmp"
projectPath: str = "/tmp/tmp"
projectFileName: str = "/tmp/tmp.pk1"
lastProjectFile: str = "lastProject.txt"
lastProjectSaved: str = ""
projectSaved: bool = False
widgetsUsed = (
    "Label",
    "Button",
    "Entry",
    "Combobox",
    "Notebook",
    "Canvas",
    "Spinbox",
    "Checkbutton",
    "Radiobutton",
    "Scale",
    "Progressbar",
)

# 'Floodgauge','Progressbar','Meter')

# Could be 'Place' 'Grid' or 'Pack'
# Some objects use Grid and Pack internally, and the root Window uses Grid
geomManager = "Place"


def sprintf(buf: str, fmt, *args) -> str:
    tmpStr: str = ""
    tmpStr.format(fmt % args)
    # buf.write(fmt % args)
    buf = tmpStr
    return buf


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


# Common Procs
def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res


def checkFontDict(font: dict) -> str:
    font_str: str = ""
    if font:
        # spaces in the family name need to be escaped
        family = font["family"]
        family_str = family.replace(" ", "\ ")
        font["family"] = family_str
        font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
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
        place = "unknown"
        try:
            place = w.place_info()
            del place["in"]
        except KeyError as e:
            log.error(
                "Key 'in' missing from place exception %s place ->%s<-",
                str(e),
                str(place),
            )
        except tk.TclError as ex:
            log.error("Widget ->%s<- raised an exception %s", str(w), str(ex))
            return {}
        widgetDict = {
            "WidgetName": w.widgetName,
            "WidgetParent": widgetParent,
            "Place": place,
        }
        keyCount = 0
        keys = w.keys()
        if keys:
            for key in keys:
                log.debug("Key->%s<-", key)
                if key != "in":
                    value = w[key]
                    if key == "image":
                        if value:
                            # The value is w.widgetName + key
                            value = widgetName + key
                    log.debug("Value->%s<-", str(value))
                    attrId = "Attribute" + str(keyCount)
                    # Ignore empty values
                    if (value is not None) and (len(str(value)) > -1):
                        widgetAttribute = {
                            attrId: {"Key": key, "Value": str(value)}}
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
    # nKeys = wDict.get(keyCount)
    nKeys = wDict[keyCount]
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
                            newImage = tk.PhotoImage(file=filename)
                            n = [newWidgetName,key,filename,newImage]
                            widgetImageFilenames.append(n)
                            log.info("New image for newWidgetName %s %s",newWidgetName,n)
                            break
                val = "myVars.getPhotoImage('" + newWidgetName + "','" + key + "')"
        # like 'to' 'from' needs to have an underscore
        if key == "from":
            key = "from_"
        # j(' is in lists for combo boxes
        if val.find("<") > -1:
            log.warning(
                "key ->%s<- value ->%s<-has a weird value dict  ->%s<- ",
                key, val, aDict,)
            # Typically, this a TK object that is in < xxx > format
            continue
        if key != 'image' and val.find("(") > -1:
            # The 'values' key has this saved format. This might be a tk thing.
            # It needs to be converted to a list
            newVal = fixComboValues(key, val)
            val = newVal
            useValQuotes = False
        if key == 'image':
            useValQuotes = False
        if len(val) > 0:
            tmpWidgetDef: str = ""
            if useValQuotes:
                tmpWidgetDef = f"{widgetDef},{key}='{val}'"
                # tmpWidgetDef = widgetDef + ',' + key + '=\'' + val + '\''
                # tmpWidgetDef = sprintf("%s,%s='%s'",widgetDef,key,val)
            else:
                tmpWidgetDef = f"{widgetDef},{key}={val}"
                # tmpWidgetDef = widgetDef + ',' + key + '=' + val
                # tmpWidgetDef = sprintf("%s,%s=%s",widgetDef,key,val)
            widgetDef = tmpWidgetDef
    # tmp = sprintf("%s%c)",widgetDef,')')
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
    t = wType.replace("ttk::", "tboot.")
    wType = t
    idx = wType.find(".")
    if idx == -1:  # Not ttk widgets
        t = "tk." + wType
        wType = t
    for ch in alphaList:
        t = wType.replace("." + ch, "." + ch.upper())
        wType = t
    return wType

def getPhotoImage(widgetName,key) -> tk.PhotoImage: 
    # the 'image=' part of tkinter widget parameters is tricky to save and restore.
    # The imageName and path to file is in myVars.widgetImageFilenames
    for w in widgetImageFilenames:
        if widgetName == w[WIDGET]:
            if key == w[KEY]:
                log.info("getPhotoImage %s",str(w))
                fileName = w[FILENAME]
                w[PHOTOIMAGE] = tk.PhotoImage(file=fileName)
                return w[PHOTOIMAGE]

