from rest_framework import serializers

# import model from models.py 
from apiHomes import models
  
# Create a model serializer  
class UsuarioAppSerializer(serializers.ModelSerializer): 
    # specify model and fields 
    class Meta: 
        model = models.UsuarioApp 
        fields = ('id', 'name', 'token_firebase') 

class TemperaturaCPUSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TemperaturaCPU
        fields = '__all__'

class MemoriaSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MemoriaSistema
        fields = '__all__'

class ArquitecturaSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArquitecturaSistema
        fields = '__all__'

class HumedadTemperaturaExternaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HumedadTemperaturaExterna
        fields = '__all__'

class HabitacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Habitacion
        fields = '__all__'

class DeteccionesWifiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeteccionesWifi
        fields = '__all__'

class StatsDeteccionesWifiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StatsDeteccionesWifi
        fields = '__all__'

class ParticulasAireSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ParticulasAire
        fields = '__all__'
        