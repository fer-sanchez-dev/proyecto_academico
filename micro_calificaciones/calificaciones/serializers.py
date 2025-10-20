from rest_framework import serializers
from .models import Calificacion, Alerta, ConfigAgente

class CalificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calificacion
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'


class ConfigAgenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigAgente
        fields = '__all__'
