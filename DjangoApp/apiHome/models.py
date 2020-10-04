from django.db import models

# Create your models here.


# USUARIOS APP
class UsuarioApp(models.Model):
    name = models.CharField(max_length=100)
    token_firebase = models.CharField(max_length=250)
    
    class Meta:
        ordering = ('-id', )