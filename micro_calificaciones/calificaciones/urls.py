# micro_calificaciones/calificaciones/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CalificacionViewSet, AlertaViewSet, ConfigAgenteViewSet

router = DefaultRouter()
router.register(r'calificaciones', CalificacionViewSet, basename='calificacion')
router.register(r'alertas', AlertaViewSet, basename='alerta')
router.register(r'configuraciones', ConfigAgenteViewSet, basename='configuracion')

urlpatterns = [
    path('', include(router.urls)),
]