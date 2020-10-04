from django.db import models

# USUARIOS APP
class UsuarioApp(models.Model):
    name = models.CharField(max_length=100)
    token_firebase = models.CharField(max_length=250)
    
    class Meta:
        ordering = ('-id', )

# TEMPERATURA DE LA CPU
class TemperaturaCPU(models.Model):
    fecha = models.CharField(max_length=30, null=True)
    temperatura = models.CharField(max_length=15)

# MEMORIA DEL SISTEMA SERVIDOR
class MemoriaSistema(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField()
    swap_total = models.IntegerField()
    usada = models.IntegerField()
    usada_swap = models.IntegerField()
    libre = models.IntegerField()
    libre_swap = models.IntegerField()
    compartida = models.IntegerField()
    compartida_swap = models.IntegerField()
    cache = models.IntegerField()
    cache_swap = models.IntegerField()
    disponible = models.IntegerField()
    disponible_swap = models.IntegerField()

    def __str__(self):
        return self.total

    class Meta:
        ordering = ('-id', )

# ARQUITECTURA DEL SISTEMA SERVIDOR
class ArquitecturaSistema(models.Model):
    arquitectura = models.CharField(max_length=50)
    byteorder = models.CharField(max_length=50)
    ncpu = models.IntegerField()
    nhilo = models.IntegerField()
    ncore = models.IntegerField()
    nsocket = models.IntegerField()
    fabricante = models.CharField(max_length=50)
    vmodel = models.IntegerField()
    model = models.CharField(max_length=50)
    maxcpu = models.CharField(max_length=50)
    mincpu = models.CharField(max_length=50)
    bogomips = models.FloatField( null=True )

# HUMEDAD Y TEMPERATURA DE UN LUGAR FISICO
class HumedadTemperaturaExterna(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    temperatura = models.FloatField()
    humedad = models.FloatField()
    
    habitacion = models.ForeignKey(
        'apiHomes.Habitacion', 
        blank=True, 
        null=True,
        default=1,
        on_delete=models.CASCADE,    
        related_name='habitacion')

    def __str__(self):
        return str(self.id)
        
    class Meta:
        ordering = ('-id', )

# LUGAR FISICO DE INTERES
class Habitacion(models.Model):
    nombre = models.CharField(max_length=100)
    metros_cuadrados = models.IntegerField()

    def __str__(self):
        return str(self.id)
        
    class Meta:
        ordering = ('-id', )

# REGISTRO DE DETECCIONES WIFI DE DISPOSITIVOS
class DeteccionesWifi(models.Model):
    mac = models.CharField(max_length=17)
    nombre = models.CharField(max_length=70)
    fecha_ini = models.IntegerField(blank=True, null=True)
    fecha_fin = models.IntegerField(blank=True, null=True)
    rssi = models.IntegerField(blank=True, null=True)
    rssi_min = models.IntegerField(blank=True, null=True)
    rssi_max = models.IntegerField(blank=True, null=True)
    canal = models.IntegerField(blank=True, null=True)
    ncanales = models.IntegerField(blank=True, null=True)
    repeticiones = models.IntegerField(default=1, blank=True, null=True)
    conocido = models.IntegerField(default=2, blank=True, null=True)
 
 # RESUMEN DE LOS REGISTROS DE DETECCIONES WIFI
class StatsDeteccionesWifi(models.Model):
    fecha = models.IntegerField()
    ndetecciones = models.IntegerField()
    nmacs = models.IntegerField()

    class Meta:
        ordering = ('-id', )

 # REGISTRO DE PARTICULAS SUSPENDIDAS EN EL AIRE
class ParticulasAire(models.Model):
    fecha = models.IntegerField()
    aqi = models.IntegerField()
    pm25 = models.FloatField()
    pm10 = models.FloatField()

    class Meta:
        ordering = ('-id', )
