import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog
from tkinter import *

class GUIHome(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold")

        #top container is used to stack frames
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (Welcome, Cleaning, User, Calibration_Home):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame

            #all frames in same location
            #stacking order determines visibility
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Welcome")

    def show_frame(self, page_name):
        #show a frame for given page name
        frame = self.frames[page_name]
        frame.tkraise()


class Welcome(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Welcome to the SnP Training Suite!", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)

        button = tk.Button(self, text="Continue",
                            command=lambda: controller.show_frame("Cleaning"))
                            
        button.pack()

class Cleaning(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Please ensure device has been appropriately cleaned before training.", font = controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Continue",
                           command=lambda: controller.show_frame("User"))

        button.pack()

class User(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="What kind of patient will be training?")
        label.pack(side="top", fill="x", pady=10)
        button1 = tk.Button(self, text="New User",
                            command=lambda: controller.show_frame("Calibration_Home"))
        button1.pack()
        button2 = tk.Button(self, text="Returning User",
                            command=lambda: filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*"))))
        button2.pack()
    

class Calibration_Home(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        w = Scale(self, from_=0, to=42)
        w.pack()
        label = tk.Label(self, text="info will go here about calibration")
        label.pack(side="top", fill="x", pady=10)


if __name__== "__main__":
    app = GUIHome()
    app.mainloop()
