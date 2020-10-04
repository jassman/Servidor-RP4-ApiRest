from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets 
  
# import local data 
from apiHome import serializers 
from apiHome import models 
  
# create a viewset 
class UsuarioAppViewSet(viewsets.ModelViewSet): 
    # define queryset 
    queryset = models.UsuarioApp.objects.all() 
      
    # specify serializer to be used 
    serializer_class = serializers.UsuarioAppSerializer 