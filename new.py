import cv2
import imutils
import time
import json
import re
import os
import numpy as np
import pytesseract
from datetime import datetime
from os import path
from PIL import Image
from picamera.array import PiRGBArray
from picamera import PiCamera
import smtplib

import mysql.connector

#####Conexion a la base de datos
miConexion = mysql.connector.connect( host='localhost', user= 'root', passwd='root', db='dateplate' )
cur = miConexion.cursor()
#######Fin de conexion

camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
rawCapture = PiRGBArray(camera, size=(640, 480))
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        cv2.imshow("Frame", image)
        key = cv2.waitKey(1) & 0xFF
        rawCapture.truncate(0)
        if key == ord("s"):
             gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
             gray = cv2.bilateralFilter(gray, 11, 17, 17) 
             edged = cv2.Canny(gray, 30, 200) 
             cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE,              cv2.CHAIN_APPROX_SIMPLE)
             cnts = imutils.grab_contours(cnts)
             cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
             screenCnt = None
             for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.018 * peri, True)
                if len(approx) == 4:
                  screenCnt = approx
                  break
             if screenCnt is None:
               detected = 0
               print ("Placa no encontrada")
             else:
               detected = 1
             if detected == 1:
               cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 3)
             mask = np.zeros(gray.shape,np.uint8)
             new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
             new_image = cv2.bitwise_and(image,image,mask=mask)
             (x, y) = np.where(mask == 255)
             (topx, topy) = (np.min(x), np.min(y))
             (bottomx, bottomy) = (np.max(x), np.max(y))
             Cropped = gray[topx:bottomx+1, topy:bottomy+1]
             text = pytesseract.image_to_string(Cropped, config='--psm 11')
             for k in text.split("\n"):
                 text = (re.sub(r"[^a-zA-Z0-9]+", '', k))
             print("Placa:",text)
             plaquita = text
             print(plaquita)
              
             rows_count = cur.execute("SELECT plate_chars, plate_acces FROM plates WHERE plate_chars ='"+plaquita+"' AND plate_acces ='true'")
             count =0
             for row in cur: 
                count = 1
                if (count == 1): 
                    print("Acceso permitido")
             if (count == 0):
                    print("Placa no registrada o denegada") 


                    miConexion.close()

             cv2.imshow("Frame", image)
             cv2.imshow('Cropped',Cropped)   
                    
             cv2.waitKey(0)
             #break
             time.sleep(1)  # pausa un segundo para despues volver a hacer el proceso.
   
cv2.destroyAllWindows()