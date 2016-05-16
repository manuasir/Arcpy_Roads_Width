
# ---------------------------------------------------------------------------
# Medir anchura media de carreteras
# May 2016
# Manuel Jiménez Bernal - Iliberi S.A.
# ---------------------------------------------------------------------------

import sys, string, os, arcgisscripting, cmath

arcpy.env.overwriteOutput = True
gp = arcgisscripting.create()

# Entradas:
# Modificar rutas
# tempo: ruta de capa de polígonos (POLYGON)
# inputlines: ruta de capa de líneas (POLYLINE)

tempo = ''
inputlines = ''

# Modificar distancia de lineas perpendiculares

distance = 20

# Variables globales

arcpy.env.workspace = r"C:\.."
testlinea = r"C:\..\perpendiculares.shp"
testpuntos = r"C:\..\testpuntos.shp"
unipuntos = r"C:\..\unipuntos.shp"
salidapuntos = r"C:\..\puntos_intersect.shp"

if arcpy.Exists(testlinea):
	arcpy.Delete_management(testlinea)
if arcpy.Exists(testpuntos):
	arcpy.Delete_management(testpuntos)
if arcpy.Exists(salidapuntos):
	arcpy.Delete_management(salidapuntos)
if arcpy.Exists(unipuntos):
	arcpy.Delete_management(unipuntos)

def crearPerpendicular(feat):
	fpx = feat.positionAlongLine(0.0,True).firstPoint.X
	fpy = feat.positionAlongLine(0.0,True).firstPoint.Y
	lpx = feat.positionAlongLine(1.0,True).firstPoint.X
	lpy = feat.positionAlongLine(1.0,True).firstPoint.Y
	mpx = feat.positionAlongLine(0.5,True).firstPoint.X
	mpy = feat.positionAlongLine(0.5,True).firstPoint.Y
	startx = float(lpx)
	starty = float(lpy)
	endx = float(fpx)
	endy = float(fpy)
	midx = float(mpx)
	midy = float(mpy)

	ptList =[[midx,midy]]
	#Si la linea es horizontal o vertical, se aplica la siguiente operacion:
	
	if starty==endy or startx==endx:
		if starty == endy:
			y1 = midy + distance
			y2 = midy - distance
			x1 = midx
			x2 = midx
    
		if startx == endx:
			y1 = midy
			y2 = midy 
			x1 = midx + distance
			x2 = midx - distance
            
	else:
        
            #obtener la inclinación de la linea
		m = ((starty - endy)/(startx - endx))
            
            #obtener el negativo reciproco
		negativereciprocal = -1*((startx - endx)/(starty - endy))
            
		if m > 0:

			if m >= 1:
				y1 = negativereciprocal*(distance)+ midy
				y2 = negativereciprocal*(-distance) + midy
				x1 = midx + distance
				x2 = midx - distance

			if m < 1:
				y1 = midy + distance
				y2 = midy - distance
				x1 = (distance/negativereciprocal) + midx
				x2 = (-distance/negativereciprocal)+ midx
                    
		if m < 0:
			if m >= -1:
				y1 = midy + distance
				y2 = midy - distance
				x1 = (distance/negativereciprocal) + midx
				x2 = (-distance/negativereciprocal)+ midx		
			if m < -1:
				y1 = negativereciprocal*(distance)+ midy
				y2 = negativereciprocal*(-distance) + midy
				x1 = midx + distance
				x2 = midx - distance
				
	coords = [(x1, y1), (x2, y2)]
	return coords
	
