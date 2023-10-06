import logging
import os
import pickle
import sys
import tkinter as tk
from collections import defaultdict
from functools import partial
from tkinter.colorchooser import askcolor
from typing import Any

import coloredlogs
import ttkbootstrap as ttk

import createWidget as cw
import pytkguivars

rootWin = ttk.Window(themename="darkly")
mainFrame: ttk.Frame()
rootWin.title('Python Tk GUI Builder')
iconBar: ttk.Frame()
mainCanvas: ttk.Canvas()
style: Any


def printf(format,*args):
    sys.stdout.write(format % args)


def newLabel():
    global mainCanvas
    label = ttk.Label(mainCanvas,text="Label",borderwidth=1,relief=tk.SOLID,anchor=tk.CENTER)
    cw.createWidget(mainCanvas,label)
    width = label.winfo_width()
    height = label.winfo_height()
    log.debug("width " + str(width) + " height " + str(height))


def newButton():
    global mainCanvas
    b = tk.Button(mainCanvas,text="Button")
    cw.createWidget(mainCanvas,b)


def newButton0():
    global mainCanvas
    b = tk.Button(mainCanvas,text="Button")
    cw.createWidget(mainCanvas,b)


def newLabel0():
    global mainCanvas
    b = tk.Label(mainCanvas,text="Label")
    cw.createWidget(mainCanvas,b)


def newCanvas0():
    global mainCanvas
    b = ttk.Canvas(mainCanvas)
    cw.createWidget(mainCanvas,b)


def newEntry0():
    global mainCanvas
    # b = ttk.Bootstyle.update_ttk_widget_style()
    b = ttk.ScrolledText(mainCanvas)
    cw.createWidget(mainCanvas,b)


def newEntry():
    global mainCanvas
    e = ttk.Entry(mainCanvas,background='lightblue',width=12)
    cw.createWidget(mainCanvas,e)


def newLabScale():
    global mainCanvas
    e = ttk.ScrolledText(mainCanvas)
    cw.createWidget(mainCanvas,e)


def newSpinbox():
    global mainCanvas
    e = ttk.Spinbox(mainCanvas)
    # e = ttk.LabeledScale(mainCanvas)
    cw.createWidget(mainCanvas,e)


