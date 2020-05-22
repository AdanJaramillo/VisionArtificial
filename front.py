import tkinter as tk
import PIL
from tkinter.filedialog import *
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import threading
import time
width, height = 800, 600
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

ventana = Tk()
ventana.bind('<Escape>', lambda e: ventana.quit())
lmain = Label(ventana)
lmain.pack()

def webcam():
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = PIL.Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    lmain.after()
    

def abrir():
   ruta=askdirectory()
   archivo=askopenfile()
   archivo = open("r")
   lines = archivo.read()

ventana=Tk()
ventana.config(bg="black")
ventana.geometry("500x400")
botonAbrir=Button(ventana,text="Seleccionar archivo", command=abrir)
botonAbrir.grid(padx=150,pady=100)
botonCompila=Button(ventana,text="Camara", command=webcam)
botonCompila.grid(padx=210,pady=10)


ventana.mainloop()