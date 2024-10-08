import logging
import os
import os.path
import pickle
import sys
import re
import tkinter as tk
from collections import defaultdict
from functools import partial
from tkinter.colorchooser import askcolor
from typing import Any
import tkfontchooser as tkfc
import coloredlogs
import ttkbootstrap as tboot
# import tkfilebrowser as tkfb
# from tkfilebrowser import askopendirname
from ttkbootstrap.dialogs.dialogs import Messagebox
from ttkbootstrap.dialogs.dialogs import Querybox
# FontDialog does not work correctly.
# from ttkbootstrap.dialogs.dialogs import FontDialog
import createWidget as cw
import pytkguivars as myVars
import cdefs as C
# This fixed a bug in ttkbootstrap
# from PIL import Image
# Image.CUBIC = Image.BICUBIC

# This will be from a project's default
useTheme = "cyborg"
rootWin = tboot.Window(themename=useTheme,iconphoto="snake.png")
rootWin.eval("tk::PlaceWindow . pointer")
mainFrame = tboot.Frame()
rootWin.title("Python Tk GUI Builder")
iconBar = tboot.Frame()
mainCanvas = tboot.Canvas()
log = logging.getLogger(name="mylogger")


def setTheme(theme: object):
    # global style
    myVars.theme = theme
    log.debug(theme)
    # style = tboot.Style(rootWin)
    myVars.style.theme_use(theme)
    # for color_label in style.colors:
    #     color = style.colors.get(color_label)
    #     print(color_label,color)


def tree():
    return defaultdict(tree)


def Merge(dict1, dict2) -> dict:
    res = {**dict1, **dict2}
    return res


def createFileName(sa,sb,sc) -> str:
    fileName = ""
    if sa is None:
        s1 = ""
    else:
        s1 = sa.strip()
    if sc is None:
        s3 = ""
    else:
        s3 = sc.strip()
    if sb is None:
        fileName = s1 + "/" + s3
    else:
        s2 = sb.rstrip()
        fileName = s1 + "/" + s2 + "/" + s3
    # For the weirdness of Windows, does nothing in Mac,Linux,Unix
    os.path.normcase(fileName)
    return fileName


def openFile(fileName,mode):
    f: any
    try:
        f = open(fileName, mode, encoding="utf8")
    except FileNotFoundError as e:
        log.warning("File not found %s exception %s", fileName, str(e))
        f = open(fileName, "x", encoding="utf8")
    return f


def createCleanNameList() -> list:
    cleanNameList = []
    for c in cw.createWidget.widgetNameList:
        name = c[cw.NAME]
        parent = c[cw.PARENT]
        children = c[cw.CHILDREN]
        cleanNameList.append([name, parent, "", children])
    return cleanNameList


def findWidgetsParent(widgetName) -> str:
    for nameEntry in cw.createWidget.widgetNameList:
        if widgetName == nameEntry[cw.NAME]:
            return nameEntry[cw.PARENT]
    log.error("Failed to find a parent for %s", widgetName)
    return ""


def workOutWidgetCreationOrder() -> list:
    createdWidgetOrder = [myVars.rootWidgetName]
    sanityCheckCount = 0
    finished = False
    while not finished:
        finished = True
        sanityCheckCount += 1
        if sanityCheckCount > 10000:
            log.critical("Loop is not exiting Ahhhhh %d", sanityCheckCount)
            break
        for nameEntry in cw.createWidget.widgetNameList:
            if nameEntry:
                widgetName = nameEntry[cw.NAME]
                widgetParent = nameEntry[cw.PARENT]
                if widgetName in createdWidgetOrder:
                    # This has already been created
                    continue
                else:
                    finished = False
                if widgetParent in createdWidgetOrder:
                    # Parent has been created, do proceed
                    createdWidgetOrder.append(widgetName)
                else:
                    finished = False
    return createdWidgetOrder

def createCleanImageList() -> []:
    cleanFilenames: [] = []
    if myVars.widgetImageFilenames is None:
        return cleanFilenames
    for f in myVars.widgetImageFilenames:
        c = [f[myVars.WIDGET],f[myVars.KEY] ,f[myVars.FILENAME],None]
        cleanFilenames.append(c)
    log.debug("widgetImageFilenames %s",str(myVars.widgetImageFilenames))
    log.debug("cleanFilenames %s",str(cleanFilenames))
    return cleanFilenames

def saveProjectFile(fileName,fileType,projectData):
    ftails = [5,4,3,2,1]
    completeFileName = fileName + fileType
    for t in ftails:
        testNameA = str(fileName) + str("-save") + str(t) + fileType
        if os.path.isfile(testNameA):
            testNameB = fileName + "-save" + str(t+1) + fileType
            os.rename(testNameA, testNameB)

    if os.path.isfile(completeFileName):
        testNameA = fileName + "-save" + str(1) + fileType
        os.rename(completeFileName, testNameA)

    f = open(completeFileName, "wb")
    try:
        pickle.dump(projectData, f)
    except TypeError as e:
        log.error("Exception TypeError %s", str(e))
        log.warning("Error in Project Data \n%s", str(projectData))
    f.close()

