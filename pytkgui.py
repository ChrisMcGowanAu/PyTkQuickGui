import tkinter as tk
from tkinter import ttk

import createWidget as cw
import pytkguivars as guivars

import sv_ttk

# Global stuff
# rootWin = tk.Tk(screenName='pytkgui')

from functools import partial
from typing import Any

rootWin = tk.Tk()
mainFrame: ttk.Frame()
rootWin.title('Draft Builder')
iconBar: ttk.Frame()
mainGrid: ttk.Frame()
mainCanvas: tk.Canvas()
moveB: ttk.Button()
moveL: tk.Label()
style: Any


def newLabel():
    global moveL
    global mainCanvas
    global mainGrid
    global xstart
    global ystart
    # label: ttk.Label
    
    # label = ttk.Label(mainCanvas, text="Label", padx=5, pady=5, bg='lightblue')
    label = ttk.Label(mainGrid, text="Label")
    cw.createWidget(mainGrid, label)
    # value1 = label.cget("padx")
    # value2 = label.cget("height")
    width = label.winfo_width()
    height = label.winfo_height()
    print("width " + str(width) + " height " + str(height))


def newButton():
    global mainGrid
    b = tk.Button(mainGrid, text="Button")
    cw.createWidget(mainGrid, b)

def newButton0():
    global mainGrid
    b = tk.Button(mainGrid, text="Button")
    cw.createWidget(mainGrid, b)
    
def newLabel0():
    global mainGrid
    b = tk.Label(mainGrid,text="Label")
    cw.createWidget(mainGrid,b)
def newCanvas0():
    global mainGrid
    b = tk.Canvas(mainGrid)
    cw.createWidget(mainGrid,b)
def newEntry0():
    global mainGrid
    b = tk.Entry(mainGrid)
    cw.createWidget(mainGrid,b)

def newEntry():
    global mainGrid
    e = ttk.Entry(mainGrid, background='lightblue', width=12)
    cw.createWidget(mainGrid, e)


def newLabScale():
    global mainGrid
    e = ttk.LabeledScale(mainGrid)
    cw.createWidget(mainGrid, e)


def newSpinbox():
    global mainGrid
    e = ttk.Spinbox(mainGrid)
    # e = ttk.LabeledScale(mainGrid)
    cw.createWidget(mainGrid, e)


def newCombobox():
    global mainGrid
    w = ttk.Combobox(mainGrid)
    cw.createWidget(mainGrid, w)


def newCheckbutton():
    global mainGrid
    w = ttk.Checkbutton(mainGrid)
    cw.createWidget(mainGrid, w)


def newRadiobutton():
    global mainGrid
    w = ttk.Radiobutton(mainGrid)
    cw.createWidget(mainGrid, w)


def newTreeview():
    global mainGrid
    w = ttk.Treeview(mainGrid)
    cw.createWidget(mainGrid, w)


def newScale():
    global mainGrid
    w = ttk.Scale(mainGrid)
    cw.createWidget(mainGrid, w)


def newNotebook():
    global mainGrid
    w = ttk.Notebook(mainGrid)
    cw.createWidget(mainGrid, w)


def newProgressbar():
    global mainGrid
    w = ttk.Progressbar(mainGrid)
    cw.createWidget(mainGrid, w)


def newSeparator():
    global mainGrid
    w = ttk.Separator(mainGrid)
    cw.createWidget(mainGrid, w)


def newTtkButton():
    global mainCanvas
    global mainGrid
    global xstart
    global ystart
    
    style = ttk.Style()
    # style.theme_use('alt')
    style.configure('TButton', background='lightblue', foreground='black')
    # width = 20, borderwidth=1, focusthickness=3, focuscolor='none')
    # style.map('TButton', background=[('active','red')])
    b = ttk.Button(mainGrid, text="Button")
    cw.createWidget(mainGrid, b)


def setTheme(theme: object):
    global rootWin
    global style
    print(theme)
    # style = ttk.Style(rootWin)
    style.theme_use(theme)


