# DetectPlates.py

import cv2
import numpy as np
import pytesseract
import math
import Main
import random

import Preprocess
import DetectChars
import PossiblePlate
import PossibleChar

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# modulo para detectar placas ##########################################################################estos numeros se pueden mover segun la placa
PLATE_WIDTH_PADDING_FACTOR = 1.8
PLATE_HEIGHT_PADDING_FACTOR = 1.4

###################################################################################################
def detectPlatesInScene(imgOriginalScene):
    listOfPossiblePlates = []                   # esto regresara un valor

    height, width, numChannels = imgOriginalScene.shape

    imgGrayscaleScene = np.zeros((height, width, 1), np.uint8)
    imgThreshScene = np.zeros((height, width, 1), np.uint8)
    imgContours = np.zeros((height, width, 3), np.uint8)

    cv2.destroyAllWindows()

    if Main.showSteps == True:
        cv2.imshow("0", imgOriginalScene)
    # end if 

    imgGrayscaleScene, imgThreshScene = Preprocess.preprocess(imgOriginalScene)  # obtiene la imagen en escala de grises

    if Main.showSteps == True: 
        cv2.imshow("1a", imgGrayscaleScene)
        cv2.imshow("1b", imgThreshScene)
    # end if 

            # busca cualquier posible caracter,
            # primero busca los contornos y despues incluye
            # los que pueden ser caracter
    listOfPossibleCharsInScene = findPossibleCharsInScene(imgThreshScene)

    if Main.showSteps == True: 
        print("step 2 - len(listOfPossibleCharsInScene) = " + str(
            len(listOfPossibleCharsInScene)))

        imgContours = np.zeros((height, width, 3), np.uint8)

        contours = []

        for possibleChar in listOfPossibleCharsInScene:
            contours.append(possibleChar.contour)
        # end for

        cv2.drawContours(imgContours, contours, -1, Main.SCALAR_WHITE)
        cv2.imshow("2b", imgContours)
    # end if

            # obtiene una lista de posibles caracteres, para despues clasificarla como una posible placa
    listOfListsOfMatchingCharsInScene = DetectChars.findListOfListsOfMatchingChars(listOfPossibleCharsInScene)

    if Main.showSteps == True: 
        print("step 3 - listOfListsOfMatchingCharsInScene.Count = " + str(
            len(listOfListsOfMatchingCharsInScene)))  
        imgContours = np.zeros((height, width, 3), np.uint8)

        for listOfMatchingChars in listOfListsOfMatchingCharsInScene:
            intRandomBlue = random.randint(0, 255)
            intRandomGreen = random.randint(0, 255)
            intRandomRed = random.randint(0, 255)

            contours = []

            for matchingChar in listOfMatchingChars:
                contours.append(matchingChar.contour)
            # end for

            cv2.drawContours(imgContours, contours, -1, (intRandomBlue, intRandomGreen, intRandomRed))
        # end for

        cv2.imshow("3", imgContours)
    # end if 

    for listOfMatchingChars in listOfListsOfMatchingCharsInScene:                   # para cada grupo de caracteres coincidentes
        possiblePlate = extractPlate(imgOriginalScene, listOfMatchingChars)         # intenta extraer la placa

        if possiblePlate.imgPlate is not None:                          # si se encuentra la placa
            listOfPossiblePlates.append(possiblePlate)                  # se añada a una lista de posibles placa
        # end if
    # end for

    print("\n" + str(len(listOfPossiblePlates)) + " possible plates found")  

    if Main.showSteps == True:
        print("\n")
        cv2.imshow("4a", imgContours)

        for i in range(0, len(listOfPossiblePlates)):
            p2fRectPoints = cv2.boxPoints(listOfPossiblePlates[i].rrLocationOfPlateInScene)

            cv2.line(imgContours, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), Main.SCALAR_RED, 2)
            cv2.line(imgContours, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), Main.SCALAR_RED, 2)
            cv2.line(imgContours, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), Main.SCALAR_RED, 2)
            cv2.line(imgContours, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), Main.SCALAR_RED, 2)

            cv2.imshow("4a", imgContours)

            print("possible plate " + str(i) + ", click on any image and press a key to continue . . .")

            cv2.imshow("4b", listOfPossiblePlates[i].imgPlate)
            cv2.waitKey(0)
        # end for

        print("\nplate detection complete, click on any image and press a key to begin char recognition . . .\n")
        cv2.waitKey(0)
    # end if

    return listOfPossiblePlates