def saveProject():
    widgetCount = 0
    createdWidgetOrder = [myVars.rootWidgetName]
    width = 0  # mainCanvas.winfo_width
    height = 0  # mainCanvas.winfo_height
    cleanList = createCleanNameList()
    projectData = {
        "ProjectName": "test",
        "ProjectPath": "/tmp/test",
        "width": width,
        "height": height,
        "theme": myVars.theme,
        "widgetNameList": cleanList,
        "backgroundColor": myVars.backgroundColor,
        "imageFileNames" : createCleanImageList(),
    }
    # Work out the order to create the Widgets so the parenting is correct
    createdWidgetOrder = workOutWidgetCreationOrder()
    log.debug("createdWidgetOrder %s", str(createdWidgetOrder))
    myVars.createdWidgetOrder = createdWidgetOrder
    for widgetName in createdWidgetOrder:
        # widgetParent = findWidgetsParent(widgetName)
        if widgetName == myVars.rootWidgetName:
            continue
        newWidget = myVars.saveWidgetAsDict(widgetName)

        log.debug("widgetCount %d newWidget %s", widgetCount, str(newWidget))
        widgetCount += 1
        # project["widgetName"] = .widgetName
        tmpData = Merge(projectData, newWidget)
        projectData = tmpData
    projectData1 = Merge(projectData, {"widgetCount": widgetCount})
    projectData = projectData1
    log.debug("projectData ->%s<-", str(projectData))
    myVars.projectDict = projectData
    fileName = myVars.projectFileName
    log.debug("projectFileName ->%s<-", fileName)
    saveProjectFile(fileName,myVars.fileType,projectData)
    log.debug("projectData %s",projectData)
    myVars.lastProjectSaved = myVars.projectFileName
    myVars.projectSaved = True
    # Store the last project saved
    # Store myVars.projectName in configPath
    configPath = getConfigPath()
    name = createFileName(configPath,None,myVars.lastProjectFile)
    sys.stdout = open(name, "w", encoding="utf8")
    print(myVars.projectName)
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    mainFrame.config(text=myVars.projectName)

