# PyTkQuickGui
# A tool to quickly layout tkinter/tkbootstrap widgets via select, drag, resize, and edit tools.

This project aims to automate the often tedious process of laying out and configuring tkinter widgets to create a Python application using tkinter. The need for this tool arises from my experience in building test tools and small to medium-sized Python and TclTk tools.

There is still a lot to do to make this tool usable by most developers, notably a user's guide and a video describing how to use it.

At this stage, I welcome feedback on what is here (still an 'alpha' release), and if others can help develop this further, that would be great. I have limited time, as I am working full-time and have limited time to devote to developing this tool.

Currently, I can build layouts and configure widgets (not all, but enough for now) and generate a Python-Tk GUI layout from this. If functions have been defined, function prototypes will be generated, as are Tk variables if defined in the widget editor.

Once finished, a PyTkQuickGui-generated Python program will have the GUI section done, with mainly blank callback procedures and some Tkinter variables (if these were set up via the tool) used as part of the widgets. The developer will then be able to write the backend code to complete the project.

It currently uses pytkbootstrap, which provides a more modern look and feel. The generated output is a single Python file with simple functions and variable creation. Once complete, a user can write the business logic without having to concern themselves with widget layouts. Later, I might add menus and more widgets.
