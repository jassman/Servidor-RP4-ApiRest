import json # Manejar json objects
import csv # Manejar archivos csv
import os # Eventos del sistema
from datetime import datetime, timedelta # Manejo de fechas
import requests

from django.shortcuts import render
from django.core.files.storage import default_storage
from django.db.models.functions import ExtractWeek, ExtractMonth, ExtractYear, ExtractDay
from django.db.models import Sum,Avg,Max,Min,Count,F,Q

from rest_framework import viewsets, status

from rest_framework.pagination import PageNumberPagination
from rest_framework.schemas import AutoSchema
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

# import local data 
from apiHomes import serializers 
from apiHomes import models 
from apiHomes.extra.wifiMonitor import WifiMonitor
  
class ResultsTempHumedadSetPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100

class ResultsDeteccionesPagination(PageNumberPagination):
    page_size = 150
    page_size_query_param = 'page_size'
    max_page_size = 100

# USUARIOAPP
class UsuarioAppViewSet(viewsets.ModelViewSet): 
    # define queryset 
    queryset = models.UsuarioApp.objects.all() 
      
    # specify serializer to be used 
    serializer_class = serializers.UsuarioAppSerializer 

# TEMPERATURA CPU
class TemperaturaCPUViewset(viewsets.ModelViewSet):

    queryset = models.TemperaturaCPU.objects.all()
    serializer_class = serializers.TemperaturaCPUSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    ### Devuelve la lista mostrando primero los ultimos insertados
    def list(self, request):
        queryset = models.TemperaturaCPU.objects.all().order_by('-id')
        serializer = serializers.TemperaturaCPUSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    ### Devuelve el ultimo insertado
    @action(
        detail=False, 
        methods=['GET'],
    )
    def last(self, request):
        last_temperature = models.TemperaturaCPU.objects.first()
        serializer = serializers.TemperaturaCPUSerializer(last_temperature)
        return Response(serializer.data, status=status.HTTP_200_OK)

# MEMORIA SISTEMA
class MemoriaSistemaViewset(viewsets.ModelViewSet):

    queryset = models.MemoriaSistema.objects.all()
    serializer_class = serializers.MemoriaSistemaSerializer

# ARQUITECTURA SISTEMA
class ArquitecturaSistemaViewset(viewsets.ModelViewSet):

    queryset = models.ArquitecturaSistema.objects.all()
    serializer_class = serializers.ArquitecturaSistemaSerializer

# HABITACIONES
class HabitacionViewset(viewsets.ModelViewSet):

    queryset = models.Habitacion.objects.all()
    serializer_class = serializers.HabitacionSerializer

