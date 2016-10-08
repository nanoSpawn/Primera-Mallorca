# Direcciones desde las que cogemos las cosas. La idea es generar un único XML
# http://resultados.as.com/resultados/futbol/segunda/clasificacion
# http://resultados.as.com/resultados/futbol/segunda/calendario

# Usamos la librería Scrapy para coger las Webs y parsearlas.
import scrapy

# Algunas variables globales
startTableXML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Root><Clasificacion><Tabla>'
endTableXML = '</Tabla></Clasificacion>'
#cellParams = ' aid:table="cell" aid:crows="1" aid:ccols="1"'
cellParams = ''
cStart = '<Celda' + cellParams + '>'
cEnd = '</Celda>'
# Posiciones donde encontramos los puntos en la tabla de clasificación
points = [0, 7, 14]

#current fixture to grab
fixture = 1


class clasification(scrapy.Spider):
    
    name = 'Clasificación'
    clasif = ''
    
    #start_urls = ['http://resultados.as.com/resultados/futbol/segunda/clasificacion',
    #              'http://resultados.as.com/resultados/futbol/segunda/calendario/']
    
    #Creamos dos callbacks diferentes para procesar cada página
    def start_requests(self):
        urls = ['http://www.muntanercomunicacio.com/segundadivision/mockup-clasif.html',
                'http://www.muntanercomunicacio.com/segundadivision/mockup-jornadas.html']
        
        yield scrapy.Request(urls[0], callback=self.parseClasif, priority=1)
        yield scrapy.Request(urls[1], callback=self.parseSched)
    
    
    def parseClasif(self, page):
        global fixture
        table = page.css('#clasificacion-total .tabla-datos > tbody')
        pointsXML = ''
        clasif = ''
        
        for pos, row in enumerate(table.css('tr')):
            posString = str(pos+1)
            position = '\n<posicion>' + posString + '</posicion>'
            team = '<nombre>' + row.css('span.nombre-equipo::text').extract_first() + '</nombre>\n'
            pointsXML += position+team
            
            vals = row.css('td::text').extract()
            
            for index, num in enumerate(vals):
                if index == 1:
                    fixture = num
                    
                if (index == points[0] or index == points[1] or index == points[2] ):
                    pointsXML += cStart + '<pts>' + num + '</pts>' + cEnd
                else:
                    pointsXML += cStart + '<num>' + num + '</num>' + cEnd
            
        clasif = startTableXML + pointsXML + endTableXML
            
        with open('xml.xml', 'w', encoding='utf-8') as xml:
            xml.write(clasif)
    
    def parseSched(self, page):
        print('Jornada: '+ str(fixture))
        schedule = page.css('.cont-modulo.resultados')
        with open('xml.xml', 'a', encoding='utf-8') as xml:
            xml.write('ESTO DEBE IR DESPUES DE LA TABLA')
            
    