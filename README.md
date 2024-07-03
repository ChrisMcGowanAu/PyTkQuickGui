# pytkgui A tool to automate the layout of tkinter/tkbootstrap widgets
This is a project to automate the often tedious process of laying out and configuring tkinter widgets to make a python applcation using tkinter widgets
The need for this tool comes from my python experience is building test tools for other mush larger projects, usually in C/C++ 
Years ago, I wrote a lot of small projects in tcl/tk for implementing a gui layey on top of a C/C++ project, and once got involved in
an Ada83 project that used TK as a gui layer (That was totally strange, but it worked) 
There are similiar projects out there, but they usually have issues that make them unsuable for me. I work in Linux, and Windows only 
projects are of no interest. There are proprietry projects, but I have not tried them at this stage. An old favorite of mine "spectcl" 
seems like it has not been updated for decades, and recent attempts to get it running have proved to be impossible (at least for me) anyway I 
want to go beyond what spectcl did.
At this stage,  I can build layouts and configure widgets ( not all but enough for now ) and aiming to generate a python-tk gui layout from
this. This will enable me to use the tool to generate new parts of the tool, thus it will help bootstrap itself.
Once finished, a pytkgui generated python program will have the gui section done and mainly blank callback procs, as well as some TK Variables (If these were setup via the tool ) 
used as part of the widgets. The developer will then be able to write the back end code for the project to complete the code.