def buildPython() -> str:
    """
    Generate python code and do a trial run
    """
    functions = []
    tkvars = []
    # if myVars.projectDict == {}:
    saveProject()
    runDict = myVars.projectDict
    nWidgets = runDict.get("widgetCount")
    largestWidth = 200
    largestHeight = 200
    # print('width',width,'height',height)
    createdWidgetOrder = workOutWidgetCreationOrder()
    print("nWidgets", nWidgets)
    print("# -------------------------")
    configPath = getConfigPath()
    fileName = configPath + "/" + "test.py"
    # sys.stdout = open("/tmp/test.py", "w", encoding="utf8")
    sys.stdout = open(fileName, "w", encoding="utf8")
    print("import tkinter as tk\nimport ttkbootstrap as tboot\n")
    themeName = myVars.theme
    title = myVars.projectName
    print("themeName = '" + themeName + "'\n")
    print("title = '" + title + "'\n")
    print("rootWin = tboot.Window(themename=themeName,title=title)")
    rootName = myVars.rootWidgetName
    print(
        rootName
        + " = tboot.Frame(rootWin, width=40, height=100, relief='ridge', borderwidth=1)"
    )
    # Create widgets on the rootFrame first
    # for widgetName in myVars.createdWidgetOrder:
    # First pass is to get the command and variable names
    for widgetName in createdWidgetOrder:
        if widgetName == rootName:
            continue
        wDict = runDict.get(widgetName)
        if wDict is not None:
            parentName = findWidgetsParent(widgetName)
            wType = wDict.get("WidgetName")
            t = myVars.fixWidgetTypeName(wType)
            wType = t
            keyCount = widgetName + "-KeyCount"
            widgetDef = widgetName + " = " + wType + "(" + parentName
            nKeys = wDict.get(keyCount)
            for a in range(nKeys):
                useValQuotes = True
                attribute = "Attribute" + str(a)
                aDict = wDict.get(attribute)
                key = aDict.get("Key")
                val = aDict.get("Value")
                if key == "image":
                    if val > "":
                        val = str(widgetName) + str(key)

                if key == "command":
                    if val > "":
                        log.info("command ->%s<-",val)
                        functions.append(val)
                if key == "textvariable":
                    if val > "":
                        log.info("textvariable ->%s<-",val)
                        tkvars.append(val)
                if key == "variable":
                    if val > "":
                        log.info("variable ->%s<-",val)
                        tkvars.append(val)

    print("")
    print("####### TK variables #######")
    for f in myVars.widgetImageFilenames:
        name = str(f[myVars.WIDGET]) + str(f[myVars.KEY])
        print(name + " = tk.PhotoImage(file='" + f[myVars.FILENAME] + "')" )
    for v in tkvars:
        print(v + " = tk.StringVar(rootWin,'0.0')")
    print("")
    print("####### Functions #######")
    for f in functions:
        print("")
        print("def " + f + "():")
        print("    print('" + f + "') ")
    print("")
    for widgetName in createdWidgetOrder:
        # widgetId = "Widget" + str(n)
        if widgetName == rootName:
            continue
        parentName = findWidgetsParent(widgetName)
        if len(parentName) < 2:
            log.warning(
                "widget %s has no parent. Has it been deleted?", widgetName)
            continue
        # Get the parent Name
        wDict = runDict.get(widgetName)
        if wDict is not None:
            log.debug("Dictionary for %s = %s", widgetName, str(wDict))
            wType = wDict.get("WidgetName")
            t = myVars.fixWidgetTypeName(wType)
            wType = t
            keyCount = widgetName + "-KeyCount"
            widgetDef = widgetName + " = " + wType + "(" + parentName
            nKeys = wDict.get(keyCount)
            specialKeys = ["command","textvariable","variable","image"]
            for a in range(nKeys):
                useValQuotes = True
                attribute = "Attribute" + str(a)
                aDict = wDict.get(attribute)
                key = aDict.get("Key")
                val = aDict.get("Value")
                if key in specialKeys:
                    useValQuotes = False
                if key == "from":
                    # Bug in tkinter -- no
                    # 'from' is a python keyword
                    key = "from_"
                if val.find("<") > -1:
                    # Typically, this a TK object that is in < xxx > format
                    log.warning(
                        "key ->%s<- value ->%s<- has a weird value", key, val)
                    continue
                if val.find("(") > -1:
                    # '(' is in lists for combo boxes
                    # The 'values' key has this saved format.
                    # This might be a tk thing.
                    # It needs to be converted to a list
                    newVal = myVars.fixComboValues(key, val)
                    val = newVal
                    useValQuotes = False
                if len(val) > 0:
                    # keys are not consistent ...
                    if useValQuotes:
                        tmpWidgetDef = widgetDef + ", " + key + "='" + val + "'"
                    else:
                        if key == "image":
                            val = str(widgetName) + key
                        tmpWidgetDef = widgetDef + ", " + key + "=" + val
                    widgetDef = tmpWidgetDef
            print(widgetDef + ")")
            if myVars.geomManager == "Place":
                place = wDict.get("Place")
                x = place.get("x")
                y = place.get("y")
                width = place.get("width")
                height = place.get("height")
                try:
                    widthPos = int(x) + int(width)
                    heightPos = int(y) + int(height)
                    if widthPos > largestWidth:
                        largestWidth = widthPos
                    if heightPos > largestHeight:
                        largestHeight = heightPos
                except ArithmeticError as e:
                    log.warning("ArithmeticError %s", str(e))
                except ValueError as e:
                    log.warning("ValueError %s", str(e))

                anchor = place.get("anchor")
                bordermode = place.get("bordermode")
                print(
                    widgetName
                    + ".place("
                    + "x="
                    + x
                    + ", y="
                    + y
                    + ", width="
                    + width
                    + ", height="
                    + height
                    + ", anchor='"
                    + anchor
                    + "', bordermode='"
                    + bordermode
                    + "')"
                )
            # if myVars.geomManager == 'Grid':
            # if myVars.geomManager == 'Pack':
            else:
                log.error("Geometry Manager %s is TBD", myVars.geomManager)
    largestWidth += 20
    largestHeight += 20
    geom = str(largestWidth) + "x" + str(largestHeight)
    print("####### Main  #######")
    print("rootWin.geometry('" + geom + "')")
    print("rootWin.resizable(True, True)")
    print("rootWin.columnconfigure(0, weight=1)")
    print("rootWin.rowconfigure(0, weight=1)")
    print("sg0 = tboot.Sizegrip(rootWin)")
    print("sg0.grid(row=1, sticky=tk.SE)")
    print(rootName + ".place(x=0, y=0, relwidth=1.0, relheight=1.0)")
    print("\nrootWin.mainloop()")
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    # sys.stdout = open(fileName, "w", encoding="utf8")
    # cmd = "python3 " + fileName + " &"
    # os.system(cmd)
    return fileName

def runMe():
    fileName = buildPython()
    log.info("python fileName ->%s<-",fileName)
    cmd = "python3 " + fileName + " &"
    os.system(cmd)

