# app/services.py
import requests
import logging
from django.conf import settings
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class MicroserviceClient:
    """Cliente para comunicarse con el microservicio de calificaciones"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'MICROSERVICE_CALIFICACIONES_URL', 'http://micro_calificaciones:8001/api')
        self.timeout = getattr(settings, 'MICROSERVICE_TIMEOUT', 5)
        self.enabled = getattr(settings, 'USE_MICROSERVICE_CALIFICACIONES', False)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Método base para hacer peticiones al microservicio"""
        if not self.enabled:
            logger.info(f"Microservicio deshabilitado. Llamada a {endpoint} omitida.")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        # 🔍 Log detallado de la petición
        logger.info(f"🔄 {method} {url}")
        if 'json' in kwargs:
            logger.info(f"📤 Payload: {kwargs['json']}")
        
        try:
            response = requests.request(method, url, **kwargs)
            
            # 🔍 Log de la respuesta ANTES de raise_for_status
            logger.info(f"📥 Response Status: {response.status_code}")
            # ✅ FIX: Convertir a string primero
            response_text = str(response.text) if response.text else ""
            logger.info(f"📥 Response Body: {response_text[:500]}") # Primeros 500 caracteres
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Timeout al llamar a {url}")
            return None
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"🔌 Error de conexión con microservicio: {url}")
            logger.error(f"   Detalle: {str(e)}")
            return None
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Error HTTP {e.response.status_code} en {url}")
            logger.error(f"   Respuesta del servidor: {e.response.text}")
            
            # Intentar parsear el error JSON si existe
            try:
                error_data = e.response.json()
                logger.error(f"   Detalles del error: {error_data}")
            except:
                pass
            
            return None
            
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"🔴 Error al decodificar JSON de {url}")
            logger.error(f"   Respuesta recibida: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"💥 Error inesperado al llamar a {url}: {type(e).__name__}")
            logger.error(f"   Detalle: {str(e)}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return None
    
    # ========== CALIFICACIONES ==========
    
    def crear_calificacion(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crear una calificación en el microservicio"""
        logger.info(f"📝 Intentando crear calificación: {data}")
        result = self._make_request('POST', 'calificaciones/', json=data)
        
        if result:
            logger.info(f"✅ Calificación creada exitosamente: ID={result.get('id')}")
        else:
            logger.error(f"❌ Error al crear calificación en microservicio")
        
        return result
    
    def obtener_calificaciones(self, estudiante_id: int = None, curso_id: int = None) -> Optional[List[Dict]]:
        """Obtener calificaciones con filtros opcionales"""
        params = {}
        if estudiante_id:
            params['estudiante_id'] = estudiante_id
        if curso_id:
            params['curso_id'] = curso_id
        
        result = self._make_request('GET', 'calificaciones/', params=params)
        return result if result else []
    
    def actualizar_calificacion(self, calificacion_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Actualizar una calificación"""
        return self._make_request('PUT', f'calificaciones/{calificacion_id}/', json=data)
    
    def eliminar_calificacion(self, calificacion_id: int) -> bool:
        """Eliminar una calificación"""
        result = self._make_request('DELETE', f'calificaciones/{calificacion_id}/')
        return result is not None
    
    def obtener_promedio_estudiante(self, estudiante_id: int) -> Optional[Dict[str, Any]]:
        """Obtener el promedio de un estudiante"""
        return self._make_request('GET', f'calificaciones/promedio_estudiante/', params={'estudiante_id': estudiante_id})
    
    def obtener_estadisticas_curso(self, curso_id: int) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de un curso"""
        return self._make_request('GET', f'calificaciones/estadisticas_curso/', params={'curso_id': curso_id})
    
    # ========== ALERTAS ==========
    
    def crear_alerta(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crear una alerta"""
        return self._make_request('POST', 'alertas/', json=data)
    
    def obtener_alertas(self, estudiante_id: int = None, nivel_riesgo: str = None) -> Optional[List[Dict]]:
        """Obtener alertas con filtros opcionales"""
        params = {}
        if estudiante_id:
            params['estudiante_id'] = estudiante_id
        if nivel_riesgo:
            params['nivel_riesgo'] = nivel_riesgo
        
        result = self._make_request('GET', 'alertas/', params=params)
        return result if result else []
    
    # ========== CONFIGURACIÓN ==========
    
    def obtener_config_activa(self) -> Optional[Dict[str, Any]]:
        """Obtener la configuración activa del agente"""
        return self._make_request('GET', 'configuraciones/activa/')
    
    def actualizar_config(self, config_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Actualizar configuración"""
        return self._make_request('PUT', f'configuraciones/{config_id}/', json=data)
    
    # ========== HEALTH CHECK ==========
    
    def health_check(self) -> bool:
        """Verificar si el microservicio está disponible"""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=2)
            return response.status_code == 200
        except:
            try:
                response = requests.get(f"{self.base_url.replace('/api', '')}/health/", timeout=2)
                return response.status_code == 200
            except:
                return False

# Instancia global del cliente
microservice_client = MicroserviceClient()