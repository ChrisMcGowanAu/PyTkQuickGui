import logging as log
import random
import tkinter as tk
from typing import Any

import ttkbootstrap as ttk
from ttkbootstrap.dialogs.dialogs import FontDialog

import editWidget as ew
import pytkguivars
import pytkguivars as guivars

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

stickyVals = [" ",tk.N,tk.S,tk.E,tk.W,tk.NS,tk.EW,tk.NSEW]
borderVals = [tk.INSIDE,tk.OUTSIDE]
anchorVals = [tk.CENTER,tk.N,tk.NE,tk.E,tk.SE,tk.S,tk.SW,tk.W,tk.NW]
justifyVals = [tk.LEFT,tk.CENTER,tk.RIGHT]
reliefVals = [tk.FLAT,tk.GROOVE,tk.RAISED,tk.RIDGE,tk.SOLID,tk.SUNKEN]
compoundVals = [tk.NONE,tk.TOP,tk.BOTTOM,tk.LEFT,tk.RIGHT]
orientVals = [tk.VERTICAL,tk.HORIZONTAL]
"""
"""


def leftMouseRelease(widget,event):
    log.info("leftMouseRelease event %s",str(event))


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
        log.debug("Row " + str(self.row) + " Col " + str(self.col) + str(event))


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
        log.error('Unable to locate pythonName ->%s<-',name)
        log.error('createWidget.widgetNameList %s',str(createWidget.widgetNameList))
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
            # print(nl)
            if nl2[WIDGET] == w:
                ParentName = nl2[NAME]
                # Check if the child is already there
                if pythonName not in nl2[CHILDREN]:
                    nl2[CHILDREN].append(pythonName)
                found = True
                break
        if not found:
            log.error("Unable to locate widget ->%s<-",str(w))
            log.error('createWidget.widgetNameList %s',str(createWidget.widgetNameList))
        else:
            nl[PARENT] = ParentName


