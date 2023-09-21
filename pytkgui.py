import tkinter as tk
from tkinter import ttk
import pickle
import createWidget as cw
import pytkguivars
import pytkguivars as guivars

from ttkthemes import ThemedTk
import sv_ttk
from functools import partial
from typing import Any
from collections import defaultdict

# rootWin = tk.Tk()
rootWin = ThemedTk()
mainFrame: ttk.Frame()
rootWin.title('Python Tk GUI Builder')
iconBar: ttk.Frame()
mainCanvas: tk.Canvas()
moveB: ttk.Button()
moveL: tk.Label()
style: Any


def newLabel():
    global moveL
    global mainCanvas
    global xstart
    global ystart
    label = ttk.Label(mainCanvas,text="Label",borderwidth=1,relief=tk.SOLID,anchor=tk.CENTER)
    cw.createWidget(mainCanvas,label)
    width = label.winfo_width()
    height = label.winfo_height()
    print("width " + str(width) + " height " + str(height))


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
    b = tk.Canvas(mainCanvas)
    cw.createWidget(mainCanvas,b)


def newEntry0():
    global mainCanvas
    b = tk.Entry(mainCanvas)
    cw.createWidget(mainCanvas,b)


def newEntry():
    global mainCanvas
    e = ttk.Entry(mainCanvas,background='lightblue',width=12)
    cw.createWidget(mainCanvas,e)


def newLabScale():
    global mainCanvas
    e = ttk.LabeledScale(mainCanvas)
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
    w = ttk.Notebook(mainCanvas)
    cw.createWidget(mainCanvas,w)


def newProgressbar():
    global mainCanvas
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
    
    style = ttk.Style()
    # style.theme_use('alt')
    style.configure('TButton',background='lightblue',foreground='black')
    # width = 20, borderwidth=1, focusthickness=3, focuscolor='none')
    # style.map('TButton', background=[('active','red')])
    b = ttk.Button(mainCanvas,text="Button")
    cw.createWidget(mainCanvas,b)


def setTheme(theme: object):
    global rootWin
    global style
    print(theme)
    # style = ttk.Style(rootWin)
    style.theme_use(theme)


def Merge(dict1,dict2):
    res = {**dict1,**dict2}
    return res


def tree(): return defaultdict(tree)
def saveMe():
    global mainCanvas
    project = tree()
    widgetCount = 0
    width = 0 # mainCanvas.winfo_width
    height = 0 # mainCanvas.winfo_height
    projectData = {"ProjectName":'test','ProjectPath':'/tmp/test','width': width,'height': height}
    for w in cw.createWidget.widgetList:
        if (w is not None) and (len(str(w)) > 2):
            print("=-----------")
            parent = w.winfo_parent()
            print('widgetName ', w.widgetName, "Parent", parent)
            project["widgetName"] = w.widgetName
            widgetId = 'Widget' + str(widgetCount)
            widgetCount += 1
            place = w.place_info()
            widgetDict = {'WidgetName':w.widgetName,'Place':place}
            place['in'] = widgetId
            project["Place"] = place
            keyCount = 0
            keys = w.keys()
            if keys:
                for key in keys:
                    print('Key->',key,'<-')
                    if key != 'in':
                        value = w[key]
                        print('Value->',value,'<-')
                        attrId = 'Attribute' + str(keyCount)
                        # widgetAttribute = {attrId: {'Key': key,'Type': type(value),'Value': str(value)}}
                        # Ignore empty values
                        if (value is not None) and (len(str(value)) > 0):
                            widgetAttribute = {attrId:{'Key':key,'Value':str(value)}}
                            newWidget = Merge(widgetDict,widgetAttribute)
                            widgetDict = newWidget
                            keyCount += 1
            widgetKeys = widgetId + '-KeyCount'
            tmpDict = Merge(widgetDict,{widgetKeys: keyCount})
            newWidget = {widgetId:tmpDict}
            tmpData = Merge(projectData,newWidget)
            projectData = tmpData
    projectData1 = Merge(projectData,{'widgetCount': widgetCount})
    projectData = projectData1
    print(projectData)
    pytkguivars.projectDict = projectData
    # pickle.loads(fp) to load
    pd = pickle.dumps(projectData)
    print(pd)
    f = open("/tmp/pytkguitest.pk1","wb")
    pickle.dump(projectData, f)
    f.close()