def generatePython():
    # configPath = getConfigPath()
    fileName = buildPython()
    home = os.environ["HOME"]
    initialFile = myVars.projectName + ".py"
    newFile = tk.filedialog.asksaveasfilename(initialdir=home,
                                              initialfile=initialFile,
                                              filetypes=[("Python file","*.py")],
                                              defaultextension="py")
    # Note: get the directory name for the samed file and add this to the .config
    myVars.saveDirName = os.path.dirname(newFile)
    log.info("save dir %s saved file = %s",myVars.saveDirName,newFile)
    cmd = "cp " + fileName + " " + newFile
    os.system(cmd)


def deleteWidgetData():
    log.info("Removing all existing Widgets")
    for w in cw.createWidget.widgetList:
        w.destroy()
    cw.createWidget.widgetNameList = []
    cw.createWidget.widgetList = []
    cw.createWidget.widgetId = 0
    cw.createWidget.lastCreated = None
    myVars.widgetImageFilenames = []


def checkWidgetNameList():
    """
    Check Name List before exporting or using. Remove deleted objects
    Check for child entries that are left over from re parenting operations
    """
    # NAME 0 PARENT 1 WIDGET 2 CHILDREN 3
    for nl1 in cw.createWidget.widgetNameList:
        widgetName1 = nl1[cw.NAME]
        parentName1 = nl1[cw.PARENT]
        for nl2 in cw.createWidget.widgetNameList:
            widgetName2 = nl2[cw.NAME]
            if parentName1 != widgetName2:
                # This is not first parent,
                # thus it should not have widgetName1 as a child
                found = False
                children2 = nl2[cw.CHILDREN]
                for child in children2:
                    if child == widgetName1:
                        found = True
                if found:
                    children2.remove(widgetName1)


def changeParentOfTo(widgetName, parentName):
    # find both widgets
    widgetList = cw.findPythonWidgetNameList(widgetName)
    parentList = cw.findPythonWidgetNameList(parentName)
    if widgetList == [] or parentList == []:
        log.error("Empty Lists")
        return
    widget = widgetList[cw.WIDGET]
    parent = parentList[cw.WIDGET]

    if myVars.geomManager == "Place":
        widget.place(in_=parent)
        widget.parent = parent
        widget.update()
    # if myVars.geomManager == 'Grid':
    # if myVars.geomManager == 'Pack':
    else:
        log.error("Geometry Manager %s is TBD", myVars.geomManager)
    tk.Misc.lift(widget, parent)
    cw.reparentWidget(widgetName, parent)


def setLabelBorderWidth(width):
    for w in cw.createWidget.widgetList:
        if w is not None:
            name = w.widgetName
            C.printf("Name %s widget %s", name, w)
            if name == "ttk::label":
                w.configure(borderwidth=width)


def hideLabelBorders():
    setLabelBorderWidth(0)


def showLabelBorders():
    setLabelBorderWidth(1)


def setThemeColor():
    for w in cw.createWidget.widgetList:
        if w is not None:
            name = w.widgetName
            C.printf("Name %s widget %s", name, w)
            # if name == 'ttk::label':
            try:
                w.configure(bootstyle="primary")
            except ValueError as e:
                log.error("%s raised exceptopn %s", w, e)


def setDefaultStyleFont():
    setDefaultFont("style")


def setDefaultLabelFont():
    setDefaultFont("label")


def setDefaultFont(which):
    font: dict
    font = tkfc.askfont(mainFrame, text="Font To Use")

    # This does not work correctly
    # using the standard askfont
    # fd = FontDialog()
    # fd.show()
    # log.info("font %s",fd.result)
    # font = fd.result
    # log.debug("font=%s", str(font))

    font_str = myVars.checkFontDict(font)
    font_str = font
    log.debug("font_str=%s", font_str)
    if font_str != "":
        if which == "style":
            myVars.style = tboot.Style()  # .style.Style()
            for w in myVars.widgetsUsed:
                objType = "T" + w
                # need to check if 'font' is valid for the widget typeG
                # themes = myVars.style.theme_names()
                # C.printf("Themes for %s == %s\n",objType,themes)
                if objType != "TCanvas":
                    myVars.style.configure(objType, font=font_str)
                    names = myVars.style.element_names()
                    # C.printf("Names for %s == %s\n",objType,names)
                    for e in names:
                        C.printf("objType %s Name: %s\n", objType, e)
                        myVars.style.configure(e, font=font_str)
                        myVars.style.configure(e, textfont=font_str)
                # Look for child widgets for label.style
                # # myVars.style.configure(objType,
                # labelfont=font_str)
        elif which == "label":
            # Walk through all label widgets and find fonts
            for w in cw.createWidget.widgetList:
                if w is not None:
                    name = w.widgetName
                    print("Name %s widget %s", name, w)
                    # if name == 'ttk::label':
                    keys = w.keys()
                    if "font" in keys:
                        try:
                            w.configure(font=font_str)
                        except ValueError as e:
                            log.error("%s raised exceptopn %s", w, e)


