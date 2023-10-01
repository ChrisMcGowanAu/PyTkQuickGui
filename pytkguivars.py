import tkinter as tk
import logging as log

projectDict: dict
stringVars: list[tk.StringVar]
childNameVars: list[tk.StringVar]
imageFileNames: list[tk.StringVar]
stringUsed: list[bool]
imagesUsed: list[tk.PhotoImage]
useGrider: bool
snapTo: int
imageIndex: int

alphaList = ["a","b","c","d","e","f","g","h","i","d","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]

def initVars():
    global stringVars
    global stringUsed
    global childNameVars
    global imageIndex
    global imagesUsed
    global imageFileNames
    global useGrider
    global snapTo
    global projectDict
    projectDict = {}
    stringVars = [tk.StringVar()] * 128
    childNameVars = [tk.StringVar()] * 64
    imageFileNames = [tk.StringVar()] * 64
    imagesUsed = [tk.PhotoImage] * 64
    stringUsed = [bool] * 64
    # useGrider = bool
    # snapTo = int
    imageIndex = 0
    snapTo = 16
    useGrider = False

# Common Procs
def Merge(dict1,dict2):
    res = {**dict1,**dict2}
    return res

def saveWidgetAsDict(widgetCount,w):
    """
    Save a Widget info as a dictonary
    :param widgetCount: Count
    :param w: Widget
    :return: Dict()
    """
    w.update()
    log.info("=-----------")
    # parent = w.winfo_parent() # This can get weird errors
    log.info('widgetName %s',w.widgetName)
    widgetName = 'Widget' + str(widgetCount)
    place = w.place_info()
    # Remove 'in' from place.
    del place['in']
    widgetDict = {'WidgetName':w.widgetName,'Place':place}
    # place['in'] = widgetName
    keyCount = 0 
    keys = w.keys()
    if keys:
        for key in keys:
            log.info('Key->%s<-',key)
            if key != 'in':
                value = w[key]
                log.info('Value->%s<-',str(value))
                attrId = 'Attribute' + str(keyCount)
                # widgetAttribute = {attrId: {'Key': key,'Type': type(value),'Value': str(value)}}
                # Ignore empty values
                if (value is not None) and (len(str(value)) > -1):
                    widgetAttribute = {attrId:{'Key':key,'Value':str(value)}}
                    newWidget = Merge(widgetDict,widgetAttribute)
                    widgetDict = newWidget
                    keyCount += 1
    widgetKeys = widgetName + '-KeyCount'
    tmpDict = Merge(widgetDict,{widgetKeys:keyCount})
    newWidget = {widgetName:tmpDict}
    return newWidget


def buildAWidget(widgetId,wDictOrig):
    # log.info('wDictOrig',wDictOrig)
    widgetAltName= 'Widget' + str(widgetId)
    testDict = wDictOrig.get(widgetAltName)
    widgetName = str(widgetId)
    if testDict is not None:
        # log.info(testDict)
        wDict = testDict
        widgetName = widgetAltName
    else:
        wDict = wDictOrig
    wType = wDict.get('WidgetName')
    # log.info('wType',wType,type(wType))
    t = wType.replace('ttk::','ttk.')
    wType = t
    idx = wType.find('.')
    if idx == -1:  # Not ttk widgets
        t = 'tk.' + wType
        wType = t
    for ch in alphaList:
        t = wType.replace('.' + ch,'.' + ch.upper())
        wType = t
    keyCount = widgetName + "-KeyCount"
    nKeys = wDict.get(keyCount)
    place = wDict.get('Place')
    widgetDef = wType + "(mainCanvas"
    for a in range(nKeys):
        attribute = 'Attribute' + str(a)
        aDict = wDict.get(attribute)
        key = aDict.get('Key')
        val = aDict.get('Value')
        # Looks like a bug in tkinter scale objects ..
        if key == 'from':
            key = 'from_'
        if val.find('<') > -1 or val.find('(') > -1:
            log.info("# key",key,"has a weird value",val)
        else:
            if len(val) > 0:
                tmpWidgetDef = widgetDef + ',' + key + '=\'' + val + '\''
                widgetDef = tmpWidgetDef
    tmp = widgetDef + ')'
    widgetDef = tmp
    return widgetDef