# TEMPERATURA Y HUMEDAD HABITACION
class HumedadTemperaturaExternaViewSet(viewsets.ModelViewSet):

    queryset = models.HumedadTemperaturaExterna.objects.all()
    serializer_class = serializers.HumedadTemperaturaExternaSerializer

    @action(
        detail=False, 
        methods=['GET'],
    )
    def metadata(self, request, *args, **kwargs):
        habitacion = request.query_params.get('habitacion')
        print(request.GET)
        print("Comando: " + str(habitacion))
        # Si no hay seleccion de habitacion se selecciona predeterminadamente la primera
        if(habitacion==None):
            habitacion = 1
            print("No hay habitacion seleccionada. Seleccion automatica.")
        # Media de toda la temperatura registrada
        media_temp = models.HumedadTemperaturaExterna.objects.filter(
                habitacion=habitacion
            ).values().aggregate(
                Avg('temperatura')
            )
        media_hum = models.HumedadTemperaturaExterna.objects.filter(
                habitacion=habitacion
            ).aggregate(
                Avg('humedad')
            )
        # Maxima y minima (Objeto entero)
        data_temp_prepare = models.HumedadTemperaturaExterna.objects.filter(
                habitacion=habitacion
            ).order_by('-temperatura')
        data_hum_prepare = models.HumedadTemperaturaExterna.objects.filter(
                habitacion=habitacion
            ).order_by('-humedad')

        maxima_temp = data_temp_prepare.first()
        minima_temp = data_temp_prepare.last()
        maxima_hum = data_hum_prepare.first()
        minima_hum = data_hum_prepare.last()

        minima_temp.fecha = minima_temp.fecha.strftime("%m/%d/%Y %H:%M:%S")
        maxima_temp.fecha = maxima_temp.fecha.strftime("%m/%d/%Y %H:%M:%S")
        minima_hum.fecha = minima_hum.fecha.strftime("%m/%d/%Y %H:%M:%S")
        maxima_hum.fecha = maxima_hum.fecha.strftime("%m/%d/%Y %H:%M:%S")
        
        serializer_temp_min = serializers.HumedadTemperaturaExternaSerializer(minima_temp)
        serializer_temp_max = serializers.HumedadTemperaturaExternaSerializer(maxima_temp)
        serializer_hum_min = serializers.HumedadTemperaturaExternaSerializer(minima_hum)
        serializer_hum_max = serializers.HumedadTemperaturaExternaSerializer(maxima_hum)

        return Response({
            "media_temp": media_temp, 
            "media_hum": media_hum, 
            "minima_temp":(serializer_temp_min.data),
            "maxima_temp": (serializer_temp_max.data),
            "minima_hum":(serializer_hum_min.data),
            "maxima_hum": (serializer_hum_max.data)
            }, status=status.HTTP_200_OK)

    @action(
        detail=False, 
        methods=['GET'],
    )
    def dia(self, request, *args, **kwargs):
        habitacion = request.query_params.get('habitacion')
        print(request.GET)
        print("Comando: " + str(habitacion))
        # Si no hay seleccion de habitacion se selecciona predeterminadamente la primera
        if(habitacion==None):
            habitacion = 1
            print("No hay habitacion seleccionada. Seleccion automatica.")
        stats = (models.HumedadTemperaturaExterna.objects
            .filter(
                habitacion=habitacion,
                fecha__gte=datetime.now()-timedelta(days=60)
            )
            .values()
        )

        values = set(map(lambda x:(x["fecha"].date()), stats))
        list_by_dia = [[y for y in stats if y["fecha"].date()==x] for x in values]
        
        response = []
        for grupo in list_by_dia:
            media_temperatura = round(sum(c["temperatura"] for c in grupo) / len(grupo), 2)
            max_temperatura = max(c["temperatura"] for c in grupo)
            min_temperatura = min(c["temperatura"] for c in grupo)
            media_humedad = round(sum(c["humedad"] for c in grupo) / len(grupo), 2)
            max_humedad = max(c["humedad"] for c in grupo)
            min_humedad = min(c["humedad"] for c in grupo)
            response.append({
                "fecha": grupo[0]["fecha"].strftime('%Y-%m-%d'),
                "media_temp": media_temperatura,
                "max_temp": max_temperatura,
                "min_temp": min_temperatura,
                "media_hum": media_humedad,
                "max_hum": max_humedad,
                "min_hum": min_humedad
            })

        response = sorted(response, key=lambda d: (int, d["fecha"].split('-')))
        print(response)
        #print(response)
        return Response({
            "response": response
            }, status=status.HTTP_200_OK)

    @action(
        detail=False, 
        methods=['GET'],
    )
    def mes(self, request, *args, **kwargs):
        habitacion = request.query_params.get('habitacion')
        print(request.GET)
        print("Comando: " + str(habitacion))
        # Si no hay seleccion de habitacion se selecciona predeterminadamente la primera
        if(habitacion==None):
            habitacion = 1
            print("No hay habitacion seleccionada. Seleccion automatica.")
        stats = (models.HumedadTemperaturaExterna.objects
            .filter(
                habitacion=habitacion,
                fecha__gte=datetime.now()-timedelta(days=365)
            )
            .values()
        )

        values = set(map(lambda x:(x["fecha"].month), stats))
        list_by_dia = [[y for y in stats if y["fecha"].month==x] for x in values]
        
        response = []
        for grupo in list_by_dia:
            media_temperatura = round(sum(c["temperatura"] for c in grupo) / len(grupo), 2)
            media_humedad = round(sum(c["humedad"] for c in grupo) / len(grupo), 2)
            max_humedad = max(c["humedad"] for c in grupo)
            min_humedad = min(c["humedad"] for c in grupo)
            max_temperatura = max(c["temperatura"] for c in grupo)
            min_temperatura = min(c["temperatura"] for c in grupo)
            print(str(media_temperatura) + ":" + str(media_humedad))
            response.append({
                "fecha": grupo[0]["fecha"].strftime('%Y-%m'),
                "media_temp": media_temperatura,
                "max_temp": max_temperatura,
                "min_temp": min_temperatura,
                "media_hum": media_humedad,
                "max_hum": max_humedad,
                "min_hum": min_humedad
            })

        #print(response)
        return Response({
            "response": response
            }, status=status.HTTP_200_OK)

    @action(
        detail=False, 
        methods=['GET'],
    )
    def last(self, request, *args, **kwargs):
        habitacion = request.query_params.get('habitacion')
        print(request.GET)
        print("Comando: " + str(habitacion))
        # Si no hay seleccion de habitacion se selecciona predeterminadamente la primera
        if(habitacion==None):
            habitacion = 1
            print("No hay habitacion seleccionada. Seleccion automatica.")
        last_th = models.HumedadTemperaturaExterna.objects.filter(
                habitacion=habitacion,
            ).first()
        serializer = serializers.HumedadTemperaturaExternaSerializer(last_th)

        return Response(serializer.data, status=status.HTTP_200_OK)