def newProject():
    configPath = getConfigPath()
    C.printf("configPath %s\n", configPath)
    name = Querybox.get_string("New Project name")
    C.printf("configPath %s %s\n", configPath, name)
    os.mkdir(configPath + "/" + name)
    myVars.projectName = name
    mainFrame.config(text=myVars.projectName)

def getConfigPath() -> str:
    if "APPDATA" in os.environ:
        confighome = os.environ["APPDATA"]
    elif "XDG_CONFIG_HOME" in os.environ:
        confighome = os.environ["XDG_CONFIG_HOME"]
    else:
        confighome = os.path.join(os.environ["HOME"], ".config")
    configPath = os.path.join(confighome, myVars.programName)
    if os.path.isdir(configPath):
        log.debug("Config Path %s %s %s", configPath,
                  confighome, myVars.programName)
    else:
        os.mkdir(configPath)
        log.info("Creating configPath %s", configPath)

    return configPath


def closeProject():
    configPath = getConfigPath()
    C.printf("Close Project %s ", configPath)


def selectDir(name):
    C.printf("Name %s", name)


# open an older saved file
def openBackupFile():
    configPath = getConfigPath()
    # Open the config path dir and search for 'tileType'
    filePath = tk.filedialog.askopenfilename(
        title="Select a backup project File",
        initialdir=configPath,
        filetypes=[("PyTkQuickGui pickle files", myVars.fileType), ("All files", "*.*")])

    if filePath:
        # Work out the probable project name
        projectPath = os.path.dirname(filePath)
        projectName = os.path.basename(projectPath)
        log.debug("Selected File: %s \nProjectPath %s \nProject %s",filePath,projectPath,projectName)
        loadProject(projectName,filePath)

def loadProject(project,altFileName):
    """
    Load a project from a saved file (in pickle format)
    """
    configPath = getConfigPath()
    folder = createFileName(configPath,None,project)
    fileName = ""
    fullFileName = ""
    if altFileName is None:
        # folder = configPath + '/' + project.strip()
        log.info("folder ->%s<-",folder)
        if project is None:
            log.info("config Path =>%s<=", configPath)
            folder = tk.filedialog.askdirectory(
                mustexist=True, initialdir=configPath, title="Select Project Directory"
            )
        log.info("Load Project ->%s<-", folder)
        if folder != configPath:
            myVars.projectName = os.path.basename(folder)
            myVars.projectPath = folder
            log.info("Load Project ->%s<- ->%s<-",
                     myVars.projectPath, myVars.projectName)
        else:
            log.warning("No project selected Try Again")
            Messagebox.show_error(title="No Project Selected", message="The Directory Selection box is not intuitive.\nDouble click on project name\nTry Again or create a new Project")
            return
        # projFileName = myVars.projectName + ".pk1"
        projFileName = myVars.projectName
        fileName = os.path.join(myVars.projectPath, projFileName)
        myVars.projectFileName = fileName
        fullFileName = fileName + myVars.fileType
    else : # loading a backup fileName
        projFileName = project
        fileName = altFileName
        myVars.projectName = os.path.basename(folder)
        myVars.projectPath = folder
        fullFileName = fileName

    mainFrame.config(text=myVars.projectName)
    data = any
    runDict = data
    nWidgets = 0
    closeFile = True
    widgetNameList = []
    deleteWidgetData()
    try:
        f = open(fullFileName, "rb")
    except FileNotFoundError as e:
        log.warning("File not found -->%s<-- exception %s", fullFileName, str(e))
        os.mknod(fullFileName)
        closeFile = False
    if closeFile:
        try:
            data = pickle.load(f)
            f.close()
        except EOFError as e:
            log.warning("pickle error (empty file?) %s exception %s",fullFileName,str(e))
        except UnicodeDecodeError as e:
            log.warning("pickle error (empty file?) %s exception %s",fullFileName,str(e))

    try:
        runDict = data
        log.debug(runDict)
        myVars.backgroundColor = runDict.get("backgroundColor")
        widgetNameList = runDict.get("widgetNameList")
        nWidgets = runDict.get("widgetCount")
        myVars.widgetImageFilenames = runDict.get("imageFileNames")

    except AttributeError as e:
        log.info("AttributeError in project file.")

    widgetsFound = 0
    n = 0
    while widgetsFound < nWidgets:
        # for n in range(nWidgets + 4):
        widgetId = "Widget" + str(n)
        wDict = runDict.get(widgetId)
        if wDict is not None:
            widgetsFound += 1
            widgetDef = myVars.buildAWidget(n, wDict)
            try:
                # widget = ast.literal_eval(widgetDef)
                log.info("widgetDef ->%s<-", widgetDef)
                # imageName = str(widgetId) + "image"
                widget = eval(widgetDef)
            except NameError as e:
                log.error("%d dict %s eval() NameError %s",
                          n, str(wDict), str(e))
                continue
            except TypeError as e:
                log.error("%d dict %s eval() TypeError %s",
                          n, str(wDict), str(e))
                continue
            # w = cw.createWidget(mainCanvas,widget)
            w = cw.createWidget(mainFrame, widget)

            if myVars.geomManager == "Place":
                place = wDict.get("Place")
                log.debug(place)
                w.addPlace(place)
            # if myVars.geomManager == 'Grid':
            # if myVars.geomManager == 'Pack':
            else:
                log.error("Geometry Manager %s is TBD", myVars.geomManager)
        n += 1
        if n > (nWidgets * 10):
            log.error(
                "Cannot locate All Widgets tried %d times expected to find %d found %d",
                n,
                nWidgets,
                widgetsFound,
            )
            break

    # using widgetNameList, set the hierarchy
    # NAME 0 PARENT 1 WIDGET 2 CHILDREN 3
    for nl in widgetNameList:
        # Does this widget have a different Parent or have Children?
        # The tcl widget names were removed from this list ( nl[WIDGET] )
        name = nl[cw.NAME]
        parent = nl[cw.PARENT]
        children = nl[cw.CHILDREN]
        if len(name) > 2:
            log.debug("name %s parent %s children %s", name, parent, children)
            for child in children:
                log.debug("    %s has a child %s", name, child)
                changeParentOfTo(child, name)
            if parent != myVars.rootWidgetName:
                log.debug("%s is the parent of %s", parent, name)
                changeParentOfTo(name, parent)
        else:
            log.warning("name %s parent %s children %s",
                        name, parent, children)
            log.warning("widgetNameList %s", str(widgetNameList))

    checkWidgetNameList()
    mainFrame.config(text=myVars.projectName)

