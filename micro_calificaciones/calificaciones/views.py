from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from .models import Calificacion, Alerta, ConfigAgente
from .serializers import CalificacionSerializer, AlertaSerializer, ConfigAgenteSerializer
import logging

logger = logging.getLogger(__name__)


class CalificacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar calificaciones
    
    Endpoints disponibles:
    - GET /api/calificaciones/ - Listar todas
    - GET /api/calificaciones/?estudiante_id=1 - Filtrar por estudiante
    - GET /api/calificaciones/?curso_id=1 - Filtrar por curso
    - GET /api/calificaciones/{id}/ - Detalle de una calificación
    - POST /api/calificaciones/ - Crear calificación
    - PUT /api/calificaciones/{id}/ - Actualizar calificación
    - DELETE /api/calificaciones/{id}/ - Eliminar calificación
    - GET /api/calificaciones/promedio_estudiante/?estudiante_id=1 - Promedio de un estudiante
    """
    queryset = Calificacion.objects.all()
    serializer_class = CalificacionSerializer

    def get_queryset(self):
        """Permitir filtrado por estudiante_id y curso_id"""
        queryset = Calificacion.objects.all()
        
        estudiante_id = self.request.query_params.get('estudiante_id', None)
        curso_id = self.request.query_params.get('curso_id', None)
        
        if estudiante_id is not None:
            queryset = queryset.filter(estudiante_id=estudiante_id)
        
        if curso_id is not None:
            queryset = queryset.filter(curso_id=curso_id)
        
        return queryset.order_by('-fecha')

    def create(self, request, *args, **kwargs):
        """
        Crear calificación y generar alerta si la nota es baja
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        calificacion = serializer.save()
        
        # Generar alerta si la nota es menor a 3.0
        if calificacion.nota < 3.0:
            Alerta.objects.create(
                estudiante_id=calificacion.estudiante_id,
                mensaje=f"Riesgo académico en curso {calificacion.curso_id}: Nota {calificacion.nota}",
                nivel_riesgo='Medio'
            )
            logger.info(f"Alerta creada para estudiante {calificacion.estudiante_id}")
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def promedio_estudiante(self, request):
        """
        Calcular el promedio de un estudiante
        GET /api/calificaciones/promedio_estudiante/?estudiante_id=1
        """
        estudiante_id = request.query_params.get('estudiante_id', None)
        
        if not estudiante_id:
            return Response(
                {"error": "Se requiere el parámetro estudiante_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        promedio = Calificacion.objects.filter(
            estudiante_id=estudiante_id
        ).aggregate(Avg('nota'))['nota__avg'] or 0
        
        total_calificaciones = Calificacion.objects.filter(
            estudiante_id=estudiante_id
        ).count()
        
        return Response({
            "estudiante_id": estudiante_id,
            "promedio": round(promedio, 2),
            "total_calificaciones": total_calificaciones
        })

    @action(detail=False, methods=['get'])
    def estadisticas_curso(self, request):
        """
        Estadísticas de un curso
        GET /api/calificaciones/estadisticas_curso/?curso_id=1
        """
        curso_id = request.query_params.get('curso_id', None)
        
        if not curso_id:
            return Response(
                {"error": "Se requiere el parámetro curso_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calificaciones = Calificacion.objects.filter(curso_id=curso_id)
        
        promedio = calificaciones.aggregate(Avg('nota'))['nota__avg'] or 0
        total = calificaciones.count()
        aprobados = calificaciones.filter(nota__gte=3.0).count()
        
        return Response({
            "curso_id": curso_id,
            "promedio": round(promedio, 2),
            "total_calificaciones": total,
            "aprobados": aprobados,
            "porcentaje_aprobacion": round((aprobados / total * 100) if total > 0 else 0, 2)
        })


class AlertaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar alertas
    
    Endpoints disponibles:
    - GET /api/alertas/ - Listar todas
    - GET /api/alertas/?estudiante_id=1 - Filtrar por estudiante
    - GET /api/alertas/?nivel_riesgo=Alto - Filtrar por nivel de riesgo
    - POST /api/alertas/ - Crear alerta manualmente
    - DELETE /api/alertas/{id}/ - Eliminar alerta
    """
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer

    def get_queryset(self):
        """Permitir filtrado por estudiante_id y nivel_riesgo"""
        queryset = Alerta.objects.all()
        
        estudiante_id = self.request.query_params.get('estudiante_id', None)
        nivel_riesgo = self.request.query_params.get('nivel_riesgo', None)
        
        if estudiante_id is not None:
            queryset = queryset.filter(estudiante_id=estudiante_id)
        
        if nivel_riesgo is not None:
            queryset = queryset.filter(nivel_riesgo=nivel_riesgo)
        
        return queryset.order_by('-fecha')


class ConfigAgenteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la configuración del agente
    
    Endpoints disponibles:
    - GET /api/configuraciones/ - Obtener configuración
    - PUT /api/configuraciones/{id}/ - Actualizar configuración
    """
    queryset = ConfigAgente.objects.all()
    serializer_class = ConfigAgenteSerializer

    @action(detail=False, methods=['get'])
    def activa(self, request):
        """
        Obtener la configuración activa (siempre devuelve la primera o crea una)
        GET /api/configuraciones/activa/
        """
        config, created = ConfigAgente.objects.get_or_create(
            id=1,
            defaults={
                'umbral_bajo': 3.0,
                'umbral_medio': 4.0,
                'frecuencia_alertas': 'semanal'
            }
        )
        serializer = self.get_serializer(config)
        return Response(serializer.data)