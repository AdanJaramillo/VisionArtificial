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

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
screenCnt = None
capture = cv2.VideoCapture("http://192.168.1.72:4747/video")  

while True:  # corre el programa.
    while screenCnt is None:  # repite el proceso cuando no detecta alguna placa
        _, img = capture.read()

        img = cv2.resize(img, (640, 480))

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # convierte a escala de grises
        gray = cv2.bilateralFilter(gray, 11, 17, 17)  # desenfoque para evitar el ruido en la imagen
        edged = cv2.Canny(gray, 30, 200)

        
        # busca los contornos en la imagen, para despues dibujarlos
        cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
        screenCnt = None

        # recorre el contorno
        for c in cnts:
            # aproximaciones del contorno
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.018 * peri, True)

            # si se los contornos se tocan en 4 lados 
            # asumiremos que hemos encontrado el contorno de la placa
            if len(approx) == 4:
                screenCnt = approx
            break

        # Bucle la sección de captura y verifique los contornos, si es 0, repita nuevamente, si es 1, rompa y continúe.

        print("Placa no detectada")

    cv2.drawContours(img, [screenCnt], -1, (0, 255, 0), 3)

    # Enmascarar la parte que no sea la matrícula
    mask = np.zeros(gray.shape, np.uint8)
    new_image = cv2.drawContours(mask, [screenCnt], 0, 255, -1, )
    new_image = cv2.bitwise_and(img, img, mask=mask)

    # nuevo corte
    (x, y) = np.where(mask == 255)
    (topx, topy) = (np.min(x), np.min(y))
    (bottomx, bottomy) = (np.max(x), np.max(y))
    Cropped = gray[topx:bottomx + 1, topy:bottomy + 1]

    # lee la placa y borra caracteres especiales
    text = pytesseract.image_to_string(Cropped, config='--psm 11')
    for k in text.split("\n"):
        text = (re.sub(r"[^a-zA-Z0-9]+", '', k))
    print("Placa:", text)  # Imprime la salida de OCR con el procesamiento de texto.

    # Abra el archivo plates.json y busca una coincidencia de texto
    with open('plates.json') as json_file:
        data = json.load(json_file)
        for p in data['plates']:
            a = p['plate']
            for k in a.split("\n"):
                plateFix = (re.sub(r"[^a-zA-Z0-9]+", '', k))  # quita los caracteres especiales
            if plateFix == text:
                print("Plate '" + p['plate'] + "' Se encuentra en BD")  # Imprime la placa encontrada en la base de datos.
                now = datetime.now()  #obtiene la hora actual
                current_time = now.strftime("%H-%M-%S")  # salva la hora en tiempo real
                if path.exists("output/images"):  # verifica que la imagen se haya guardado
                    os.chdir('output/images/')  # si es verdadero se cambia el origen de donde se guardara
                else:
                    os.makedirs("output/images/")  # si no, crea un directorio nuevo
                    os.chdir('output/images/')  # cambia el directorio para guardar la imagen
                fileName = text + '_-_' + current_time + '.jpg'  # crea un archivo para la imagen
                cv2.imwrite(fileName, img, params=None)  # salva la imagen
                

    # cv2.imshow('Cropped', Cropped)  
    # cv2.imshow('image', img)  
    #  key = cv2.waitKey(1)  
    time.sleep(1)  # pausa un segundo para despues volver a hacer el proceso.
    screenCnt = None  # configura la screenCnt con un valor 'None' para reiniciar el parametro.
    cv2.destroyAllWindows()  # cierra la imagen si se encuentra abierta.
