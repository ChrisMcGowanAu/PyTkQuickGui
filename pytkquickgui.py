import ast
import json
import logging
import os
import os.path
import pickle
import re
import shutil
import sys
import tkinter as tk
from collections import defaultdict
from functools import partial
from tkinter.colorchooser import askcolor
from typing import Any

import coloredlogs
import tkfontchooser as tkfc
import ttkbootstrap as tboot
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox, Querybox
from ttkbootstrap.widgets.scrolled import ScrolledFrame, ScrolledText

import cdefs as C
import createWidget as cw
import pytkguivars as myVars
import undoredo

# FontDialog does not work correctly.
# from ttkbootstrap.dialogs.dialogs import FontDialog

# This will be from a project's default
useTheme = "cyborg"
rootWin = tboot.Window(themename=useTheme, iconphoto="snake.png")
rootWin.eval("tk::PlaceWindow . pointer")
mainFrame = tboot.Frame()
rootWin.title("Python Tk GUI Builder")
iconBar = tboot.Frame()
mainCanvas = tboot.Canvas()
# geomWidgetFrame: inner Frame inside mainCanvas for Grid/Pack modes.
# For Place mode this is None (widgets go directly on mainCanvas).
geomWidgetFrame = None
# _gridOverlayCanvas: transparent tk.Canvas placed *inside* geomWidgetFrame
# so grid guide-lines are drawn on top of the frame background but below widgets.
_gridOverlayCanvas = None
# Grid divider drag state: (axis, index, start_pixel, original_minsize)
# axis: "col" or "row";  index: column or row index being dragged
_grid_drag_state: dict = {}
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


def createFileName(sa, sb, sc) -> str:
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


def openFile(fileName, mode):
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
        c = [f[myVars.WIDGET], f[myVars.KEY], f[myVars.FILENAME], None]
        cleanFilenames.append(c)
    log.debug("widgetImageFilenames %s", str(myVars.widgetImageFilenames))
    log.debug("cleanFilenames %s", str(cleanFilenames))
    return cleanFilenames


def saveProjectFile(fileName, fileType, projectData):
    """Save project data as a human-readable JSON file with rolling backups.

    The file format is plain JSON so projects can be inspected and edited
    in any text editor.  Be careful when hand-editing – an invalid JSON file
    will prevent the project from loading.
    """
    if not projectData:
        log.error("projectData is empty. Not saving")
        return
    # Ensure the directory exists (handles the 'tmp' default project case)
    dirName = os.path.dirname(fileName)
    if dirName and not os.path.isdir(dirName):
        try:
            os.makedirs(dirName, exist_ok=True)
            log.info("Created project directory %s", dirName)
        except OSError as e:
            log.error("Cannot create project directory %s: %s", dirName, e)
            return
    ftails = [5, 4, 3, 2, 1]
    completeFileName = fileName + fileType
    for t in ftails:
        testNameA = str(fileName) + str("-save") + str(t) + fileType
        if os.path.isfile(testNameA):
            testNameB = fileName + "-save" + str(t + 1) + fileType
            os.rename(testNameA, testNameB)

    if os.path.isfile(completeFileName):
        testNameA = fileName + "-save" + str(1) + fileType
        os.rename(completeFileName, testNameA)

    try:
        with open(completeFileName, "w", encoding="utf-8") as f:
            json.dump(projectData, f, indent=2, default=str)
        log.info("Project saved as JSON to %s", completeFileName)
    except (TypeError, OSError) as e:
        log.error("Exception saving JSON %s", str(e))
        log.warning("Error in Project Data \n%s", str(projectData))