def newCombobox():
    global mainCanvas
    w = ttk.Combobox(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newCheckbutton():
    global mainCanvas
    w = ttk.Checkbutton(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newRadiobutton():
    global mainCanvas
    w = ttk.Radiobutton(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newTreeview():
    global mainCanvas
    w = ttk.Treeview(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newScale():
    global mainCanvas
    w = ttk.Scale(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newNotebook():
    global mainCanvas
    w = ttk.Notebook(mainCanvas,height=100,width=100)
    cw.createWidget(mainCanvas,w)
    frame1 = ttk.Frame(w)
    cw.createWidget(w,frame1)
    # frame2 = ttk.Frame(w)
    label1 = ttk.Label(frame1,text="This is Window One")
    cw.createWidget(frame1,label1)
    label1.pack(pady=50,padx=20)
    w.add(frame1,text="Window 1")


# newFrame newLabelFrame newPanedWindow newScrollbar
def newScrollbar():
    global mainCanvas
    w = ttk.Scrollbar(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newPanedWindow():
    global mainCanvas
    w = ttk.Panedwindow(mainCanvas,height=50,width=50)
    cw.createWidget(mainCanvas,w)


def newLabelFrame():
    global mainCanvas
    w = ttk.Labelframe(mainCanvas,borderwidth=1,height=50,width=50,text='Labelframe')
    cw.createWidget(mainCanvas,w)


def newFrame():
    global mainCanvas
    w = ttk.Frame(mainCanvas,borderwidth=1,height=50,width=50)
    cw.createWidget(mainCanvas,w)


def newProgressbar():
    global mainCanvas
    # x = ttk.Widget()
    w = ttk.Progressbar(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newSeparator():
    global mainCanvas
    w = ttk.Separator(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newTtkButton():
    global mainCanvas
    global xstart
    global ystart

    mystyle = ttk.Style()
    mystyle.configure('TButton',background='lightblue',foreground='black')
    b = ttk.Button(mainCanvas,text="Button")  # style=mystyle)
    cw.createWidget(mainCanvas,b)


def setTheme(theme: object):
    global style
    log.debug(theme)
    # style = ttk.Style(rootWin)
    style.theme_use(theme)

    for color_label in style.colors:
        color = style.colors.get(color_label)
        print(color_label,color)


def tree(): return defaultdict(tree)


def Merge(dict1,dict2):
    res = {**dict1,**dict2}
    return res


def createCleanNameList() -> list:
    cleanNameList = []
    for c in cw.createWidget.widgetNameList:
        name = c[cw.NAME]
        parent = c[cw.PARENT]
        children = c[cw.CHILDREN]
        cleanNameList.append([name,parent,'',children])
    return cleanNameList


def findWidgetsParent(widgetName) -> str:
    for nameEntry in cw.createWidget.widgetNameList:
        if widgetName == nameEntry[cw.NAME]:
            return nameEntry[cw.PARENT]
    log.error("Failed to find a parent for %s",widgetName)
    return ''


def saveProject():
    global mainCanvas
    widgetCount = 0
    createdWidgetOrder = [pytkguivars.rootWidgetName]
    width = 0  # mainCanvas.winfo_width
    height = 0  # mainCanvas.winfo_height
    cleanList = createCleanNameList()
    projectData = {"ProjectName":'test','ProjectPath':'/tmp/test','width':width,'height':height,
                   'theme':pytkguivars.theme,'widgetNameList':cleanList,
                   'backgroundColor':pytkguivars.backgroundColor}
    # Work out the order to create the Widgets so the parenting is correct
    sanityCheckCount = 0
    finished = False
    while not finished:
        finished = True
        sanityCheckCount += 1
        if sanityCheckCount > 1000:
            log.critical("Loop is not exiting Ahhhhh %d",sanityCheckCount)
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
    log.debug('createdWidgetOrder %s',str(createdWidgetOrder))
    pytkguivars.createdWidgetOrder = createdWidgetOrder
    for widgetName in createdWidgetOrder:
        # widgetParent = findWidgetsParent(widgetName)
        if widgetName == pytkguivars.rootWidgetName:
            continue
        newWidget = pytkguivars.saveWidgetAsDict(widgetName)

        log.debug('widgetCount %d newWidget %s',widgetCount,str(newWidget))
        widgetCount += 1
        # project["widgetName"] = .widgetName
        tmpData = Merge(projectData,newWidget)
        projectData = tmpData
    projectData1 = Merge(projectData,{'widgetCount':widgetCount})
    projectData = projectData1
    log.debug('projectData ->%s<-',str(projectData))
    pytkguivars.projectDict = projectData
    f = open("/tmp/pytkguitest.pk1","wb")
    try:
        pickle.dump(projectData,f)
    except TypeError as e:
        log.error("Exception TypeError %s",str(e))
        log.warning("Error in Project Data \n%s",str(projectData))
    f.close()


alphaList = ["a","b","c","d","e","f","g","h","i","d","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]


def runMe():
    global alphaList
    if pytkguivars.projectDict == {}:
        saveProject()
    runDict = pytkguivars.projectDict
    nWidgets = runDict.get('widgetCount')
    largestWidth = 200
    largestHeight = 200
    # print('width',width,'height',height)
    print('nWidgets',nWidgets)
    print("# -------------------------")
    sys.stdout = open('/tmp/test.py','w')
    print("import tkinter as tk\nfrom tkinter import ttk\nfrom ttkthemes import ThemedTk")
    print("import sv_ttk\n")
    print("rootWin = ThemedTk()")
    rootName = pytkguivars.rootWidgetName
    print(rootName + "= ttk.Frame(rootWin, width=40, height=100, relief='ridge', borderwidth=1)")
    print("sv_ttk.use_light_theme()")
    print("style = ttk.Style(rootWin)")
    print("style.theme_use('clam')\n")
    # Create widgets on the rootFrame first
    for widgetName in pytkguivars.createdWidgetOrder:
        # widgetId = "Widget" + str(n)
        if widgetName == rootName:
            continue
        parentName = findWidgetsParent(widgetName)
        # Get the parent Name
        wDict = runDict.get(widgetName)
        if wDict != {}:
            log.debug('Dictionary for %s = %s',widgetName,str(wDict))
            wType = wDict.get('WidgetName')
            t = pytkguivars.fixWidgetTypeName(wType)
            wType = t
            keyCount = widgetName + "-KeyCount"
            widgetDef = widgetName + ' = ' + wType + '(' + parentName
            nKeys = wDict.get(keyCount)
            for a in range(nKeys):
                useValQuotes = True
                attribute = 'Attribute' + str(a)
                aDict = wDict.get(attribute)
                key = aDict.get('Key')
                val = aDict.get('Value')
                if key == 'from':
                    # Bug in tkinter -- no
                    # 'from' is a python keyword
                    key = 'from_'
                if val.find('<') > -1:
                    # Typically, this a TK object that is in < xxx > format
                    log.warning("key %s ->%s<-has a weird value",key,val)
                    continue
                if val.find('(') > -1:
                    # '(' is in lists for combo boxes
                    # The 'values' key has this saved format. This might be a tk thing.
                    # It needs to be converted to a list
                    newVal = pytkguivars.fixComboValues(key,val)
                    val = newVal
                    useValQuotes = False
                if len(val) > 0:
                    # keys are not consistent ...
                    if useValQuotes:
                        tmpWidgetDef = widgetDef + ',' + key + '=\'' + val + '\''
                    else:
                        tmpWidgetDef = widgetDef + ',' + key + '=' + val
                    widgetDef = tmpWidgetDef
            print(widgetDef + ')')
            place = wDict.get('Place')
            # print(place)
            x = place.get('x')
            y = place.get('y')
            width = place.get('width')
            height = place.get('height')
            try:
                widthPos = int(x) + int(width)
                heightPos = int(y) + int(height)
                if widthPos > largestWidth:
                    largestWidth = widthPos
                if heightPos > largestHeight:
                    largestHeight = heightPos
            except ArithmeticError as e:
                log.warning('ArithmeticError %s',str(e))
            except ValueError as e:
                log.warning('ValueError %s',str(e))

            anchor = place.get('anchor')
            bordermode = place.get('bordermode')
            print(
                widgetName + ".place(" + "x=" + x + ",y=" + y + ",width=" + width + ",height=" +
                height + ",anchor='" + anchor + "',bordermode='" + bordermode + "')")
    largestWidth += 20
    largestHeight += 20
    geom = str(largestWidth) + 'x' + str(largestHeight)
    print("rootWin.geometry('" + geom + "')")
    print("rootWin.resizable(True,True)")
    print("rootWin.columnconfigure(0,weight=1)")
    print("rootWin.rowconfigure(0,weight=1)")
    print("sg0 = ttk.Sizegrip(rootWin)")
    print("sg0.grid(row=1,sticky=tk.SE)")
    print(rootName + ".place(x=0, y=0, relwidth=1.0, relheight=1.0)")
    print("\nrootWin.mainloop()")
    sys.stdout.close()
    sys.stdout = sys.__stdout__
    cmd = "python3 /tmp/test.py &"
    os.system(cmd)


def checkWidgetNameList():
    # Check for cild entries that are left over from reparenting operations
    # NAME 0 PARENT 1 WIDGET 2 CHILDREN 3
    for nl1 in cw.createWidget.widgetNameList:
        widgetName1 = nl1[cw.NAME]
        parentName1 = nl1[cw.PARENT]
        for nl2 in cw.createWidget.widgetNameList:
            widgetName2 = nl2[cw.NAME]
            if parentName1 != widgetName2:
                # This is not first parent, thus it should not have widgetName1 as a child
                found = False
                children2 = nl2[cw.CHILDREN]
                for child in children2:
                    if child == widgetName1:
                        found = True
                if found:
                    children2.remove(widgetName1)


def changeParentOfTo(widgetName,parentName):
    # find both widgets
    widgetList = cw.findPythonWidgetNameList(widgetName)
    parentList = cw.findPythonWidgetNameList(parentName)
    if widgetList == [] or parentList == []:
        log.error("Empty Lists")
        return
    widget = widgetList[cw.WIDGET]
    parent = parentList[cw.WIDGET]
    widget.place(in_=parent)
    widget.parent = parent
    widget.update()
    tk.Misc.lift(widget,parent)
    cw.updateWidgetNameList(widgetName,parent)


def loadProject():
    global alphaList
    f = open("/tmp/pytkguitest.pk1","rb")
    data = pickle.load(f)
    f.close()
    runDict = data
    log.debug(runDict)
    pytkguivars.backgroundColor = runDict.get('backgroundColor')
    widgetNameList = runDict.get('widgetNameList')
    nWidgets = runDict.get('widgetCount')
    widgetsFound = 0
    n = 0
    while widgetsFound < nWidgets:
        # for n in range(nWidgets + 4):
        widgetId = "Widget" + str(n)
        wDict = runDict.get(widgetId)
        if wDict is not None:
            widgetsFound += 1
            widgetDef = pytkguivars.buildAWidget(n,wDict)
            try:
                widget = eval(widgetDef)
            except TypeError as e:
                log.error("%d dict %s eval() Exception %s",n,str(wDict),str(e))
                continue
            w = cw.createWidget(mainCanvas,widget)
            place = wDict.get('Place')
            log.debug(place)
            w.addPlace(place)
        n += 1
        if  n > (nWidgets * 10):
            log.error("Cannot locate All Widgets tried %d times expected to find %d found %d",
                      n,nWidgets,widgetsFound)
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
            log.debug("name %s parent %s children %s",name,parent,children)
            for child in children:
                log.debug("    %s has a child %s",name,child)
                changeParentOfTo(child,name)
            if parent != pytkguivars.rootWidgetName:
                log.debug("%s is the parent of %s",parent,name)
                changeParentOfTo(name,parent)
        else:
            log.warning("name %s parent %s children %s",name,parent,children)
            log.warning('widgetNameList %s',str(widgetNameList))

    checkWidgetNameList()


def exitApp():
    rootWin.destroy()


def widgetTree():
    for w in cw.createWidget.widgetList:
        print("WidgetList",
              str(w),
              w.winfo_class(),
              w.winfo_parent(),
              w.winfo_children(),
              w.winfo_geometry())
    for nl in cw.createWidget.widgetNameList:
        print("WidgetNameList",nl)


def chooseBackground():
    global mainCanvas
    colors = askcolor(title="Tkinter color chooser")
    if colors[1] is not None:
        mainCanvas.configure(bg=colors[1])
        mainCanvas.update()
        pytkguivars.backgroundColor = colors[1]


def buildMenu():
    global rootWin
    global newLabel
    global mainFrame
    global style
    menuBar = ttk.Menu(rootWin)
    style = ttk.style.Style()
    themes = []
    for themeName in style.theme_names():
        themes.append(themeName)
    # style = ttk.Style(rootWin)
    # themes = style.theme_names()
    # log.debug(themes[1])
    # themes
    rootWin.config(menu=menuBar)
    fileMenu = ttk.Menu(menuBar,tearoff=0)
    # add menu items to the File menu
    fileMenu.add_command(label='New')
    fileMenu.add_command(label='Open',command=loadProject)
    fileMenu.add_command(label='Close')
    fileMenu.add_command(label='Save',command=saveProject)
    fileMenu.add_command(label='Run',command=runMe)
    fileMenu.add_command(label='Widget Tree',command=widgetTree)
    fileMenu.add_separator()

    fileMenu.add_command(label='Exit',command=exitApp)

    # add a submenu
    subMenu = ttk.Menu(fileMenu,tearoff=0)
    # subMenu.add_command(label='Keyboard Shortcuts')
    subMenu.add_command(label='Background Color',command=chooseBackground)
    subMenu.add_command(label='Themes')
    subMenu.add_command(label='Color Themes')

    menuBar.add_cascade(label="File",menu=fileMenu,underline=0)
    # widget Menu
    widgetMenu = tk.Menu(menuBar,tearoff=1)
    widgetMenu.add_command(label='Button',command=newButton0)
    widgetMenu.add_command(label='Label',command=newLabel0)
    widgetMenu.add_command(label='Canvas',command=newCanvas0)
    widgetMenu.add_command(label='Entry',command=newEntry0)
    menuBar.add_cascade(label="tk Widgets",menu=widgetMenu,underline=0)
    ttkWidgetMenu = tk.Menu(menuBar,tearoff=1)
    # ttkWidgetMenu.add_command(label='tk Button', command=newButton)
    ttkWidgetMenu.add_command(label='Button',command=newTtkButton)
    ttkWidgetMenu.add_command(label='Checkbutton',command=newCheckbutton)
    ttkWidgetMenu.add_command(label='Entry',command=newEntry)
    ttkWidgetMenu.add_command(label='Frame',command=newFrame)
    ttkWidgetMenu.add_command(label='Label',command=newLabel)
    ttkWidgetMenu.add_command(label='LabelFrame',command=newLabelFrame)
    ttkWidgetMenu.add_command(label='PanedWindow',command=newPanedWindow)
    ttkWidgetMenu.add_command(label='Radiobutton',command=newRadiobutton)
    ttkWidgetMenu.add_command(label='Scale',command=newScale)
    ttkWidgetMenu.add_command(label='Scrollbar',command=newScrollbar)
    ttkWidgetMenu.add_command(label='Spinbox',command=newSpinbox)
    ttkWidgetMenu.add_command(label='Notebook',command=newNotebook)
    ttkWidgetMenu.add_command(label='Treeview',command=newTreeview)
    ttkWidgetMenu.add_command(label='LabledScale',command=newLabScale)
    ttkWidgetMenu.add_command(label='Combobox',command=newCombobox)
    ttkWidgetMenu.add_command(label='Progressbar',command=newProgressbar)
    ttkWidgetMenu.add_command(label='Seperator',command=newSeparator)
    menuBar.add_cascade(label="ttk Widgets",menu=ttkWidgetMenu,underline=0)
    themeMenu = ttk.Menu(menuBar,tearoff=0)
    for t in themes:
        mypartial = partial(setTheme,t)
        themeMenu.add_command(label=t,command=mypartial)

    # create the Help menu
    helpMenu = ttk.Menu(menuBar,tearoff=0)
    # helpMenu = ttk.OptionMenu(menuBar, tearoff=0)

    helpMenu.add_command(label='Welcome')
    helpMenu.add_command(label='About...')

    menuBar.add_cascade(label="Theme",menu=themeMenu,underline=0)
    # add the Help menu to the menuBar
    menuBar.add_cascade(label="Help",menu=helpMenu,underline=0)

    # add the File menu to the menuBar
    fileMenu.add_cascade(label="Preferences",menu=subMenu)


def leftMotion(arg):
    # x = arg.x
    # y = arg.y
    pass


def leftClick(arg):
    # global xstart
    # global ystart
    # xstart = arg.x_root
    # ystart = arg.y_root
    pass


def doNothing():
    # Not sure what this is for . Delete later
    pass


def leftRelease(arg):
    global mainFrame
    global rect
    # Arg1 is an Event
    log.info('Release--->' + str(arg) + '<---')
    # moveB.unbind("<B1-Motion>")


def frameMove(event):
    # log.debug(event)
    # log.debug(event.x)
    pass


def drawGridLines():
    """

    """
    global mainCanvas
    # Get dimensions ....
    mainCanvas.update()
    width = mainCanvas.winfo_width()
    height = mainCanvas.winfo_height()
    # log.debug("width ",width," height ",height," snapTo ",pytkguivars.snapTo)
    log.debug("Width %d height %d snapTo %s",width,height,pytkguivars.snapTo)


def sizeGripRelease(event):
    log.debug(event)
    drawGridLines()


def rightMouseDown():
    global mainCanvas


def buildGrid(rows,cols):
    """
    :rtype: object
    """
    global mainFrame
    global mainCanvas
    # mainCanvas = ttk.Frame(mainFrame, width=40, height=100, relief="ridge", borderwidth=2 )
    # mainCanvas = ttk.Canvas(mainFrame,width=40,height=100,relief=tk.SOLID,borderwidth=1,bg=pytkguivars.backgroundColor)
    mainCanvas = ttk.Canvas(mainFrame,width=40,height=100,relief=tk.SOLID,borderwidth=1)
    mainCanvas.grid(row=0,column=0,columnspan=cols,rowspan=rows,padx=5,pady=5,sticky="NSEW")
    mainCanvas.bind('<Button-3>',rightMouseDown)
    drawGridLines()
    mainCanvas.bind('<Motion>',frameMove)


def buildMainGui():
    global rootWin
    global mainFrame
    global style

    buildMenu()

    mainFrame = ttk.Frame(rootWin,width=600,height=150)
    mainFrame.grid(row=0,column=0,sticky='NWES')

    mainFrame.columnconfigure(0,weight=1)
    mainFrame.rowconfigure(0,weight=1)
    sg0 = ttk.Sizegrip(mainFrame)
    sg0.grid(row=1,sticky=tk.SE)
    sg0.bind("<ButtonRelease-1>",sizeGripRelease)

    rootWin.geometry('600x600')
    rootWin.resizable(True,True)
    rootWin.columnconfigure(0,weight=1)
    rootWin.rowconfigure(0,weight=1)

    buildGrid(24,24)


if __name__ == '__main__':
    logging.basicConfig()
    # logging.basicConfig(format=logFormat)
    log = logging.getLogger(name='mylogger')
    coloredlogs.install(logger=log,fmt='%(levelname)-8s| %(lineno)-4d %(filename)-20s| %(message)s')

    coloredlogs.set_level(logging.INFO)
    # coloredlogs.set_level(logging.WARN)
    # coloredlogs.set_level(logging.DEBUG)

    pytkguivars.initVars()
    buildMainGui()
    style = ttk.style.Style()
    rootWin.mainloop()