def saveMe():
    for w in cw.createWidget.widgetList:
            print("=-----------")
            print('widgetName ' + w.widgetName)
            place = w.place_info()
            print('Place')
            for p in place:
                try:
                    print(str(p) + " " + str(w[p]))
                except:
                    None
            print(place)
            print('Keys')
            print(w.keys())
            keys = w.keys()
            if keys:
              # print(w.)
              for key in keys:
                print("Attribute: {:<20}".format(key),end=' ')
                value = w[key]
                vtype = type(value)
                print('Type: {:<30} Value: {}'.format(str(vtype),value))
            print("=-----------")
        # cw.createWidget.saveTest(w);
        # print(w)
    # cw.saveTest()

def exitApp():
    rootWin.destroy()
    qot
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
    fileMenu = tk.Menu(menuBar, tearoff=0)
    # add menu items to the File menu
    fileMenu.add_command(label='New')
    fileMenu.add_command(label='Open...')
    fileMenu.add_command(label='Close')
    fileMenu.add_command(label='Save', command=saveMe)
    fileMenu.add_separator()
    
    fileMenu.add_command(label='Exit', command=exitApp)
    
    # add a submenu
    subMenu = tk.Menu(fileMenu, tearoff=0)
    # subMenu.add_command(label='Keyboard Shortcuts')
    subMenu.add_command(label='Themes')
    subMenu.add_command(label='Color Themes')
    
    menuBar.add_cascade(label="File", menu=fileMenu, underline=0)
    # widget Menu
    widgetMenu = tk.Menu(menuBar, tearoff=1)
    widgetMenu.add_command(label='Button', command=newButton0)
    widgetMenu.add_command(label='Label', command=newLabel0)
    widgetMenu.add_command(label='Canvas', command=newCanvas0)
    widgetMenu.add_command(label='Entry', command=newEntry0)
    menuBar.add_cascade(label="tk Widgets", menu=widgetMenu, underline=0)
    ttkWidgetMenu = tk.Menu(menuBar, tearoff=1)
    # ttkWidgetMenu.add_command(label='tk Button', command=newButton)
    ttkWidgetMenu.add_command(label='Button', command=newTtkButton)
    ttkWidgetMenu.add_command(label='Label', command=newLabel)
    ttkWidgetMenu.add_command(label='Notebook', command=newNotebook)
    ttkWidgetMenu.add_command(label='Treeview', command=newTreeview)
    ttkWidgetMenu.add_command(label='Entry', command=newEntry)
    ttkWidgetMenu.add_command(label='LabledScale', command=newLabScale)
    ttkWidgetMenu.add_command(label='Spinbox', command=newSpinbox)
    ttkWidgetMenu.add_command(label='Combobox', command=newCombobox)
    ttkWidgetMenu.add_command(label='Checkbutton', command=newCheckbutton)
    ttkWidgetMenu.add_command(label='Radiobutton', command=newRadiobutton)
    ttkWidgetMenu.add_command(label='Scale', command=newScale)
    ttkWidgetMenu.add_command(label='Progressbar', command=newProgressbar)
    ttkWidgetMenu.add_command(label='Seperator', command=newSeparator)
    menuBar.add_cascade(label="ttk Widgets", menu=ttkWidgetMenu, underline=0)
    themeMenu = tk.Menu(menuBar, tearoff=0)
    for t in themes:
        mypartial = partial(setTheme, t)
        themeMenu.add_command(label=t, command=mypartial)
    
    # create the Help menu
    helpMenu = tk.Menu(menuBar, tearoff=0)
    # helpMenu = ttk.OptionMenu(menuBar, tearoff=0)
    
    helpMenu.add_command(label='Welcome')
    helpMenu.add_command(label='About...')
    
    menuBar.add_cascade(label="Theme", menu=themeMenu, underline=0)
    # add the Help menu to the menuBar
    menuBar.add_cascade(label="Help", menu=helpMenu, underline=0)
    
    # add the File menu to the menuBar
    fileMenu.add_cascade(label="Preferences", menu=subMenu)


rectSizeX = 50
rectSizeY = 20
rect: Any
xstart = 0
ystart = 0


def leftLabelMotion(arg):
    global mainCanvas
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
        # mainCanvas.
        moveL.place(x=xpos, y=ypos)
        # moveB.place(x=x, y=y)
        # moveB.place()
        print(
            'Motion --->' + str(etype) + ' ' + str(arg) + ' x_root ' + str(x_root) + ' y_root ' + str(y_root) + '<---')


