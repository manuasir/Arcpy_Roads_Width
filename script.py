
# ---------------------------------------------------------------------------
# Medir anchura media de carreteras
# May 2016
# Manuel Jiménez Bernal - Iliberi S.A.
# ---------------------------------------------------------------------------

import sys, string, os, arcgisscripting, cmath

arcpy.env.overwriteOutput = True
gp = arcgisscripting.create()

# Entradas
tempo = r"C:\USERS\NATALIA\DESKTOP\Prueba\tempo.shp"
inputlines = r"C:\USERS\NATALIA\DESKTOP\prueba\eje_prueba_spliteado.shp"

#tempo = r"C:\USERS\NATALIA\DESKTOP\Prueba\MANZANAS_PARALELAS_dissolve.shp"
#inputlines = r"C:\USERS\NATALIA\DESKTOP\prueba\And_ejes_e00.shp"

# Modificar distancia de lineas perpendiculares

distance = 600.0

# Variables globales

arcpy.env.workspace = r"C:\USERS\NATALIA\DESKTOP"
testlinea = r"C:\USERS\NATALIA\DESKTOP\temp\perpendiculares.shp"
testpuntos = r"C:\USERS\NATALIA\DESKTOP\temp\testpuntos.shp"
unipuntos = testpuntos = r"C:\USERS\NATALIA\DESKTOP\temp\unipuntos.shp"
salidapuntos = r"C:\USERS\NATALIA\DESKTOP\temp\puntos_intersect.shp"

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
	# midx = float((startx+endx)/2)
	# midy = float((starty+endy)/2)
	midx = float(mpx)
	midy = float(mpy)

	ptList =[[midx,midy]]
	#if the line is horizontal or vertical the slope and negreciprocal will fail so do this instead.
	
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
        
            #get the slope of the line
		m = ((starty - endy)/(startx - endx))
            
            #get the negative reciprocal, 
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
	salida = {}
	salidacopy = {}
	try:
		cursorpuntos = arcpy.da.SearchCursor(puntos,fields)
		tupla = cursorpuntos.next()
	except:
		print "Error.Pruebe aumentando el rango."
		raise sys.exit("Error")
	
	for tupla in cursorpuntos:
		listatemp = []
		# print "contador dos {}".format(tupla[0])
		indice = tupla[0] 
		valor = tupla[1]
		if indice in salida:
			listatemp=salida[indice]
			listatemp.append(valor)
			salida[indice] = listatemp
			
		else:
			# salida[indice] = valor
			listatemp.append(valor)
			salida[indice] = listatemp
	return salida
	
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
	for key in list(mapa):
		if len(temp[key]) < 2:
			del temp[key]
		elif len(temp[key]) > 2:
			del temp[key][1]
	return temp

def calcularDistancias(x1,y1,x2,y2):

	# x1 = struct[key][0][0]
	# y1 = struct[key][0][1]
	# x2 = struct[key][1][0]
	# y2 = struct[key][1][1]
	temp = math.sqrt( ((x2-x1)**2) + ((y2 - y1)**2))
	return temp
				
def crearLineas(struct):
	point = arcpy.Point()
	array = arcpy.Array()
	featureList = []
	arcpy.CreateFeatureclass_management("C:/USERS/NATALIA/DESKTOP/temp" , "lineasbuenas.shp", "POLYLINE")
	arcpy.AddField_management(r"C:/USERS/NATALIA/DESKTOP/temp/lineasbuenas.shp", "Distancia", "LONG", 9)
	cursor = arcpy.InsertCursor(r"C:\USERS\NATALIA\DESKTOP\temp\lineasbuenas.shp")
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
		# Create a Polyline object based on the array of points
		polyline = arcpy.Polyline(array)
		# Clear the array for future use
		array.removeAll()
		# Append to the list of Polyline objects
		featureList.append(polyline)
		# Insert the feature
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
arcpy.Delete_management(testlinea)
arcpy.Delete_management(salidapuntos)
conjunto = intersectar(unipuntos)
fin = filtrarResultados(conjunto)
salida = crearLineas(fin)
arcpy.Delete_management(testpuntos)
del gp