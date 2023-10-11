import logging as log
import tkinter as tk
import tkinter.filedialog as filedialog

import ttkbootstrap as ttk
from PIL import ImageTk
# import urllib.request
import webbrowser
from tkfontchooser import askfont
from ttkbootstrap.dialogs.colorchooser import ColorChooserDialog
# from ttkbootstrap.dialogs.dialogs import FontDialog
from ttkbootstrap.widgets import Frame,Entry,LabelFrame
import pytkguivars

stickyVals = [" ",tk.N,tk.S,tk.E,tk.W,tk.NS,tk.EW,tk.NSEW]
borderVals = [tk.INSIDE,tk.OUTSIDE]
anchorVals = [tk.CENTER,tk.N,tk.NE,tk.E,tk.SE,tk.S,tk.SW,tk.W,tk.NW]
justifyVals = [tk.LEFT,tk.CENTER,tk.RIGHT]
reliefVals = [tk.FLAT,tk.GROOVE,tk.RAISED,tk.RIDGE,tk.SOLID,tk.SUNKEN]
compoundVals = [tk.NONE,tk.TOP,tk.BOTTOM,tk.LEFT,tk.RIGHT]
orientVals = [tk.VERTICAL,tk.HORIZONTAL]
cursorVals = ['arrow','circle','tcross','cross','exchange','plus','star',
              'clock','mouse','pirate','spider','target','trek']
ignoredKeys=('class','format','show','default','takefocus','state','validate',
             'validatecommand', 'xscrollcommand','invalidcommand')
comboWidth = 10
entryWidth = 12
spinboxWidth = 9
otherWidth = 12
buttonWidth = 12

