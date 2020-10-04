import requests as req
import json
import time
import csv  
import json  
from datetime import datetime, timedelta
  
class WifiMonitor:

    MINUTOS_OUT_HOME = 60
    MINUTOS_RANGO = 30

    dispositivos_conocidos = [] # Guarda las macs conocidas
    dispositivos_semiconocidos = [] # Guarda las macs semiconocidas
    detectiones = [] # Detecciones agrupadas por rangos
    ultimo_leido = 0
    fecha_hoy = 0

    # Contine todas las detecciones de macs
    registros = {
        "mac": [], # Lista de macs
        "registro":{}, # Cada deteccion
        "count":0 # Cuenta total de detecciones
    }

    def __init__(self):
        if(len(self.dispositivos_conocidos) == 0):
            self.inicializa_datos_conocidos() # Registro de macs conocidas
        if(len(self.dispositivos_semiconocidos) == 0):
            self.inicializa_datos_desconocidos() # Registro de macs semiconocidas
        ##self.carga_datos("2020-02-24") # Carga de datos del fichero
        ##self.procesa_datos() # Procesa las detecciones agrupadas por mac y rangos de tiempo
        #print(self.detectiones)
    
    # Recarga los datos del fichero y los procesa
    def reload(self):
        self.carga_datos("2020-02-24") # Carga de datos del fichero
        self.procesa_datos() # Procesa las detecciones agrupadas por mac y rangos de tiempo

    # Recarga los datos del fichero y lee unicamente los nuevos
    def reload_live(self, day, primero):
        # Abrir un CSV
        f = open( '/home/pi/Servidores/datoswifi/datos_' + day + '.csv', 'r' )
        # Lee archivo por columnas
        reader = csv.DictReader( f, fieldnames = ("fecha","mota","mac","rssi","canal"))  
        # Parece CSV a json
        data_list = list()
        x = 0 # Indice lineas leidas
        for row in reader:
            if(x > primero): # Si es una nueva deteccion
                data_list.append(row)
            x += 1

        return json.loads(json.dumps( data_list ) )

    def get_detections_by_mac(self, mac):
        for d in self.detectiones:
            if d["mac"].startswith(mac):
                f = d["fecha_ini"]
                fn = d["fecha_fin"]
                print(d)
                print(datetime.fromtimestamp(int(f)).isoformat())
                print(datetime.fromtimestamp(int(fn)).isoformat())
                print("------------------------------------------------------------------")

    # Las fechas se puede no hacer al introducir ultimo leido. 
    # Devuelve los dispositivos detectados
    def get_in_home_now(self):
        reconectados = [] # Dispositivos que se han vuelto a conectar
        nuevos_conectados = [] # Nuevos dispositivos
        if(self.fecha_hoy != datetime.today().strftime('%Y-%m-%d')):
            self.fecha_hoy = datetime.today().strftime('%Y-%m-%d')
            self.ultimo_leido = 0
        # Compara mac y la ultima hora de deteccion
        for d in self.reload_live(self.fecha_hoy, self.ultimo_leido):
            self.ultimo_leido += 1 # lineas leidas
            for conocido in self.dispositivos_conocidos:
                # Si es un dispositivo conocido
                if d["mac"] == conocido["mac"]:
                    #Si ya se ha detectado
                    if(conocido["last_detect"] != 0):
                        # Si es una fecha posterior a la ultima deteccion registrada
                        if(d["fecha"] > conocido["last_detect"]):
                            conocido["last_detect"] = d["fecha"] # Actualiza ultima deteccion
                            conocido["last_format_date"] = str(datetime.fromtimestamp(int(conocido["last_detect"])).strftime('%H:%M:%S'))
                            # Si no estaba en casa
                            if(conocido["home"] == False): 
                                #print("INFO DE CAMBIO: Esta en casa " + conocido["nombre"] + " con fecha: " + str(datetime.fromtimestamp(int(conocido["last_detect"])).strftime('%H:%M:%S')))
                                conocido["home"] = True
                                reconectados.append(conocido)
                            #print("SIN CAMBIOS: Esta en casa " + conocido["nombre"] +" " + str(conocido["home"]) + " con fecha: " + str(datetime.fromtimestamp(int(conocido["last_detect"]))))
                            #print("Sigue en casa " + conocido["nombre"] + " con fecha: " + str(datetime.fromtimestamp(int(conocido["last_detect"]))))
                    else:
                        #print("INFO DE INICIO: Esta en casa por primera vez hoy: " + conocido["nombre"])
                        conocido["home"] = True # Esta en casa
                        conocido["last_detect"] = d["fecha"] # Crea la deteccion
                        conocido["last_format_date"] = str(datetime.fromtimestamp(int(conocido["last_detect"])).strftime('%H:%M:%S'))
                        nuevos_conectados.append(conocido)
        return reconectados, nuevos_conectados
        
    # Devuelve una lista con los dispositivos que se han dejado de detectar
    def get_out_home_now(self):
        desconectados = [] # Dispositivos desconectados
        # Comprueba hora de ultima deteccion
        for conocido in self.dispositivos_conocidos:
            if(conocido["last_detect"] != 0): 
                # Minutos transcurridos desde la ultima deteccion
                t_d = (int(conocido["last_detect"]) - datetime.now().timestamp())/60
                #print(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                if(abs(t_d) > self.MINUTOS_OUT_HOME and conocido["home"]):
                    #print("INFO DE CAMBIO: Se ha ido " + conocido["nombre"] + " con fecha: " + str(datetime.fromtimestamp(int(conocido["last_detect"])).strftime('%H:%M:%S')))
                    conocido["home"] = False
                    conocido["last_format_date"] = str(datetime.fromtimestamp(int(conocido["last_detect"])).strftime('%H:%M:%S'))
                    desconectados.append(conocido)
                #print("Sigue en casa: " + conocido["nombre"])
        return desconectados

    # Procesa los datos y los agrupa por rangos
    def procesa_datos(self):
        nConocidos = 0 # Numero de dispositivos conocidos
        # Lee los registros
        for dispositivo in self.registros["registro"]:
            # Creacion del objeto (Puede crearse fuera con copia)
            registros_format = {
                "mac": "",
                "nombre": "Desconocido",
                "fecha_ini": "",
                "fecha_fin": "",
                "rssi": {},
                "rssi_min": {},
                "rssi_max": {},
                "canal": {}, 
                "ncanales": {}, 
                "repeticiones":0
            }
            #############################################################################
            # ASIGNACION DE NOMBRE Y MAC
            #############################################################################
            registros_format["mac"] = dispositivo # Mac del dispositivo
            # Compara con las macs conocidas
            for dc in self.dispositivos_conocidos:
                if(dispositivo == dc["mac"]):
                    registros_format["nombre"] = dc["nombre"]
                    registros_format["wifi"] = dc["wifi"]
                    nConocidos += 1
                    break
            for dc in self.dispositivos_semiconocidos:
                if(dispositivo == dc["mac"]):
                    registros_format["nombre"] = dc["nombre"]
                    nConocidos += 1
                    break
            # Si no ha encontrado ningun nombre se le asigna uno
            #if(registros_format["nombre"] == ""):
            #    registros_format["nombre"] = "Desconocido"

            #############################################################################
            # ASIGNACION DE FECHAS Y RSSI
            #############################################################################
            # Si solo se ha detectado una vez
            if(self.registros["registro"][dispositivo]["repeticiones"] == 0):
                registros_format["fecha_ini"] = self.registros["registro"][dispositivo]["fechas"][0]
                registros_format["fecha_fin"] = self.registros["registro"][dispositivo]["fechas"][0]
                registros_format["rssi"] = self.registros["registro"][dispositivo]["rssi"]
                registros_format["rssi_min"] = self.registros["registro"][dispositivo]["rssi"]
                registros_format["rssi_max"] = self.registros["registro"][dispositivo]["rssi"]
                registros_format["repeticiones"] = 0
                #print(registros["registro"][dispositivo]["fechas"])
            # Si se ha detectado mas de una vez
            else:   
                rango_inicio = 0
                rango_final = 0
                fecha_anterior = 0
                rssi_rango = []
                iterador = 0
                # Recorre todas las detecciones agrupadas por mac
                for f in self.registros["registro"][dispositivo]["fechas"]:
                    ultima_detect = False
                    registros_format["repeticiones"] += 1
                    rssi_rango.append(self.registros["registro"][dispositivo]["rssi"][iterador])
                    fecha_actual = datetime.fromtimestamp(int(f)) 
                    iterador += 1
                    # Si empieza un rango de detecciones
                    if (rango_inicio == 0):
                        rango_inicio = fecha_actual
                        rango_final = fecha_actual
                    
                    # Si es la primera deteccion
                    if (fecha_anterior == 0):
                        fecha_anterior = fecha_actual
                    # Si no es la primera deteccion comparamos las fechas de las detecciones
                    else:
                        # Si es mayor de un tiempo determinado separamos en un rango
                        if abs(fecha_anterior - fecha_actual) > timedelta(minutes=self.MINUTOS_RANGO):
                            registros_format["fecha_ini"] = int(datetime.timestamp(rango_inicio))
                            registros_format["fecha_fin"] = int(datetime.timestamp(rango_final))
                            registros_format["rssi_max"] = max(rssi_rango)
                            registros_format["rssi_min"] = min(rssi_rango)
                            registros_format["rssi"] = round(sum(list(map(int, rssi_rango)))/len(rssi_rango))
                            registros_format["canal"] = self.registros["registro"][dispositivo]["canal"][0]
                            registros_format["ncanales"] = len(set(self.registros["registro"][dispositivo]["canal"]))
                            nombre = registros_format["nombre"]
                            mac = registros_format["mac"]
                            ultima_detect = True
                            self.detectiones.append(registros_format.copy())
                            registros_format.clear()
                            registros_format = {
                                "mac": mac,
                                "nombre": nombre,
                                "fecha_ini": int(datetime.timestamp(rango_inicio)),
                                "fecha_fin": int(datetime.timestamp(rango_final)),
                                "rssi": {},
                                "rssi_min": {},
                                "rssi_max": {},
                                "canal": {}, 
                                "ncanales": {}, 
                                "repeticiones":0
                            }
                            rssi_rango.clear()
                            rango_inicio = 0
                        # Si no es mayor se considera el mismo rango
                        else:
                            rango_final = fecha_actual
                            #print("Sigue aqui")
                    fecha_anterior = fecha_actual
            ### Fin recorrer detecciones

            # Asignacion de canal y canales totales
            registros_format["canal"] = self.registros["registro"][dispositivo]["canal"][0]
            registros_format["ncanales"] = len(set(self.registros["registro"][dispositivo]["canal"]))
            
            # Si se detecta siempre (No ha dejado de detectarse)
            if(registros_format["fecha_fin"] == ""):
                registros_format["fecha_ini"] = rango_inicio
                registros_format["fecha_fin"] = rango_final
                registros_format["rssi_max"] = max(rssi_rango)
                registros_format["rssi_min"] = min(rssi_rango)
                registros_format["rssi"] = round(sum(list(map(int, rssi_rango)))/len(rssi_rango))

            # Formatear fechas para que sean numericas otra vez
            if(type(registros_format["fecha_ini"]) == datetime or type(registros_format["fecha_fin"]) == datetime):
                tini = datetime.timestamp(registros_format["fecha_ini"])
                tfin = datetime.timestamp(registros_format["fecha_fin"])
                registros_format["fecha_ini"] = int(tini)
                registros_format["fecha_fin"] = int(tfin)
            
            # Ultimo rango de registros despues de otros rangos
            if(registros_format["mac"] == "" or registros_format["rssi"] == {}):
                registros_format["mac"] = dispositivo
                if rssi_rango:
                    registros_format["rssi_max"] = max(rssi_rango)
                    registros_format["rssi_min"] = min(rssi_rango)
                    registros_format["rssi"] = round(sum(list(map(int, rssi_rango)))/len(rssi_rango))

                if(type(rango_inicio) == datetime):   
                    tini = datetime.timestamp(rango_inicio)
                    registros_format["fecha_ini"] = int(tini)
                if(type(rango_final) == datetime):
                    tfin = datetime.timestamp(rango_final)
                    registros_format["fecha_fin"] = int(tfin)
                if(rango_inicio == 0):
                    registros_format["fecha_ini"] = datetime.fromtimestamp(int(f))
                if(rango_final == 0):
                    registros_format["fecha_fin"] = datetime.fromtimestamp(int(f))
            
            # Ultima deteccion de un rango
            if(ultima_detect == False):
                self.detectiones.append(registros_format.copy())
                rssi_rango.clear()
    
    # Carga los datos a una estructura
    def carga_datos(self, day):
        # Abre un csv
        f = open( '/home/pi/Servidores/datoswifi/datos_' + day + '.csv', 'r' )
        # Carga los datos 
        reader = csv.DictReader( f, fieldnames = ("fecha","mota","mac","rssi","canal"))  
        # Parsea CSV a JSON  
        out = json.dumps( [ row for row in reader ] )  
        # print ("JSON parsed!")
        # Por cada linea de fichero
        for detect in json.loads(out):
            # Si todavia no se ha detectado se crea el registro
            if(detect["mac"] not in self.registros["mac"]):
                self.registros["mac"].append(detect["mac"]) # Añade la mac nueva a la lista de macs
                self.registros["registro"][detect["mac"]] = {} # Inicializa la deteccion a la lista de detecciones
                self.registros["registro"][detect["mac"]]["fechas"] = [] 
                self.registros["registro"][detect["mac"]]["rssi"] = []
                self.registros["registro"][detect["mac"]]["canal"] = []
                self.registros["registro"][detect["mac"]]["nombre"] = "Desconocido"
                self.registros["registro"][detect["mac"]]["repeticiones"] = 0
                self.registros["registro"][detect["mac"]]["fechas"].append(detect["fecha"])
                self.registros["registro"][detect["mac"]]["rssi"].append(detect["rssi"])
                self.registros["registro"][detect["mac"]]["canal"].append(detect["canal"])
                self.registros["count"] += 1
            # Si ya se ha detectado se añade el registro
            else:
                self.registros["registro"][detect["mac"]]["fechas"].append(detect["fecha"])
                self.registros["registro"][detect["mac"]]["rssi"].append(detect["rssi"])
                self.registros["registro"][detect["mac"]]["canal"].append(detect["canal"])
                self.registros["registro"][detect["mac"]]["repeticiones"] += 1

    def inicializa_datos_conocidos(self):
        self.dispositivos_conocidos.append({"mac":"08:12:A5:1B:9B:DD", "nombre":"Fire Stick Casa", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"CC:FA:00:EB:C9:E0", "nombre":"Nexus 5 Jas", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"04:B4:29:6D:56:A1", "nombre":"Galaxy A40 Jas", "home":False, "last_detect":0, "wifi":5})
        self.dispositivos_conocidos.append({"mac":"B8:27:EB:50:54:28", "nombre":"Raspberry", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"34:95:6C:0E:B2:2D", "nombre":"LG OLED SALON", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"54:99:63:70:C1:23", "nombre":"iPad Mami", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"00:50:B6:BE:FB:CA", "nombre":"Generico (Por saber)", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"BB:86:87:C4:B8:67", "nombre":"Generico (Por saber)", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"70:28:8B:56:BD:8A", "nombre":"Samsung J7 Mami", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"04:B4:29:0D:DD:F3", "nombre":"Samsung M30s Papi", "home":False, "last_detect":0, "wifi":5})
        self.dispositivos_conocidos.append({"mac":"E0:37:17:AD:9E:A4", "nombre":"Agile TV", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"BC:EC:23:C3:15:D8", "nombre":"PC sobremesa Jas", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"5C:B1:3E:99:9C:60", "nombre":"Mi wifi", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"A8:5C:2C:87:7A:F0", "nombre":"iPhone Jenny", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"88:AE:07:50:DD:E1", "nombre":"iPad Jenny", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"FA:8B:CA:33:62:48", "nombre":"Sotano V Chromecast Casa", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"A4:38:CC:CE:EF:75", "nombre":"Nintendo Switch", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"F8:45:1C:E7:B4:C1", "nombre":"PS4", "home":False, "last_detect":0, "wifi":2})
        self.dispositivos_conocidos.append({"mac":"D0:7E:35:44:F1:2E", "nombre":"Portatil Jas", "home":False, "last_detect":0, "wifi":5})

    def inicializa_datos_desconocidos(self):    

        self.dispositivos_semiconocidos.append({"mac":"78:8A:20:E6:AB:3D", "nombre":"Colina40 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"D8:FB:5E:0B:58:E3", "nombre":"PepePlus (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"C6:FB:5E:0B:58:E3", "nombre":"Pepe3 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"FC:EC:DA:24:CC:B5", "nombre":"Colina2 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"78:8A:20:E6:AA:D5", "nombre":"Colina50 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"04:18:D6:36:A3:5F", "nombre":"NETLLAR_COLMAS (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"80:2A:A8:A6:DB:09", "nombre":"NETLLAR_COLNAQ (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"D4:7B:B0:E9:E8:73", "nombre":"MOVISTAR_PLUS_E865 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"C6:7B:B0:E9:E8:73", "nombre":"MOVISTAR_E865 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"D8:0D:17:B8:FE:7D", "nombre":"MOVISTAR_36EA (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"F8:FB:56:2B:02:67", "nombre":"MOVISTAR_025E (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"70:4F:57:68:86:17", "nombre":"MOVISTAR_98D1 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"34:57:60:D7:79:0E", "nombre":"MOVISTAR_790C (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"40:16:7E:A3:C0:98", "nombre":"MOVISTAR_5183 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"98:97:D1:77:21:4F", "nombre":"MOVISTAR_214E (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"78:29:ED:B2:D9:BC", "nombre":"MOVISTAR_D9BB (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"70:4F:57:CD:03:47", "nombre":"MOVISTAR_3CBE (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"18:83:BF:90:32:61", "nombre":"ORANGE-325F (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"98:97:D1:74:03:8F", "nombre":"MCFLY (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"00:1D:7E:55:B4:5E", "nombre":"DHARMA (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"78:8A:20:E6:AB:3D", "nombre":"HUAWEI P30 lite (Desconocido)"})
        self.dispositivos_semiconocidos.append({"mac":"0A:12:A5:1B:1B:DD", "nombre":"Red Oculta (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"50:78:B3:EE:C2:44", "nombre":"MIWIFI_SQPF (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"44:FE:3B:3F:FB:75", "nombre":"WIRELESS_GGG (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"D8:0D:17:D6:DB:34", "nombre":"TPLINK_DB34 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"C0:25:E9:7A:45:DC", "nombre":"TPLINK_45DC (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"D8:B6:B7:12:3C:27", "nombre":"JAZZTEL_3C27 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"00:D1:2A:92:B9:14", "nombre":"JAZZTEL_1242 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"D4:60:E3:EC:47:E1", "nombre":"VODAFONE47DC (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"38:4F:F0:3B:4A:B1", "nombre":"PS3-5113391 (AC)"})
        self.dispositivos_semiconocidos.append({"mac":"5C:B1:3E:99:9C:60", "nombre":"Red Oculta (Desconocido)"})
        self.dispositivos_semiconocidos.append({"mac":"0A:12:A5:1B:1B:DD", "nombre":"Direct-nf-FireTV_194c (Desconocido)"})

    def get_macs_conocidas(self):
        list_conocidas = []
        for dispositivo in self.detectiones:
            if dispositivo["nombre"] != "Desconocido":
                list_conocidas.append(dispositivo)
                #f = dispositivo["fecha_ini"]
                #fn = dispositivo["fecha_fin"]
                #print(dispositivo)
                #print(datetime.fromtimestamp(int(f)).isoformat())
                #print(datetime.fromtimestamp(int(fn)).isoformat())
                #print("------------------------------------------------------------------")
        return list_conocidas