def leftButtonMotion(arg):
    global mainCanvas
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
        # mainCanvas.
        moveB.place(x=xpos, y=ypos)
        # moveB.place(x=x, y=y)
        # moveB.place()
        print( 'Motion --->' + str(etype) + ' ' + str(arg) + ' x_root ' +
               str(x_root) + ' y_root ' + str(y_root) + '<---')


def leftMotion(arg):
    global mainCanvas
    global rect
    global moveB
    # print('Motion --->' + str(arg) + '<---')
    x = arg.x
    y = arg.y
    # mainCanvas.moveto(rect, x, y)
    # mainCanvas.moveto(moveB, x + 20, y + 20)


def leftClick(arg):
    global mainCanvas
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
    
    print('Left--->' + str(arg) + '<---')
    # rect = mainCanvas.create_rectangle(x, y, x + rectSizeX, y + rectSizeY, fill='red')
    moveB = ttk.Button(mainCanvas, text="Button")
    # moveB.cget("width",
    cw.createWidget(mainCanvas, moveB)


def doNothing():
    var = None


def leftRelease(arg):
    global mainCanvas
    global mainFrame
    global rect
    # Arg1 is an Event
    print('Release--->' + str(arg) + '<---')
    # moveB.unbind("<B1-Motion>")


def frameMove(event):
    print(event)
    print(event.x)


def buildGrid(rows, cols):
    global mainFrame
    global mainGrid
    mainGrid = ttk.Frame(mainFrame, width=40, height=100, relief="ridge", borderwidth=2 )
    mainGrid.grid(row=0, column=0, columnspan=cols, rowspan=rows, padx=5, pady=5)
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
            w = tk.Label(mainGrid, text=lab, padx=0, pady=0, bg=colour, width=3, height=1, borderwidth=1,
                         relief=tk.SUNKEN)
            w.grid(row=r, column=c, sticky='WENS')
            cw.GridWidget(mainGrid, w, r, c)
    
    mainGrid.bind('<Motion>', frameMove)


def buildCanvas():
    global mainFrame
    global iconBar
    global mainCanvas
    global rect
    mainCanvas = tk.Canvas(mainFrame, bg="white", height=300, width=300)
    # mainCanvas = ttk.Canvas(mainFrame, height=300, width=300)
    # mainCanvas.grid()
    mainCanvas.grid(row=0, column=5, sticky='NE', padx=5, pady=5, columnspan=12)
    # rect = mainCanvas.create_rectangle(x, y, x+width, y+height, fill='red')


def buildIconbar():
    global mainFrame
    global iconBar
    iconBarRow = 0
    colSpan = 4
    iconBar = ttk.Frame(mainFrame, width=40, height=100, bg='lightblue')
    iconBar.grid(row=0, column=0, sticky='NE', padx=5, pady=5, columnspan=colSpan)
    b1 = ttk.Button(iconBar, bg='yellow1', text='Button', relief=tk.RAISED)
    b1.grid(row=iconBarRow, column=0, columnspan=4)
    b1.bind("<Button-1>", leftClick)
    b1.bind("<B1-Motion>", leftMotion)
    b1.bind("<ButtonRelease-1>", leftRelease)


def buildMainGui():
    global rootWin
    global mainFrame
    global style
    
    sv_ttk.SunValleyTtkTheme.load_theme(rootWin)
    sv_ttk.use_light_theme()
    style = ttk.Style(rootWin)
    style.theme_use('sun-valley-light')
    buildMenu()
    
    # mainFrame = ttk.Frame(rootWin, width=400, height=100, bg='lightblue')
    mainFrame = ttk.Frame(rootWin, width=600, height=150)
    mainFrame.grid(row=0, column=0, sticky='NWES', padx=5, pady=5, columnspan=4)
    # mainFrame.pack()
    mainFrame.rowconfigure(0, weight=1)
    mainFrame.columnconfigure(16, weight=1)  # the lastcol goes along with rigth side expanding
    
    # buildIconbar()
    buildGrid(24, 24)
    # buildCanvas()


if __name__ == '__main__':
    # global rootWin
    # global createWidget
    guivars.initVars()
    
    buildMainGui()
    rootWin.mainloop()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