class widgetEditPopup:
    def __init__(self,root,widget):
        self.keys = None
        self.widget = widget
        self.root = root
        self.stringDict = {}
        self.childNameDict = {}
        # clickCanvas.bind('<B1-Motion>',leftMouseDrag)
        # clickCanvas2.bind('<B1-Motion>',leftMouseDragResize)
    
    def addToChildNamesDict(self,key,val):
        self.childNameDict.update({key + ':',val})
    
    def addToStringDict(self,key,val):
        log.debug('key is ->%s<- val is ->%s<-',key,str(val))
        self.stringDict[key] = val
    
    def fontChange(self,key):
        # ttkbootstrap font dialog has issues
        font = askfont(self.root)
        # It needs a quick tidy ...
        font_str = ""
        if font:
            # spaces in the family name need to be escaped
            font['family'] = font['family'].replace(' ','\ ')
            font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
            if font['underline']:
                font_str += ' underline'
                font_str += ' overstrike'
            
            log.info("Font is %s",str(font_str))
            self.addToStringDict(key,font_str)
    
    def popupCallback(self,key):
        widgetKey = key + 'Widget'
        popupWidget = self.stringDict.get(widgetKey)
        log.warning("popupCallback widgetKey %s val %s key %s",widgetKey,popupWidget,key)
        val = popupWidget.get()
        self.addToStringDict(key,val)
        # This is needed to keep the validatecommand going
        return True
    
    def changeColour(self,key):
        colorDialog = ColorChooserDialog()
        colorDialog.show()
        colors = colorDialog.result
        if colors[2] != '':
            # self.stringDict[row].set(colors[2])
            self.addToStringDict(key,colors[2])
        else:
            log.warning("Color Chooser did not return anything")
    
    def leftMouseDragResize(self,event):
        widget = event.widget.master
        width = widget.winfo_width()
        height = widget.winfo_height()
        newHeight = height + event.y
        newWidth = width + event.x
        widget.place(height=newHeight,width=newWidth)
        log.info("Resize height %s width %s event.x %s event.y %s x_root %s y_root %s",
                 str(height),str(width),str(event.x),str(event.y),str(event.x_root),str(event.y_root))
    
    def leftMouseDrag(self,event):
        # This is a weird algorithm
        # it is a hack to get around using event.x_root and event.y_root
        # which seems tricky. However it does work (sort of)
        # The yellow dot/triangle on the popup is uses as a selection point
        widget = event.widget.master
        x = int(widget.place_info().get('x'))
        y = int(widget.place_info().get('y'))
        moveX = event.x
        moveY = event.y
        threshold = 12
        if abs(event.x) > threshold:
            if event.x > 0:
                moveX = threshold
            else:
                moveX = -1 * threshold
        if abs(event.y) > threshold:
            if event.y > 0:
                moveY = threshold
            else:
                moveY = -1 * threshold
        
        newX = x + moveX
        newY = y + moveY
        widget.place(x=newX,y=newY)
    
    def leftMouseRelease(self,event):
        log.info("leftMouseRelease event %s",str(event))
    
    def selectImage(self,key):
        # Need to convert this to skimage (or other package. PIL has issues with github pylint)
        log.warning("selectImage is Expermental")
        # return
        f_types = [('Png Files','*.png'),('Jpg kFiles','*.jpg')]
        filename = filedialog.askopenfilename(filetypes=f_types)
        image = ImageTk.PhotoImage(file=filename)
        filePath = key + 'filename'
        self.addToStringDict(key,image)
        self.addToStringDict(filePath,filename)
        self.widget.configure(image=image)
    
    def applyLayoutSettings(self):
        logString = 'Layout %s new value %s'
        log.debug("Apply Layout settings")
        onlyThese = ['x','y','width','height']
        for p in onlyThese:
            origName = str(p) + 'Orig'
            oldVal = self.stringDict.get(origName)
            newVal = self.stringDict.get(p)
            if newVal == 'None' or newVal is None:
                newVal = ''
            if oldVal != newVal:
                log.info("Widget %s Layout %s old ->%s<- new ->%s<-",self.widget,p,oldVal,newVal)
                try:
                    log.info(logString,str(p),str(newVal))
                    self.widget.place(**{p:newVal})
                except Exception as e:
                    log.error(e)
                    log.warning("k %s val %s",str(p),str(newVal))

    def applyEditSettings(self):
        keys = self.widget.keys()
        logString = 'key %s new value %s'
        log.debug("Apply edit settings")
        for key in keys:
            # row += 1
            if type(key) is tuple:
                # childW = key[0]
                k = key[1]  # child_widget = getattr(self.widget,childW)
            else:
                k = key
            if k:
                if k is None:
                    continue
                if k in ignoredKeys:
                    continue
                oldVal = self.widget.cget(k)
                newVal = self.stringDict.get(k)
                if newVal == 'None' or newVal is None:
                    newVal = ''
                if oldVal != newVal:
                    log.info("Widget %s Key %s old ->%s<- new ->%s<-",self.widget,k,oldVal,newVal)

                if k in ignoredKeys:
                    continue
                    # log.warning("Ignore %s",k)
                elif k == 'values':
                    values = self.reformatValues(newVal)
                    log.info(logString,str(k),str(values))
                    # This seems to be the way to add values
                    self.widget['values'] = newVal
                
                elif k == 'style' or k == 'bootstyle':
                    log.debug(logString,str(k),str(oldVal))
                    newVal = self.stringDict.get(k)
                    log.debug(logString,str(k),str(newVal))
                    # Don't do this .... self.widget.configure(style=newVal)
                    self.widget.configure(bootstyle=newVal)
                else:
                    log.debug(logString,str(k),str(newVal))
                    # self.addToStringDict(k,val)
                    if oldVal != newVal:
                        try:
                            log.info(logString,str(k),str(newVal))
                            self.widget.configure(**{k:newVal})
                        except Exception as e:
                            log.error(e)
                            log.warning("k %s val %s",str(k),str(newVal))
   
    def reformatValues(self,values) -> list:
        # There is possibly a better way to do this
        # configure does not work for lists. change directly ...
        # It needs a string list like this .
        # self.widget['values'] = "1 2 3 4 5"
        try:
            val = values.replace('(','')
            newVal = val.replace(')','')
            val = newVal
            newVal = val.replace(',',' ')
            val = newVal
            newVal= val.replace('\'','')
            return newVal
        except Exception as e:
            log.error("reformartValues %s",str(e))
            return []

    def createDragPoint(self,rootFrame,dragType):
        # This creates a yellow dot which can be used to drag the Frame
        clickCanvas = ttk.Canvas(rootFrame,width=20,height=20,)
        clickCanvas.grid(row=0,column=0,sticky='NW')
        if dragType == 'triangle':
            points = [0,20,0,0,20,0]
            clickCanvas.create_polygon(points,fill='yellow')
        else:
            clickCanvas.create_oval(1,1,20,20,fill='yellow')
        clickCanvas.bind('<B1-Motion>',self.leftMouseDrag)
    
    def createLayoutPopup(self):
        gridRow = 0
        wName = pytkguivars.fixWidgetName(self.widget.widgetName)
        log.info("Widget %s name %s",self.widget,wName)
        label= "Edit layout for " + wName
        layoutPopupFrame = LabelFrame(self.root,text=label,labelanchor='n',padding=2,borderwidth=1,relief='solid')
        layoutPopupFrame.place(x=300,y=10)

        self.createDragPoint(layoutPopupFrame,'triangle')

        w = ttk.Label(layoutPopupFrame,text=' ')
        w.grid(row=gridRow,column=1,columnspan=3,sticky=tk.NS)
        
        place = self.widget.place_info()
        # layoutPopupFrame.title("Edit Widget Layout")
        for p in place:
            onlyThese = ['x','y','width','height']
            if p not in onlyThese:
                continue
            gridRow += 1
            lab1 = ttk.Label(layoutPopupFrame,text=p)
            ###############################
            # Spinbox fields
            ###############################
            val = place[p]
            origName = str(p) + 'Orig'
            self.addToStringDict(origName,val)
            self.addToStringDict(p,val)
            uniqueName = p + str(gridRow)
            w = ttk.Spinbox(layoutPopupFrame,width=5,name=uniqueName,from_=0,to=299,increment=1,
                            validate='focusout',
                            validatecommand=lambda pp=p:self.popupCallback(pp))
            widgetKey = p + 'Widget'
            self.addToStringDict(widgetKey,w)
            w.set(val)
            lab1.grid(row=gridRow,column=0,sticky=tk.NE)
            w.grid(row=gridRow,column=3,sticky=tk.SW)
        # blank Label to make the layout better
        gridRow += 1
        lab2 = ttk.Label(layoutPopupFrame,text="  ")
        lab2.grid(row=gridRow,column=2)
        gridRow += 1
        b1 = ttk.Button(layoutPopupFrame,style='warning',width=5,text="Close",command=layoutPopupFrame.destroy)
        b2 = ttk.Button(layoutPopupFrame,style='sucess',width=5,text="Apply",command=self.applyLayoutSettings)
        b1.grid(row=gridRow,column=0)
        b2.grid(row=gridRow,column=3)
        
    def getHelp(self):
        wName = pytkguivars.fixWidgetName(self.widget.widgetName)
        if wName == 'label':
            webbrowser.open('https://docs.python.org/3/library/tkinter.ttk.html#label-options')
        else:
            webbrowser.open('https://docs.python.org/3/library/tkinter.ttk.html#ttk-widgets')
        print(wName)
    def createEditPopup(self):
        row = 0
        gridRow = 0
        wName = pytkguivars.fixWidgetName(self.widget.widgetName)
        log.info("Widget %s name %s",self.widget,wName)
        label= "Edit attributes for " + wName
        editPopupFrame = LabelFrame(self.root,text=label,labelanchor='n',padding=2,borderwidth=1,relief='solid')
        editPopupFrame.place(x=300,y=10)
        self.createDragPoint(editPopupFrame,'triangle')
        # w = ttk.Label(editPopupFrame,text='Edit ' + wName,justify=tk.CENTER,anchor=tk.CENTER)
        # w.grid(row=gridRow,column=1,columnspan=3,sticky=tk.NS)
        gridRow += 1
        keys = self.widget.keys()
        if keys == {}:
            editPopupFrame.destroy()
            return
        log.info("Keys %s",str(keys))
        self.keys = keys
        print('self.keys',self.keys)
        labelCol = 0
        controlCol = 3
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
            
            l1 = ttk.Label(editPopupFrame,text=k)
            uniqueName = k + str(row)
            if k in ignoredKeys:
                continue
            ###############################
            # Special cases. Most will default to an entry widget
            ###############################
            elif k == 'font':
                self.addToStringDict(k,val)
                w = ttk.Button(editPopupFrame,name=uniqueName,text="Select a Font",
                               width=buttonWidth,command=lambda kk=k:self.fontChange(kk))
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            ###############################
            # spinbox integer tags
            ###############################
            elif k in ('height','columns','width','borderwidth','displaycolumns','padding'):
                self.addToStringDict(k,val)
                w = ttk.Spinbox(editPopupFrame,width=spinboxWidth,name=uniqueName,from_=0,to=299,increment=1,
                                validate='focusout',
                                validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
                w.set(val)
            ###############################
            # Combobox fields
            ###############################
            elif k == 'anchor':
                self.addToStringDict(k,val)
                w = ttk.Combobox(editPopupFrame,values=anchorVals,width=comboWidth,name=uniqueName,
                                 validate='focusout',
                                 validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.set(val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            elif k == 'justify':
                self.addToStringDict(k,val)
                w = ttk.Combobox(editPopupFrame,values=justifyVals,width=comboWidth,name=uniqueName,
                                 validate='focusout',
                                 validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.set(val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            elif k == 'relief':
                self.addToStringDict(k,val)
                varName = self.stringDict.get(k)
                w = ttk.Combobox(editPopupFrame,values=reliefVals,width=comboWidth,name=uniqueName,
                                 validate='focusout',
                                 validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.set(val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            elif k == 'compound':
                self.addToStringDict(k,val)
                varName = self.stringDict.get(k)
                w = ttk.Combobox(editPopupFrame,values=compoundVals,width=comboWidth,name=uniqueName,
                                 validate='focusout',
                                 validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.set(val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            elif k == 'cursor':
                self.addToStringDict(k,val)
                w = ttk.Combobox(editPopupFrame,values=cursorVals,width=comboWidth,name=uniqueName,
                                 validate='focusout',
                                 validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.set(val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            elif k == 'orient':
                self.addToStringDict(k,val)
                w = ttk.Combobox(editPopupFrame,values=orientVals,width=comboWidth,name=uniqueName,
                                 validate='focusout',
                                 validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.set(val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            ###############################
            # Style is tricky -- using ttkbootstrap
            ###############################
            elif k == 'style':
                self.addToStringDict(k,val)
                # varName = self.stringDict.get(k)
                style = ttk.style.Style()
                colours = []
                for color_label in style.colors:
                    colours.append(color_label)
                w = ttk.Combobox(editPopupFrame,values=colours,width=comboWidth,name=uniqueName,
                                 validate='focusout',
                                 validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.insert(tk.END,val)
                # python or tk change the format to 'name.wiget-type'
                # bval = self.widget.cget('bootstyle') # This does not work
                try:
                    bval = self.widget.cget('style')
                    bvalList = bval.split('.')
                    if bvalList[0] not in colours:
                        val = ''
                    else:
                        val = bvalList[0]
                except Exception as e:
                    log.error("Style parsing val %s got Exception %s",str(val),str(e))
                # self.addToStringDict(k,val)
                self.addToStringDict('bootstyle',val)
                w.set(val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            ###############################
            # Image need work TBD Does not get saved correctly
            ###############################
            elif k == 'image':
                # thisRow1 = row
                self.addToStringDict(k,val)
                w = ttk.Button(editPopupFrame,name=uniqueName,text="Select Image",
                               width=buttonWidth,command=lambda kk=k:self.selectImage(kk))
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            ###############################
            # Colour selection possibly a canvas with the colour
            ###############################
            elif k == 'fg' or k == 'bg' or k == 'foreground' or k == 'background':
                self.addToStringDict(k,val)
                varName = self.stringDict.get(k)
                # w = ttk.Combobox(editPopupFrame,values=orientVals,width=comboWidth,name=uniqueName,
                w = ttk.Button(editPopupFrame,name=uniqueName,text="Select Color",
                               width=buttonWidth,command=lambda kk=k:self.changeColour(kk))
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)
            ###############################
            # The Default --- use and entry widget for all other tags
            ###############################
            else:
                self.addToStringDict(k,val)
                # varName = self.stringDict.get(k)
                w = Entry(editPopupFrame,name=uniqueName,width=entryWidth,
                          validate='focusout',
                          validatecommand=lambda kk=k:self.popupCallback(kk))
                widgetKey = k + 'Widget'
                self.addToStringDict(widgetKey,w)
                w.insert(tk.END,val)
                w.grid(row=gridRow,column=controlCol,columnspan=3,sticky=tk.SW)

            # if stringUsed[row]:
            l1.grid(row=gridRow,column=labelCol,columnspan=3,sticky=tk.E)
        
        # Some widgets have 'children'
        kids = self.widget.children
        if kids:
            for k in kids:
                try:
                    widgetName = k.widgetName
                except AttributeError as e:
                    log.warning('child widget ->%s<- got exception %s',str(k),str(e))
                    continue
                log.debug(widgetName)
                l0 = ttk.Label(editPopupFrame,text=widgetName,borderwidth=1,border=tk.SOLID,justify=tk.CENTER)
                l0.grid(row=gridRow,column=1,columnspan=5,sticky=tk.EW)
                row += 1
                gridRow += 1
                if widgetName == 'ttk::notebook':
                    log.debug(widgetName)
                elif widgetName == 'ttk::labelframe':
                    keys1 = self.widget.label.keys()
                    for k1 in keys1:
                        keys.append(tuple(('label',k1)))
                    keys2 = self.widget.scale.keys()
                    for k2 in keys2:
                        keys.append(tuple(('scale',k2)))
                    log.debug(keys)
                else:
                    log.debug('unhandled child %s',widgetName)
        # self.labelKeys = ['text', 'background', 'foreground', 'font', 'width', 'anchor', 'textvariable']
        b1 = ttk.Button(editPopupFrame,bootstyle='warning',width=5,text="Close",command=editPopupFrame.destroy)
        b2 = ttk.Button(editPopupFrame,bootstyle='info',width=5,text="Help",command=self.getHelp)
        b3 = ttk.Button(editPopupFrame,bootstyle='sucess',width=5,text="Apply",command=self.applyEditSettings)
        # blank Label to make the layout better
        lab2 = ttk.Label(editPopupFrame,text="   ")
        lab2.grid(row=gridRow,column=2)
        gridRow+=1
        b1.grid(row=gridRow,column=0,columnspan=2,sticky='EW')
        b2.grid(row=gridRow,column=2,columnspan=2,sticky='EW')
        b3.grid(row=gridRow,column=4,columnspan=2,sticky='EW')
        row += 1
        gridRow += 1
        clickCanvas2 = ttk.Canvas(editPopupFrame,width=20,height=20,)
        clickCanvas2.grid(row=gridRow,column=5,sticky='SE')
        points = [20,0,0,20,20,20]
        clickCanvas2.create_polygon(points,fill='grey')
        clickCanvas2.bind('<B1-Motion>',self.leftMouseDragResize)