def loadLastProject():
    configPath = getConfigPath()
    fileName = createFileName(configPath,None,myVars.lastProjectFile)
    # f = C.fopen(fileName,"r")
    f = openFile(fileName,"r")
    project = f.read()
    f.close()
    loadProject(project,None)
    mainFrame.config(text=myVars.projectName)

def loadProjectWrapper():
    loadProject(None,None)

def exitApp():
    mb = Messagebox.yesnocancel("Save project before exiting ?","Save Project")
    if mb == "Cancel":
        return
    elif mb == "Yes":
        saveProject()
    rootWin.destroy()


def widgetTree():
    for w in cw.createWidget.widgetList:
        print(
            "WidgetList",
            str(w),
            w.winfo_class(),
            w.winfo_parent(),
            w.winfo_children(),
            w.winfo_geometry(),
        )
    for nl in cw.createWidget.widgetNameList:
        print("WidgetNameList", nl)

    for il in myVars.widgetImageFilenames:
        print("widgetImageFilename %s",il)


def chooseBackground():
    # global mainCanvas
    colors = askcolor(title="Tkinter color chooser")
    if colors[1] is not None:
        mainCanvas.configure(bg=colors[1])
        mainCanvas.update()
        myVars.backgroundColor = colors[1]
def welcome():
    about = '''PyTkGui:
    Chris McGowan 2024.
    A tool to build a simple TkInter GUI.
	This tool uses ttkbootstrap widgets.
	A website - youtube - pdf TBD.'''
    
    # remove leading whitespace from each line
    # this does not work on python 3.12
    # about2 = re.sub("\n\s*", "\n", about)
    about2 = about
    Messagebox.show_info(message=about2,title="Welcome")

def helpMe():
    about = '''Basic Actions:
    Right click on the background to get a list of Widgets.
    A selected Widget will place itself where the mouse is.
    Left click hold and drag to move Widgets around.
    Left click and drag close to the inside edge of Widgets to resize.
    Right Click on Widgets to choose Edit and Layout windows.'''

    # remove leading whitespace from each line
    # this does not work on python 3.12
    # about2 = re.sub("\n\s*", "\n", about)
    about2 = about
    Messagebox.show_info(message=about2,title="Help")

