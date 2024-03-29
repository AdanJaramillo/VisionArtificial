#Dependencias 
import os

import cv2
import numpy as np
import pytesseract
import math
import random

import Main
import Preprocess
import PossibleChar

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# variables de nivel de módulo **********************************************************************

kNearest = cv2.ml.KNearest_create()

        # constantes esto verifica solo un posible carácter (no se compara con otro carácter)
MIN_PIXEL_WIDTH = 2
MIN_PIXEL_HEIGHT = 8

MIN_ASPECT_RATIO = 0.25
MAX_ASPECT_RATIO = 1.0

MIN_PIXEL_AREA = 80

        # constantes para comparar dos caracteres
MIN_DIAG_SIZE_MULTIPLE_AWAY = 0.3
MAX_DIAG_SIZE_MULTIPLE_AWAY = 5.0

MAX_CHANGE_IN_AREA = 0.5

MAX_CHANGE_IN_WIDTH = 0.8
MAX_CHANGE_IN_HEIGHT = 0.2

MAX_ANGLE_BETWEEN_CHARS = 12.0

        # otras constantes
MIN_NUMBER_OF_MATCHING_CHARS = 3

RESIZED_CHAR_IMAGE_WIDTH = 20
RESIZED_CHAR_IMAGE_HEIGHT = 30

MIN_CONTOUR_AREA = 100

###################################################################################################
def loadKNNDataAndTrainKNN():
    allContoursWithData = []                # declarar listas vacías,
    validContoursWithData = []              # los llenaremos en breve

    try:
        npaClassifications = np.loadtxt("classifications.txt", np.float32)                  # leer en clasificaciones de entrenamiento
    except:                                                                                 # si el archivo no se pudo abrir
        print("error, no se puede abrir clasificaciones.txt, saliendo del programa\n")  # mostrar mensaje de error
        os.system("pause")
        return False                                                                        # Y devolver Falso
    # Fin del try

    try:
        npaFlattenedImages = np.loadtxt("flattened_images.txt", np.float32)                 # leer en imágenes de entrenamiento
    except:                                                                                 # si el archivo no se pudo abrir
        print("error, no se puede abrir flattened_images.txt, saliendo del programa\n")  # mostrar mensaje de error
        os.system("pause")
        return False                                                                        # Y devolver Falso
    # Fin del try

    npaClassifications = npaClassifications.reshape((npaClassifications.size, 1))      # remodelar matriz numpy a 1d, necesario pasar para llamar a entrenar

    kNearest.setDefaultK(1)                                                             # establece K por defecto en 1

    kNearest.train(npaFlattenedImages, cv2.ml.ROW_SAMPLE, npaClassifications)           # entrenar objeto KNN

    return True                             # si llegamos aquí el entrenamiento fue exitoso, así que regrese verdadero
# Fin de function

