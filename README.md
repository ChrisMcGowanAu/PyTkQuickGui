# pytkgui
# A tool to automate the layout of tkinter/tkbootstrap widgets

This project aims to automate the often tedious process of laying out and configuring tkinter widgets to create a Python application using tkinter. The need for this tool arises from my experience in building test tools for larger projects, usually in C/C++.

There are similar projects available, but they often have issues that make them unsuitable for me. I work in Linux, so Windows-only projects are of no interest. There are proprietary projects, but I have not tried them yet. An old favorite of mine, "spectcl," seems to have not been updated for decades, and my recent attempts to get it running have been unsuccessful. Anyway, I want to go beyond what spectcl did. I also wanted python/tk output

At this stage, I can build layouts and configure widgets (not all, but enough for now) and aim to generate a Python-Tk GUI layout from this. This will enable me to use the tool to generate new parts of the tool, helping it bootstrap itself.

Once finished, a pytkgui-generated Python program will have the GUI section done, with mainly blank callback procedures and some Tkinter variables (if these were set up via the tool) used as part of the widgets. The developer will then be able to write the backend code to complete the project.

It currently uses pytkbootstrap, which provides a more modern look and feel. The generated output is a single Python file with simple functions and variable creation. Once complete, a user can write the business logic without having to concern themselves with widget layouts. Later, I might add menus and more widgets.