def saveProject():
    widgetCount = 0
    createdWidgetOrder = [myVars.rootWidgetName]
    width = 0  # mainCanvas.winfo_width
    height = 0  # mainCanvas.winfo_height
    cleanList = createCleanNameList()
    projectData = {
        "ProjectName": myVars.projectName,
        "ProjectPath": myVars.projectPath,
        "width": width,
        "height": height,
        "theme": myVars.theme,
        "geomManager": myVars.geomManager,
        "generatedPyFile": myVars.generatedPyFile,
        "widgetNameList": cleanList,
        "backgroundColor": myVars.backgroundColor,
        "imageFileNames": createCleanImageList(),
        "groups": myVars.groups,
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
    saveProjectFile(fileName, myVars.fileType, projectData)
    log.debug("projectData %s", projectData)
    myVars.lastProjectSaved = myVars.projectFileName
    myVars.projectSaved = True
    # Store the last project saved
    # Store myVars.projectName in configPath
    configPath = getConfigPath()
    name = createFileName(configPath, None, myVars.lastProjectFile)
    sys.stdout = open(name, "w", encoding="utf8")
    print(myVars.projectName)
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    mainFrame.config(text=myVars.projectName)


# ---------------------------------------------------------------------------
# Smart code preservation helpers
# ---------------------------------------------------------------------------

# Sentinel comment written into every auto-generated function stub so we can
# detect whether the user has changed it.
_STUB_SENTINEL = "# AUTO-GENERATED STUB"

# Marker written at the top of every generated section so the parser can
# locate the boundaries reliably.
_SEC_TKVARS = "####### TK variables #######"
_SEC_FUNCTIONS = "####### Functions #######"
_SEC_WIDGETS = "####### Widgets #######"
_SEC_MAIN = "####### Main  #######"


def _parseExistingPython(filePath: str) -> tuple[dict, dict]:
    """Parse *filePath* (a previously generated .py file) and return:

    * ``func_bodies``  – ``{func_name: full_source_string}`` for every
      function that the user has modified (stub sentinel absent).
    * ``tkvar_lines``  – ``{var_name: init_line}`` for every tk variable
      line that differs from the plain auto-generated default
      (``var = tk.StringVar(rootWin,'0.0')``).

    Returns two empty dicts if the file cannot be read or parsed.
    """
    func_bodies: dict[str, str] = {}
    tkvar_lines: dict[str, str] = {}

    if not filePath or not os.path.isfile(filePath):
        return func_bodies, tkvar_lines

    try:
        src = open(filePath, "r", encoding="utf-8").read()
    except OSError as e:
        log.warning("_parseExistingPython: cannot read %s: %s", filePath, e)
        return func_bodies, tkvar_lines

    lines = src.splitlines(keepends=True)

    # ---- Locate section boundaries by scanning for the sentinel comments --
    sec_tkvars = sec_functions = sec_widgets = sec_main = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == _SEC_TKVARS:
            sec_tkvars = i
        elif stripped == _SEC_FUNCTIONS:
            sec_functions = i
        elif stripped == _SEC_WIDGETS:
            sec_widgets = i
        elif stripped == _SEC_MAIN:
            sec_main = i

    # ---- Extract user-modified tk variable lines -------------------------
    if sec_tkvars is not None:
        end = sec_functions if sec_functions is not None else len(lines)
        # pattern: <name> = tk.StringVar(rootWin, ...)
        var_pat = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*tk\.StringVar\s*\(.*\)")
        for line in lines[sec_tkvars + 1 : end]:
            m = var_pat.match(line.strip())
            if m:
                var_name = m.group(1)
                default_line = f"{var_name} = tk.StringVar(rootWin,'0.0')"
                actual_line = line.rstrip()
                if actual_line.strip() != default_line:
                    tkvar_lines[var_name] = actual_line.strip()
                    log.debug("_parseExistingPython: preserved tkvar %s", var_name)

    # ---- Extract user-modified function bodies ---------------------------
    if sec_functions is not None:
        end = (
            sec_widgets
            if sec_widgets is not None
            else (sec_main if sec_main is not None else len(lines))
        )
        # Walk function definitions using the AST for reliability
        func_region = "".join(lines[sec_functions + 1 : end])
        try:
            ast_tree = ast.parse(func_region)
        except SyntaxError as e:
            log.warning("_parseExistingPython: SyntaxError in functions section: %s", e)
            ast_tree = None
        if ast_tree:
            region_lines = func_region.splitlines(keepends=True)
            for node in ast.walk(ast_tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                name = node.name
                # Grab source lines for this function
                start = node.lineno - 1  # ast lines are 1-based
                end_ln = node.end_lineno  # inclusive 1-based
                func_src = "".join(region_lines[start:end_ln])
                # Check for stub sentinel anywhere in body
                if _STUB_SENTINEL not in func_src:
                    func_bodies[name] = func_src
                    log.debug("_parseExistingPython: preserved user function %s", name)
    return func_bodies, tkvar_lines


def buildPython() -> str:
    """
    Generate python code and do a trial run
    """
    functions = []
    tkvars = []
    saveProject()
    runDict = myVars.projectDict
    nWidgets = runDict.get("widgetCount")
    largestWidth = 200
    largestHeight = 200
    createdWidgetOrder = workOutWidgetCreationOrder()
    log.info("nWidgets %s", nWidgets)
    configPath = getConfigPath()
    fileName = configPath + "/" + "test.py"

    # ---- Load existing user edits (if any) from the last saved .py ------
    _preserved_funcs, _preserved_tkvars = _parseExistingPython(myVars.generatedPyFile)
    if _preserved_funcs or _preserved_tkvars:
        log.info(
            "buildPython: preserving %d function(s) and %d tkvar(s) from %s",
            len(_preserved_funcs),
            len(_preserved_tkvars),
            myVars.generatedPyFile,
        )
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

                if key == "command" or key == "postcommand":
                    if val > "":
                        log.info("command ->%s<-", val)
                        functions.append(val)
                if key == "textvariable":
                    if val > "":
                        log.info("textvariable ->%s<-", val)
                        tkvars.append(val)
                if key == "variable":
                    if val > "":
                        log.info("variable ->%s<-", val)
                        tkvars.append(val)

    print("")
    print(_SEC_TKVARS)
    for f in myVars.widgetImageFilenames:
        name = str(f[myVars.WIDGET]) + str(f[myVars.KEY])
        print(name + " = tk.PhotoImage(file='" + f[myVars.FILENAME] + "')")
    # Deduplicate tk variables (one widget may reference the same variable)
    seen_vars: set = set()
    for v in tkvars:
        if v and v not in seen_vars:
            seen_vars.add(v)
            if v in _preserved_tkvars:
                # User has changed this initialisation – keep their version
                print(_preserved_tkvars[v])
            else:
                print(v + " = tk.StringVar(rootWin,'0.0')")
    print("")
    print(_SEC_FUNCTIONS)
    for f in functions:
        if not f:
            continue
        print("")
        if f in _preserved_funcs:
            # Emit the user's version verbatim (already dedented relative to
            # the region we parsed, so just print it)
            print(_preserved_funcs[f].rstrip())
        else:
            # Emit a blank stub with the sentinel so we know it's untouched
            print("def " + f + "():")
            print("    " + _STUB_SENTINEL)
            print("    print('" + f + "')")
    print("")
    print(_SEC_WIDGETS)
    for widgetName in createdWidgetOrder:
        # widgetId = "Widget" + str(n)
        if widgetName == rootName:
            continue
        parentName = findWidgetsParent(widgetName)
        if len(parentName) < 2:
            log.warning("widget %s has no parent. Has it been deleted?", widgetName)
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
            specialKeys = [
                "postcommand",
                "command",
                "textvariable",
                "variable",
                "image",
            ]
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
                    log.warning("key ->%s<- value ->%s<- has a weird value", key, val)
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
            geomData = wDict.get("GeomData", {})
            if myVars.geomManager == "Place":
                place = wDict.get("Place", geomData)
                x = place.get("x", "0")
                y = place.get("y", "0")
                width = place.get("width", "72")
                height = place.get("height", "32")
                try:
                    widthPos = int(x) + int(width)
                    heightPos = int(y) + int(height)
                    if widthPos > largestWidth:
                        largestWidth = widthPos
                    if heightPos > largestHeight:
                        largestHeight = heightPos
                except (ArithmeticError, ValueError) as e:
                    log.warning("Dimension error %s", str(e))
                anchor = place.get("anchor", "nw")
                bordermode = place.get("bordermode", "inside")
                print(
                    f"{widgetName}.place(x={x}, y={y}, width={width},"
                    f" height={height}, anchor='{anchor}',"
                    f" bordermode='{bordermode}')"
                )
            elif myVars.geomManager == "Grid":
                row = geomData.get("row", "0")
                col = geomData.get("column", "0")
                columnspan = int(geomData.get("columnspan", 1))
                rowspan = int(geomData.get("rowspan", 1))
                sticky = geomData.get("sticky", "")
                padx = geomData.get("padx", "2")
                pady = geomData.get("pady", "2")
                ipadx = int(geomData.get("ipadx", 0))
                ipady = int(geomData.get("ipady", 0))
                extra_args = ""
                if columnspan > 1:
                    extra_args += f", columnspan={columnspan}"
                if rowspan > 1:
                    extra_args += f", rowspan={rowspan}"
                if ipadx:
                    extra_args += f", ipadx={ipadx}"
                if ipady:
                    extra_args += f", ipady={ipady}"
                print(
                    f"{widgetName}.grid(row={row}, column={col}{extra_args},"
                    f" sticky='{sticky}', padx={padx}, pady={pady})"
                )
            elif myVars.geomManager == "Pack":
                side = geomData.get("side", "top")
                fill = geomData.get("fill", "none")
                expand = geomData.get("expand", "0")
                padx = geomData.get("padx", "2")
                pady = geomData.get("pady", "2")
                anchor = geomData.get("anchor", "center")
                print(
                    f"{widgetName}.pack(side='{side}', fill='{fill}',"
                    f" expand={expand}, padx={padx}, pady={pady},"
                    f" anchor='{anchor}')"
                )
            else:
                log.error("Unknown geometry manager %s", myVars.geomManager)
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
    if myVars.geomManager == "Place":
        print(rootName + ".place(x=0, y=0, relwidth=1.0, relheight=1.0)")
    elif myVars.geomManager == "Grid":
        print(rootName + ".grid(row=0, column=0, sticky='NSEW')")
    elif myVars.geomManager == "Pack":
        print(rootName + ".pack(fill='both', expand=True)")
    print("\nrootWin.mainloop()")
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    # sys.stdout = open(fileName, "w", encoding="utf8")
    # cmd = "python3 " + fileName + " &"
    # os.system(cmd)
    return fileName


def runMe():
    fileName = buildPython()
    log.info("python fileName ->%s<-", fileName)
    cmd = "python3 " + fileName + " &"
    os.system(cmd)


def generatePython():
    """Ask for a save path, generate Python and copy the file there.

    The chosen path is stored in myVars.generatedPyFile so that the next
    call to buildPython() can load and preserve any user edits.
    """
    # If we already know a target file, pre-fill the dialog with it.
    home = os.environ["HOME"]
    initialDir = myVars.saveDirName if myVars.saveDirName else home
    initialFile = (
        os.path.basename(myVars.generatedPyFile)
        if myVars.generatedPyFile
        else myVars.projectName + ".py"
    )
    newFile = tk.filedialog.asksaveasfilename(
        initialdir=initialFile
        and os.path.dirname(myVars.generatedPyFile)
        or initialDir,
        initialfile=initialFile,
        filetypes=[("Python file", "*.py")],
        defaultextension="py",
    )
    if not newFile:
        return  # user cancelled

    # Remember where the user is keeping their generated file.
    myVars.saveDirName = os.path.dirname(newFile)
    myVars.generatedPyFile = newFile
    log.info("save dir %s saved file = %s", myVars.saveDirName, newFile)

    # Now build (with preservation) and copy.
    fileName = buildPython()
    try:
        shutil.copy2(fileName, newFile)
        log.info("Generated Python written to %s", newFile)
    except OSError as e:
        log.error("Failed to copy generated file: %s", e)
        Messagebox.show_error(
            title="Generate Error", message=f"Could not write to {newFile}:\n{e}"
        )


def deleteWidgetData():
    log.info("Removing all existing Widgets")
    for w in cw.createWidget.widgetList:
        w.destroy()
    cw.createWidget.widgetNameList = []
    cw.createWidget.widgetList = []
    cw.createWidget.widgetObjectList = []
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

    mgr = myVars.geomManager
    if mgr == "Place":
        widget.place(in_=parent)
        widget.parent = parent
        widget.update()
    elif mgr == "Grid":
        # Preserve existing grid info if available, else default to 0,0
        try:
            gi = widget.grid_info()
            row = gi.get("row", 0)
            col = gi.get("column", 0)
        except tk.TclError:
            row, col = 0, 0
        # Read current cwo values so we preserve span/sticky from last edit
        cwo_r = cw.findCreateWidgetObject(widgetName)
        col_span = cwo_r.columnspan if cwo_r is not None else 2
        row_span = cwo_r.rowspan if cwo_r is not None else 2
        sticky_r = cwo_r.sticky if cwo_r is not None else "nsew"
        widget.grid(
            in_=parent,
            row=row,
            column=col,
            columnspan=col_span,
            rowspan=row_span,
            padx=2,
            pady=2,
            sticky=sticky_r,
        )
        if cwo_r is not None:
            cwo_r.col = col
            cwo_r.row = row
    elif mgr == "Pack":
        widget.pack(in_=parent, padx=4, pady=4, anchor="nw")
    else:
        log.error("Geometry Manager %s is TBD", mgr)
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
    log.info("configPath %s", configPath)
    name = Querybox.get_string("New Project name")
    if not name:
        return

    # Ask for geometry manager once at project creation
    geom_choice = _askGeomManager()
    if not geom_choice:
        return

    path = os.path.join(configPath, name)
    # Create directory only if it doesn't already exist
    os.makedirs(path, exist_ok=True)
    log.info("configPath %s project name %s path %s", configPath, name, path)
    myVars.projectName = name
    myVars.projectPath = path
    projFileName = myVars.projectName
    fileName = os.path.join(myVars.projectPath, projFileName)
    myVars.projectFileName = fileName
    log.info("projectFileName %s", myVars.projectFileName)

    # Apply geometry manager (canvas is empty so setGeomManager will accept it)
    myVars.geomManager = geom_choice
    if hasattr(rootWin, "_geomLabel"):
        rootWin._geomLabel.config(text="Layout: " + geom_choice)
    _rebuild_canvas_for_geom()
    mainFrame.config(text=myVars.projectName)


def _askGeomManager() -> str:
    """Show a simple dialog to choose Place / Grid / Pack.
    Returns the chosen manager string, or empty string if cancelled."""
    # Use tk.Toplevel to avoid ttkbootstrap positional-arg conflict with 'title'
    top = tk.Toplevel(rootWin)
    top.title("Choose Geometry Manager")
    top.resizable(False, False)
    top.grab_set()
    # Centre over rootWin once the window has been drawn
    top.update_idletasks()
    rw = rootWin.winfo_width() or 900
    rh = rootWin.winfo_height() or 820
    rx = rootWin.winfo_rootx()
    ry = rootWin.winfo_rooty()
    tw = top.winfo_reqwidth() or 380
    th = top.winfo_reqheight() or 200
    top.geometry(f"{tw}x{th}+{rx + (rw - tw)//2}+{ry + (rh - th)//2}")
    tboot.Label(
        top, text="Choose how widgets will be positioned:", font="TkDefaultFont 10 bold"
    ).pack(pady=(16, 4), padx=16)

    # descriptions_x = {
    #     "Place": "Free-form drag & drop (absolute x/y)  ← recommended",
    #     "Grid":  "Row / column grid layout",
    #     "Pack":  "Stack widgets top-to-bottom or left-to-right",
    descriptions = {
        "Place": "Free-form drag & drop (absolute x/y)  ← recommended",
        "Grid": "Row / column grid layout",
        "Pack": "TBD -- Stack widgets top-to-bottom or left-to-right",
    }
    chosen = tk.StringVar(value="Place")
    for mgr, desc in descriptions.items():
        tboot.Radiobutton(
            top, text=f"{mgr}  —  {desc}", variable=chosen, value=mgr
        ).pack(anchor="w", padx=24, pady=2)

    result = [""]

    def _ok():
        result[0] = chosen.get()
        top.destroy()

    def _cancel():
        top.destroy()

    bf = tboot.Frame(top)
    bf.pack(pady=(12, 16))
    tboot.Button(bf, text="OK", bootstyle="primary", command=_ok).pack(
        side=tk.LEFT, padx=8
    )
    tboot.Button(bf, text="Cancel", bootstyle="secondary", command=_cancel).pack(
        side=tk.LEFT, padx=8
    )
    top.wait_window()
    return result[0]


def getConfigPath() -> str:
    if "APPDATA" in os.environ:
        confighome = os.environ["APPDATA"]
    elif "XDG_CONFIG_HOME" in os.environ:
        confighome = os.environ["XDG_CONFIG_HOME"]
    else:
        confighome = os.path.join(os.environ["HOME"], ".config")
    configPath = os.path.join(confighome, myVars.programName)
    if os.path.isdir(configPath):
        log.debug("Config Path %s %s %s", configPath, confighome, myVars.programName)
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
        filetypes=[
            ("PyTkQuickGui JSON files", "*.json"),
            ("PyTkQuickGui legacy pickle files", "*.pk1"),
            ("All files", "*.*"),
        ],
    )

    if filePath:
        # Work out the probable project name
        projectPath = os.path.dirname(filePath)
        projectName = os.path.basename(projectPath)
        log.debug(
            "Selected File: %s \nProjectPath %s \nProject %s",
            filePath,
            projectPath,
            projectName,
        )
        loadProject(projectName, filePath)


def _loadProjectData(fullFileName: str):
    """Return the project dict from *fullFileName*.

    Tries JSON first; if that fails (e.g. the file is an old pickle save)
    falls back to pickle so existing projects keep working.
    Returns None when the file is empty or cannot be parsed.
    """
    if not os.path.isfile(fullFileName):
        return None
    if os.path.getsize(fullFileName) == 0:
        return None

    # ---- Try JSON -------------------------------------------------------
    try:
        with open(fullFileName, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.info("Loaded project from JSON: %s", fullFileName)
        return data
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass  # fall through to pickle

    # ---- Legacy pickle --------------------------------------------------
    try:
        with open(fullFileName, "rb") as f:
            data = pickle.load(f)
        log.info("Loaded project from legacy pickle: %s", fullFileName)
        Messagebox.show_info(
            title="Legacy Format",
            message=(
                f"Project '{os.path.basename(fullFileName)}' was loaded from the "
                "old pickle format.\nIt will be converted to JSON next time you save."
            ),
        )
        return data
    except Exception as e:
        log.error("Failed to load project file %s: %s", fullFileName, str(e))
        return None


def loadProject(project, altFileName):
    """Load a project from a saved file (JSON or legacy pickle)."""
    configPath = getConfigPath()
    folder = createFileName(configPath, None, project)
    fileName = ""
    fullFileName = ""
    if altFileName is None:
        log.info("folder ->%s<-", folder)
        if project is None:
            log.info("config Path =>%s<=", configPath)
            folder = tk.filedialog.askdirectory(
                mustexist=True, initialdir=configPath, title="Select Project Directory"
            )
        log.info("Load Project ->%s<-", folder)
        if folder != configPath:
            myVars.projectName = os.path.basename(str(folder))
            myVars.projectPath = folder
            log.info(
                "Load Project ->%s<- ->%s<-", myVars.projectPath, myVars.projectName
            )
        else:
            log.warning("No project selected Try Again")
            Messagebox.show_error(
                title="No Project Selected",
                message=(
                    "The Directory Selection box is not intuitive.\n"
                    "Double click on project name\nTry Again or create a new Project"
                ),
            )
            return
        projFileName = myVars.projectName
        fileName = os.path.join(myVars.projectPath, projFileName)
        myVars.projectFileName = fileName
        # Try JSON file first, then legacy pickle
        jsonFile = fileName + myVars.fileType
        legacyFile = fileName + myVars.legacyFileType
        if os.path.isfile(jsonFile):
            fullFileName = jsonFile
        elif os.path.isfile(legacyFile):
            fullFileName = legacyFile
        else:
            fullFileName = jsonFile  # will be created on save
    else:  # loading a backup / specific fileName
        # altFileName is the full path to the file chosen by the user.
        # 'folder' above was built from (configPath, project) so it may not
        # exist if project is e.g. a raw filename – derive everything from
        # altFileName instead.
        fullFileName = altFileName
        projectPath = os.path.dirname(altFileName)
        # The project name is the *directory* name that contains the file,
        # which matches how newProject/loadProject create the folder layout.
        myVars.projectName = (
            os.path.basename(projectPath)
            or os.path.splitext(os.path.basename(altFileName))[0]
        )
        myVars.projectPath = projectPath
        myVars.projectFileName = os.path.join(projectPath, myVars.projectName)

    mainFrame.config(text=myVars.projectName)
    deleteWidgetData()

    data = _loadProjectData(fullFileName)
    if data is None:
        # Brand new or empty project – just start fresh
        log.info("No data found in %s – starting with empty canvas.", fullFileName)
        mainFrame.config(text=myVars.projectName)
        return

    try:
        runDict = data
        log.debug(runDict)
        myVars.backgroundColor = runDict.get("backgroundColor")
        widgetNameList = runDict.get("widgetNameList")
        nWidgets = runDict.get("widgetCount")
        myVars.widgetImageFilenames = runDict.get("imageFileNames")
        savedGeom = runDict.get("geomManager")
        if savedGeom and savedGeom in myVars.GEOM_MANAGERS:
            myVars.geomManager = savedGeom
            if hasattr(rootWin, "_geomLabel"):
                rootWin._geomLabel.config(text="Layout: " + savedGeom)
        savedPyFile = runDict.get("generatedPyFile", "")
        if savedPyFile and os.path.isfile(savedPyFile):
            myVars.generatedPyFile = savedPyFile
            myVars.saveDirName = os.path.dirname(savedPyFile)
            log.info("Restored generatedPyFile path: %s", savedPyFile)
        savedGroups = runDict.get("groups", {})
        if isinstance(savedGroups, dict):
            myVars.groups = savedGroups
            log.info("Restored %d group(s) from project.", len(savedGroups))
    except AttributeError:
        log.info("AttributeError in project file.")

    # Rebuild the canvas inner frame BEFORE creating widgets so they land in
    # the correct (new) geomWidgetFrame for the loaded project's geometry manager.
    _rebuild_canvas_for_geom()

    widgetsFound = 0
    n = 0
    while widgetsFound < nWidgets:
        # for n in range(nWidgets + 4):
        widgetId = "Widget" + str(n)
        wDict = runDict.get(widgetId)
        if wDict is not None:
            widgetsFound += 1
            widgetDef = myVars.buildAWidget(n, wDict)
            # Route to the correct parent for the active geometry manager.
            # The eval'd widget def uses 'mainFrame' as parent token — we shadow
            # it here so the widget is created inside geomWidgetFrame directly.
            _load_parent = (
                geomWidgetFrame if geomWidgetFrame is not None else mainCanvas
            )
            try:
                # widget = ast.literal_eval(widgetDef)
                log.info("widgetDef ->%s<-", widgetDef)
                # Evaluate with mainFrame aliased to _load_parent so the widget
                # is created as a child of the correct container.
                # pylint: disable=eval-used
                widget = eval(widgetDef, globals(), {"mainFrame": _load_parent})
            except NameError as e:
                log.error("%d dict %s eval() NameError %s", n, str(wDict), str(e))
                continue
            except TypeError as e:
                log.error("%d dict %s eval() TypeError %s", n, str(wDict), str(e))
                continue
            w = cw.createWidget(_load_parent, widget)

            # In Grid mode, container widgets need their own row/column
            # configuration so child widgets can be reparented into them.
            if myVars.geomManager == "Grid":
                wn = wDict.get("WidgetName", "")
                if wn in myVars.containerWidgetsUsed:
                    _configure_container_grid(widget)

            mgr = myVars.geomManager
            if mgr == "Place":
                place = wDict.get("Place") or {}
                if place:
                    log.debug(place)
                    w.addPlace(place)
            elif mgr == "Grid":
                geomData = wDict.get("GeomData") or {}
                row = int(geomData.get("row", 0))
                col = int(geomData.get("column", 0))
                columnspan = max(1, int(geomData.get("columnspan", 1)))
                rowspan = max(1, int(geomData.get("rowspan", 1)))
                sticky = geomData.get("sticky", "WE")
                padx = int(geomData.get("padx", 2))
                pady = int(geomData.get("pady", 2))
                ipadx = int(geomData.get("ipadx", 0))
                ipady = int(geomData.get("ipady", 0))
                w.row = row
                w.col = col
                w.columnspan = columnspan
                w.rowspan = rowspan
                w.sticky = sticky
                w.padx = padx
                w.pady = pady
                w.ipadx = ipadx
                w.ipady = ipady
                w.widget.grid(
                    row=row,
                    column=col,
                    columnspan=columnspan,
                    rowspan=rowspan,
                    sticky=sticky,
                    padx=padx,
                    pady=pady,
                    ipadx=ipadx,
                    ipady=ipady,
                )
            elif mgr == "Pack":
                geomData = wDict.get("GeomData") or {}
                side = geomData.get("side", "top")
                fill = geomData.get("fill", "none")
                expand = int(geomData.get("expand", 0))
                padx = int(geomData.get("padx", 4))
                pady = int(geomData.get("pady", 4))
                anchor = geomData.get("anchor", "center")
                w.pack_side = side
                w.pack_fill = fill
                w.pack_expand = expand
                w.pack_padx = padx
                w.pack_pady = pady
                w.pack_anchor = anchor
                w.widget.pack(
                    side=side,
                    fill=fill,
                    expand=expand,
                    padx=padx,
                    pady=pady,
                    anchor=anchor,
                )
            else:
                log.error("Geometry Manager %s unknown", mgr)
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
            log.warning("name %s parent %s children %s", name, parent, children)
            log.warning("widgetNameList %s", str(widgetNameList))

    checkWidgetNameList()
    mainFrame.config(text=myVars.projectName)
    # Force tkinter to process all pending geometry requests so that
    # winfo_x() / winfo_y() return correct values immediately after load.
    rootWin.update_idletasks()
    # Clear undo history – actions from the old project aren't reachable
    undoredo.stack.clear()


def loadLastProject():
    configPath = getConfigPath()
    fileName = createFileName(configPath, None, myVars.lastProjectFile)
    # f = C.fopen(fileName,"r")
    f = openFile(fileName, "r")
    project = f.read()
    f.close()
    loadProject(project, None)
    mainFrame.config(text=myVars.projectName)


def loadProjectWrapper():
    loadProject(None, None)


def exitApp():
    mb = Messagebox.yesnocancel("Save project before exiting ?", "Save Project")
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
        print("widgetImageFilename %s", il)


def chooseBackground():
    # global mainCanvas
    colors = askcolor(title="Tkinter color chooser")
    if colors[1] is not None:
        mainCanvas.configure(bg=colors[1])
        mainCanvas.update()
        myVars.backgroundColor = colors[1]


def welcome():
    about = """PyTkGui:
    Chris McGowan 2024.
    A tool to build a simple TkInter GUI.
	This tool uses ttkbootstrap widgets.
	A website - youtube - pdf TBD."""

    # remove leading whitespace from each line
    # this does not work on python 3.12
    # about2 = re.sub("\n\s*", "\n", about)
    about2 = about
    Messagebox.show_info(message=about2, title="Welcome")


# ---------------------------------------------------------------------------
# In-app Help window  (tabbed, scrollable)
# ---------------------------------------------------------------------------

_HELP_TABS = {
    "Getting Started": """
PyTkQuickGui  –  Quick-start guide
===================================

1.  CREATE A PROJECT
    File > New Project  then enter a name.

2.  ADD WIDGETS
    Right-click anywhere on the canvas.
    A pop-up menu lists all available widget types.
    Container widgets (Frame, Labelframe…) appear first.
    Click a name to place the widget at the cursor.

3.  MOVE A WIDGET
    Left-click in the centre of a widget and drag.

4.  RESIZE A WIDGET
    Left-click near any edge of a widget and drag.
    The cursor changes to indicate resize mode.
    Sizes snap to a 16-pixel grid on mouse release.

5.  EDIT ATTRIBUTES
    Right-click a widget > Edit.
    Change text, colour, font, style, command names, etc.
    Click Apply to commit, Close to discard.

6.  CHANGE LAYOUT POSITION (Place mode)
    Right-click a widget > Layout.
    Enter exact x, y, width, height values.

7.  SAVE
    File > Save Project  (Ctrl+S equivalent from menu).
    Projects are stored as JSON files in ~/.config/pytkgui/.

8.  GENERATE CODE
    File > Generate Python  – choose where to save the .py file.
    File > Trial Run  – generate & run immediately.
""",
    "Mouse & Keyboard": """
Mouse Actions
=============

  Right-click canvas          Open widget palette (add new widget)
  Right-click widget          Context menu (Edit / Layout / Clone / Delete…)
  Left-drag (centre)          Move widget
  Left-drag (near edge)       Resize widget
    – right edge              Stretch / shrink width
    – left edge               Move left edge (adjusts x and width)
    – bottom edge             Stretch / shrink height
    – top edge                Move top edge (adjusts y and height)
  Left-drag size-grip         Resize the canvas

Snap Grid
=========
  Widgets snap to a 16-pixel grid when you release the mouse.

Widget Context Menu
===================
  Edit          Open attribute editor popup
  Layout        Open x/y/width/height editor (Place mode)
  Clone         Duplicate the widget
  DeepClone     Duplicate container + all children
  Re-Parent     Move widget into the container it overlaps
  Delete        Remove the widget
  Close         Dismiss the menu
""",
    "Geometry Managers": """
Geometry Managers
==================
Choose one from the toolbar BEFORE placing widgets.
The choice is saved in the project file and restored on load.

PLACE  (default)
  Widgets are positioned with absolute pixel coordinates.
  Generated code:  myWidget.place(x=…, y=…, width=…, height=…)
  Best for: pixel-perfect prototypes, tool UIs.

GRID
  Widgets are placed in a row/column table.
  Drop position is translated to the nearest grid cell.
  Generated code:  myWidget.grid(row=…, column=…, sticky=…)
  Best for: forms, dialog boxes, structured layouts.

PACK
  Widgets are stacked sequentially.
  Generated code:  myWidget.pack(side=…, fill=…, expand=…)
  Best for: simple vertical / horizontal stacks.

Note: changing the geometry manager after placing widgets may
cause the canvas to look different because existing widgets
were placed with the old manager's rules.
""",
    "Widgets": """
ttkbootstrap Widgets
====================
  Frame          Container – holds other widgets
  Labelframe     Frame with a border title
  Panedwindow    Adjustable splitter container
  Label          Static text or image
  Button         Clickable button
  Entry          Single-line text input
  Combobox       Drop-down list
  Spinbox        Numeric spinner
  Checkbutton    Tick-box
  Radiobutton    Radio selector
  Scale          Slider (horizontal or vertical)
  Progressbar    Progress bar
  Floodgauge     Animated fill gauge (ttkbootstrap)
  Meter          Circular gauge (ttkbootstrap)
  Notebook       Tabbed container
  Canvas         Drawing / image surface

Standard tk / ttk Widgets
==========================
  Text           Multi-line text area
  Listbox        Scrollable list
  Treeview       Table / tree view
  Scrollbar      Scroll bar – attach via the Edit popup
  Separator      Horizontal or vertical dividing line
  Sizegrip       Window resize handle (bottom-right corner)

All widgets expose their configurable keys in the Edit popup.
Common attribute types:
  Combobox  →  anchor, relief, justify, orient, cursor, style
  Spinbox   →  height, width, borderwidth, padding
  Button    →  font, foreground/background colour, image
  Entry     →  text, command, variable names, etc.
""",
    "Project Files": """
Project File Format  (JSON)
============================
Projects are stored as plain JSON files:

  ~/.config/pytkgui/<ProjectName>/<ProjectName>.json

Rolling backups are kept automatically:
  <ProjectName>-save1.json   (most recent previous save)
  <ProjectName>-save2.json
  ...up to save5

The JSON file can be opened in any text editor.
You can edit widget properties by hand – but be careful:
an invalid JSON file will prevent the project from loading.

Legacy Format (.pk1)
====================
Older versions saved projects as Python pickle (.pk1) files.
These are still loaded automatically. A notice is shown and
the project will be re-saved as JSON next time you save.

File > Open backup file allows you to load any .json or .pk1
backup file directly.
""",
    "Code Generation": """
Generated Python File
======================
File > Generate Python  produces a single .py file:

  import tkinter as tk
  import ttkbootstrap as tboot

  themeName = 'cyborg'
  title     = 'MyProject'
  rootWin   = tboot.Window(themename=themeName, title=title)
  rootWidget = tboot.Frame(rootWin, ...)

  ####### TK variables #######
  myVar = tk.StringVar(rootWin, '0.0')

  ####### Functions #######
  def onButtonClick():
      # AUTO-GENERATED STUB
      print('onButtonClick')

  ####### Widgets #######
  Widget0 = tboot.Button(rootWidget, text='Click', command=onButtonClick)
  Widget0.place(x=80, y=48, width=120, height=32, ...)

  ####### Main #######
  rootWin.geometry('800x600')
  rootWin.mainloop()

Preserving Your Code
====================
Re-generating does NOT overwrite code you have written!

  Functions
    Each new function stub contains a comment:
        # AUTO-GENERATED STUB
    When you edit a function (add real code, remove the
    stub comment), the generator detects the change and
    preserves your version on every future re-generation.

  TK Variables
    Variables initialised as the default
        myVar = tk.StringVar(rootWin,'0.0')
    are replaced if you change the initial value, e.g.:
        myVar = tk.StringVar(rootWin, 'Hello')
    or use a different variable type entirely.

  Widget layout & widget list
    These are ALWAYS regenerated from the builder state
    – that is the point of re-generation.  Do not put
    custom code in the ####### Widgets ####### section.

Workflow
========
  1. Build layout in PyTkQuickGui.
  2. File > Generate Python  – choose a .py file to save.
  3. Edit that .py: implement function bodies, tweak vars.
  4. Go back to PyTkQuickGui, adjust layout, re-generate
     (using File > Generate Python and choosing the SAME
     file, or just hitting Generate Python which pre-fills
     the dialog with the last used path).
  5. Your code is merged back automatically.

Tips
====
  - Set the 'command' attribute in the Edit popup to the
    function name you want called on click.
  - Set 'textvariable' or 'variable' to a variable name;
    the generator creates  myVar = tk.StringVar(…)  for you.
  - File > Trial Run generates + runs a temporary copy;
    it does NOT update the user's .py file.
""",
    "Tips & Troubleshooting": """
Useful Tips
===========
  • Use Frames and Labelframes to group related widgets.
    Drag a widget into a frame; it re-parents automatically.

  • Use Tools > Hide Label Borders / Show Label Borders to
    toggle the 1-pixel debug border on all Label widgets.

  • Use Tools > Widget Tree to print the full widget hierarchy
    to the terminal – useful for debugging parent/child issues.

  • Use Tools > Open backup file to recover from an accidental
    deletion by loading a previous auto-save.

  • Themes are applied live – use the Theme menu to preview
    how your layout looks in different colour schemes.

Troubleshooting
===============
  Widget disappeared
    → It may be behind another widget. Right-click a widget
      and use Re-Parent, or check Tools > Widget Tree.

  Project won't load
    → The JSON file may be corrupted. Open it in a text editor
      and check for syntax errors, or load a backup file.

  Meter widget looks wrong
    → Use File > Trial Run to see how it renders in the final
      application window.

  Scrollbars not working
    → Scrollbar auto-wiring (vertical_scrollbar /
      horizontal_scrollbar in the Edit popup) only works
      with the Grid geometry manager.

  Generated code has unexpected geometry
    → Check that you saved the project AFTER final adjustments
      and re-generate. The code is always built from the
      last saved state.
""",
}


def helpMe():
    """Open the tabbed in-app help window."""
    helpWin = tboot.Toplevel(rootWin)
    helpWin.title("PyTkQuickGui – Help")
    helpWin.geometry("700x520")
    helpWin.resizable(True, True)

    nb = tboot.Notebook(helpWin)
    nb.pack(fill="both", expand=True, padx=8, pady=8)

    for tab_title, tab_text in _HELP_TABS.items():
        frame = tboot.Frame(nb)
        nb.add(frame, text=tab_title)

        # Scrollable text area
        vsb = tboot.Scrollbar(frame, orient="vertical", style="info round")
        txt = tk.Text(
            frame,
            wrap="word",
            state="normal",
            font=("Courier", 10),
            padx=8,
            pady=4,
            borderwidth=0,
            yscrollcommand=vsb.set,
        )
        vsb.config(command=txt.yview)
        vsb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", tab_text.strip())
        txt.config(state="disabled")

    close_btn = tboot.Button(
        helpWin, text="Close", style="warning", command=helpWin.destroy
    )
    close_btn.pack(pady=(0, 8))


# ---------------------------------------------------------------------------
# Group / Ungroup helpers (called from Edit menu)
# ---------------------------------------------------------------------------


def _groupSelected():
    """Create a named group from the current multi-selection."""
    sel = getattr(myVars, "selectedWidgets", [])
    if len(sel) < 2:
        Messagebox.show_info(
            title="Group",
            message="Select two or more widgets first (Shift+click), then group them.",
        )
        return
    name = Querybox.get_string(
        prompt="Group name:",
        title="Create Widget Group",
        initialvalue=f"group{len(myVars.groups) + 1}",
    )
    if not name:
        return
    undoredo.stack.push(undoredo.GroupCommand(name, list(sel)))
    Messagebox.show_info(title="Group", message=f"Created group '{name}'.")


def _ungroupSelected():
    """Dissolve all groups whose members overlap the current selection."""
    sel = set(getattr(myVars, "selectedWidgets", []))
    dissolved = []
    for gname, members in list(myVars.groups.items()):
        if sel & set(members):
            undoredo.stack.push(undoredo.UngroupCommand(gname))
            dissolved.append(gname)
    if dissolved:
        Messagebox.show_info(
            title="Ungroup", message="Dissolved: " + ", ".join(dissolved)
        )
    else:
        Messagebox.show_info(
            title="Ungroup", message="No groups found for the current selection."
        )


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
    toolsMenu.add_command(label="Set default bootstyle type", command=setThemeColor)
    toolsMenu.add_command(label="Set default label font", command=setDefaultLabelFont)
    toolsMenu.add_command(label="Set default style font", command=setDefaultStyleFont)
    toolsMenu.add_command(label="Open backup file", command=openBackupFile)
    toolsMenu.add_command(label="Widget Tree", command=widgetTree)

    # ---- Edit menu (Undo / Redo) ----------------------------------------
    editMenu = tboot.Menu(menuBar, tearoff=0)
    editMenu.add_command(label="Undo\tCtrl+Z", command=undoredo.stack.undo)
    editMenu.add_command(label="Redo\tCtrl+Y", command=undoredo.stack.redo)
    editMenu.add_separator()
    editMenu.add_command(label="Group Selected", command=_groupSelected)
    editMenu.add_command(label="Ungroup", command=_ungroupSelected)
    menuBar.add_cascade(label="Edit", menu=editMenu, underline=0)

    # create the Help menu
    helpMenu = tboot.Menu(menuBar, tearoff=0)

    helpMenu.add_command(label="Welcome", command=welcome)
    helpMenu.add_command(label="Help", command=helpMe)

    menuBar.add_cascade(label="Theme", menu=themeMenu, underline=0)
    # add the Help menu to the menuBar
    menuBar.add_cascade(label="Tools", menu=toolsMenu, underline=0)
    menuBar.add_cascade(label="Help", menu=helpMenu, underline=0)

    # add the File menu to the menuBar
    fileMenu.add_cascade(label="Preferences", menu=subMenu)


def doNothing():
    # Not sure what this is for . Delete later
    pass


def _make_grid_overlay(frame: tboot.Frame) -> tk.Canvas:  # type: ignore[name-defined]
    """Create (or recreate) the transparent overlay Canvas inside *frame*.

    The canvas is placed to fill the entire frame with .place() so it does
    not participate in the grid layout. It is immediately lowered to the
    bottom of the stacking order so all grid-managed child widgets appear
    on top.  Returns the new Canvas.
    """
    global _gridOverlayCanvas
    if _gridOverlayCanvas is not None:
        try:
            _gridOverlayCanvas.destroy()
        except tk.TclError:
            pass
    oc = tk.Canvas(
        frame,
        highlightthickness=0,
        bd=0,
        takefocus=False,
    )
    # Place it so it covers the full frame regardless of size
    oc.place(x=0, y=0, relwidth=1.0, relheight=1.0)
    # Lower the overlay widget below all siblings so grid-children appear on top.
    # tk.Misc.lower() lowers in the window stacking order (not a canvas item op).
    tk.Misc.lower(oc)
    # Right-clicks on the overlay canvas must still open the widget-creation menu
    oc.bind("<Button-3>", rightMouseDown)
    oc.bind("<Button-1>",        _grid_overlay_btn1)
    oc.bind("<B1-Motion>",       _grid_overlay_drag)
    oc.bind("<ButtonRelease-1>", _grid_overlay_release)
    _gridOverlayCanvas = oc
    return oc


# ---------------------------------------------------------------------------
# Grid overlay interaction helpers
# ---------------------------------------------------------------------------
# Visual constants for the overlay
_HANDLE_HALF  = 5   # px — half-size of the draggable handle square on each divider
_ADD_RADIUS   = 7   # px — radius of the "+" add-column/row circle
_ADD_MARGIN   = 14  # px — how far from the edge the "+" circles sit


def _grid_collect_lines(frame, oc_w, oc_h):
    """Return (col_xs_sorted, row_ys_sorted) from grid_bbox, capped to overlay size.

    Uses grid_size() to get the configured column/row count so we never loop
    more times than the grid actually has cells.
    """
    try:
        n_cols, n_rows = frame.grid_size()
    except tk.TclError:
        n_cols, n_rows = 0, 0

    col_xs = {0}
    for col in range(n_cols):
        try:
            bbox = frame.grid_bbox(col, 0)
        except tk.TclError:
            break
        if bbox is None:
            break
        x, _y, w, _h = bbox
        if x >= oc_w:
            break
        col_xs.add(x)
        if w > 0:
            col_xs.add(min(x + w, oc_w))

    row_ys = {0}
    for row in range(n_rows):
        try:
            bbox = frame.grid_bbox(0, row)
        except tk.TclError:
            break
        if bbox is None:
            break
        _x, y, _w, h = bbox
        if y >= oc_h:
            break
        row_ys.add(y)
        if h > 0:
            row_ys.add(min(y + h, oc_h))

    return sorted(col_xs), sorted(row_ys)


def _grid_overlay_btn1(event):
    """Handle left-click on the grid overlay canvas.

    • Clicking a "+" add-column circle  → insert a new column at that position
    • Clicking a "+" add-row circle     → insert a new row at that position
    • Clicking a divider handle         → start a drag to resize that column/row
    """
    global _grid_drag_state
    if geomWidgetFrame is None:
        return
    oc = _gridOverlayCanvas
    if oc is None:
        return
    oc_w = oc.winfo_width()
    oc_h = oc.winfo_height()
    col_xs, row_ys = _grid_collect_lines(geomWidgetFrame, oc_w, oc_h)
    ex, ey = event.x, event.y

    # --- Check "+" add-column circles (drawn at top, centred on each divider x) ---
    for i, gx in enumerate(col_xs[1:], 1):   # skip x=0 boundary
        cx, cy = gx, _ADD_MARGIN
        if abs(ex - cx) <= _ADD_RADIUS + 2 and abs(ey - cy) <= _ADD_RADIUS + 2:
            # Insert a new column AFTER index (i-1) by pushing minsize up
            _grid_insert_col(i - 1)
            return

    # --- Check "+" add-row circles (drawn at left, centred on each divider y) ---
    for i, gy in enumerate(row_ys[1:], 1):
        cx, cy = _ADD_MARGIN, gy
        if abs(ex - cx) <= _ADD_RADIUS + 2 and abs(ey - cy) <= _ADD_RADIUS + 2:
            log.info("Before _grid_insert_row i=%d",i)
            _grid_insert_row(i - 1)
            return

    # --- Check draggable divider handles on interior col lines ---
    for i, gx in enumerate(col_xs[1:-1], 1):   # skip first and last boundary
        if abs(ex - gx) <= _HANDLE_HALF + 2:
            # Determine which column index this right-hand boundary belongs to
            col_idx = i - 1
            try:
                bbox = geomWidgetFrame.grid_bbox(col_idx, 0)
                orig_size = bbox[2] if bbox else 60
            except tk.TclError:
                orig_size = 60
            _grid_drag_state = {
                "axis":      "col",
                "index":     col_idx,
                "start_px":  ex,
                "orig_size": orig_size,
            }
            oc.configure(cursor="sb_h_double_arrow")
            return

    # --- Check draggable divider handles on interior row lines ---
    for i, gy in enumerate(row_ys[1:-1], 1):
        if abs(ey - gy) <= _HANDLE_HALF + 2:
            row_idx = i - 1
            try:
                bbox = geomWidgetFrame.grid_bbox(0, row_idx)
                orig_size = bbox[3] if bbox else 30
            except tk.TclError:
                orig_size = 30
            _grid_drag_state = {
                "axis":      "row",
                "index":     row_idx,
                "start_px":  ey,
                "orig_size": orig_size,
            }
            oc.configure(cursor="sb_v_double_arrow")
            return


def _grid_overlay_drag(event):
    """Resize a column or row while the user drags a divider handle."""
    if not _grid_drag_state or geomWidgetFrame is None:
        return
    axis      = _grid_drag_state.get("axis")
    idx       = _grid_drag_state.get("index")
    start_px  = _grid_drag_state.get("start_px", 0)
    orig_size = _grid_drag_state.get("orig_size", 40)

    if axis == "col":
        delta     = event.x - start_px
        new_size  = max(20, orig_size + delta)
        geomWidgetFrame.columnconfigure(idx, minsize=new_size, weight=1)
    elif axis == "row":
        delta     = event.y - start_px
        new_size  = max(12, orig_size + delta)
        geomWidgetFrame.rowconfigure(idx, minsize=new_size, weight=1)

    geomWidgetFrame.update_idletasks()
    drawGridLines()


def _grid_overlay_release(_event):
    """Finish a divider drag and restore the cursor."""
    global _grid_drag_state
    _grid_drag_state = {}
    if _gridOverlayCanvas is not None:
        try:
            _gridOverlayCanvas.configure(cursor="")
        except tk.TclError:
            pass
    drawGridLines()


def _grid_insert_col(after_col: int):
    """Insert a new column after *after_col* by splitting its minsize in two."""
    if geomWidgetFrame is None:
        return
    # Find current pixel width of the column being split via grid_bbox
    try:
        bbox = geomWidgetFrame.grid_bbox(after_col, 0)
        cur_size = bbox[2] if bbox else 60
    except tk.TclError:
        cur_size = 60
    half = max(20, cur_size // 2)

    # grid_size() returns (cols, rows) — the exact configured grid dimensions.
    # This avoids polling grid_bbox() in a loop (which never returns None on a
    # pre-configured frame and caused an infinite loop).
    try:
        n_cols, _ = geomWidgetFrame.grid_size()
    except tk.TclError:
        n_cols = _CONTAINER_GRID_COLS
    n_cols = max(n_cols, after_col + 2)

    # Shift all columns after the insertion point right by one, reading each
    # column's current minsize from columnconfigure before overwriting it.
    for c in range(n_cols, after_col, -1):
        try:
            info = geomWidgetFrame.columnconfigure(c - 1)
            src_size = int(info.get("minsize", 60))
        except (tk.TclError, TypeError, ValueError):
            src_size = 60
        geomWidgetFrame.columnconfigure(c, minsize=src_size, weight=1)

    # Resize the split column and the new insertion slot
    geomWidgetFrame.columnconfigure(after_col,     minsize=half, weight=1)
    geomWidgetFrame.columnconfigure(after_col + 1, minsize=half, weight=1)

    geomWidgetFrame.update_idletasks()
    drawGridLines()


def _grid_insert_row(after_row: int):
    """Insert a new row after *after_row* by splitting its minsize in two."""
    if geomWidgetFrame is None:
        return
    try:
        bbox = geomWidgetFrame.grid_bbox(0, after_row)
        cur_size = bbox[3] if bbox else 30
    except tk.TclError:
        cur_size = 30
    half = max(12, cur_size // 2)

    # grid_size() returns (cols, rows) — exact configured dimensions, no loop needed.
    try:
        _, n_rows = geomWidgetFrame.grid_size()
    except tk.TclError:
        n_rows = _CONTAINER_GRID_ROWS
    n_rows = max(n_rows, after_row + 2)

    for r in range(n_rows, after_row, -1):
        try:
            info = geomWidgetFrame.rowconfigure(r - 1)
            src_size = int(info.get("minsize", 30))
        except (tk.TclError, TypeError, ValueError):
            src_size = 30
        geomWidgetFrame.rowconfigure(r, minsize=src_size, weight=1)

    geomWidgetFrame.rowconfigure(after_row,     minsize=half, weight=1)
    geomWidgetFrame.rowconfigure(after_row + 1, minsize=half, weight=1)

    geomWidgetFrame.update_idletasks()
    drawGridLines()


def drawGridLines():
    """Draw column/row guide lines.

    Lines are drawn on:
      Place mode  – mainCanvas (dot grid, faint grey, snapTo spacing)
      Grid mode   – _gridOverlayCanvas inside geomWidgetFrame (thin grey lines
                    with draggable resize handles and +add buttons)
      Pack mode   – nothing (Pack stacks automatically)
    """
    mainCanvas.update()
    width = mainCanvas.winfo_width()
    height = mainCanvas.winfo_height()
    log.debug(
        "drawGridLines Width %d height %d geomManager %s",
        width,
        height,
        myVars.geomManager,
    )

    # Remove old guide lines from mainCanvas (Place mode dot grid)
    mainCanvas.delete("gridline")

    mgr = myVars.geomManager

    if mgr == "Place":
        # Light dot grid at snapTo spacing drawn directly on mainCanvas
        snap = max(8, int(myVars.snapTo))
        dot_color = "#c0c0c0"
        for gx in range(0, width, snap):
            for gy in range(0, height, snap):
                mainCanvas.create_rectangle(
                    gx, gy, gx + 1, gy + 1, fill=dot_color, outline="", tags="gridline"
                )

    elif mgr == "Grid":
        # ----------------------------------------------------------------
        # Grid lines are drawn on _gridOverlayCanvas inside geomWidgetFrame.
        # Positions come from geomWidgetFrame.grid_bbox() so they always
        # match where the geometry manager actually places cell boundaries.
        # ----------------------------------------------------------------
        if _gridOverlayCanvas is None or not _gridOverlayCanvas.winfo_exists():
            return
        if geomWidgetFrame is None or not geomWidgetFrame.winfo_exists():
            return
        oc = _gridOverlayCanvas
        oc_w = oc.winfo_width()
        oc_h = oc.winfo_height()
        if oc_w < 2 or oc_h < 2:
            oc_w = width
            oc_h = height

        oc.delete("gridline")

        line_color   = "#c0c0c0"
        label_color  = "#a0a0a0"
        handle_color = "#7090c0"   # blue-grey handles on interior dividers
        add_color    = "#50b050"   # green "+" add buttons

        col_xs, row_ys = _grid_collect_lines(geomWidgetFrame, oc_w, oc_h)

        # --- Draw vertical column-boundary lines ---
        for gx in col_xs:
            oc.create_line(gx, 0, gx, oc_h, fill=line_color, width=1, tags="gridline")

        # --- Draw horizontal row-boundary lines ---
        for gy in row_ys:
            oc.create_line(0, gy, oc_w, gy, fill=line_color, width=1, tags="gridline")

        # --- Column index labels just inside each column's left edge ---
        for i, gx in enumerate(col_xs[:-1]):
            oc.create_text(
                gx + 3, 3,
                text=str(i),
                anchor="nw",
                fill=label_color,
                font=("TkDefaultFont", 7),
                tags="gridline",
            )

        # --- Row index labels just below each row's top edge ---
        for i, gy in enumerate(row_ys[:-1]):
            oc.create_text(
                3, gy + 3,
                text=str(i),
                anchor="nw",
                fill=label_color,
                font=("TkDefaultFont", 7),
                tags="gridline",
            )

        # --- Draggable resize handles: small rectangles on interior col dividers ---
        # (skip index 0 = left edge and last = right edge)
        mid_y = oc_h // 2
        for gx in col_xs[1:-1]:
            hx1, hx2 = gx - _HANDLE_HALF, gx + _HANDLE_HALF
            hy1, hy2 = mid_y - _HANDLE_HALF, mid_y + _HANDLE_HALF
            oc.create_rectangle(
                hx1, hy1, hx2, hy2,
                fill=handle_color, outline="white", width=1,
                tags="gridline",
            )

        # --- Draggable resize handles: small rectangles on interior row dividers ---
        mid_x = oc_w // 2
        for gy in row_ys[1:-1]:
            hx1, hx2 = mid_x - _HANDLE_HALF, mid_x + _HANDLE_HALF
            hy1, hy2 = gy - _HANDLE_HALF, gy + _HANDLE_HALF
            oc.create_rectangle(
                hx1, hy1, hx2, hy2,
                fill=handle_color, outline="white", width=1,
                tags="gridline",
            )

        # --- "+" add-column circles: centred on each interior col divider at top ---
        for gx in col_xs[1:-1]:
            cx, cy = gx, _ADD_MARGIN
            r = _ADD_RADIUS
            oc.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=add_color, outline="white", width=1,
                tags="gridline",
            )
            oc.create_text(cx, cy, text="+", fill="white",
                           font=("TkDefaultFont", 8, "bold"), tags="gridline")

        # --- "+" add-row circles: centred on each interior row divider at left ---
        for gy in row_ys[1:-1]:
            cx, cy = _ADD_MARGIN, gy
            r = _ADD_RADIUS
            oc.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=add_color, outline="white", width=1,
                tags="gridline",
            )
            oc.create_text(cx, cy, text="+", fill="white",
                           font=("TkDefaultFont", 8, "bold"), tags="gridline")


def sizeGripRelease(event):
    log.debug(event)
    drawGridLines()


# ---- Grid layout: number of rows/columns pre-configured in each container ----
_CONTAINER_GRID_COLS = 16
_CONTAINER_GRID_ROWS = 16


def _configure_container_grid(widget):
    """Give a container widget its own internal grid so child widgets can
    be reparented into it using Grid layout.

    Called whenever a Frame / Labelframe / Panedwindow is created in Grid mode.
    Without this, grid(in_=container) raises a TclError because the container
    has no column/row configuration.
    """
    for c in range(_CONTAINER_GRID_COLS):
        widget.columnconfigure(c, weight=1, minsize=40)
    for r in range(_CONTAINER_GRID_ROWS):
        widget.rowconfigure(r, weight=1, minsize=24)


def _placeNewWidget(w, x: int, y: int, width: int = 72, height: int = 32) -> None:
    """Position a newly created widget according to the active geometry manager."""
    mgr = myVars.geomManager
    if mgr == "Place":
        w.place(x=x, y=y, width=width, height=height)
    elif mgr == "Grid":
        # Map pixel click to grid cell using grid_location (exact) or fallback.
        parent = geomWidgetFrame if geomWidgetFrame is not None else mainCanvas
        try:
            col, row = parent.grid_location(x, y)
            col = max(0, col)
            row = max(0, row)
        except tk.TclError:
            cell = 60
            col = max(0, x // cell)
            row = max(0, y // cell)
        # Default: span 2 columns and 2 rows, fill the cells completely.
        col_span = 2
        row_span = 2
        new_sticky = "nsew"
        w.grid(
            in_=parent,
            row=row,
            column=col,
            columnspan=col_span,
            rowspan=row_span,
            padx=2,
            pady=2,
            sticky=new_sticky,
        )
        # Sync the authoritative cwo fields so drags and popups see the defaults.
        cwo = cw.findCreateWidgetObject(
            w.pythonName if hasattr(w, "pythonName") else ""
        )
        if cwo is not None:
            cwo.col = col
            cwo.row = row
            cwo.columnspan = col_span
            cwo.rowspan = row_span
            cwo.sticky = new_sticky
        # Re-lower the overlay canvas so it stays behind the new widget
        if _gridOverlayCanvas is not None:
            try:
                tk.Misc.lower(_gridOverlayCanvas)
            except tk.TclError:
                pass
        w.after_idle(drawGridLines)
    elif mgr == "Pack":
        parent = geomWidgetFrame if geomWidgetFrame is not None else mainCanvas
        w.pack(in_=parent, padx=4, pady=4, anchor="nw")
    else:
        log.error("Unknown geometry manager %s", mgr)


def createWidgetPopup(event, widgetName):
    defaultStyle = "primary"
    defaultCursor = "arrow"
    # Create a widget 'widgetName' at the current mouse pos (x,y)
    x = event.x
    y = event.y
    w: Any

    # Route the parent to the correct frame:
    # Place  -> mainCanvas (widgets float freely via .place())
    # Grid / Pack -> geomWidgetFrame (isolated inner frame inside mainCanvas)
    _parent = geomWidgetFrame if geomWidgetFrame is not None else mainCanvas

    # ---- Container widgets -------------------------------------------
    if widgetName == "Frame":
        w = tboot.Frame(_parent, cursor=defaultCursor, style=defaultStyle)
        if myVars.geomManager == "Grid":
            _configure_container_grid(w)
    elif widgetName == "Labelframe":
        w = tboot.Labelframe(
            _parent,
            text=widgetName,
            borderwidth=1,
            relief=tk.SOLID,
            labelanchor=tk.N,
            cursor=defaultCursor,
            style=defaultStyle,
        )
        if myVars.geomManager == "Grid":
            _configure_container_grid(w)
    elif widgetName == "Panedwindow":
        w = tboot.Panedwindow(_parent, cursor=defaultCursor, style=defaultStyle)
        if myVars.geomManager == "Grid":
            _configure_container_grid(w)
    # ---- ttkbootstrap widgets ----------------------------------------
    elif widgetName == "Label":
        w = tboot.Label(
            _parent,
            text=widgetName,
            borderwidth=1,
            relief=tk.SOLID,
            anchor=tk.CENTER,
            cursor=defaultCursor,
            style=defaultStyle,
        )
    elif widgetName == "ScrolledText":
        w = ScrolledText(_parent, padding=5, height=20, autohide=True)
    elif widgetName == "ScrolledFrame":
        w = ScrolledFrame(_parent, padding=5, height=20, autohide=True)
    elif widgetName == "Button":
        w = tboot.Button(
            _parent, text=widgetName, cursor=defaultCursor, style=defaultStyle
        )

    elif widgetName == "Entry":
        w = tboot.Entry(_parent, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Combobox":
        w = tboot.Combobox(_parent, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Notebook":
        w = tboot.Notebook(_parent, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Canvas":
        w = tboot.Canvas(_parent, borderwidth=1, relief=tk.SOLID, cursor=defaultCursor)
    elif widgetName == "Spinbox":
        w = tboot.Spinbox(_parent, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Checkbutton":
        # Each Checkbutton needs its own IntVar so it renders and saves correctly.
        _cbv = tk.IntVar(rootWin, 0)
        w = tboot.Checkbutton(
            _parent,
            text=widgetName,
            cursor=defaultCursor,
            style=defaultStyle,
            variable=_cbv,
        )
        w._tkvar = _cbv  # keep a reference so the var isn't garbage-collected
    elif widgetName == "Radiobutton":
        # Each Radiobutton group shares a variable; give each a unique default.
        _rbv = tk.IntVar(rootWin, 0)
        w = tboot.Radiobutton(
            _parent,
            text=widgetName,
            cursor=defaultCursor,
            style=defaultStyle,
            variable=_rbv,
            value=0,
        )
        w._tkvar = _rbv
    elif widgetName == "Scale":
        w = tboot.Scale(_parent, cursor=defaultCursor, style=defaultStyle)
    elif widgetName == "Progressbar":
        w = tboot.Progressbar(
            _parent, value=50.0, cursor=defaultCursor, style=defaultStyle
        )
    elif widgetName == "Floodgauge":
        w = tboot.Floodgauge(
            _parent, value=50, cursor=defaultCursor, style=defaultStyle
        )
    elif widgetName == "Meter":
        w = tboot.Meter(
            _parent,
            metersize=150,
            padding=5,
            amountused=25,
            metertype="semi",
            subtext="value",
            interactive=True,
        )
    # ---- Standard tk / ttk widgets -----------------------------------
    elif widgetName == "tk.Button":
        w = tk.Button(_parent, text=widgetName, cursor=defaultCursor)
    elif widgetName == "Text":
        w = tk.Text(
            _parent,
            width=20,
            height=5,
            cursor=defaultCursor,
            borderwidth=1,
            relief=tk.SOLID,
        )
    elif widgetName == "Listbox":
        w = tk.Listbox(
            _parent,
            width=20,
            height=6,
            cursor=defaultCursor,
            borderwidth=1,
            relief=tk.SOLID,
            selectmode=tk.BROWSE,
        )
    elif widgetName == "Treeview":
        w = tboot.Treeview(
            _parent,
            columns=("col1",),
            show="headings",
            cursor=defaultCursor,
        )
        w.heading("col1", text="Column 1")
    elif widgetName == "Scrollbar":
        w = tboot.Scrollbar(_parent, orient=tk.VERTICAL, style=defaultStyle)
    elif widgetName == "Separator":
        # Separator requires a fully-qualified style name: orient is baked in.
        sep_style = f"{defaultStyle}.Horizontal.TSeparator"
        w = tboot.Separator(_parent, orient=tk.HORIZONTAL, style=sep_style)
    elif widgetName == "Sizegrip":
        w = tboot.Sizegrip(_parent, style=defaultStyle)
    else:
        log.warning("Widget %s not implemented", widgetName)
        return

    cw.createWidget(_parent, w)
    _placeNewWidget(w, x, y, width=72, height=32)


def rightMouseDown(event):
    # global mainCanvas
    log.debug("rightMouseDown -- event %s", str(event))
    popup = tboot.Menu(mainFrame, tearoff=0)
    for wName in myVars.containerWidgetsUsed:
        popup.add_command(
            label=wName, command=lambda e=event, w=wName: createWidgetPopup(e, w)
        )
    for wName in myVars.widgetsUsed:
        popup.add_command(
            label=wName, command=lambda e=event, w=wName: createWidgetPopup(e, w)
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
    global mainCanvas, geomWidgetFrame
    mainCanvas = tboot.Canvas(
        mainFrame, width=40, height=100, relief=tk.SOLID, borderwidth=1
    )
    mainCanvas.grid(
        row=0, column=0, columnspan=cols, rowspan=rows, padx=5, pady=5, sticky="NSEW"
    )
    mainCanvas.bind("<Button-3>", rightMouseDown)

    # For Grid / Pack modes create an inner Frame that fills the canvas.
    # Widgets are parented to this frame so their geometry manager is
    # isolated from mainFrame's grid (which owns mainCanvas itself).
    mgr = myVars.geomManager
    if mgr in ("Grid", "Pack"):
        geomWidgetFrame = tboot.Frame(mainCanvas)
        # Give the inner frame a large initial size so widgets aren't clipped.
        # The canvas create_window will be resized on every <Configure> event.
        geomWidgetFrame.configure(width=1200, height=900)
        # Allow every column/row to expand so grid cells grow with the frame
        for c in range(32):
            geomWidgetFrame.columnconfigure(c, weight=1, minsize=60)
        for r in range(32):
            geomWidgetFrame.rowconfigure(r, weight=1, minsize=30)
        # Place the frame so it fills the whole canvas
        mainCanvas.create_window(
            0, 0, window=geomWidgetFrame, anchor="nw", tags="geomframe"
        )
        # Bug fix: right-click on empty frame background must reach rightMouseDown.
        # geomWidgetFrame covers the entire canvas so mainCanvas never sees the event.
        geomWidgetFrame.bind("<Button-3>", rightMouseDown)
        # Overlay canvas for grid guide-lines (drawn inside geomWidgetFrame so
        # they appear above the frame background but below child widgets).
        _make_grid_overlay(geomWidgetFrame)

        # Expand the window when the canvas is resized; also redraw guides
        def _resize_geom_frame(event):
            mainCanvas.itemconfig("geomframe", width=event.width, height=event.height)
            if _gridOverlayCanvas is not None:
                _gridOverlayCanvas.place(
                    x=0, y=0, width=event.width, height=event.height
                )
                tk.Misc.lower(_gridOverlayCanvas)
            drawGridLines()

        mainCanvas.bind("<Configure>", _resize_geom_frame)
        cw.createWidget.baseRoot = geomWidgetFrame
    else:
        geomWidgetFrame = None
        cw.createWidget.baseRoot = mainCanvas
        # For Place mode, redraw dot grid on resize
        mainCanvas.bind("<Configure>", lambda e: drawGridLines())

    drawGridLines()
    # mainCanvas.bind('<Motion>',frameMove)


def setGeomManager(mgr: str) -> None:
    """Change the active geometry manager.

    Only allowed when the canvas is empty.  Once widgets exist the manager
    is locked for the lifetime of the project to avoid geometry conflicts.
    """
    if cw.createWidget.widgetList:
        Messagebox.show_warning(
            title="Cannot change geometry manager",
            message=(
                "Widgets already exist on the canvas.\n\n"
                "Mixing geometry managers causes tkinter conflicts.\n"
                "Start a New Project to choose a different manager."
            ),
        )
        return
    myVars.geomManager = mgr
    log.info("Geometry manager set to %s", mgr)
    if hasattr(rootWin, "_geomLabel"):
        rootWin._geomLabel.config(text="Layout: " + mgr)
    # Rebuild the canvas inner frame for the new manager
    _rebuild_canvas_for_geom()


def _rebuild_canvas_for_geom():
    """Recreate the inner geomWidgetFrame (or clear it) to match the
    current myVars.geomManager.  Call after geomManager changes."""
    global geomWidgetFrame, _gridOverlayCanvas
    if mainCanvas is None:
        return
    # Destroy old inner frame if present (also destroys _gridOverlayCanvas child)
    if geomWidgetFrame is not None:
        try:
            geomWidgetFrame.destroy()
        except tk.TclError:
            pass
        geomWidgetFrame = None
    _gridOverlayCanvas = None
    # Clear any leftover canvas windows
    mainCanvas.delete("geomframe")
    mainCanvas.unbind("<Configure>")

    mgr = myVars.geomManager
    if mgr in ("Grid", "Pack"):
        geomWidgetFrame = tboot.Frame(mainCanvas)
        # Give the inner frame a large initial size so widgets aren't clipped.
        geomWidgetFrame.configure(width=1200, height=900)
        # Allow every column/row to expand so grid cells grow with the frame
        for c in range(32):
            geomWidgetFrame.columnconfigure(c, weight=1, minsize=60)
        for r in range(32):
            geomWidgetFrame.rowconfigure(r, weight=1, minsize=30)
        mainCanvas.create_window(
            0, 0, window=geomWidgetFrame, anchor="nw", tags="geomframe"
        )
        # Bug fix: right-click on empty frame background must reach rightMouseDown.
        geomWidgetFrame.bind("<Button-3>", rightMouseDown)
        # Overlay canvas for grid guide-lines
        _make_grid_overlay(geomWidgetFrame)

        def _resize_geom_frame(event):
            mainCanvas.itemconfig("geomframe", width=event.width, height=event.height)
            if _gridOverlayCanvas is not None:
                _gridOverlayCanvas.place(
                    x=0, y=0, width=event.width, height=event.height
                )
                tk.Misc.lower(_gridOverlayCanvas)
            drawGridLines()

        mainCanvas.bind("<Configure>", _resize_geom_frame)
        cw.createWidget.baseRoot = geomWidgetFrame
    else:
        geomWidgetFrame = None
        cw.createWidget.baseRoot = mainCanvas
        mainCanvas.bind("<Configure>", lambda e: drawGridLines())
    drawGridLines()


def buildMainGui():
    global mainFrame

    buildMenu()

    # ---- Toolbar row (row 0) -------------------------------------------
    toolbarFrame = tboot.Frame(rootWin)
    toolbarFrame.grid(row=0, column=0, sticky="EW", padx=4, pady=2)

    # Show the active geometry manager as a read-only label.
    # The manager is chosen once at New Project time; the buttons have been
    # removed to prevent mid-session switching confusion.
    tboot.Label(toolbarFrame, text="Layout:").pack(side=tk.LEFT, padx=(0, 2))
    geomLabel = tboot.Label(toolbarFrame, text=myVars.geomManager, bootstyle="info")
    geomLabel.pack(side=tk.LEFT, padx=(0, 8))
    rootWin._geomLabel = geomLabel

    # ---- Undo/Redo status label (right side of toolbar) ---------------
    undoLabel = tboot.Label(
        toolbarFrame, text="", bootstyle="secondary", font=("TkDefaultFont", 8)
    )
    undoLabel.pack(side=tk.RIGHT, padx=(8, 4))
    rootWin._undoLabel = undoLabel

    def _refresh_undo_label():
        try:
            rootWin._undoLabel.config(text=undoredo.stack.describe())
        except tk.TclError:
            pass

    undoredo.stack.on_change = _refresh_undo_label

    # Keyboard bindings for undo / redo
    rootWin.bind("<Control-z>", lambda e: undoredo.stack.undo())
    rootWin.bind("<Control-Z>", lambda e: undoredo.stack.undo())
    rootWin.bind("<Control-y>", lambda e: undoredo.stack.redo())
    rootWin.bind("<Control-Y>", lambda e: undoredo.stack.redo())
    rootWin.bind("<Control-Shift-z>", lambda e: undoredo.stack.redo())
    rootWin.bind("<Control-Shift-Z>", lambda e: undoredo.stack.redo())

    # ---- Main canvas frame (row 1) ------------------------------------
    mainFrame = tboot.Labelframe(
        rootWin, width=600, height=150, labelanchor=tk.N, text="No Project Selected"
    )
    mainFrame.grid(row=1, column=0, sticky="NWES")
    # baseRoot is set inside buildGrid() once mainCanvas is created

    mainFrame.columnconfigure(0, weight=1)
    mainFrame.rowconfigure(0, weight=1)
    sg0 = tboot.Sizegrip(mainFrame)
    sg0.grid(row=1, sticky=tk.SE)
    sg0.bind("<ButtonRelease-1>", sizeGripRelease)

    rootWin.geometry("900x820")
    rootWin.resizable(True, True)
    rootWin.columnconfigure(0, weight=1)
    rootWin.rowconfigure(1, weight=1)  # row 1 is the canvas, let it expand

    buildGrid(24, 24)


if __name__ == "__main__":
    logging.basicConfig()
    # logging.basicConfig(format=logFormat)
    # log = logging.getLogger(name='mylogger')
    coloredlogs.install(
        logger=log, fmt="%(levelname)-8s| %(lineno)-4d %(filename)-20s| %(message)s"
    )
    # arg1 = "warn"
    # arg1 = "info"
    try:
        arg1 = sys.argv[1]
    except IndexError:
        # arg1 = "warn"
        arg1 = "info"

    if arg1 == "info":
        coloredlogs.set_level(logging.INFO)
    elif arg1 == "debug":
        coloredlogs.set_level(logging.DEBUG)
    else:
        coloredlogs.set_level(logging.WARN)
    myVars.initVars()
    myVars.theme = useTheme
    log.info("mainFrame %s %s", mainFrame, str(mainFrame))

    buildMainGui()
    myVars.style = tboot.Style()
    # Expose drawGridLines to createWidget without a circular import
    myVars.redrawGridLines = drawGridLines
    rootWin.mainloop()