# end function

###################################################################################################
def findPossibleCharsInScene(imgThresh):
    listOfPossibleChars = []                # retorna un a valor

    intCountOfPossibleChars = 0

    imgThreshCopy = imgThresh.copy()

    contours, npaHierarchy = cv2.findContours(imgThreshCopy, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)   # busca todos los contornos

    height, width = imgThresh.shape
    imgContours = np.zeros((height, width, 3), np.uint8)

    for i in range(0, len(contours)):                       # para cada contorno

        if Main.showSteps == True: 
            cv2.drawContours(imgContours, contours, i, Main.SCALAR_WHITE)
        # end if

        possibleChar = PossibleChar.PossibleChar(contours[i])

        if DetectChars.checkIfPossibleChar(possibleChar):                  
            intCountOfPossibleChars = intCountOfPossibleChars + 1           
            listOfPossibleChars.append(possibleChar)                       
        # end if
    # end for

    if Main.showSteps == True: 
        print("\nstep 2 - len(contours) = " + str(len(contours)))  
        print("step 2 - intCountOfPossibleChars = " + str(intCountOfPossibleChars))  
        cv2.imshow("2a", imgContours)
    # end if 

    return listOfPossibleChars
# end function


###################################################################################################
def extractPlate(imgOriginal, listOfMatchingChars):
    possiblePlate = PossiblePlate.PossiblePlate()           # retorna un valor

    listOfMatchingChars.sort(key = lambda matchingChar: matchingChar.intCenterX)        # ordenar caracteres de izquierda a derecha según la posición x

            # calcula el punto central de la placa
    fltPlateCenterX = (listOfMatchingChars[0].intCenterX + listOfMatchingChars[len(listOfMatchingChars) - 1].intCenterX) / 2.0
    fltPlateCenterY = (listOfMatchingChars[0].intCenterY + listOfMatchingChars[len(listOfMatchingChars) - 1].intCenterY) / 2.0

    ptPlateCenter = fltPlateCenterX, fltPlateCenterY

            # calcular el ancho y la altura de la placa
    intPlateWidth = int((listOfMatchingChars[len(listOfMatchingChars) - 1].intBoundingRectX + 
    listOfMatchingChars[len(listOfMatchingChars) - 1].intBoundingRectWidth - listOfMatchingChars[0].intBoundingRectX) *
    PLATE_WIDTH_PADDING_FACTOR)

    intTotalOfCharHeights = 0

    for matchingChar in listOfMatchingChars:
        intTotalOfCharHeights = intTotalOfCharHeights + matchingChar.intBoundingRectHeight
    # end for

    fltAverageCharHeight = intTotalOfCharHeights / len(listOfMatchingChars)

    intPlateHeight = int(fltAverageCharHeight * PLATE_HEIGHT_PADDING_FACTOR)

            # calcula el ángulo de corrección del lugar de la placa
    fltOpposite = listOfMatchingChars[len(listOfMatchingChars) - 1].intCenterY - listOfMatchingChars[0].intCenterY
    fltHypotenuse = DetectChars.distanceBetweenChars(listOfMatchingChars[0], listOfMatchingChars[len(listOfMatchingChars) - 1])
    fltCorrectionAngleInRad = math.asin(fltOpposite / fltHypotenuse)
    fltCorrectionAngleInDeg = fltCorrectionAngleInRad * (180.0 / math.pi)

            # MEDIDAS DEPENDIENDO POR EL LUGAR DE LA PLACA ANCHO Y ALTO
    possiblePlate.rrLocationOfPlateInScene = ( tuple(ptPlateCenter), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg )


            # obtener la matriz de rotación para nuestro ángulo de corrección calculado
    rotationMatrix = cv2.getRotationMatrix2D(tuple(ptPlateCenter), fltCorrectionAngleInDeg, 1.0)

    height, width, numChannels = imgOriginal.shape      

    imgRotated = cv2.warpAffine(imgOriginal, rotationMatrix, (width, height))       # rota la imagen

    imgCropped = cv2.getRectSubPix(imgRotated, (intPlateWidth, intPlateHeight), tuple(ptPlateCenter))

    possiblePlate.imgPlate = imgCropped         # copie la imagen de la placa recortada en la variable miembro aplicable de la placa posible

    

    return possiblePlate
# end function