def buildMenu():
    # global rootWin
    menuBar = tboot.Menu(rootWin)
    mystyle = tboot.Style()
    themes = []
    for themeName in mystyle.theme_names():
        themes.append(themeName)
    # style = tboot.Style(rootWin)
    # themes = style.theme_names()
    # log.debug(themes[1])
    # themes
    rootWin.config(menu=menuBar)
    fileMenu = tboot.Menu(menuBar, tearoff=0)
    # add menu items to the File menu
    fileMenu.add_command(label="New Project", command=newProject)
    fileMenu.add_command(label="Open last Project", command=loadLastProject)
    fileMenu.add_command(label="Open Project", command=loadProjectWrapper)
    fileMenu.add_command(label="Close Project", command=closeProject)
    fileMenu.add_command(label="Save Project", command=saveProject)
    fileMenu.add_command(label="Trial Run", command=runMe)
    fileMenu.add_command(label="Generate Python", command=generatePython)
    fileMenu.add_separator()

    fileMenu.add_command(label="Exit", command=exitApp)

    # add a submenu
    subMenu = tboot.Menu(fileMenu, tearoff=0)
    # subMenu.add_command(label='Keyboard Shortcuts')
    subMenu.add_command(label="Background Color", command=chooseBackground)
    subMenu.add_command(label="Themes")
    subMenu.add_command(label="Color Themes")

    menuBar.add_cascade(label="File", menu=fileMenu, underline=0)
    # widget Menu
    themeMenu = tboot.Menu(menuBar, tearoff=0)
    for t in themes:
        mypartial = partial(setTheme, t)
        themeMenu.add_command(label=t, command=mypartial)

    toolsMenu = tboot.Menu(menuBar, tearoff=0)
    toolsMenu.add_command(label="Hide Label Borders", command=hideLabelBorders)
    toolsMenu.add_command(label="Show Label Borders", command=showLabelBorders)
    toolsMenu.add_command(
        label="Set default bootstyle type", command=setThemeColor)
    toolsMenu.add_command(label="Set default label font",
                          command=setDefaultLabelFont)
    toolsMenu.add_command(label="Set default style font",
                          command=setDefaultStyleFont)
    toolsMenu.add_command(label="Open backup file", command=openBackupFile)
    toolsMenu.add_command(label="Widget Tree", command=widgetTree)
    # create the Help menu
    helpMenu = tboot.Menu(menuBar, tearoff=0)

    helpMenu.add_command(label="Welcome",command=welcome)
    helpMenu.add_command(label="Help",command=helpMe)

    menuBar.add_cascade(label="Theme", menu=themeMenu, underline=0)
    # add the Help menu to the menuBar
    menuBar.add_cascade(label="Tools", menu=toolsMenu, underline=0)
    menuBar.add_cascade(label="Help", menu=helpMenu, underline=0)

    # add the File menu to the menuBar
    fileMenu.add_cascade(label="Preferences", menu=subMenu)


def doNothing():
    # Not sure what this is for . Delete later
    pass


def drawGridLines():
    # Get dimensions ....
    mainCanvas.update()
    width = mainCanvas.winfo_width()
    height = mainCanvas.winfo_height()
    # log.debug("width ",width," height ",height," snapTo ",myVars.snapTo)
    log.debug("Width %d height %d snapTo %s", width, height, myVars.snapTo)


def sizeGripRelease(event):
    log.debug(event)
    drawGridLines()


