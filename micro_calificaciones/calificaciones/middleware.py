# micro_calificaciones/calificaciones/middleware.py

class CustomCommonMiddleware:
    """
    Versión modificada de CommonMiddleware que no valida ALLOWED_HOSTS
    de forma estricta en peticiones internas de Docker
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Permitir cualquier host que venga de la red interna de Docker
        host = request.META.get('HTTP_HOST', '')
        if ':' in host:
            # Si tiene puerto, removerlo para validación
            host_without_port = host.split(':')[0]
            if host_without_port in ['micro_calificaciones', 'localhost', '127.0.0.1']:
                # Es una petición interna válida
                pass
        
        response = self.get_response(request)
        return response

class DisableCSRFForAPIMiddleware:
    """Middleware para deshabilitar CSRF en rutas de API"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Deshabilitar CSRF para todas las rutas /api/ y /health/
        if request.path.startswith('/api/') or request.path.startswith('/health/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        response = self.get_response(request)
        return response