###################################################################################################
def detectCharsInPlates(listOfPossiblePlates):
    intPlateCounter = 0
    imgContours = None
    contours = []

    if len(listOfPossiblePlates) == 0:          # si la lista de posibles platos está vacía
        return listOfPossiblePlates             # regreso
    # Fin de if

            # en este punto podemos estar seguros de que la lista de posibles placas tiene al menos una placa

    for possiblePlate in listOfPossiblePlates:          # para cada placa posible, este es un gran bucle for que ocupa la mayor parte de la función

        possiblePlate.imgGrayscale, possiblePlate.imgThresh = Preprocess.preprocess(possiblePlate.imgPlate)     # preproceso para obtener imágenes en escala de grises y umbral

        if Main.showSteps == True: # mostrar pasos ###################################################
            cv2.imshow("5a", possiblePlate.imgPlate)
            cv2.imshow("5b", possiblePlate.imgGrayscale)
            cv2.imshow("5c", possiblePlate.imgThresh)
        # Fin de if # mostrar pasos #####################################################################

                # Aumentar el tamaño de la imagen de la placa para facilitar la visualización y la detección del caracter
        possiblePlate.imgThresh = cv2.resize(possiblePlate.imgThresh, (0, 0), fx = 1.6, fy = 1.6)

                # umbral nuevamente para eliminar cualquier área gris
        thresholdValue, possiblePlate.imgThresh = cv2.threshold(possiblePlate.imgThresh, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        if Main.showSteps == True: # mostar pasos ###################################################
            cv2.imshow("5d", possiblePlate.imgThresh)
        # fin if # mostrar pasos #####################################################################

                # encuentra todos los caracteres posibles en la placa,
                # esta función primero encuentra todos los contornos, luego solo incluye los contornos que podrían ser caracteres (sin comparación con otros caracteres aún)
        listOfPossibleCharsInPlate = findPossibleCharsInPlate(possiblePlate.imgGrayscale, possiblePlate.imgThresh)

        if Main.showSteps == True: # mostrar pasos ###################################################
            height, width, numChannels = possiblePlate.imgPlate.shape
            imgContours = np.zeros((height, width, 3), np.uint8)
            del contours[:]                                         # borrar la lista de contornos

            for possibleChar in listOfPossibleCharsInPlate:
                contours.append(possibleChar.contour)
            # fin for

            cv2.drawContours(imgContours, contours, -1, Main.SCALAR_WHITE)

            cv2.imshow("6", imgContours)
        # finaliza if # muestra los pasos ############################################ #########################

               # dada una lista de todos los caracteres posibles, encuentre grupos de caracteres coincidentes dentro de la placa
        listOfListsOfMatchingCharsInPlate = findListOfListsOfMatchingChars(listOfPossibleCharsInPlate)

        if Main.showSteps == True: # mostrar pasos ###################################################
            imgContours = np.zeros((height, width, 3), np.uint8)
            del contours[:]

            for listOfMatchingChars in listOfListsOfMatchingCharsInPlate:
                intRandomBlue = random.randint(0, 255)
                intRandomGreen = random.randint(0, 255)
                intRandomRed = random.randint(0, 255)

                for matchingChar in listOfMatchingChars:
                    contours.append(matchingChar.contour)
                # fin for
                cv2.drawContours(imgContours, contours, -1, (intRandomBlue, intRandomGreen, intRandomRed))
            # fin for
            cv2.imshow("7", imgContours)
        # fin if # mostar pasos #####################################################################

        if (len(listOfListsOfMatchingCharsInPlate) == 0):			# if (no se encontraron grupos de caracteres coincidentes en la placa)
            if Main.showSteps == True: # mostar pasos  ###############################################
                print("chars found in plate number " + str(
                    intPlateCounter) + " = (none), click on any image and press a key to continue . . .")
                intPlateCounter = intPlateCounter + 1
                cv2.destroyWindow("8")
                cv2.destroyWindow("9")
                cv2.destroyWindow("10")
                cv2.waitKey(0)
            # fin if # mostar pasos #################################################################

            possiblePlate.strChars = ""
            continue						# volver al principio del bucle
        # fin if

        for i in range(0, len(listOfListsOfMatchingCharsInPlate)):                              # dentro de cada lista de caracteres coincidentes
            listOfListsOfMatchingCharsInPlate[i].sort(key = lambda matchingChar: matchingChar.intCenterX)        # ordenar caracteres de izquierda a derecha
            listOfListsOfMatchingCharsInPlate[i] = removeInnerOverlappingChars(listOfListsOfMatchingCharsInPlate[i])              # y eliminar caracteres superpuestos internos
        # fin for

        if Main.showSteps == True: # mostar pasos ###################################################
            imgContours = np.zeros((height, width, 3), np.uint8)

            for listOfMatchingChars in listOfListsOfMatchingCharsInPlate:
                intRandomBlue = random.randint(0, 255)
                intRandomGreen = random.randint(0, 255)
                intRandomRed = random.randint(0, 255)

                del contours[:]

                for matchingChar in listOfMatchingChars:
                    contours.append(matchingChar.contour)
                # fin for

                cv2.drawContours(imgContours, contours, -1, (intRandomBlue, intRandomGreen, intRandomRed))
            # fin for
            cv2.imshow("8", imgContours)
        # fin if # ver pasos #####################################################################

                # dentro de cada placa posible, supongamos que la lista más larga de caracteres coincidentes potenciales es la lista real de caracteres
        intLenOfLongestListOfChars = 0
        intIndexOfLongestListOfChars = 0

                # recorrer todos los vectores de caracteres coincidentes, obtener el índice del que tiene más caracteres
        for i in range(0, len(listOfListsOfMatchingCharsInPlate)):
            if len(listOfListsOfMatchingCharsInPlate[i]) > intLenOfLongestListOfChars:
                intLenOfLongestListOfChars = len(listOfListsOfMatchingCharsInPlate[i])
                intIndexOfLongestListOfChars = i
            # fin if
        # fin for

                # supongamos que la lista más larga de caracteres coincidentes dentro de la placa es la lista real de caracteres
        longestListOfMatchingCharsInPlate = listOfListsOfMatchingCharsInPlate[intIndexOfLongestListOfChars]

        if Main.showSteps == True: # ver pasos ###################################################
            imgContours = np.zeros((height, width, 3), np.uint8)
            del contours[:]

            for matchingChar in longestListOfMatchingCharsInPlate:
                contours.append(matchingChar.contour)
            # fin for

            cv2.drawContours(imgContours, contours, -1, Main.SCALAR_WHITE)

            cv2.imshow("9", imgContours)
        # fin if # ver pasos #####################################################################

        possiblePlate.strChars = recognizeCharsInPlate(possiblePlate.imgThresh, longestListOfMatchingCharsInPlate)

        if Main.showSteps == True: # ver pasos ###################################################
            print("caracteres encontrados en el número de placa " + str(
                intPlateCounter) + " = " + possiblePlate.strChars + ", haga clic en cualquier imagen y presione una tecla para continuar . . .")
            intPlateCounter = intPlateCounter + 1
            cv2.waitKey(0)
        # fin if # ver pasos #####################################################################

    # Fin del bucle for grande que ocupa la mayor parte de la función

    if Main.showSteps == True:
        print("\nchar detección completa, haga clic en cualquier imagen y presione una tecla para continuar . . .\n")
        cv2.waitKey(0)
    # fin if

    return listOfPossiblePlates
# fin de funcion

###################################################################################################
def findPossibleCharsInPlate(imgGrayscale, imgThresh):
    listOfPossibleChars = []                        # este será el valor de retorno
    contours = []
    imgThreshCopy = imgThresh.copy()

            # encontrar todos los contornos en placa
    contours, npaHierarchy = cv2.findContours(imgThreshCopy, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:                        # for (cada contorno)
        possibleChar = PossibleChar.PossibleChar(contour)

        if checkIfPossibleChar(possibleChar):              # Si el contorno es un posible carácter, tenga en cuenta que esto no se compara con otros caracteres (todavía). . .
            listOfPossibleChars.append(possibleChar)       # agregar a la lista de posibles caracteres
        # fin if
    # fin for

    return listOfPossibleChars
# fin de funcion

###################################################################################################
def checkIfPossibleChar(possibleChar):
            # esta función es un "primer paso" que realiza una verificación aproximada de un contorno para ver si podría ser un char,
            # tenga en cuenta que (todavía) no estamos comparando el carácter con otros caracteres para buscar un grupo
    if (possibleChar.intBoundingRectArea > MIN_PIXEL_AREA and
        possibleChar.intBoundingRectWidth > MIN_PIXEL_WIDTH and possibleChar.intBoundingRectHeight > MIN_PIXEL_HEIGHT and
        MIN_ASPECT_RATIO < possibleChar.fltAspectRatio and possibleChar.fltAspectRatio < MAX_ASPECT_RATIO):
        return True
    else:
        return False
    # fin if
# fin de funcion

###################################################################################################
def findListOfListsOfMatchingChars(listOfPossibleChars):
            # Con esta función, comenzamos con todos los caracteres posibles en una gran lista
            # El propósito de esta función es reorganizar la gran lista de caracteres en una lista de listas de caracteres coincidentes,
            # tenga en cuenta que los caracteres que no se encuentran en un grupo de coincidencias no necesitan considerarse más
    listOfListsOfMatchingChars = []                  # este será el valor de retorno

    for possibleChar in listOfPossibleChars:                        # for cada posible personaje en la gran lista de caracteres
        listOfMatchingChars = findListOfMatchingChars(possibleChar, listOfPossibleChars)        # encuentra todos los caracteres en la lista grande que coinciden con el carácter actual

        listOfMatchingChars.append(possibleChar)                # también agregue el carácter actual a la lista actual posible de caracteres coincidentes

        if len(listOfMatchingChars) < MIN_NUMBER_OF_MATCHING_CHARS:     # if La lista actual posible de caracteres coincidentes no es lo suficientemente larga como para constituir una placa posible
            continue                            # Vuelva a la parte superior del bucle for y vuelva a intentarlo con el siguiente carácter, tenga en cuenta que no es necesario
                                                # guardar la lista de ninguna manera ya que no tenía suficientes caracteres para ser una placa posible
        # end if

                                                # si llegamos aquí, la lista actual pasó la prueba como un "grupo" o "grupo" de caracteres coincidentes
        listOfListsOfMatchingChars.append(listOfMatchingChars)      # así que agregue a nuestra lista de listas de caracteres coincidentes

        listOfPossibleCharsWithCurrentMatchesRemoved = []

                                                # eliminar la lista actual de caracteres coincidentes de la lista grande para que no usemos esos mismos caracteres dos veces,
                                                # asegúrese de hacer una nueva lista grande para esto ya que no queremos cambiar la lista grande original
        listOfPossibleCharsWithCurrentMatchesRemoved = list(set(listOfPossibleChars) - set(listOfMatchingChars))

        recursiveListOfListsOfMatchingChars = findListOfListsOfMatchingChars(listOfPossibleCharsWithCurrentMatchesRemoved)      # llamada recursiva

        for recursiveListOfMatchingChars in recursiveListOfListsOfMatchingChars:        # para cada lista de caracteres coincidentes encontrados por llamada recursiva
            listOfListsOfMatchingChars.append(recursiveListOfMatchingChars)             # agregar a nuestra lista original de listas de caracteres coincidentes
        # end for

        break       # exit for

    # end for

    return listOfListsOfMatchingChars
# end function

###################################################################################################
def findListOfMatchingChars(possibleChar, listOfChars):
            #El propósito de esta función es, dado un posible carácter y una gran lista de posibles caracteres,
            # encuentre todos los caracteres en la lista grande que coincidan con el carácter único posible y devuelva los caracteres coincidentes como una lista
    listOfMatchingChars = []                # este será el valor de retorno
    for possibleMatchingChar in listOfChars:                # for cada personaje en la lista grande
        if possibleMatchingChar == possibleChar:    # if el carácter para el que intentamos encontrar coincidencias es exactamente el mismo carácter que el carácter en la lista grande que estamos verificando actualmente
                                                    # entonces no deberíamos incluirlo en la lista de coincidencias b / c que terminarían siendo dobles, incluido el carácter actual
            continue                                # así que no agregue a la lista de coincidencias y salte al principio del ciclo for
        # fin if
                    # calcular cosas para ver si los caracteres son compatibles
        fltDistanceBetweenChars = distanceBetweenChars(possibleChar, possibleMatchingChar)

        fltAngleBetweenChars = angleBetweenChars(possibleChar, possibleMatchingChar)

        fltChangeInArea = float(abs(possibleMatchingChar.intBoundingRectArea - possibleChar.intBoundingRectArea)) / float(possibleChar.intBoundingRectArea)

        fltChangeInWidth = float(abs(possibleMatchingChar.intBoundingRectWidth - possibleChar.intBoundingRectWidth)) / float(possibleChar.intBoundingRectWidth)
        fltChangeInHeight = float(abs(possibleMatchingChar.intBoundingRectHeight - possibleChar.intBoundingRectHeight)) / float(possibleChar.intBoundingRectHeight)

                # comprobar si los caracteres coinciden
        if (fltDistanceBetweenChars < (possibleChar.fltDiagonalSize * MAX_DIAG_SIZE_MULTIPLE_AWAY) and
            fltAngleBetweenChars < MAX_ANGLE_BETWEEN_CHARS and
            fltChangeInArea < MAX_CHANGE_IN_AREA and
            fltChangeInWidth < MAX_CHANGE_IN_WIDTH and
            fltChangeInHeight < MAX_CHANGE_IN_HEIGHT):

            listOfMatchingChars.append(possibleMatchingChar)        # si los caracteres coinciden, agregue el carácter actual a la lista de caracteres coincidentes
        # fin if
    # fin for

    return listOfMatchingChars                  # Devolver el resultado
# fin de funcion 

###################################################################################################
# use el teorema de Pitágoras para calcular la distancia entre dos caracteres
def distanceBetweenChars(firstChar, secondChar):
    intX = abs(firstChar.intCenterX - secondChar.intCenterX)
    intY = abs(firstChar.intCenterY - secondChar.intCenterY)

    return math.sqrt((intX ** 2) + (intY ** 2))
# fin de funcion

###################################################################################################
# usar trigonometría básica (SOH CAH TOA) para calcular el ángulo entre caracteres
def angleBetweenChars(firstChar, secondChar):
    fltAdj = float(abs(firstChar.intCenterX - secondChar.intCenterX))
    fltOpp = float(abs(firstChar.intCenterY - secondChar.intCenterY))

    if fltAdj != 0.0:                          
        fltAngleInRad = math.atan(fltOpp / fltAdj)    
    else:
        fltAngleInRad = 1.5708                         
    # fim if

    fltAngleInDeg = fltAngleInRad * (180.0 / math.pi)       

    return fltAngleInDeg
# fin de funcion 

###################################################################################################
#si tenemos dos caracteres superpuestos o cerca uno del otro para posiblemente ser caracteres separados, elimine el carácter interno (más pequeño),
# esto es para evitar incluir el mismo carácter dos veces si se encuentran dos contornos para el mismo carácter,
# por ejemplo, para la letra 'O', tanto el anillo interno como el anillo externo se pueden encontrar como contornos, pero solo debemos incluir el carácter una vez
def removeInnerOverlappingChars(listOfMatchingChars):
    listOfMatchingCharsWithInnerCharRemoved = list(listOfMatchingChars)                # este será el valor de retorno

    for currentChar in listOfMatchingChars:
        for otherChar in listOfMatchingChars:
            if currentChar != otherChar:        # if los caracteres actuales y otros caracteres no son el mismo carácter . . .
                                                                            # if los caracteres actuales y otros caracteres tienen puntos centrales en casi la misma ubicación . . .
                if distanceBetweenChars(currentChar, otherChar) < (currentChar.fltDiagonalSize * MIN_DIAG_SIZE_MULTIPLE_AWAY):
                                # if entramos aquí hemos encontrado caracteres superpuestos
                                # a continuación identificamos qué carácter es más pequeño, luego, si ese carácter aún no se eliminó en un pase anterior, elimínelo
                    if currentChar.intBoundingRectArea < otherChar.intBoundingRectArea:         # if char actual es más pequeño que otro char
                        if currentChar in listOfMatchingCharsWithInnerCharRemoved:              # if el carácter actual no se eliminó en un pase anterior . . .
                            listOfMatchingCharsWithInnerCharRemoved.remove(currentChar)         # luego elimine el carácter actual
                        # fin if
                    else:                                                                       # else if otro carácter es más pequeño que el carácter actual
                        if otherChar in listOfMatchingCharsWithInnerCharRemoved:                # si no se eliminó otro carácter en un pase anterior . . .
                            listOfMatchingCharsWithInnerCharRemoved.remove(otherChar)           # luego quite otro char
                        # fin if
                    # fin if
                # fin if
            # fin if
        # fin for
    # fin  for
    return listOfMatchingCharsWithInnerCharRemoved
# fin de funcion
#***********************************************************************
# aquí es donde aplicamos el reconocimiento de char real
def recognizeCharsInPlate(imgThresh, listOfMatchingChars):
    strChars = ""               # este será el valor de retorno, los caracteres en la placa lic

    height, width = imgThresh.shape

    imgThreshColor = np.zeros((height, width, 3), np.uint8)

    listOfMatchingChars.sort(key = lambda matchingChar: matchingChar.intCenterX)        # ordenar caracteres de izquierda a derecha

    cv2.cvtColor(imgThresh, cv2.COLOR_GRAY2BGR, imgThreshColor)                     # haga una versión en color de la imagen de umbral para que podamos dibujar contornos en color en ella

    for currentChar in listOfMatchingChars:                                         # for (cada char en placa)
        pt1 = (currentChar.intBoundingRectX, currentChar.intBoundingRectY)
        pt2 = ((currentChar.intBoundingRectX + currentChar.intBoundingRectWidth), (currentChar.intBoundingRectY + currentChar.intBoundingRectHeight))

        cv2.rectangle(imgThreshColor, pt1, pt2, Main.SCALAR_GREEN, 2)           # dibuja un cuadro verde alrededor del carbón

                # recortar la imagen fuera del umbral
        imgROI = imgThresh[currentChar.intBoundingRectY : currentChar.intBoundingRectY + currentChar.intBoundingRectHeight,
                           currentChar.intBoundingRectX : currentChar.intBoundingRectX + currentChar.intBoundingRectWidth]

        imgROIResized = cv2.resize(imgROI, (RESIZED_CHAR_IMAGE_WIDTH, RESIZED_CHAR_IMAGE_HEIGHT))           # cambiar el tamaño de la imagen, esto es necesario para el reconocimiento de caracteres

        npaROIResized = imgROIResized.reshape((1, RESIZED_CHAR_IMAGE_WIDTH * RESIZED_CHAR_IMAGE_HEIGHT))        # aplanar la imagen en una matriz numpy 1d

        npaROIResized = np.float32(npaROIResized)               # convertir de 1d numpy array de ints a 1d numpy array de flotadores

        retval, npaResults, neigh_resp, dists = kNearest.findNearest(npaROIResized, k = 1)              # finalmente podemos llamar a findNearest !!!

        strCurrentChar = str(chr(int(npaResults[0][0])))            # obtener carácter de los resultados

        strChars = strChars + strCurrentChar                        # agregar char actual a la cadena completa

    # fin de for

    if Main.showSteps == True: # mostrar pasos 
        cv2.imshow("10", imgThreshColor)
    # fin de if # mostrar pasos 

    return strChars
# fin de funcion

