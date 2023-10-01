import logging as log
import random
import tkinter as tk
from functools import partial
from tkinter import filedialog
from tkinter import ttk
from tkinter.colorchooser import askcolor
from typing import Any

import tkfontchooser
from PIL import ImageTk

import pytkguivars
import pytkguivars as guivars

testImage: ImageTk
string1: Any
string2: Any
string3: Any

pytkguivars.useGrider = False
pytkguivars.snapTo = 16
pytkguivars.imageIndex = 0

# This is my enum type for list indicies
NAME: int = 0
PARENT: int = 1
WIDGET: int = 2
CHILDREN: int = 3

class GridWidget:
    lastx = 0
    lasty = 0
    
    def __init__(self,root,widget,row,col):
        self.root = root
        self.widget = widget
        self.row = row
        self.col = col
        self.widget.grid(row=self.row,column=self.col,sticky='WENS')
    
    def mouseEnter(self,event):
        log.info("Row " + str(self.row) + " Col " + str(self.col))


def snapToClosest(v: int) -> int:
    newV = int(v)
    remV = int(v) % int(pytkguivars.snapTo)
    if remV < pytkguivars.snapTo / 2:
        newV -= remV
    else:
        newV += pytkguivars.snapTo - remV
    if newV < 0:
        newV = 0
    return newV


def findPythonWidgetNameList(name: str) -> list:
    found = False
    # [pythonName,parentName,widget,[children,...]])
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    for nl in createWidget.widgetNameList:
        # print('Name',name,'nl[0]',nl[NAME])
        if nl[NAME] == name:
            found = True
            return nl
    if not found:
        log.error("Unable to locate pythonName ->%s<-",name)
        for w in createWidget.widgetNameList:
            print(str(w))
        return []


def updateWidgetNameList(pythonName,w):
    # createWidget.widgetNameList.append([self.pythonName,'toolRoot',self.widget,[]])
    # [pythonName,parentName,widget,[children,...]])
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    nl = findPythonWidgetNameList(pythonName)
    if nl != []:
        # Replace the parent
        ParentName = ''
        found = False
        for nl2 in createWidget.widgetNameList:
            print(nl)
            if nl2[WIDGET] == w:
                ParentName = nl2[NAME]
                nl2[CHILDREN].append(pythonName)
                found = True
                break
        if not found:
            log.error("Unable to locate widget ->%s<-",str(w))
            print(createWidget.widgetNameList)
        nl[PARENT] = ParentName


def deleteWidgetFromLists(pythonName,widget):
    # [pythonName,parentName,widget,[children,...]])
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    commands = []
    nl = findPythonWidgetNameList(pythonName)
    children = nl[CHILDREN]
    if children:
        for child in children:
            log.warning("Deleting %s from %s children=%s",child,pythonName,children)
            childNl = findPythonWidgetNameList(child)
            if childNl:
                name = childNl[NAME]
                childWidget = childNl[WIDGET]
                commands.append([name,childWidget])
                # Dont call this here. The  deletes are saved for later
                # deleteWidgetFromLists(name,childWidget)
        for c in commands:
            deleteWidgetFromLists(c[0],c[1])
    
    parent = nl[PARENT]
    if parent != 'toolRoot':
        parentNl = findPythonWidgetNameList(parent)
        # Remove pythonName from the children
        parentNl[CHILDREN].remove(pythonName)
    log.warning("Deleting %s and %s",str(nl),str(widget))
    createWidget.widgetList.remove(widget)
    createWidget.widgetNameList.remove(nl)


def raiseChildren(pythonName):
    # [pythonName,parentName,widget,[children,...]])
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    nl = findPythonWidgetNameList(pythonName)
    if nl:
        children = nl[CHILDREN]
        if children:
            for child in children:
                childNl = findPythonWidgetNameList(child)
                if childNl:
                    childNl[WIDGET].lift()
                    childName = childNl[NAME]
                    raiseChildren(childName)
    else:
        log.warning("Failed to find %s",pythonName)