alphaList = ["a","b","c","d","e","f","g","h","i","d","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]


def runMe():
    global alphaList
    if pytkguivars.projectDict == {}:
        saveMe()
    runDict = pytkguivars.projectDict
    nWidgits = runDict.get('widgetCount')
    largestWidth = 200
    largestHeight= 200
    # print('width',width,'height',height)
    print('nWidgets',nWidgits)
    print("# -------------------------")
    print("import tkinter as tk\nfrom tkinter import ttk\nfrom ttkthemes import ThemedTk")
    print("import sv_ttk\n")
    print("rootWin = ThemedTk()")
    print("rootFrame = ttk.Frame(rootWin, width=40, height=100, relief='ridge', borderwidth=1)")
    print("sv_ttk.use_light_theme()")
    print("style = ttk.Style(rootWin)")
    print("style.theme_use('scidblue')\n")
    for n in range(nWidgits):
        widgetId = "Widget" + str(n)
        wDict = runDict.get(widgetId)
        if wDict != {}:
            wType = wDict.get('WidgetName')
            t = wType.replace('ttk::','ttk.')
            wType = t
            idx = wType.find('.')
            if idx == -1: # Not ttk widgets
                t = 'tk.' + wType
                wType = t
            for ch in alphaList:
                t = wType.replace('.' + ch , '.' + ch.upper() )
                wType = t
            widgetDef= widgetId + ' = ' + wType + '(rootFrame'
            keyCount = widgetId + "-KeyCount"
            nKeys = wDict.get(keyCount)
            for a in range(nKeys):
                attribute = 'Attribute' + str(a)
                aDict = wDict.get(attribute)
                key = aDict.get('Key')
                val = aDict.get('Value')
                tmpWidgetDef =  widgetDef + ', ' + key + '=\'' + val + '\' '
                widgetDef = tmpWidgetDef
            print(widgetDef + ')')
            place = wDict.get('Place')
            # print(place)
            x = place.get('x')
            y = place.get('y')
            try:
                width = place.get('width')
                height = place.get('height')
                widthPos = int(x) + int(width)
                heightPos = int(y) + int(height)
                if widthPos > largestWidth:
                    largestWidth = widthPos
                if heightPos > largestHeight:
                    largestHeight = heightPos
            except ArithmeticError:
                None
            except ValueError:
                None
                
            anchor = place.get('anchor')
            bordermode = place.get('bordermode')
            print(widgetId + ".place(" + "x=" + x + ",y=" + y + ",width=" + width + ",height=" + height + ",anchor='" + anchor + "',bordermode='" + bordermode + "')")
    # print("rootFrame.place(x=0, y=0, width=" + str(largestWidth) + " ,height=" + str(largestHeight) +")" )
    largestWidth += 20
    largestHeight += 20
    geom = str(largestWidth) + 'x' + str(largestHeight)
    print("rootWin.geometry('" + geom + "')")
    print("rootWin.resizable(True,True)")
    print("rootWin.columnconfigure(0,weight=1)")
    print("rootWin.rowconfigure(0,weight=1)")
    print("sg0 = ttk.Sizegrip(rootWin)")
    print("sg0.grid(row=1,sticky=tk.SE)")
    print("rootFrame.place(x=0, y=0, relwidth=1.0, relheight=1.0)")
    print("\nrootWin.mainloop()")

def buildAWidget(widgetId,wDict):
    wType = wDict.get('WidgetName')
    t = wType.replace('ttk::','ttk.')
    wType = t
    idx = wType.find('.')
    if idx == -1:  # Not ttk widgets
        t = 'tk.' + wType
        wType = t
    for ch in alphaList:
        t = wType.replace('.' + ch,'.' + ch.upper())
        wType = t
    keyCount = widgetId + "-KeyCount"
    nKeys = wDict.get(keyCount)
    place = wDict.get('Place')
    widgetDef= wType + "(mainCanvas"
    for a in range(nKeys):
        attribute = 'Attribute' + str(a)
        aDict = wDict.get(attribute)
        key = aDict.get('Key')
        val = aDict.get('Value')
        tmpWidgetDef = widgetDef + ', ' + key + '=\'' + val + '\' '
        widgetDef = tmpWidgetDef
    tmp = widgetDef + ')'
    widgetDef = tmp
    widget = eval(widgetDef)
    w = cw.createWidget(mainCanvas,widget)
    print(place)
    w.addPlace(place)

"""
label = ttk.Label(mainCanvas,text="Label",borderwidth=1,relief=tk.SOLID,anchor=tk.CENTER)
cw.createWidget(mainCanvas,label)
cw.createWidget(mainCanvas,wType)
"""


def loadProject():
    global alphaList
    f = open("/tmp/pytkguitest.pk1","rb")
    data = pickle.load(f)
    f.close()
    runDict = data
    print(runDict)
    nWidgits = runDict.get('widgetCount')
    for n in range(nWidgits):
        widgetId = "Widget" + str(n)
        wDict = runDict.get(widgetId)
        if wDict != {}:
            buildAWidget(widgetId,wDict)
            # Example .....
def exitApp():
    rootWin.destroy()


def buildMenu():
    global rootWin
    global newLabel
    global mainFrame
    global style
    menuBar = tk.Menu(rootWin)
    style = ttk.Style(rootWin)
    themes = style.theme_names()
    # print(themes[1])
    # themes
    rootWin.config(menu=menuBar)
    fileMenu = tk.Menu(menuBar,tearoff=0)
    # add menu items to the File menu
    fileMenu.add_command(label='New')
    fileMenu.add_command(label='Open',command=loadProject)
    fileMenu.add_command(label='Close')
    fileMenu.add_command(label='Save',command=saveMe)
    fileMenu.add_command(label='Run',command=runMe)
    fileMenu.add_separator()
    
    fileMenu.add_command(label='Exit',command=exitApp)
    
    # add a submenu
    subMenu = tk.Menu(fileMenu,tearoff=0)
    # subMenu.add_command(label='Keyboard Shortcuts')
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
    ttkWidgetMenu.add_command(label='Label',command=newLabel)
    ttkWidgetMenu.add_command(label='Notebook',command=newNotebook)
    ttkWidgetMenu.add_command(label='Treeview',command=newTreeview)
    ttkWidgetMenu.add_command(label='Entry',command=newEntry)
    ttkWidgetMenu.add_command(label='LabledScale',command=newLabScale)
    ttkWidgetMenu.add_command(label='Spinbox',command=newSpinbox)
    ttkWidgetMenu.add_command(label='Combobox',command=newCombobox)
    ttkWidgetMenu.add_command(label='Checkbutton',command=newCheckbutton)
    ttkWidgetMenu.add_command(label='Radiobutton',command=newRadiobutton)
    ttkWidgetMenu.add_command(label='Scale',command=newScale)
    ttkWidgetMenu.add_command(label='Progressbar',command=newProgressbar)
    ttkWidgetMenu.add_command(label='Seperator',command=newSeparator)
    menuBar.add_cascade(label="ttk Widgets",menu=ttkWidgetMenu,underline=0)
    themeMenu = tk.Menu(menuBar,tearoff=0)
    for t in themes:
        mypartial = partial(setTheme,t)
        themeMenu.add_command(label=t,command=mypartial)
    
    # create the Help menu
    helpMenu = tk.Menu(menuBar,tearoff=0)
    # helpMenu = ttk.OptionMenu(menuBar, tearoff=0)
    
    helpMenu.add_command(label='Welcome')
    helpMenu.add_command(label='About...')
    
    menuBar.add_cascade(label="Theme",menu=themeMenu,underline=0)
    # add the Help menu to the menuBar
    menuBar.add_cascade(label="Help",menu=helpMenu,underline=0)
    
    # add the File menu to the menuBar
    fileMenu.add_cascade(label="Preferences",menu=subMenu)


rectSizeX = 50
rectSizeY = 20
rect: Any
xstart = 0
ystart = 0


def leftLabelMotion(arg):
    global mainFrame
    global rect
    global moveL
    global xstart
    global ystart
    
    x_root = arg.x_root
    y_root = arg.y_root
    if xstart == 0:
        xstart = x_root
        ystart = y_root
    else:
        xpos = x_root - xstart
        ypos = y_root - ystart
        etype = 1  # arg.event
        moveL.place(x=xpos,y=ypos)
        # print( 'Motion --->' + str(etype) + ' ' + str(arg) + ' x_root ' + str(x_root) + ' y_root ' + str(y_root) + '<---')


def leftButtonMotion(arg):
    global mainFrame
    global rect
    global moveB
    global xstart
    global ystart
    
    x_root = arg.x_root
    y_root = arg.y_root
    if xstart == 0:
        xstart = x_root
        ystart = y_root
    else:
        xpos = x_root - xstart
        ypos = y_root - ystart
        etype = 1  # arg.event
        moveB.place(x=xpos,y=ypos)
        # print('Motion --->' + str(etype) + ' ' + str(arg) + ' x_root ' + str(x_root) + ' y_root ' + str(y_root) + '<---')


def leftMotion(arg):
    global rect
    global moveB
    x = arg.x
    y = arg.y


def leftClick(arg):
    global mainFrame
    global rect
    global moveB
    global xstart
    global ystart
    # Arg1 is an Event
    x = arg.x
    y = arg.y
    xstart = arg.x_root
    ystart = arg.y_root
    


def doNothing():
    var = None


def leftRelease(arg):
    global mainFrame
    global rect
    # Arg1 is an Event
    # print('Release--->' + str(arg) + '<---')
    # moveB.unbind("<B1-Motion>")


def frameMove(event):
    # print(event)
    # print(event.x)
    None


def drawGridLines():
    global mainCanvas
    # Get dimensions ....
    mainCanvas.update()
    width = mainCanvas.winfo_width()
    height = mainCanvas.winfo_height()
    print("width ",width," height ",height," snapTo ",pytkguivars.snapTo)
    for i in range(width):
        if i % pytkguivars.snapTo == 0:
            mainCanvas.create_line(0,i,height,i,fill="#f0d0d0")
    for i in range(height):
        if i % pytkguivars.snapTo == 0:
            mainCanvas.create_line(i,0,i,width,fill="#f0d0d0")


def sizeGripRelease(event):
    print(event)
    drawGridLines()


def buildGrid(rows,cols):
    global mainFrame
    global mainCanvas
    # mainCanvas = ttk.Frame(mainFrame, width=40, height=100, relief="ridge", borderwidth=2 )
    mainCanvas = tk.Canvas(mainFrame,width=40,height=100,relief=tk.SOLID,borderwidth=1,bg="#f0f0d0")
    mainCanvas.grid(row=0,column=0,columnspan=cols,rowspan=rows,padx=5,pady=5,sticky="NSEW")
    drawGridLines()
    """
    valuesR = range(rows)
    valuesC = range(cols)
    for r in valuesR:
        for c in valuesC:
            lab = "  "
            colour='#fafad0'
            if r == 0 :
                lab = str(c)
                colour = "#d9fafb"
            if c == 0:
                lab = str(r)
                colour = "#d9fafb"
            w = tk.Label(mainCanvas, text=lab, padx=0, pady=0, bg=colour, width=3, height=1, borderwidth=1,
                         relief=tk.SUNKEN)
            w.grid(row=r, column=c, sticky='WENS')
            cw.GridWidget(mainCanvas, w, r, c)
    
    """
    mainCanvas.bind('<Motion>',frameMove)


def buildIconbar():
    global mainFrame
    global iconBar
    iconBarRow = 0
    colSpan = 4
    iconBar = ttk.Frame(mainFrame,width=40,height=100,bg='lightblue')
    iconBar.grid(row=0,column=0,sticky='NE',padx=5,pady=5,columnspan=colSpan)
    b1 = ttk.Button(iconBar,bg='yellow1',text='Button',relief=tk.RAISED)
    b1.grid(row=iconBarRow,column=0,columnspan=4)
    b1.bind("<Button-1>",leftClick)
    b1.bind("<B1-Motion>",leftMotion)
    b1.bind("<ButtonRelease-1>",leftRelease)


def buildMainGui():
    global rootWin
    global mainFrame
    global style
    
    # sv_ttk.SunValleyTtkTheme.load_theme(rootWin)
    sv_ttk.use_light_theme()
    style = ttk.Style(rootWin)
    style.theme_use('scidblue')
    buildMenu()
    
    # mainFrame = ttk.Frame(rootWin, width=400, height=100, bg='lightblue')
    mainFrame = ttk.Frame(rootWin,width=600,height=150)
    mainFrame.grid(row=0,column=0,sticky='NWES')
    
    # mainFrame.pack()
    # mainFrame.rowconfigure(0, weight=1)
    # mainFrame.columnconfigure(16, weight=1)  # the lastcol goes along with rigth side expanding
    
    # mainFrame.geometry('600x600')
    # mainFrame.resizable(True, True)
    mainFrame.columnconfigure(0,weight=1)
    mainFrame.rowconfigure(0,weight=1)
    sg0 = ttk.Sizegrip(mainFrame)
    sg0.grid(row=1,sticky=tk.SE)
    sg0.bind("<ButtonRelease-1>",sizeGripRelease)
    
    rootWin.geometry('600x600')
    rootWin.resizable(True,True)
    rootWin.columnconfigure(0,weight=1)
    rootWin.rowconfigure(0,weight=1)
    # sg = ttk.Sizegrip(rootWin)
    # sg.grid(row=1,sticky=tk.SE)
    
    # buildIconbar()
    buildGrid(24,24)


if __name__ == '__main__':
    # global rootWin
    # global createWidget
    guivars.initVars()
    
    buildMainGui()
    rootWin.mainloop()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
