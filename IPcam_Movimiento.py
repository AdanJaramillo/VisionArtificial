import cv2
import numpy as np
import pytesseract

#Habilitar Pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'


placa = []
video = cv2.VideoCapture('http://192.168.1.72:4747/video')
i = 0
while True:
  ret, frame = video.read()
  if ret == False: break
  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  #Deteccion de bordes 
  canny = cv2.Canny(gray,150,200)
  canny = cv2.dilate(canny,None,iterations=1)
  if i == 20:
    bgGray = gray
  if i > 20:
    _, th = cv2.threshold(canny, 40, 255, cv2.THRESH_BINARY)
    # Para OpenCV 3
    #_, cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Para OpenCV 4
    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #cv2.drawContours(frame, cnts, -1, (0,0,255),2)        
    
    for c in cnts:
      area = cv2.contourArea(c)
      #Identifica que sea un rectangulo
      x,y,w,h = cv2.boundingRect(c)
      epsilon = 0.02*cv2.arcLength(c,True)
      approx = cv2.approxPolyDP(c,epsilon,True)
      if len(approx)==4 and area>5000:
        print('area=',area)
        cv2.drawContours(frame,[approx],0,(0,255,0),3)
        aspect_ratio = float(w)/h
        if aspect_ratio>2.4:

          #OCR con pytesseract
          placa = gray[y:y+h,x:x+w]
          text = pytesseract.image_to_string(placa,config='--psm 11')
          cv2.putText(frame,text,(x-20,y-10),1,2.2,(0,255,0),3)
          print('PLACA: ',text)

  cv2.imshow('Frame',frame)
  i = i+1
  if cv2.waitKey(30) & 0xFF == ord ('q'):
    break
video.release()