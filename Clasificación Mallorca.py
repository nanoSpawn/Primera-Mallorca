#!/usr/bin/python3

# Direcciones desde las que cogemos las cosas. La idea es generar un único XML
# Este contendrá primero la clasificación, y luego las 2 jornadas.
# http://resultados.as.com/resultados/futbol/segunda/clasificacion
# http://resultados.as.com/resultados/futbol/segunda/calendario

# Usamos la librería Scrapy 1.2 para coger las Webs y parsearlas.
import re
import scrapy

# Hacemos el script totalmente standalone, sin necesidad de crear el árbol de directorios de Scrapy.
from scrapy.crawler import CrawlerProcess

# Algunas variables globales
xmlFileName = 'clasificacion_jornadas.xml'
tableParams = ''
tableParams = ' xmlns:aid="http://ns.adobe.com/AdobeInDesign/4.0/" aid:table="table" aid:trows="24" aid:tcols="23"'
startTableXML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Root><Clasificacion><Tabla' + tableParams + '>'
endTableXML = '</Tabla></Clasificacion>\n'
cellParams = ''
cellParams = ' aid:table="cell" aid:crows="1" aid:ccols="1"'
cStart = '<Celda' + cellParams + '>'
cEnd = '</Celda>'
# Posiciones donde encontramos los puntos en la tabla de clasificación
points = [0, 7, 14]

#Variables para las jornadas
schedXML = ''
start = '<Jornada>'
end = '</Jornada>\n'

# Jornada a coger. Lo cambiaremos luego cuando procesemos la clasificación.
fixture = 1

# Antes de la clase principal definiremos funciones que necesitamos

# Reemplaza meses cortos por largos, el código no es mío, está sacado de StackOverflow
# http://stackoverflow.com/questions/2400504/easiest-way-to-replace-a-string-using-a-dictionary-of-replacements
def fix_months(text):
    months = {
        'Ene' : 'Enero',
        'Feb' : 'Febrero',
        'Mar' : 'Marzo',
        'Abr' : 'Abril',
        'May' : 'Mayo',
        'Jun' : 'Junio',
        'Jul' : 'Julio',
        'Ago' : 'Agosto',
        'Sep' : 'Septiembre',
        'Oct' : 'Octubre',
        'Nov' : 'Noviembre',
        'Dec' : 'Diciembre',
    }
    
    pattern = re.compile(r'\b(' + '|'.join(months.keys()) + r')\b')
    return pattern.sub(lambda x: months[x.group()], text)


class clasification(scrapy.Spider):
    
    name = 'Clasificación'
    
    #Creamos dos callbacks diferentes para procesar cada página
    def start_requests(self):
        #urls = ['http://www.muntanercomunicacio.com/segundadivision/mockup-clasif.html',
        #        'http://www.muntanercomunicacio.com/segundadivision/mockup-jornadas.html']
        urls = ['http://resultados.as.com/resultados/futbol/segunda/clasificacion',
                'http://resultados.as.com/resultados/futbol/segunda/calendario']
        
        # El atributo "priority" hace estas llamadas "síncronas". Es necesario, dado que
        # el XML he de generarlo secuencialmente, primero una URL, luego la otra.
        yield scrapy.Request(urls[0], callback=self.parseClasif, priority=1)
        yield scrapy.Request(urls[1], callback=self.parseSched)
    
    
    # Función que procesa la clasificación
    def parseClasif(self, page):
        global fixture
        table = page.css('#clasificacion-total .tabla-datos > tbody')
        pointsXML = ''
        
        # Recorremos todas las filas de la tabla, las 22, necesitamos numerarlas
        for pos, row in enumerate(table.css('tr')):
            posString = str(pos+1)
            position = '\n<posicion' + cellParams + '>' + posString + '</posicion>'
            team = cStart + '<nombre>' + row.css('span.nombre-equipo::text').extract_first() + '</nombre>' + cEnd +'\n'
            pointsXML += position+team
            
            vals = row.css('td::text').extract()
            
            # Para cada fila recorremos todos sus valores y los tratamos acordemente
            for index, num in enumerate(vals):
                if index == 1:
                    fixture = num
                    
                if (index == points[0] or index == points[1] or index == points[2] ):
                    pointsXML += cStart + '<pts>' + num + '</pts>' + cEnd
                else:
                    pointsXML += cStart + '<num>' + num + '</num>' + cEnd
            
        with open(xmlFileName, 'w', encoding='utf-8') as xml:
            print('Escribimos la clasificación procesada')
            xml.write(startTableXML + pointsXML + endTableXML)
            
            
    # Función que procesa las jornadas
    def parseSched(self, page):
        # Primero cogemos las jornadas que cribaremos, las dos próximas
        print('Jornada: ', fixture)
        intFixture = int(fixture)
        cf = '#jornada-' + str(intFixture+1)
        nf = '#jornada-' + str(intFixture+2)
        
        # Capturamos ahora todos los divs de jornadas, solo esos, y luego cribamos
        # Imprimimos la longitud para revisar que esté bien, debería ser 42 en 2016
        schedule = page.css('.cont-modulo.resultados')
        print('Número de jornadas: ', len(schedule))
        #currentFixtures = schedule.css(cf)
        #nextFixtures = schedule.css(nf)
        finalFixtures = schedule.css(cf) + schedule.css(nf)
        
        # Empezamos a inicializar el XML
        for fixtures in finalFixtures:
            global schedXML
            schedXML += start
            schedXML += '<fechas>'+fix_months(fixtures.css('span.fecha-evento::text').extract_first())+'</fechas>\n'
            
            matches = fixtures.css('tbody > tr')
            
            for match in matches:
                day = match.css('.resultado::text').extract_first().strip()[:1]
                hour = '<hora>' + match.css('.resultado::text').extract_first().strip()[2:] + '</hora>\n'
                
                if day == 'V':
                    schedXML += '<viernes>' + day + '</viernes>\t'
                elif day == 'S':
                    schedXML += '<sabado>' + day + '</sabado>\t'
                elif day == 'D':
                    schedXML += '<domingo>' + day + '</domingo>\t'
                
                teamhome = match.css('.nombre-equipo::text')[0].extract()
                teamaway = match.css('.nombre-equipo::text')[1].extract()
                
                if teamhome == 'Mallorca' or teamaway == 'Mallorca':
                    schedXML += '<partidoMallorca>' + teamhome + ' - ' + teamaway + '</partidoMallorca>\t'
                else:
                    schedXML += '<partido>' + teamhome + ' - ' + teamaway + '</partido>\t'
                                
                schedXML += hour
            schedXML += end
            
        schedXML += '</Root>'
            
        # Abrimos el archivo en modo append, para escribir después de procesar la clasificación
        # (es por esto que tenemos que hacer las llamadas secuencialmente)
        with open(xmlFileName, 'a', encoding='utf-8') as xml:
            print('Escribimos el archivo. Todo correcto!')
            xml.write(schedXML)

# Funciones necesarias para que este script sea standalone.            
process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
})

process.crawl(clasification)
process.start() # the script will block here until the crawling is finished
    