# import serializer from rest_framework 
from rest_framework import serializers 
  
# import model from models.py 
from apiHome import models
  
# Create a model serializer  
class UsuarioAppSerializer(serializers.ModelSerializer): 
    # specify model and fields 
    class Meta: 
        model = models.UsuarioApp 
        fields = ('id', 'name', 'token_firebase') 