# micro_calificaciones/micro_calificaciones/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.views import APIView

class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        return Response({
            "status": "ok",
            "service": "micro_calificaciones",
            "version": "1.0.0"
        })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('api/health/', HealthCheckView.as_view(), name='api-health-check'),
    path('api/', include('calificaciones.urls')),
]