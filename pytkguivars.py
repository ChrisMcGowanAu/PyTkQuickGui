import tkinter as tk
from PIL import Image, ImageTk
import tkinter.ttk as ttk

projectDict: dict
stringVars: list[tk.StringVar]
childNameVars: list[tk.StringVar]
imageFileNames: list[tk.StringVar]
stringUsed: list[bool]
imagesUsed: list[tk.PhotoImage]
useGrider: bool
snapTo: int
imageIndex: int

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