def intersectar(puntos):

	fields = ['FID_perpen','SHAPE@XY']
	campos = ['FID','SHAPE@XY', 'SHAPE@']
	salida = {}
	centros = {}
	salidacopy = {}
	try:
		cursorpuntos = arcpy.da.SearchCursor(puntos,fields)
		cursorperpendiculares = arcpy.da.SearchCursor(inputlines,campos)
		tupla = cursorpuntos.next()
	except:
		print "Error.Pruebe aumentando el rango."
		raise sys.exit("Error")
	
	for linea in cursorperpendiculares:
		indice = linea[0]
		x = linea[2]
		fpx = x.positionAlongLine(0.5,True).firstPoint.X
		fpy = x.positionAlongLine(0.5,True).firstPoint.Y		
		centros[indice] = [fpx,fpy]

	
	for tupla in cursorpuntos:
		listatemp = []
		indice = tupla[0] 
		valor = tupla[1]
		if indice in salida:
			listatemp=salida[indice]
			listatemp.append(valor)
			salida[indice] = listatemp	
		else:
			listatemp.append(valor)
			salida[indice] = listatemp
		
	resul = filtrarResultados(salida)
	
	for key in resul.keys():
		if (((resul[key][0][0] > centros[key][0] and resul[key][1][0] > centros[key][0]) or (resul[key][0][0] < centros[key][0] and resul[key][1][0] < centros[key][0])) or ((resul[key][0][1] > centros[key][1] and resul[key][1][1] > centros[key][1]) or (resul[key][0][1] < centros[key][1] and resul[key][1][1] < centros[key][1]))):
			del resul[key]
			
			
	return resul
	
def generaCapaPerpendicular(inputlines):
	polilineas = []
	rows = gp.SearchCursor(inputlines)
	row = rows.Next()
		#Rellena array de perpendiculares
	while row:
		# Crear el objeto con la geometría
		feat = row.Shape
		coords = crearPerpendicular(feat)
		ar = arcpy.Array()
		for x, y in coords:
			ar.add(arcpy.Point(x, y))
		polyline = arcpy.Polyline(ar)
		polilineas.append(polyline)
		row = rows.Next()
		
	del row
	del rows
	return polilineas

def filtrarResultados(mapa):
	temp = {}
	temp = mapa
	puntosMedios = {}
	for key in list(mapa):
		if len(temp[key]) < 2 or len(temp[key]) > 2:
			del temp[key]			
	return temp

def calcularDistancias(x1,y1,x2,y2):
	temp = math.sqrt( ((x2-x1)**2) + ((y2 - y1)**2))
	return temp
				
def crearLineas(struct):
	point = arcpy.Point()
	array = arcpy.Array()
	featureList = []
	nombreSalida = inputlines + "_perpendiculares.shp"
	rutaSalida = "C:/USERS/NATALIA/DESKTOP/temp/"+nombreSalida
	arcpy.CreateFeatureclass_management("C:/USERS/NATALIA/DESKTOP/temp" , nombreSalida, "POLYLINE")
	arcpy.AddField_management(r"C:/USERS/NATALIA/DESKTOP/temp/"+nombreSalida, "Distancia", "LONG", 9)
	cursor = arcpy.InsertCursor(rutaSalida)
	feat = cursor.newRow()
	# cur = arcpy.UpdateCursor(r)
	for key in list(struct):
		# Set X and Y for start and end points
		point.X = struct[key][0][0]
		point.Y = struct[key][0][1]
		array.add(point)
		point.X = struct[key][1][0]
		point.Y = struct[key][1][1]
		
		array.add(point)   
		distancia = calcularDistancias(struct[key][0][0],struct[key][0][1],struct[key][1][0],struct[key][1][1])
		# Crear objeto polilinea a partir de un array
		polyline = arcpy.Polyline(array)
		# Limpiar array
		array.removeAll()
		# Añadir a la lista de figuras
		featureList.append(polyline)
		# Insertar propiedades
		feat.shape = polyline
		feat.setValue('Id',key)
		feat.setValue('Distancia',distancia)
		cursor.insertRow(feat)
	del feat
	del cursor

nuevasLineas = generaCapaPerpendicular(inputlines)
arcpy.CopyFeatures_management(nuevasLineas, testlinea)

try:
	arcpy.Intersect_analysis ([testlinea, tempo], salidapuntos , "ALL", "", "point")
except:
	print "aumentar rango"

arcpy.MultipartToSinglepart_management(salidapuntos,unipuntos)

if arcpy.Exists(salidapuntos):
	arcpy.Delete_management(salidapuntos)
conjunto = intersectar(unipuntos)
salida = crearLineas(conjunto)
if arcpy.Exists(testpuntos):
	arcpy.Delete_management(testpuntos)
if arcpy.Exists(unipuntos):
	arcpy.Delete_management(unipuntos)
if arcpy.Exists(testlinea):
	arcpy.Delete_management(testlinea)
del gp