class createWidget:
    # This just a list of widgets in the order they are created
    widgetList = []
    # Widget Name list will have child lists in the form
    # This just a list of widgets in the order they are created
    # [widgetName, parentName , widget, childList]
    widgetNameList = []
    widgetId = 0
    dragType = ['move','dragEast','dragWest','dragNorth','dragSouth']
    
    def __init__(self,root,widget):
        self.parentX = 0
        self.parentY = 0
        self.popup = None
        self.cornerX = None
        self.cornerY = None
        # self.bordermode = None
        self.anchor = None
        self.height = None
        self.relwidth = None
        self.width = None
        self.relx = None
        self.rely = None
        self.keys = None
        self.labelKeys = None
        self.dragType = 'move'
        self.ipadx = 0
        self.ipady = 0
        self.padx = 0
        self.pady = 0
        self.vars = [Any] * 32
        self.sticky = " "
        self.colSpan = 2
        self.rowSpan = 1
        self.start = (0,0)
        self.gridPopupFrame = None
        self.editPopupFrame = None
        self.tkVar = "abcd"
        self.root = root
        self.widget: tk.Widget
        self.widget = widget
        w = tk.Widget.getint(self.widget,3)
        h = tk.Widget.getint(self.widget,5)
        # tk.wantobjects()
        log.info(self.widget.widgetName)
        #######################
        # Notebook is a funny case, just 'raw' it does not display
        if self.widget.widgetName == 'ttk::notebook':
            log.warning('Notebook is not yet done correctly')
        self.x = random.randint(50,50)
        self.y = random.randint(50,50)
        # log.info(random.randint(3, 9))
        self.row = 4
        self.col = 4
        self.x_root = self.x
        self.y_root = self.y
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
        
        log.info(self.widget.widgetName)
        self.pythonName = 'Widget' + str(createWidget.widgetId)
        log.info("Widget ID " + str(createWidget.widgetId))
        createWidget.widgetList.append(self.widget)
        createWidget.widgetNameList.append([self.pythonName,'toolRoot',self.widget,[]])
        self.widgetId = createWidget.widgetId
        createWidget.widgetId += 1
        #  K_UP, K_DOWN, K_LEFT, and K_RIGHT
        self.widget.bind('<Button-3>',self.rightMouseDown)
        self.widget.bind('<Button-1>',self.leftMouseDown)
        self.widget.bind('<B1-Motion>',self.leftMouseDrag)
        self.widget.bind("<ButtonRelease-1>",self.leftMouseRelease)
        if pytkguivars.useGrider:
            self.widget.grid(row=self.row,column=self.col)
        else:
            # self.widget.place(x=self.x,y=self.y,width=self.width,height=self.height)
            self.widget.place(x=self.x,y=self.y)
        
        self.widget.update()
        self.width = self.widget.winfo_width()
        self.height = self.widget.winfo_height()
        if pytkguivars.useGrider:
            log.warning("Gridder Used TBD")
        else:
            self.widget.place(x=self.x,y=self.y,width=self.width,height=self.height)

        log.info("Width %d Height %d",self.width,self.height)
        # log.info("Width",self.width,"Height",self.height)
    
    def addPlace(self,placeDict):
        log.info(placeDict)
        self.x = int(placeDict.get('x'))
        self.y = int(placeDict.get('y'))
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
        width = placeDict.get('width')
        height = placeDict.get('height')
        if width == '' or height == '':
            self.widget.place(x=self.x,y=self.y)
        else:
            self.width = int(width)
            self.height = int(height)
            self.widget.place(x=self.x,y=self.y,width=self.width,height=self.height)
    
    def keyPress(self,event):
        # self.widget.widgetName
        if event.keysym == 'Down':
            self.row += 1
        elif event.keysym == 'Up':
            self.row -= 1
        elif event.keysym == 'Left':
            self.col -= 1
        elif event.keysym == 'Right':
            self.col += 1
        if self.row < 1:
            self.row = 1
        if self.col < 1:
            self.col = 1
        self.widget.grid(row=self.row,column=self.col)
    
    def keyUp(self,event):
        self.row += 1
        if self.row < 1:
            self.row = 0
        if self.row > 23:
            self.row = 23
        self.widget.grid(row=self.row,column=self.col)
    
    def keyDown(self,event):
        self.row -= 1
        if self.row < 1:
            self.row = 0
        if self.row > 23:
            self.row = 23
        self.widget.grid(row=self.row,column=self.col)
    
    def fontChange(self,row):
        font = tkfontchooser.askfont(self.root)
        if font:
            # spaces in the family name need to be escaped
            font['family'] = font['family'].replace(' ','\ ')
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
            if font['underline']:
                font_str += ' underline'
                font_str += ' overstrike'
            log.info("Font=" + str(font_str) + " row=" + str(row))
            guivars.stringVars[row].set(font_str)
            #    self.widget.configure(font=font_str, text='Chosen font: ' + font_str.replace('\ ', ' '))
    
    @staticmethod
    def changeColour(row):
        colors = askcolor(title="Tkinter color chooser")
        if colors[1] is not None:
            guivars.stringVars[row].set(colors[1])
    
    def incColSpan(self):
        self.colSpan += 1
        log.info("incColSpan " + str(self.colSpan))
        self.widget.grid(row=self.row,column=self.col,columnspan=self.colSpan)
    
    def decColSpan(self):
        if self.colSpan > 1:
            self.colSpan -= 1
        log.info("decColSpan " + str(self.colSpan))
        self.widget.grid(row=self.row,column=self.col,columnspan=self.colSpan)
    
    def gridMe(self):
        self.widget.grid(row=self.row,column=self.col,ipadx=self.ipadx,ipady=self.ipady,padx=self.padx,pady=self.pady,
                         columnspan=self.colSpan,rowspan=self.rowSpan,sticky=self.sticky)
    
    def applyGridSettings(self):
        # Apply grid popup settings
        log.info("Apply grid settings")
        kids = self.gridPopupFrame.children
        # Children are ttk.Spinbox widgits with the name set as the grid name
        self.row = int(kids['row'].get())
        self.col = int(kids['column'].get())
        self.colSpan = int(kids['columnspan'].get())
        self.rowSpan = int(kids['rowspan'].get())
        self.ipadx = int(kids['ipadx'].get())
        self.ipady = int(kids['ipady'].get())
        self.padx = int(kids['padx'].get())
        self.pady = int(kids['pady'].get())
        self.sticky = kids['sticky'].get()
    
    def applyPlaceSettings(self):
        # Apply grid popup settings
        log.info("Apply place settings")
        kids = self.gridPopupFrame.children
        log.info(kids)
        # width = self.widget.winfo_width()
        # height = self.widget.winfo_height()
        self.x = int(kids['x'].get())
        self.y = int(kids['y'].get())
        self.width = int(kids['width'].get())
        self.height = int(kids['height'].get())
        self.anchor = kids['anchor'].get()
        self.bordermode = kids['bordermode'].get()
        self.widget.place(x=self.x,y=self.y,width=self.width,height=self.height,anchor=self.anchor,
                          bordermode=self.bordermode)
    
    def grid_popup(self):
        # colour='azure'
        popup = tk.Tk()
        x = popup.winfo_pointerx()
        y = popup.winfo_pointery()
        # popup.geometry('%dx%d+%d+%d' % (200, 200, x, y))
        popup.geometry(f'+{x:d}+{y:d}')
        popup.wm_title("Edit Widget Layout")
        colour = 'bisque'
        style = ttk.Style(popup)
        style.configure('TFrame',background=colour,foreground='black')
        style.configure('TLabel',background=colour,foreground='black')
        style.configure('TCombobox',background=colour,foreground='black')
        style.configure('TSpinbox',background=colour,foreground='black')
        # style.configure('TButton', background='lightgreen1', foreground='black')
        self.gridPopupFrame = ttk.Frame(popup,borderwidth=2,relief='sunken')
        gi = self.widget.grid_info()
        if gi == {}:
            return
        self.gridPopupFrame.grid(row=self.row,column=self.col + self.colSpan,rowspan=16,columnspan=4)
        spinVars = [Any] * 16
        lab0 = ttk.Label(self.gridPopupFrame,text="Grid layout settings for " + self.widget.widgetName)
        lab0.grid(row=0,column=0,columnspan=4,sticky=tk.NS)
        log.info(gi)
        row = 1
        stickyVals = [" ",tk.N,tk.S,tk.E,tk.W,tk.NS,tk.EW,tk.NSEW]
        for x in gi:
            if x != 'in':
                val = gi[x]
                spinVars[row] = val
                lab1 = ttk.Label(self.gridPopupFrame,text=x)
                w: Any
                if x == 'sticky':
                    w = ttk.Combobox(self.gridPopupFrame,values=stickyVals,width=6,name=x)
                    w.set(val)
                else:
                    self.vars[row] = val
                    w = ttk.Spinbox(self.gridPopupFrame,width=5,name=x,from_=0,to=99,increment=1)
                    w.set(int(val))
                log.info("self.vals " + str(row) + " " + str(val))
                lab1.grid(row=row,column=0,sticky=tk.NE)
                w.grid(row=row,column=3,sticky=tk.SW)
                row += 1
        b1 = ttk.Button(self.gridPopupFrame,width=8,text="Close",command=popup.destroy)
        b2 = ttk.Button(self.gridPopupFrame,width=8,text="Apply",command=self.applyGridSettings)
        b1.grid(row=row,column=0)
        row += 1
        # blank Label to make the layout better
        lab2 = ttk.Label(self.gridPopupFrame,text="   ")
        lab2.grid(row=row,column=2)
        b2.grid(row=row,column=3)
        row += 1
    
    def place_popup(self):
        # colour='azure'
        popup = tk.Tk()
        popup.update()
        x = popup.winfo_pointerx()
        y = popup.winfo_pointery()
        # popup.geometry('%dx%d+%d+%d' % (200, 200, x, y))
        popup.geometry('+%d+%d' % (x,y))
        popup.wm_title("Edit Widget Layout")
        colour = 'bisque'
        style = ttk.Style(popup)
        style.configure('TFrame',background=colour,foreground='black')
        style.configure('TLabel',background=colour,foreground='black')
        style.configure('TCombobox',background=colour,foreground='black')
        style.configure('TSpinbox',background=colour,foreground='black')
        # style.configure('TButton', background='lightgreen1', foreground='black')
        self.gridPopupFrame = ttk.Frame(popup,borderwidth=2,relief='sunken')
        # gi = self.widget.grid_info()
        gi = self.widget.place_info()
        if gi == {}:
            return
        self.gridPopupFrame.grid(row=self.row,column=self.col + self.colSpan,rowspan=16,columnspan=4)
        spinVars = [Any] * 16
        lab0 = ttk.Label(self.gridPopupFrame,text="Grid layout settings for " + self.widget.widgetName)
        lab0.grid(row=0,column=0,columnspan=4,sticky=tk.NS)
        log.info(gi)
        row = 1
        stickyVals = [" ",tk.N,tk.S,tk.E,tk.W,tk.NS,tk.EW,tk.NSEW]
        anchorVals = [tk.CENTER,tk.N,tk.NE,tk.E,tk.SE,tk.S,tk.SW,tk.W,tk.NW]
        borderVals = [tk.INSIDE,tk.OUTSIDE]
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        
        for x in gi:
            if x != 'in':
                val = gi[x]
                log.info(str(val))
                if val == '':
                    val = 0
                spinVars[row] = val
                lab1 = ttk.Label(self.gridPopupFrame,text=x)
                w: Any
                if x == 'sticky':
                    w = ttk.Combobox(self.gridPopupFrame,values=stickyVals,width=6,name=x)
                    w.set(val)
                elif x == "bordermode":
                    w = ttk.Combobox(self.gridPopupFrame,values=borderVals,width=6,name=x)
                    w.set(val)
                elif x == "anchor":
                    w = ttk.Combobox(self.gridPopupFrame,values=anchorVals,width=6,name=x)
                    w.set(val)
                elif x == 'height':
                    w = ttk.Spinbox(self.gridPopupFrame,width=5,name=x,from_=0,to=999,increment=1)
                    w.set(int(height))
                elif x == 'width':
                    w = ttk.Spinbox(self.gridPopupFrame,width=5,name=x,from_=0,to=999,increment=1)
                    w.set(int(width))
                else:
                    self.vars[row] = val
                    w = ttk.Spinbox(self.gridPopupFrame,width=5,name=x,from_=0,to=99,increment=1)
                    w.set(int(val))
                log.info("self.vals " + str(row) + " " + str(val))
                lab1.grid(row=row,column=0,sticky=tk.NE)
                w.grid(row=row,column=3,sticky=tk.SW)
                row += 1
        b1 = ttk.Button(self.gridPopupFrame,width=8,text="Close",command=popup.destroy)
        b2 = ttk.Button(self.gridPopupFrame,width=8,text="Apply",command=self.applyPlaceSettings)
        b1.grid(row=row,column=0)
        row += 1
        # blank Label to make the layout better
        lab2 = ttk.Label(self.gridPopupFrame,text="   ")
        lab2.grid(row=row,column=2)
        b2.grid(row=row,column=3)
    
    def selectImage(self,row):
        global testImage
        f_types = [ ('Png Files','*.png'), ('Jpg kFiles','*.jpg') ]
        filename = filedialog.askopenfilename(filetypes=f_types)
        idx = pytkguivars.imageIndex
        pytkguivars.imagesUsed[idx] = ImageTk.PhotoImage(file=filename)
        self.widget.configure(image=pytkguivars.imagesUsed[idx])
        pytkguivars.imageIndex += 1
    
    def defineStyle(self):
        log.info('defineStyle TBD')
        style = ttk.Style(self.root)
        log.info(style.element_names())
        log.info(style.theme_names())
        styleVals = style.element_names()  # log.info(styleVals)
    
    def applyEditSettings(self):
        # keys = self.widget.keys()
        keys = self.keys
        log.info("Apply edit settings")
        kids = self.widget.children
        log.info(kids)
        row = 0
        for key in keys:
            row += 1
            val = ''
            if type(key) is tuple:
                # childW = key[0]
                k = key[1]  # child_widget = getattr(self.widget,childW)
            else:
                k = key
                val = self.widget.cget(k)
            if k:
                if not pytkguivars.stringUsed[row]:
                    log.info("NOT USED Key " + k + " Value " + str(val))
                else:
                    strVar = pytkguivars.stringVars[row]
                    log.info("Row %d StringVar %s",row,str(strVar))
                    val = strVar.get()
                    log.info("Key " + k + " Value " + str(val))
                    # Yep this is weird python shit. configure would not use the tag name as a variable
                    # eg. self.widget.configure(k:val)
                    # so chat gpt-ity said to do this
                    child = guivars.childNameVars[row].get()
                    if child:
                        log.info("Configure tag=" + str(k) + " Child=" + str(child) + " Row=" + str(row) + " Value=" + str(
                            val))
                        # child_widget = getattr(self.widget,child)
                        # command_str = f"child_widget.configure({{k: {val}}})"
                        # log.info(command_str)
                        if child == 'label':
                            self.widget.label.configure(**{k:val})
                        elif child == 'scale':
                            self.widget.scale.configure(**{k:val})
                        else:
                            log.info(child + " child not handled")
                    else:
                        # command_str = f"self.widget.configure({{k: {val}}})"
                        # log.info(command_str)
                        log.info("Configure tag=" + str(k) + " Row=" + str(row) + " Value=" + str(val))
                        if (k == 'anchor' or k == 'justify') and len(val) < 1:
                            log.info("Ignored")
                        else:
                            # if val is not int:
                            #    val = 0
                            log.info("k %s val %s",str(k),str(val))
                            try:
                                self.widget.configure(**{k:val})
                            except Exception as e:
                                log.error(e)
                                log.warning("k %s val %s",str(k),str(val))
    
    def editTtkPopup(self,popup):
        global string1
        global string2
        row = 0
        gridRow = 0
        wname = self.widget.widgetName
        w = ttk.Label(popup,text=wname,borderwidth=1,relief=tk.SOLID,justify=tk.CENTER)
        # w = ttk.Label(popup,text=wname,borderwidth=1,justify=tk.CENTER)
        w.grid(row=gridRow,column=1,columnspan=4,sticky=tk.SW)
        gridRow += 1
        keys = self.widget.keys()
        if keys == {}:
            popup.destroy()
            return
        log.info(keys)
        anchorVals = [tk.CENTER,tk.N,tk.NE,tk.E,tk.SE,tk.S,tk.SW,tk.W,tk.NW]
        justifyVals = [tk.LEFT,tk.CENTER,tk.RIGHT]
        reliefVals = [tk.FLAT,tk.GROOVE,tk.RAISED,tk.RIDGE,tk.SOLID,tk.SUNKEN]
        compoundVals = [tk.NONE,tk.TOP,tk.BOTTOM,tk.LEFT,tk.RIGHT]
        orientVals = [tk.VERTICAL,tk.HORIZONTAL]
        self.keys = keys
        for key in self.keys:
            row += 1
            gridRow += 1
            k = key
            childW = ""
            if type(key) is tuple:
                childW = key[0]
                k = key[1]
                child_widget = getattr(self.widget,childW)
                val = child_widget.cget(k)
            else:
                val = self.widget.cget(k)
            
            l1 = ttk.Label(popup,text=k)
            # l1.grid(row=row,column=1,columnspan=5,sticky=tk.SW)
            guivars.stringVars[row] = tk.StringVar(popup)
            guivars.childNameVars[row] = tk.StringVar(popup)
            guivars.stringVars[row].set(val)
            guivars.childNameVars[row].set(childW)
            # These are ignored for now at least
            guivars.stringUsed[row] = True
            # These are ignored --- the no entry is added for these
            uniqueName = k + str(row)
            if k in ('class','cursor','show','default','takefocus','state'):
                guivars.stringUsed[row] = False
            ###############################
            # Special cases. Most will default to an entry widget
            ###############################
            elif k == 'font':
                # rowX = row
                w = ttk.Button(popup,name=uniqueName,text="Select a Font",command=lambda row=row:self.fontChange(row))
                w.grid(row=gridRow,column=3,columnspan=2,sticky=tk.SW)
            ###############################
            # spinbox integer tags
            ###############################
            elif k in ('height','columns','width','borderwidth','displaycolumns','padding'):
                w = ttk.Spinbox(popup,width=5,name=uniqueName,from_=0,to=99,increment=1,
                                textvariable=guivars.stringVars[row])
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            ###############################
            # Combobox fields
            ###############################
            elif k == 'anchor':
                w = ttk.Combobox(popup,values=anchorVals,width=6,name=uniqueName,textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            elif k == 'justify':
                w = ttk.Combobox(popup,values=justifyVals,width=6,name=uniqueName,textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            elif k == 'relief':
                w = ttk.Combobox(popup,values=reliefVals,width=6,name=uniqueName,textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            elif k == 'compound':
                w = ttk.Combobox(popup,values=compoundVals,width=6,name=uniqueName,textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            elif k == 'orient':
                w = ttk.Combobox(popup,values=orientVals,width=6,name=uniqueName,textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            ###############################
            # Style is tricky TBD
            ###############################
            elif k == 'style':
                w = ttk.Button(popup,name=uniqueName,text="Define/Select a Style",command=self.defineStyle)
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            ###############################
            # Image need work TBD
            ###############################
            elif k == 'image':
                # thisRow1 = row
                w = ttk.Button(popup,name=uniqueName,text="Select an image",
                               command=lambda row=row:self.selectImage(row))
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            ###############################
            # Colour selection possibly a canvas with the colour
            ###############################
            elif k == 'bg' or k == 'foreground' or k == 'background':
                w = ttk.Button(popup,name=uniqueName,text="Select a Color",
                               command=lambda row=row:self.changeColour(row))
                w.grid(row=gridRow,column=3,columnspan=2,sticky=tk.SW)
            ###############################
            # The Default --- use and entry widget for all other tags
            ###############################
            else:
                w = tk.Entry(popup,name=uniqueName,textvariable=guivars.stringVars[row])
                w.grid(row=gridRow,column=3,sticky=tk.SW)
            
            if guivars.stringUsed[row]:
                l1.grid(row=gridRow,column=0,columnspan=2,sticky=tk.E)
        
        # Some widgets have 'children'
        kids = self.widget.children
        if kids:
            for k in kids:
                widgetName = k.widgetName
                log.info(widgetName)
                l0 = ttk.Label(popup,text=widgetName,borderwidth=1,border=tk.SOLID,justify=tk.CENTER)
                l0.grid(row=gridRow,column=1,columnspan=5,sticky=tk.SW)
                row += 1
                gridRow += 1
                if widgetName == 'ttk::notebook':
                    log.info(widgetName)
                elif widgetName == 'ttk::labelframe':
                    keys1 = self.widget.label.keys()
                    for k1 in keys1:
                        keys.append(tuple(('label',k1)))
                    keys2 = self.widget.scale.keys()
                    for k2 in keys2:
                        keys.append(tuple(('scale',k2)))
                    log.info(keys)
                else:
                    log.info('unhandled child %s',widgetName)
        # self.labelKeys = ['text', 'background', 'foreground', 'font', 'width', 'anchor', 'textvariable']
        b1 = ttk.Button(popup,width=8,text="Close",command=popup.destroy)
        b2 = ttk.Button(popup,width=8,text="Apply",command=self.applyEditSettings)
        b1.grid(row=gridRow,column=0)
        b2.grid(row=gridRow,column=3)
        row += 1
        gridRow += 1
        # blank Label to make the layout better
        lab2 = ttk.Label(popup,text="   ")
        lab2.grid(row=gridRow,column=2)
        popup.mainloop()
    
    def editTtkButton(self,root):
        keys = self.widget.keys()
        if keys == {}:
            root.destroy()
            return
        log.info(keys)
    
    def editWidget(self,w):
        # Build the edit widget
        popup = tk.Tk()
        x = popup.winfo_pointerx()
        y = popup.winfo_pointery()
        popup.wm_title("Edit Widget")
        popup.geometry('+%d+%d' % (x,y))
        colour = 'lightgreen'
        style = ttk.Style(popup)
        style.configure('TFrame',background=colour,foreground='black')
        style.configure('TLabel',background=colour,foreground='black')
        style.configure('TCombobox',background=colour,foreground='black')
        style.configure('TSpinbox',background=colour,foreground='black')
        style.configure('TButton',background=colour,foreground='black')
        style.configure('TLabel',background=colour,foreground='black')
        self.editPopupFrame = ttk.Frame(popup,borderwidth=2,relief='sunken')
        self.editTtkPopup(popup)
    
    def findParentWidget(self):
        parent = self.widget.place_info().get('in')
        log.info('Parent %s self.root %s',str(parent),str(self.root))
        if self.root == parent:
            return parent
        else:
            for w in createWidget.widgetList:
                if w is not None and w != self.widget:
                    # wName = w.widgetName
                    if w == parent:
                        return w
        return self.root
    
    def reParent(self):
        name0 = self.widget.widgetName
        place = self.widget.place_info()
        # log.info(place)
        x1 = int(place.get('x'))
        y1 = int(place.get('y'))
        w = int(place.get('width'))
        h = int(place.get('height'))
        x2 = x1 + w
        y2 = y1 + h
        # log.info("Name",name0,"nw",x1,",",y1,"se",x2,",",y2)
        # log.info("This Name",name0,"x",place.get('x'),"y",place.get('y'),"width",place.get('width'),"height",
        #      place.get('height'))
        # log.info(self.widget.keys())
        for w in createWidget.widgetList:
            if w is not None and w != self.widget:
                name = w.widgetName
                place = w.place_info()
                # log.info(place)
                wx1 = int(place.get('x'))
                wy1 = int(place.get('y'))
                try:
                    width = int(place.get('width'))
                    height = int(place.get('height'))
                except ValueError as e:
                    log.error(e)
                    width = 10
                    height = 10
                wx2 = wx1 + width
                wy2 = wy1 + height
                # log.info("Name",name,"nw",wx1,",",wy1,"se",wx2,",",wy2)
                # log.info("Name",name,"x",place.get('x'),"y",place.get('y'),"width",place.get('width'),"height",
                #      place.get('height'))
                if x1 >= wx1 and y1 >= wy1 and x2 <= wx2 and y2 <= wy2:
                    log.info("Match Name %s fits inside %s",name0,name)
                    newX = x1 - wx1
                    newY = y1 - wy1
                    # self.widget.place('in=',w,'x=',newX,'y=',newY)
                    self.widget.place(in_=w,x=newX,y=newY)
                    # w.children.append(self.widget)
                    updateWidgetNameList(self.pythonName,w)
                    # createWidget.widgetNameList.append([self.pythonName,'toolRoot',self.widget,[]])
                    self.widget.parent = w
                    # It has to above the parent
                    tk.Misc.lift(self.widget,aboveThis=None)
                    # tk.Misc.lift(self.widget,aboveThis=w)
                    self.widget.update()
    
    def clone(self):
        mainCanvas = self.root
        widgetId = createWidget.widgetId
        newWidgetDict = pytkguivars.saveWidgetAsDict(widgetId,self.widget)
        widgetDef = pytkguivars.buildAWidget(widgetId,newWidgetDict)
        # widgetAltName = 'Widget' + str(widgetId)
        # widgetDict = newWidgetDict.get(widgetAltName)
        widget = eval(widgetDef)
        # place = widgetDict.get('Place')
        createWidget(mainCanvas,widget)
        widget.place(x=self.x + 16,y=self.y + 16,width=self.width,height=self.height)
    
    def deleteWidget(self):
        deleteWidgetFromLists(self.pythonName,self.widget)
        self.widget.destroy()
        
    def makePopup(self):
        # Add Menu
        self.popup = tk.Menu(self.root,tearoff=0)
        
        # Adding Menu Items
        mypartial = partial(self.editWidget,self.widget)
        self.popup.add_command(label="Edit",command=mypartial)
        # self.popup.add_command(label="Edit", command=self.editWidget)
        self.popup.add_command(label="Layout",command=self.place_popup)
        self.popup.add_command(label="Clone",command=self.clone)
        self.popup.add_command(label="Re-Parent",command=self.reParent)
        # self.popup.add_command(label="Col Span +",command=self.incColSpan)
        # self.popup.add_command(label="Col Span -",command=self.decColSpan)
        self.popup.add_command(label="Delete",command=self.deleteWidget)
        self.popup.add_command(label="Save",command=self.saveTestxxx)
        self.popup.add_separator()
        self.popup.add_command(label="Quit",command=self.popup.destroy)
    
    def menu_popup(self,event):
        # display the popup menu
        try:
            self.popup.tk_popup(event.x_root,event.y_root,0)
        finally:
            # Release the grab
            self.popup.grab_release()
            # self.widget.unbind("<Button-3>")
            self.popup.bind("<Button-3>",
                            self.menu_popup)  # button = ttk.Button(self.popup, text="Quit", command=self.popup.destroy)  # button.pack()
    
    def rightMouseDown(self,event):
        # popup a menu for the type of object
        log.info(self.widget.widgetName)
        # log.info(event)
        # log.info(createWidget.widgetList[self.widgetId].widgetName)
        # self.widget.destroy()
        self.makePopup()
        self.menu_popup(event)
    
    def leftMouseDown(self,event):
        self.start = (event.x,event.y)
        self.dragType = ''
        parent = self.findParentWidget()
        if parent != self.root:
            # log.info(parent,self.root)
            px = parent.place_info().get('x')
            py = parent.place_info().get('y')
            # log.info(px,py)
            # log.info("Before",self.start)
            self.parentX = int(px)
            self.parentY = int(py)
            self.start = (event.x + int(px),event.y + int(py))  # log.info("After",self.start)
        
        x = self.widget.winfo_x() + event.x - self.start[0]
        y = self.widget.winfo_y() + event.y - self.start[1]
        self.x = x
        self.y = y
        
        # Is the stuff above all crap?
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        self.x = self.widget.winfo_x()
        self.y = self.widget.winfo_y()
        self.cornerY = self.y + height
        self.cornerX = self.x + width
        log.info("Left Mouse Down --  Width " + str(width) + " Height " + str(height))
        if event.x > (width - 4):
            self.dragType = 'dragEast'
            log.info("Drag right Side")
        elif event.x < 4:
            self.dragType = 'dragWest'
            log.info("Drag left Side")
        if event.y > (height - 4):
            self.dragType = 'dragSouth'
            log.info("Drag bottom Side")
        elif event.y < 5:
            self.dragType = 'dragNorth'
            log.info("Drag top Side")  # log.info(event)
        # Make sure any children are on top.
        self.widget.lift()
        raiseChildren(self.pythonName)
    
    def leftMouseDrag(self,event):
        # log.info(event)
        x = self.widget.winfo_x() + event.x - self.start[0]
        y = self.widget.winfo_y() + event.y - self.start[1]
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        """
        try:
            tk.Misc.lift(self.widget,aboveThis=None)
        except Exception as e:
            log.error("Lift exception ",e)
        """
        
        if self.dragType == 'dragEast':
            width = event.x + self.parentX
        elif self.dragType == 'dragSouth':
            height = event.y + self.parentY
        elif self.dragType == 'dragWest':
            self.x = x
            width = self.cornerX - self.x
        elif self.dragType == 'dragNorth':
            self.y = y
            height = self.cornerY - self.y
        else:
            self.x = x
            self.y = y
        self.widget.place(x=self.x,y=self.y,width=width,height=height)
    
    def leftMouseRelease(self,event):
        self.dragType = ''
        newX = snapToClosest(self.x)
        newY = snapToClosest(self.y)
        self.x = newX
        self.y = newY
        if pytkguivars.useGrider:
            z = self.root.grid_location(self.x,self.y)
            self.row = z[1]
            self.col = z[0]
            self.widget.grid(row=self.row,column=self.col)
            log.info("Left Mouse Release -- col,row " + str(z))
        else:
            self.widget.place(x=self.x,y=self.y)
    
    def saveTestxxx(self):
        # return None
        for w in createWidget.widgetList:
            if w is not None:
                place = w.place_info()
                log.info(place)
                grid = w.grid_info()
                log.info(grid)
                keys = w.keys()
                log.info(keys)
                tags = w.bindtags()
                log.info(tags)
                t = w.winfo_class()
                log.info(t)
                # w.__getattribute__(string1)
                for k in keys:
                    log.info(k)
                    try:
                        val = k.cget()
                        if val is not None:
                            log.info(k,": ",str(val))
                    except Exception as e:
                        log.error(k," exception ",e)
                    """
                    val = w.cget()
                    if val == None:
                        pass
                    else:
                        try:
                            log.info(k + " " + val)
                        finally:
                            log.info("Unable to print val")
                    """
