# Main.py

import tkinter as tk
from tkinter.filedialog import askopenfilename
import PIL
from tkinter.filedialog import *
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
width, height = 800, 600


import cv2
import numpy as np
import pytesseract
import os

import DetectChars
import DetectPlates
import PossiblePlate

import mysql.connector


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
miConexion = mysql.connector.connect( host='localhost', user= 'root', passwd='root', db='dateplate' )
cur = miConexion.cursor()
# variables ##########################################################################
SCALAR_BLACK = (0.0, 0.0, 0.0)
SCALAR_WHITE = (255.0, 255.0, 255.0)
SCALAR_YELLOW = (0.0, 255.0, 255.0)
SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)

showSteps = False

def webcam():
     
        imgOriginalScene = cv2.VideoCapture("http://192.168.1.72:8080/video")

        while True:
            
            ret, frame = imgOriginalScene.read()
            
            cv2.imshow('Video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        
        imgOriginalScene.release()
        cv2.destroyAllWindows() 
#
def abrir():
    #    ruta=askdirectory()
#    archivo=askopenfile()
#    archivo = open(archivo)
#    lines = archivo.read()
    Tk().withdraw() 
    filename = askopenfilename() 
    print(filename)

    blnKNNTrainingSuccessful = DetectChars.loadKNNDataAndTrainKNN()         

    if blnKNNTrainingSuccessful == False:                               # si KNN tiene errores
        print("\nerror: KNN traning was not successful\n")  # muestra un mensaje de error
        return                                                          # y termina la app
    # end if

    imgOriginalScene  = cv2.imread(r""+filename)               # abre imagen

    if imgOriginalScene is None:                            # si la imagen no se encuentra
        print("\nerror: image not read from file \n\n")  # muestra un mensaje en pantalla
        os.system("pause")                                  # hace una pausa para que el usuario vea el mensaje
        return                                              # y termina la app
    # end if

    listOfPossiblePlates = DetectPlates.detectPlatesInScene(imgOriginalScene)           # detecta placas

    listOfPossiblePlates = DetectChars.detectCharsInPlates(listOfPossiblePlates)        # detecta las letras en las placas

    cv2.imshow("imgOriginalScene", imgOriginalScene)            

    if len(listOfPossiblePlates) == 0:                          # si no se encuentran las placas
        print("\nno license plates were detected\n")  # informa al usuario que no se encontraron
    else:                                                       # si no
                # si obtenemos por lo menos una placa

                # ordenar la lista de posibles placas en orden DESCENDENTE 
                # (la mayor cantidad de caracteres a la menor cantidad de caracteres)
        listOfPossiblePlates.sort(key = lambda possiblePlate: len(possiblePlate.strChars), reverse = True)

        licPlate = listOfPossiblePlates[0]

        cv2.imshow("imgPlate", licPlate.imgPlate)           # muestra la imagen de la placa recortada
        cv2.imshow("imgThresh", licPlate.imgThresh)

        if len(licPlate.strChars) == 0:                     # si no encuentra caracteres en la placa
            print("\nno characters were detected\n\n")  # muestra mensaje
            return                                          # sale de la app
        # end if

        drawRedRectangleAroundPlate(imgOriginalScene, licPlate)             # dibuja un rectangulo rojo en donde estan los caracteres

        print("\nPLACA = " + licPlate.strChars + "\n")  # escribe los caracteres en la ventana
        print("---------------------------------------- ")
        plaquita = licPlate.strChars
        ######consulta
        
        rows_count = cur.execute("SELECT plate_chars, plate_acces FROM plates WHERE plate_chars ='"+plaquita+"' AND plate_acces ='true'")
        count =0
        for row in cur: 
            count = 1 
            if (count == 1): 
                print("Acceso permitido")
        if count == 0: 
            print("Placa no registrada o denegada") 

        miConexion.close()
        ##########Termino de consulta
        writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)           # escribe en la imagen los caracteres

        cv2.imshow("imgOriginalScene", imgOriginalScene)                # vuelve a mostrar la imagen

        cv2.imwrite("imgOriginalScene.png", imgOriginalScene)           # crea un archivo nuevo de imagen

    # end if else

    cv2.waitKey(0)					

    return

###end abrir

#end function   

#########################################################################################################
def main():
   
    ventana=Tk()
    ventana.config(bg="black")
    ventana.geometry("500x400")
    botonAbrir=Button(ventana,text="Seleccionar archivo", command=abrir)
    botonAbrir.grid(padx=150,pady=100)
    botonCompila=Button(ventana,text="Camara", command=webcam)
    botonCompila.grid(padx=210,pady=10)
    
    ventana.mainloop()

# end main

###################################################################################################




###################################################################################################
def drawRedRectangleAroundPlate(imgOriginalScene, licPlate):

    p2fRectPoints = cv2.boxPoints(licPlate.rrLocationOfPlateInScene)            # obtiene los 4 lados del rectangulo

    cv2.line(imgOriginalScene, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), SCALAR_GREEN, 2)         # dibuja las 4 lineas
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), SCALAR_GREEN, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), SCALAR_GREEN, 2)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), SCALAR_GREEN, 2)
# end function

###################################################################################################
def writeLicensePlateCharsOnImage(imgOriginalScene, licPlate):
    ptCenterOfTextAreaX = 0                             #  este será el centro del área donde se escribirá el texto
    ptCenterOfTextAreaY = 0

    ptLowerLeftTextOriginX = 0                          # esta será la parte inferior izquierda del área donde se escribirá el texto
    ptLowerLeftTextOriginY = 0

    sceneHeight, sceneWidth, sceneNumChannels = imgOriginalScene.shape
    plateHeight, plateWidth, plateNumChannels = licPlate.imgPlate.shape

    intFontFace = cv2.FONT_HERSHEY_SIMPLEX                      # se elige la fuente de la letra
    fltFontScale = float(plateHeight) / 30.0                    # altura y lugar donde se escribira
    intFontThickness = int(round(fltFontScale * 1.5))           # grosor de la letra

    textSize, baseline = cv2.getTextSize(licPlate.strChars, intFontFace, fltFontScale, intFontThickness)        

    ( (intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg ) = licPlate.rrLocationOfPlateInScene

    intPlateCenterX = int(intPlateCenterX)              # hacer que el centro sea un número entero
    intPlateCenterY = int(intPlateCenterY)

    ptCenterOfTextAreaX = int(intPlateCenterX)         # la ubicación horizontal del área de texto es la misma que la placa

    if intPlateCenterY < (sceneHeight * 0.75):                                                  # si la placa está en los 3/4 superiores de la imagen
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) + int(round(plateHeight * 1.6))      # escribe en la parte inferior de la placa
    else:                                                                                       # de lo contrario, si la placa está en el 1/4 inferior de la imagen
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) - int(round(plateHeight * 1.6))      # escribe en la parte superior de la placa
    # end if

    textSizeWidth, textSizeHeight = textSize                

    ptLowerLeftTextOriginX = int(ptCenterOfTextAreaX - (textSizeWidth / 2))           # calcular el origen inferior izquierdo del área de texto
    ptLowerLeftTextOriginY = int(ptCenterOfTextAreaY + (textSizeHeight / 2))          # basado en el centro del área de texto, ancho y alto

            # escribe el texto en la imagen
    cv2.putText(imgOriginalScene, licPlate.strChars, (ptLowerLeftTextOriginX, ptLowerLeftTextOriginY), intFontFace, fltFontScale, SCALAR_YELLOW, intFontThickness)
# end function 
###################################################################################################
if __name__ == "__main__":
    main()