# ESTADISTICAS DETECCIONES WIFI
class StatsDeteccionesWifiViewSet(viewsets.ModelViewSet):
    queryset = models.StatsDeteccionesWifi.objects.all()
    serializer_class = serializers.StatsDeteccionesWifiSerializer

    @action(detail=False, methods=['GET'])
    def voice(self, request, *args, **kwargs):
        print(request.POST)
        comando = request.query_params.get('frase')
        print("Comando: " + str(comando))
        cmd = 'espeak -v es "'+ str(comando) +'" --stdout | aplay'
        os.system(cmd)

        return Response({}, status=status.HTTP_200_OK)

    @action(
        detail=False, 
        methods=['POST'],
    )
    def voice(self, request, *args, **kwargs):
        print(request.POST)
        comando = request.query_params.get('frase')
        frase = request.data.get("frase", None)
        #exec(open('/home/pi/Servidores/voice_assistant.py').read())
        ######################################################################
        #ESTO
        # import vlc
        # from gtts import gTTS as tts
        # import os

        # speech = tts(text=frase, lang='es')
        # speech_file = 'frase.mp3'
        # speech.save(speech_file)
        

        # os.system("cvlc --play-and-exit input.mp3")
        ##########################################################################
        

        # cmd = 'espeak -v es ' + frase +' --stdout | aplay'
        # os.system(cmd)
        #print("Hola")

        response = requests.post('http://192.168.1.43:8000/api/v1/statsWifi/voice/?frase=' + frase)
        #print(response)
        #obj_json = json.dumps(json.load(response))
        j_result = (response.json())

        return Response({
                    "response": j_result,
                    }, status=status.HTTP_200_OK)

# DETECCIONES WIFI
class DeteccionesWifiViewSet(viewsets.ModelViewSet):
    #permission_classes = (AllowAny,)
    queryset = models.DeteccionesWifi.objects.all()
    serializer_class = serializers.DeteccionesWifiSerializer
    pagination_class = ResultsDeteccionesPagination

    def create(self, request, *args, **kwargs):
        """
        #checks if post request data is an array initializes serializer with many=True
        else executes default CreateModelMixin.create function 
        """
        is_many = isinstance(request.data, list)
        if not is_many:
            return super(DeteccionesWifiViewSet, self).create(request, *args, **kwargs)
        else:
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response("dato", status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['GET'])
    def livedata(self, request, *args, **kwargs):
        f = open( '/home/pi/Servidores/datoswifi/datos_2020-02-24.csv', 'r' )
        # Change each fieldname to the appropriate field name. I know, so difficult.  
        reader = csv.DictReader( f, fieldnames = ("fecha","mota","mac","rssi","canal"))  
        # Parse the CSV into JSON  
        out = json.dumps( [ row for row in reader ] )  
        print ("JSON parsed!")  

        return Response({
            "media_temp": out, 
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def getDispositivosNow(self, request, *args, **kwargs):
        estan = []
        fecha_hoy = datetime.today().strftime('%Y-%m-%d')
        monitor = WifiMonitor()
        #han_vuelto, primera_vez = monitor.get_in_home_now()
        #no_estan = monitor.get_out_home_now()
        #monitor.carga_datos(fecha_hoy)
        #monitor.procesa_datos()
        #rangos_conocidos = monitor.get_macs_conocidas()
        #print(monitor.dispositivos_conocidos)
        for d in monitor.dispositivos_conocidos:
            if d["home"] :
                estan.append(d)
        
        #return Response({
        #            "estan": estan,
                    #"primera_vez":primera_vez, 
                    #"han_vuelto":han_vuelto, 
                    #"no_estan":no_estan, 
        #            }, status=status.HTTP_200_OK)

        response = requests.get('http://192.168.1.43:8000/api/v1/detectWifi/getDispositivosNow/')
        #print(response)
        #obj_json = json.dumps(json.load(response))
        j_result = (response.json())
        return Response({"response": (j_result)}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def getRangos(self, request, *args, **kwargs):

        t_ini = request.query_params.get('t_ini')
        t_fin = request.query_params.get('t_fin')

        if t_ini != None and t_fin != None :
            queryset_detecciones = models.DeteccionesWifi.objects.filter(
                fecha_ini__gt=t_ini, 
                fecha_fin__lte=t_fin).values().order_by('id')
        else:
            queryset_detecciones = models.DeteccionesWifi.objects.all()

        page = self.paginate_queryset(queryset_detecciones)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = serializers.DeteccionesWifiSerializer(queryset_detecciones, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

# ARQUITECTURA SISTEMA
class ParticulasAireViewset(viewsets.ModelViewSet):

    queryset = models.ParticulasAire.objects.all()
    serializer_class = serializers.ParticulasAireSerializer