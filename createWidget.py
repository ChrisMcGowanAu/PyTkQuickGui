import random
import typing
from functools import partial
from typing import Any
import tkinter as tk
from PIL import ImageTk
from tkinter import ttk
from tkinter import filedialog

import pytkguivars
import pytkguivars as guivars

from tkinter.colorchooser import askcolor
import tkfontchooser

testImage: ImageTk

string1: Any
string2: Any
string3: Any

pytkguivars.useGrider = False
pytkguivars.snapTo = 16
pytkguivars.imageIndex = 0


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
        print("Row " + str(self.row) + " Col " + str(self.col))


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


class createWidget:
    widgetList = [None] * 64
    widgetId = 0
    dragType = ['move','dragEast','dragWest','dragNorth','dragSouth']
    
    def __init__(self,root,widget):
        self.popup = None
        self.cornerX = None
        self.cornerY = None
        self.bordermode = None
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
        # self.tkVar = tk.StringVar()
        self.tkVar = "abcd"
        self.root = root
        self.widget: tk.Widget
        self.widget = widget
        w = tk.Widget.getint(self.widget,3)
        h = tk.Widget.getint(self.widget,5)
        # tk.wantobjects()
        print(self.widget.widgetName)
        #######################
        # Notebook is a funny case, just 'raw' it does not display
        if self.widget.widgetName == 'ttk::notebook':
            print('Notebook')
            # Frame 1 and 2
            frame1 = ttk.Frame(self.widget)
            frame2 = ttk.Frame(self.widget)
            label1 = ttk.Label(frame1,text="This is Window One")
            label1.pack(pady=50,padx=20)
            label2 = ttk.Label(frame2,text="This is Window Two")
            label2.pack(pady=50,padx=20)
            frame1.pack(fill=tk.BOTH,expand=True)
            frame2.pack(fill=tk.BOTH,expand=True)
            self.widget.add(frame1,text="Window 1")
            self.widget.add(frame2,text="Window 2")
        # self.widget.place(x=50, y=50)
        self.x = random.randint(50,300)
        self.y = random.randint(50,300)
        # print(random.randint(3, 9))
        self.row = 4
        self.col = 4
        self.x_root = self.x
        self.y_root = self.y
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
        
        print(self.widget.widgetName)
        print("Widget ID " + str(createWidget.widgetId))
        createWidget.widgetList[createWidget.widgetId] = widget
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
    def addPlace(self,placeDict):
        print(placeDict)
        self.x = int(placeDict.get('x'))
        self.y = int(placeDict.get('y'))
        self.width = int(placeDict.get('width'))
        self.height = int(placeDict.get('height'))
        self.start_x = self.x  # Set start_x on mouse down
        self.start_y = self.y  # Set start_y on mouse down
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
    
    def saveTestxxxxx(self):
        for w in self.widgetList:
            # lprint(w.cget(''))
            print("=-----------")
            keys = w.keys()
            for key in keys:
                print("Attribute: {:<20}".format(key),end=' ')
                value = w[key]
                vtype = type(value)
                print('Type: {:<30} Value: {}'.format(str(vtype),value))
            print("=-----------")
    
    def fontChange(self,row):
        font = tkfontchooser.askfont(self.root)
        font_str = ""
        if font:
            # spaces in the family name need to be escaped
            font['family'] = font['family'].replace(' ','\ ')
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
            if font['underline']:
                font_str += ' underline'
                font_str += ' overstrike'
            print("Font=" + str(font_str) + " row=" + str(row))
            guivars.stringVars[row].set(font_str)
        #    self.widget.configure(font=font_str, text='Chosen font: ' + font_str.replace('\ ', ' '))
    
    def changeColour(self,row):
        colors = askcolor(title="Tkinter color chooser")
        guivars.stringVars[row].set(colors[1])
        """
        if key == 'background':
            self.widget.configure(background=colors[1])
        else:
            self.widget.configure(foreground=colors[1])
        print(key)
        """
        # print(colors[1])
    
    def incColSpan(self):
        self.colSpan += 1
        print("incColSpan " + str(self.colSpan))
        self.widget.grid(row=self.row,column=self.col,columnspan=self.colSpan)
    
    def decColSpan(self):
        if self.colSpan > 1:
            self.colSpan -= 1
        print("decColSpan " + str(self.colSpan))
        self.widget.grid(row=self.row,column=self.col,columnspan=self.colSpan)
    
    def gridMe(self):
        self.widget.grid(row=self.row,column=self.col,
                         ipadx=self.ipadx,ipady=self.ipady,padx=self.padx,pady=self.pady,
                         columnspan=self.colSpan,rowspan=self.rowSpan,sticky=self.sticky)
    
    def applyGridSettings(self):
        # Apply grid popup settings
        print("Apply grid settings")
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
        print("Apply place settings")
        kids = self.gridPopupFrame.children
        print(kids)
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        self.x = int(kids['x'].get())
        self.y = int(kids['y'].get())
        self.width = int(kids['width'].get())
        self.height = int(kids['height'].get())
        self.anchor = kids['anchor'].get()
        self.bordermode = kids['bordermode'].get()
        self.widget.place(x=self.x,y=self.y,width=self.width,height=self.height,
                          anchor=self.anchor,bordermode=self.bordermode)
    
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
        print(gi)
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
                print("self.vals " + str(row) + " " + str(val))
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
        print(gi)
        row = 1
        stickyVals = [" ",tk.N,tk.S,tk.E,tk.W,tk.NS,tk.EW,tk.NSEW]
        anchorVals = [tk.CENTER,tk.N,tk.NE,tk.E,tk.SE,tk.S,tk.SW,tk.W,tk.NW]
        borderVals = [tk.INSIDE,tk.OUTSIDE]
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        
        for x in gi:
            if x != 'in':
                val = gi[x]
                print(str(val))
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
                print("self.vals " + str(row) + " " + str(val))
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
        print('selectImage TBD')
        f_types = [('Jpg kFiles','*.jpg'),('Png Files','*.png')]
        filename = filedialog.askopenfilename(filetypes=f_types)
        idx = pytkguivars.imageIndex
        pytkguivars.imagesUsed[idx] = ImageTk.PhotoImage(file=filename)
        self.widget.configure(image=pytkguivars.imagesUsed[idx])
        pytkguivars.imageIndex += 1
    
    def defineStyle(self):
        print('defineStyle TBD')
        style = ttk.Style(self.root)
        style.element_names()
        styleVals = style.element_names()
        print(styleVals)
    
    def applyEditSettings(self):
        # keys = self.widget.keys()
        keys = self.keys
        print("Apply edit settings")
        kids = self.widget.children
        print(kids)
        row = 0
        for key in keys:
            row += 1
            if type(key) is tuple:
                childW = key[0]
                k = key[1]
                # child_widget = getattr(self.widget,childW)
            else:
                k = key
                val = self.widget.cget(k)
            if k:
                if not pytkguivars.stringUsed[row]:
                    print("NOT USED Key " + k + " Value " + str(val))
                else:
                    strVar = pytkguivars.stringVars[row]
                    print("Row", row, "StringVar", strVar)
                    val = strVar.get()
                    print("Key " + k + " Value " + str(val))
                    # Yep this is weird python shit. configure would not use the tag name as a variable
                    # eg. self.widget.configure(k:val)
                    # so chat gpt-ity said to do this
                    child = guivars.childNameVars[row].get()
                    if child:
                        print("Configure tag=" + str(k) + " Child=" + str(child) + " Row=" + str(row) + " Value=" + str(
                            val))
                        # child_widget = getattr(self.widget,child)
                        # command_str = f"child_widget.configure({{k: {val}}})"
                        # print(command_str)
                        if child == 'label':
                            self.widget.label.configure(**{k:val})
                        elif child == 'scale':
                            self.widget.scale.configure(**{k:val})
                        else:
                            print(child + " child not handled")
                    else:
                        # command_str = f"self.widget.configure({{k: {val}}})"
                        # print(command_str)
                        print("Configure tag=" + str(k) + " Row=" + str(row) + " Value=" + str(val))
                        if (k == 'anchor' or k == 'justify') and len(val) < 1:
                            print("Ignored")
                        else:
                            # if val is not int:
                            #    val = 0
                            print("k",k,"val",val,"val")
                            try:
                                self.widget.configure(**{k: val})
                            except Exception as e:
                                print(e)

    def editTtkPopup(self, popup):
        global string1
        global string2
        keys = self.widget.keys()
        row = 0
        if keys == {}:
            popup.destroy()
            return
        print(keys)
        kids = self.widget.children
        if kids:
            widgetName = self.widget.widgetName
            print(widgetName)
            l0 = ttk.Label(popup,text=widgetName)
            l0.grid(row=row,column=1,columnspan=5,sticky=tk.SW)
            row += 1
            if widgetName == 'ttk::notebook':
                print(widgetName)
            elif widgetName == 'ttk::frame':
                keys1 = self.widget.label.keys()
                for k1 in keys1:
                    keys.append(tuple(('label',k1)))
                keys2 = self.widget.scale.keys()
                for k2 in keys2:
                    keys.append(tuple(('scale',k2)))
                
                print(keys)
            else:
                print('unhandled child' + widgetName)
        # self.labelKeys = ['text', 'background', 'foreground', 'font', 'width', 'anchor', 'textvariable']
        anchorVals = [tk.CENTER,tk.N,tk.NE,tk.E,tk.SE,tk.S,tk.SW,tk.W,tk.NW]
        justifyVals = [tk.LEFT,tk.CENTER,tk.RIGHT]
        reliefVals = [tk.FLAT,tk.GROOVE,tk.RAISED,tk.RIDGE,tk.SOLID,tk.SUNKEN]
        compoundVals = [tk.NONE,tk.TOP,tk.BOTTOM,tk.LEFT,tk.RIGHT]
        orientVals = [tk.VERTICAL,tk.HORIZONTAL]
        self.keys = keys
        for key in self.keys:
            row += 1
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
            if k == 'class' or k == 'cursor' or k == 'show' or k == 'default' or k == 'takefocus' or k == 'state':
                guivars.stringUsed[row] = False
            ###############################
            # Special cases. Most will default to an entry widget
            ###############################
            elif k == 'font':
                # rowX = row
                w = ttk.Button(popup,name=uniqueName,text="Select a Font",command=lambda row=row:self.fontChange(row))
                w.grid(row=row,column=3,columnspan=2,sticky=tk.SW)
            ###############################
            # spinbox integer tags
            ###############################
            elif (k == 'height' or k == 'columns' or k == 'width' or
                  k == 'borderwidth' or k == 'displaycolumns' or k == 'padding'):
                w = ttk.Spinbox(popup,width=5,name=uniqueName,from_=0,to=99,increment=1,
                                textvariable=guivars.stringVars[row])
                w.grid(row=row,column=3,sticky=tk.SW)
            ###############################
            # Combobox fields
            ###############################
            elif k == 'anchor':
                w = ttk.Combobox(popup,values=anchorVals,width=6,name=uniqueName,
                                 textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=row,column=3,sticky=tk.SW)
            elif k == 'justify':
                w = ttk.Combobox(popup,values=justifyVals,width=6,name=uniqueName,
                                 textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=row,column=3,sticky=tk.SW)
            elif k == 'relief':
                w = ttk.Combobox(popup,values=reliefVals,width=6,name=uniqueName,
                                 textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=row,column=3,sticky=tk.SW)
            elif k == 'compound':
                w = ttk.Combobox(popup,values=compoundVals,width=6,name=uniqueName,
                                 textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=row,column=3,sticky=tk.SW)
            elif k == 'orient':
                w = ttk.Combobox(popup,values=orientVals,width=6,name=uniqueName,
                                 textvariable=guivars.stringVars[row])
                w.set(val)
                w.grid(row=row,column=3,sticky=tk.SW)
            ###############################
            # Style is tricky TBD
            ###############################
            elif k == 'style':
                w = ttk.Button(popup,name=uniqueName,text="Define/Select a Style",command=self.defineStyle)
                w.grid(row=row,column=3,sticky=tk.SW)
            ###############################
            # Image need work TBD
            ###############################
            elif k == 'image':
                # thisRow1 = row
                w = ttk.Button(popup,name=uniqueName,text="Select an image",
                               command=lambda row=row:self.selectImage(row))
                w.grid(row=row,column=3,sticky=tk.SW)
            ###############################
            # Colour selection possibly a canvas with the colour
            ###############################
            elif k == 'foreground' or k == 'background':
                w = ttk.Button(popup,name=uniqueName,text="Select a Color",
                               command=lambda row=row:self.changeColour(row))
                w.grid(row=row,column=3,columnspan=2,sticky=tk.SW)
            ###############################
            # The Default --- use and entry widget for all other tags
            ###############################
            else:
                w = tk.Entry(popup,name=uniqueName,textvariable=guivars.stringVars[row])
                w.grid(row=row,column=3,sticky=tk.SW)
            
            if guivars.stringUsed[row]:
                l1.grid(row=row,column=0,columnspan=2,sticky=tk.E)
        
        # Some widgets have 'children'
        b1 = ttk.Button(popup,width=8,text="Close",command=popup.destroy)
        b2 = ttk.Button(popup,width=8,text="Apply",command=self.applyEditSettings)
        b1.grid(row=row,column=0)
        b2.grid(row=row,column=3)
        row += 1
        # blank Label to make the layout better
        lab2 = ttk.Label(popup,text="   ")
        lab2.grid(row=row,column=2)
        popup.mainloop()
    
    def editTtkButton(self,root):
        keys = self.widget.keys()
        if keys == {}:
            root.destroy()
            return
        print(keys)
        
        root.mainloop()
    
    def editWidget(self,w):
        # Build the edit widget
        popup = tk.Tk()
        x = popup.winfo_pointerx()
        y = popup.winfo_pointery()
        popup.wm_title("Edit Widget")
        popup.geometry('+%d+%d' % (x,y))
        colour = 'bisque'
        style = ttk.Style(popup)
        style.configure('TFrame',background=colour,foreground='black')
        style.configure('TLabel',background=colour,foreground='black')
        style.configure('TCombobox',background=colour,foreground='black')
        style.configure('TSpinbox',background=colour,foreground='black')
        # style.configure('TButton', background='lightgreen1', foreground='black')
        self.editPopupFrame = ttk.Frame(popup,borderwidth=2,relief='sunken')
        
        self.editTtkPopup(popup)
        # match self.widget.widgetName:
        #     case 'ttk::label':
        #         self.editTtkPopup(popup)
        #     case 'ttk::button':
        #         self.editTtkButton(popup) */
    
    def makePopup(self):
        # Add Menu
        self.popup = tk.Menu(self.root,tearoff=0)
        
        # Adding Menu Items
        mypartial = partial(self.editWidget,self.widget)
        self.popup.add_command(label="Edit",command=mypartial)
        # self.popup.add_command(label="Edit", command=self.editWidget)
        self.popup.add_command(label="Layout",command=self.place_popup)
        self.popup.add_command(label="Clone")
        self.popup.add_command(label="Col Span +",command=self.incColSpan)
        self.popup.add_command(label="Col Span -",command=self.decColSpan)
        self.popup.add_command(label="Delete",command=self.widget.destroy)
        self.popup.add_command(label="Save",command=self.saveTest)
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
            self.popup.bind("<Button-3>",self.menu_popup)
            # button = ttk.Button(self.popup, text="Quit", command=self.popup.destroy)
            # button.pack()
    
    def rightMouseDown(self,event):
        # popup a menu for the type of object
        print(self.widget.widgetName)
        # print(event)
        print(createWidget.widgetList[self.widgetId].widgetName)
        # self.widget.destroy()
        self.makePopup()
        self.menu_popup(event)
    
    def leftMouseDown(self,event):
        self.start = (event.x,event.y)
        self.x_root = event.x_root - self.start_x
        self.y_root = event.y_root - self.start_y
        self.dragType = 'move'
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        x = self.widget.winfo_x() + event.x - self.start[0]
        y = self.widget.winfo_y() + event.y - self.start[1]
        self.x = x
        self.y = y
        self.cornerY = self.y + height
        self.cornerX = self.x + width
        print("Left Mouse Down --  Width " + str(width) + " Height " + str(height))
        if event.x > (width - 4):
            self.dragType = 'dragEast'
            print("Drag right Side")
        elif event.x < 4:
            self.dragType = 'dragWest'
            print("Drag left Side")
        if event.y > (height - 4):
            self.dragType = 'dragSouth'
            print("Drag bottom Side")
        elif event.y < 5:
            self.dragType = 'dragNorth'
            print("Drag top Side")
        # print(event)
    
    def leftMouseDragxx(self,event):
        self.xpos = event.x_root - self.x_root
        self.ypos = event.y_root - self.y_root
        self.widget.place(x=self.xpos,y=self.ypos)
    
    def leftMouseDrag(self,event):
        # print(event)
        x = self.widget.winfo_x() + event.x - self.start[0]
        y = self.widget.winfo_y() + event.y - self.start[1]
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        try:
            self.widget.lift()
        except Exception as e:
            print("Lift exception ",e)
        if self.dragType == 'dragEast':
            width = event.x
        elif self.dragType == 'dragSouth':
            height = event.y
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
        z = self.root.grid_location(self.x,self.y)
        self.row = z[1]
        self.col = z[0]
        newX = snapToClosest(self.x)
        newY = snapToClosest(self.y)
        self.x = newX
        self.y = newY
        
        self.widget.place(x=self.x,y=self.y)
        if pytkguivars.useGrider:
            self.widget.grid(row=self.row,column=self.col)
        print("Left Mouse Release -- col,row " + str(z))
    
    def leftMouseReleaseXX(self,event):
        self.start_x = self.widget.winfo_x()
        self.start_y = self.widget.winfo_y()
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()
        x = event.x_root - self.widget.winfo_rootx()
        y = event.y_root - self.widget.winfo_rooty()
        self.x = x
        self.y = y

    def saveTest(self):
        # return None
        for w in createWidget.widgetList:
            if w is not None:
                place = w.place_info()
                print(place)
                grid = w.grid_info()
                print(grid)
                keys = w.keys()
                print(keys)
                tags = w.bindtags()
                print(tags)
                t = w.winfo_class()
                print(t)
                # w.__getattribute__(string1)
                for k in keys:
                    print(k)
                    try:
                        val = k.cget()
                        if val is not None:
                            print(k , ": " , str(val))
                    except Exception as e:
                        print(k , " exception ",e)
                    """
                    val = w.cget()
                    if val == None:
                        pass
                    else:
                        try:
                            print(k + " " + val)
                        finally:
                            print("Unable to print val")
                    """