def deleteWidgetFromLists(pythonName,widget):
    # NAME: int = 0 PARENT: int = 1 WIDGET: int = 2 CHILDREN: int = 3
    commands = []
    nl = findPythonWidgetNameList(pythonName)
    children = nl[CHILDREN]
    if children:
        for child in children:
            log.info("Deleting %s from %s children=%s",child,pythonName,children)
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
    if parent != pytkguivars.rootWidgetName:
        parentNl = findPythonWidgetNameList(parent)
        # Remove pythonName from the children
        parentNl[CHILDREN].remove(pythonName)
    log.info("Deleting %s and %s",str(nl),str(widget))
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
                    w = childNl[WIDGET]
                    try:
                        w.lift()
                    except AttributeError as e:
                        log.error("Widget ->%s<- got Exception %s",w,str(e))
                    
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
    lastCreated = None
    dragType = ['move','dragEast','dragWest','dragNorth','dragSouth']
    
    def __init__(self,root,widget):
        self.bordermode = None
        self.stylePopupFrame = None
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
        # self.gridPopupFrame = None
        # self.editPopupFrame = None
        self.tkVar = "abcd"
        self.root = root
        self.widget: tk.Widget
        self.widget = widget
        # w = tk.Widget.getint(self.widget,3)
        # h = tk.Widget.getint(self.widget,5)
        # tk.wantobjects()
        log.debug(self.widget.widgetName)
        #######################
        # Notebook is a funny case, just 'raw' it does not display
        if self.widget.widgetName == 'ttk::notebook':
            log.warning('Notebook is not yet done correctly')
        self.x = random.randint(50,50)
        self.y = random.randint(50,50)
        # log.debug(random.randint(3, 9))
        self.row = 4
        self.col = 4
        self.x_root = self.x
        self.y_root = self.y
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
        
        log.debug(self.widget.widgetName)
        self.pythonName = 'Widget' + str(createWidget.widgetId)
        log.debug("Widget ID " + str(createWidget.widgetId))
        createWidget.widgetList.append(self.widget)
        createWidget.widgetNameList.append([self.pythonName,pytkguivars.rootWidgetName,self.widget,[]])
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
            self.widget.place(x=self.x,y=self.y)
        
        self.widget.update()
        self.width = self.widget.winfo_width()
        self.height = self.widget.winfo_height()
        if pytkguivars.useGrider:
            log.warning("Gridder Used TBD")
        else:
            # The second place is needed after the 'update()'
            self.widget.place(x=self.x,y=self.y,width=self.width,height=self.height)
        log.debug("New %s WidgetId %d Width %d Height %d",self.widget.widgetName,self.widgetId,self.width,self.height)
        createWidget.lastCreated = self
    
    def addPlace(self,placeDict):
        log.debug(placeDict)
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
    
    def fontChange(self,row):
        fd = FontDialog()
        fd.show()
        font = fd.result
        # font = tkfontchooser.askfont(self.root)
        guivars.stringVars[row].set(font)
    
    
    def incColSpan(self):
        self.colSpan += 1
        log.debug("incColSpan " + str(self.colSpan))
        self.widget.grid(row=self.row,column=self.col,columnspan=self.colSpan)
    
    def decColSpan(self):
        if self.colSpan > 1:
            self.colSpan -= 1
        log.debug("decColSpan " + str(self.colSpan))
        self.widget.grid(row=self.row,column=self.col,columnspan=self.colSpan)
    
    def gridMe(self):
        self.widget.grid(row=self.row,column=self.col,ipadx=self.ipadx,ipady=self.ipady,
                         padx=self.padx,pady=self.pady,columnspan=self.colSpan,
                         rowspan=self.rowSpan,sticky=self.sticky)
    
    def applyGridSettings(self):
        # Apply grid popup settings
        log.debug("Apply grid settings")
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
    
    def applyPlaceSettings(self,gridPopupFrame):
        # Apply grid popup settings
        log.debug("Apply place settings")
        kids = gridPopupFrame.children
        log.debug(kids)
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
        self.popup.update()
    
    def place_popup(self):
        # colour='azure'
        gi = self.widget.place_info()
        if gi == {}:
            return
        # popup = tk.Tk()
        popup = ttk.Window(themename="darkly")
        popup.title("Place Widget")
        # popup.update()
        x = popup.winfo_pointerx()
        y = popup.winfo_pointery()
        # popup.geometry('%dx%d+%d+%d' % (200, 200, x, y))
        popup.geometry(f'+{x:d}+{y:d}')
        popup.title("Edit Widget Layout")
        gridPopupFrame = ttk.Frame(popup,borderwidth=2,relief='sunken')
        # gi = self.widget.grid_info()
        gridPopupFrame.grid(row=self.row,column=self.col + self.colSpan,rowspan=16,columnspan=4)
        spinVars = [Any] * 16
        lab0 = ttk.Label(gridPopupFrame,text="Place settings for " + self.widget.widgetName)
        lab0.grid(row=0,column=0,columnspan=4,sticky=tk.NS)
        log.debug(gi)
        row = 1
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        
        for x in gi:
            ignoreThese = ['in','relx','rely','relwidth','relheight']
            if x not in ignoreThese:
                val = gi[x]
                log.debug(str(val))
                if val == '':
                    val = 0
                spinVars[row] = val
                lab1 = ttk.Label(gridPopupFrame,text=x)
                w: Any
                if x == 'sticky':
                    w = ttk.Combobox(gridPopupFrame,values=stickyVals,width=6,name=x)
                    w.set(val)
                elif x == "bordermode":
                    w = ttk.Combobox(gridPopupFrame,values=borderVals,width=6,name=x)
                    w.set(val)
                elif x == "anchor":
                    w = ttk.Combobox(gridPopupFrame,values=anchorVals,width=6,name=x)
                    w.set(val)
                elif x == 'height':
                    w = ttk.Spinbox(gridPopupFrame,width=5,name=x,from_=0,to=999,increment=1)
                    w.set(int(height))
                elif x == 'width':
                    w = ttk.Spinbox(gridPopupFrame,width=5,name=x,from_=0,to=999,increment=1)
                    w.set(int(width))
                else:
                    self.vars[row] = val
                    w = ttk.Spinbox(gridPopupFrame,width=5,name=x,from_=0,to=99,increment=1)
                    w.set(int(val))
                log.debug("self.vals " + str(row) + " " + str(val))
                lab1.grid(row=row,column=0,sticky=tk.NE)
                w.grid(row=row,column=3,sticky=tk.SW)
                row += 1
        b1 = ttk.Button(gridPopupFrame,width=8,text="Close",command=popup.destroy)
        b2 = ttk.Button(gridPopupFrame,width=8,text="Apply",command=lambda:self.applyPlaceSettings(gridPopupFrame))
        lab2 = ttk.Label(gridPopupFrame,text="   ")
        # row += 1
        # blank Label to make the layout better
        b1.grid(row=row,column=0)
        lab2.grid(row=row,column=2)
        b2.grid(row=row,column=3)
        popup.update()
    
    def applyEditSettings(self):
        # keys = self.widget.keys()
        keys = self.keys
        log.debug("Apply edit settings")
        kids = self.widget.children
        log.debug(kids)
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
                    log.debug("NOT USED Key " + k + " Value " + str(val))
                else:
                    strVar = pytkguivars.stringVars[row]
                    log.debug("Row %d StringVar %s",row,str(strVar))
                    val = strVar.get()
                    log.debug("Key " + k + " Value " + str(val))
                    # Yep this is weird python shit. configure would not use the tag name as a variable
                    # eg. self.widget.configure(k:val)
                    # so chat gpt-ity said to do this
                    child = guivars.childNameVars[row].get()
                    if child:
                        log.debug(
                            "Configure tag=" + str(k) + " Child=" + str(child) + " Row=" +
                            str(row) + " Value=" + str(val))
                        # child_widget = getattr(self.widget,child)
                        # command_str = f"child_widget.configure({{k: {val}}})"
                        # log.debug(command_str)
                        if child == 'label':
                            self.widget.label.configure(**{k:val})
                        elif child == 'scale':
                            self.widget.scale.configure(**{k:val})
                        else:
                            log.debug(child + " child not handled")
                    else:
                        # command_str = f"self.widget.configure({{k: {val}}})"
                        # log.debug(command_str)
                        logString = 'k %s val %s'
                        log.debug("Configure tag=" + str(k) + " Row=" + str(row) + " Value=" + str(val))
                        if (k == 'anchor' or k == 'justify') and len(val) < 1:
                            log.debug("Ignored")
                        elif k == 'values':
                            log.debug(logString,str(k),str(val))
                            # self.widget.configure(values=list(val.strip()))
                            # configure does not work for lists. change directly ...
                            # It needs a string list like this .
                            # self.widget['values'] = "1 2 3 4 5"
                            newVal = val.replace('(','')
                            val = newVal
                            newVal = val.replace(')','')
                            val = newVal
                            newVal = val.replace(',',' ')
                            val = newVal
                            newVal = val.replace('\'','')
                            val = newVal
                            log.debug(logString,str(k),val)
                            self.widget['values'] = val
                        
                        elif k == 'style':
                            log.debug(logString,str(k),str(val))
                            self.widget.configure(bootstyle=val)
                        else:
                            log.debug(logString,str(k),str(val))
                            try:
                                self.widget.configure(**{k:val})
                            except Exception as e:
                                log.error(e)
                                log.warning("k %s val %s",str(k),str(val))
    
    def editPlacePopup(self):
        popup = ew.widgetEditPopup(self.root,self.widget)
        popup.createLayoutPopup()

    def editTtkPopup(self):
        popup = ew.widgetEditPopup(self.root,self.widget)
        popup.createEditPopup()
    
    def findParentWidget(self):
        parent = self.widget.place_info().get('in')
        log.debug('Parent %s self.root %s',str(parent),str(self.root))
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
        # log.debug(place)
        x1 = int(place.get('x'))
        y1 = int(place.get('y'))
        w = int(place.get('width'))
        h = int(place.get('height'))
        x2 = x1 + w
        y2 = y1 + h
        for w in createWidget.widgetList:
            if w is not None and w != self.widget:
                name = w.widgetName
                place = w.place_info()
                # log.debug(place)
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
                if x1 >= wx1 and y1 >= wy1 and x2 <= wx2 and y2 <= wy2:
                    log.debug("Match Name %s fits inside %s",name0,name)
                    newX = x1 - wx1
                    newY = y1 - wy1
                    self.changeParentTo(w)
                    self.widget.place(x=newX,y=newY)
    
    def changeParentTo(self,newParentWidget):
        self.widget.place(in_=newParentWidget)
        updateWidgetNameList(self.pythonName,newParentWidget)
        self.widget.parent = newParentWidget
        tk.Misc.lift(self.widget,aboveThis=None)
        self.widget.update()
    
    def clone(self):
        mainCanvas = self.root
        # widgetId = createWidget.widgetId
        originalName = 'Widget' + str(self.widgetId)
        origWidgetDict = pytkguivars.saveWidgetAsDict(originalName)
        print('origWidgetDict:',origWidgetDict)
        useDict = origWidgetDict.get(originalName)
        print('useDict',useDict)
        widgetDef = pytkguivars.buildAWidget(self.widgetId,useDict)
        print(widgetDef)
        widget = eval(widgetDef)
        place = useDict.get('Place')
        widgetParent = useDict.get('WidgetParent')
        width = place.get('width')
        height = place.get('height')
        createWidget(mainCanvas,widget)
        newW = createWidget.lastCreated
        if pytkguivars.rootWidgetName != widgetParent:
            nameDetails = findPythonWidgetNameList(widgetParent)
            print('widgetParent:',widgetParent)
            print('nameDetails:',nameDetails)
            try:
                w = nameDetails[WIDGET]
                newW.changeParentTo(w)
            except Exception as e:
                log.error("Exception %s",str(e))
        newW.widget.place(x=self.x + 16,y=self.y + 16,width=width,height=height)
    
    def deleteWidget(self):
        deleteWidgetFromLists(self.pythonName,self.widget)
        self.widget.destroy()
    
    def makePopup(self):
        # Add Menu
        self.popup = ttk.Menu(self.root,tearoff=0)
        
        # Adding Menu Items
        self.popup.add_command(label="Edit",command=self.editTtkPopup)
        self.popup.add_command(label="Layout",command=self.editPlacePopup)
        self.popup.add_command(label="Clone",command=self.clone)
        self.popup.add_command(label="Re-Parent",command=self.reParent)
        self.popup.add_command(label="Delete",command=self.deleteWidget)
        self.popup.add_separator()
        self.popup.add_command(label="Close",command=self.popup.destroy)
    
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
        log.debug(self.widget.widgetName)
        # log.debug(event)
        # log.debug(createWidget.widgetList[self.widgetId].widgetName)
        # self.widget.destroy()
        self.makePopup()
        self.menu_popup(event)
    
    def leftMouseDown(self,event):
        self.start = (event.x,event.y)
        self.dragType = ''
        parent = self.findParentWidget()
        if parent != self.root:
            # log.debug(parent,self.root)
            px = parent.place_info().get('x')
            py = parent.place_info().get('y')
            # log.debug(px,py)
            # log.debug("Before",self.start)
            self.parentX = int(px)
            self.parentY = int(py)
            self.start = (event.x + int(px),event.y + int(py))  # log.debug("After",self.start)
        
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
        log.debug("Left Mouse Down --  Width " + str(width) + " Height " + str(height))
        if event.x > (width - 4):
            self.dragType = 'dragEast'
            log.debug("Drag right Side")
        elif event.x < 4:
            self.dragType = 'dragWest'
            log.debug("Drag left Side")
        if event.y > (height - 4):
            self.dragType = 'dragSouth'
            log.debug("Drag bottom Side")
        elif event.y < 5:
            self.dragType = 'dragNorth'
            log.debug("Drag top Side")  # log.info(event)
        # Make sure any children are on top.
        try:
            self.widget.lift()
        except tk.TclError as e:
            log.warning("self.widget.lift Failed with exception %s",str(e))
        raiseChildren(self.pythonName)
    
    def leftMouseDrag(self,event):
        # log.debug(event)
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
        newWidth = snapToClosest(self.widget.winfo_width())
        newHeight = snapToClosest(self.widget.winfo_height())
        self.x = newX
        self.y = newY
        if newWidth < 16:
            newWidth = 16
        if newHeight < 16:
            newHeight = 16
        self.height = newHeight
        self.width = newWidth
        if pytkguivars.useGrider:
            z = self.root.grid_location(self.x,self.y)
            self.row = z[1]
            self.col = z[0]
            self.widget.grid(row=self.row,column=self.col)
            log.debug("Left Mouse Release -- col,row %s %s",str(z),str(event))
        else:
            self.widget.place(x=self.x,y=self.y,height=self.height,width=self.width)