def createWidgetPopup(event, widgetName):
    defaultStyle = "primary"
    defaultCursor = "arrow"
    # Create a widget 'widgetName' at the current mouse pos (x,y)
    x = event.x
    y = event.y
    w: Any
    if widgetName == "Frame":
        w = tboot.Frame(mainFrame, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Labelframe":
        w = tboot.Labelframe(
            mainFrame,
            text=widgetName,
            borderwidth=1,
            relief=tk.SOLID,
            labelanchor=tk.N,
            cursor=defaultCursor,
            style=defaultStyle,
        )
    elif widgetName == "Panedwindow":
        w = tboot.Panedwindow(
            mainFrame, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Label":
        w = tboot.Label(
            mainFrame,
            text=widgetName,
            borderwidth=1,
            relief=tk.SOLID,
            anchor=tk.CENTER,
            cursor=defaultCursor,
            style=defaultStyle,
        )
    elif widgetName == "Button":
        w = tboot.Button(
            mainFrame, text=widgetName, cursor=defaultCursor, style=defaultStyle
        )
    elif widgetName == "Entry":
        w = tboot.Entry(mainFrame, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Combobox":
        w = tboot.Combobox(mainFrame, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Notebook":
        w = tboot.Notebook(mainFrame, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Canvas":
        w = tboot.Canvas(
            mainFrame, borderwidth=1, relief=tk.SOLID, cursor=defaultCursor
        )
        #                 ,highlightthickness=1,highlightbackground='red')
        # w.configure(scrollregion = w.bbox("all"))
    elif widgetName == "Spinbox":
        w = tboot.Spinbox(mainFrame, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Checkbutton":
        w = tboot.Checkbutton(
            mainFrame, text=widgetName, cursor=defaultCursor, style=defaultStyle
        )
    elif widgetName == "Radiobutton":
        w = tboot.Radiobutton(
            mainFrame, text=widgetName, cursor=defaultCursor, style=defaultStyle
        )
    elif widgetName == "Scale":
        w = tboot.Scale(mainFrame, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Progressbar":
        w = tboot.Progressbar(
            mainFrame, value=50.0, cursor=defaultCursor, style=defaultStyle
        )
    elif widgetName == "Floodgauge":
        w = tboot.Floodgauge(
            mainFrame, value=50, cursor=defaultCursor, style=defaultStyle
        )
    # Meter does not work correctly
    elif widgetName == "Meter":
        # Meter dows not have a parent ....
        w = tboot.Meter(
            metersize=180,
            padding=5,
            amountused=25,
            metertype="semi",
            subtext="miles per hour",
            interactive=True,
        )
        # w.configure(subtext="Read the Docs!")
    # Labeled Scale is not in ttk bootstrap
    # elif widgetName == 'Labelscale':
    #    w = tboot.LabeledScale(mainFrame,cursor=defaultCursor,
    # style=defaultStyle)
    else:
        log.warning("Widget %s not implemented", widgetName)
        return
    cw.createWidget(mainFrame, w)

    if myVars.geomManager == "Place":
        w.place(x=x, y=y, width=72, height=32)
    # elif myVars.geomManager == 'Grid':
    # elif myVars.geomManager == 'Pack':
    else:
        log.error("Geometry Manager %s is TBD", myVars.geomManager)


def rightMouseDown(event):
    # global mainCanvas
    log.debug("rightMouseDown -- event %s", str(event))
    popup = tboot.Menu(mainFrame, tearoff=0)
    for wName in myVars.containerWidgetsUsed:
        popup.add_command(
            label=wName, command=lambda e=event, w=wName: createWidgetPopup(
                e, w)
        )
    for wName in myVars.widgetsUsed:
        popup.add_command(
            label=wName, command=lambda e=event, w=wName: createWidgetPopup(
                e, w)
        )
    popup.add_separator()
    popup.add_command(label="Close", command=popup.destroy)
    try:
        popup.tk_popup(event.x_root, event.y_root, 0)
    finally:
        popup.grab_release()


def buildGrid(rows, cols):
    """
    :rtype: object
    """
    global mainCanvas
    mainCanvas = tboot.Canvas(
        mainFrame, width=40, height=100, relief=tk.SOLID, borderwidth=1
    )
    mainCanvas.grid(
        row=0, column=0, columnspan=cols, rowspan=rows, padx=5, pady=5, sticky="NSEW"
    )
    mainCanvas.bind("<Button-3>", rightMouseDown)
    drawGridLines()
    # mainCanvas.bind('<Motion>',frameMove)


def buildMainGui():
    global mainFrame

    buildMenu()

    # topFrame = tboot.Frame(rootWin, width=600, height=15)
    # topFrame = tboot.Frame(rootWin)
    # topFrame.grid(row=0, column=0, sticky="N")
    # topLabel = tboot.Label(topFrame, text="TBD");
    # topLabel.grid(row=0, column=0, sticky="W")
    mainFrame = tboot.Labelframe(rootWin, width=600, height=150, labelanchor=tk.N,text="No Project Selected")
    mainFrame.grid(row=0, column=0, sticky="NWES")
    cw.createWidget.baseRoot = mainFrame

    mainFrame.columnconfigure(0, weight=1)
    mainFrame.rowconfigure(0, weight=1)
    sg0 = tboot.Sizegrip(mainFrame)
    sg0.grid(row=1, sticky=tk.SE)
    sg0.bind("<ButtonRelease-1>", sizeGripRelease)

    rootWin.geometry("800x800")
    rootWin.resizable(True, True)
    rootWin.columnconfigure(0, weight=1)
    rootWin.rowconfigure(0, weight=1)
    # rootWin.getLogger()

    buildGrid(24, 24)


if __name__ == "__main__":
    logging.basicConfig()
    # logging.basicConfig(format=logFormat)
    # log = logging.getLogger(name='mylogger')
    coloredlogs.install(
        logger=log, fmt="%(levelname)-8s| %(lineno)-4d %(filename)-20s| %(message)s"
    )
    # arg1 = "warn"
    arg1 = "info"
    try:
        arg1 = sys.argv[1]
    except IndexError:
        arg1 = "warn"

    if arg1 == 'info':
        coloredlogs.set_level(logging.INFO)
    elif arg1 == 'debug':
        coloredlogs.set_level(logging.DEBUG)
    else:
        coloredlogs.set_level(logging.WARN)
    myVars.initVars()
    myVars.theme = useTheme
    log.info("mainFrame %s %s",mainFrame, str(mainFrame))

    buildMainGui()
    myVars.style = tboot.Style()
    rootWin.mainloop()
