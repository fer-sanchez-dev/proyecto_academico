import logging
import torch
import torch.nn as nn
from torch.autograd import Variable
from django.db import IntegrityError, connections
from django.db.models import Avg, Count, Q  # Añadir Q explícitamente
from django.db.utils import OperationalError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from .forms import CustomUserCreationForm, CalificacionForm, PerfilForm, CursoForm, ConfigAgenteForm, EstudianteForm, CustomUserEditForm
from .models import CustomUser, Estudiante, Curso, Calificacion, Alerta, ConfigAgente
from .services import microservice_client

from .services import microservice_client 
logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, '¡Inicio de sesión exitoso!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Correo o contraseña incorrectos. Verifica tus datos.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('login')

def registro_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Crear objeto Estudiante si el rol es 'estudiante'
                if form.cleaned_data['role'] == 'estudiante':
                    Estudiante.objects.create(usuario=user)
                login(request, user)
                messages.success(request, 'Registro exitoso.')
                return redirect('dashboard')
            except IntegrityError:
                messages.error(request, 'Error en el registro: el correo electrónico ya está en uso.')
        else:
            messages.error(request, 'Error en el registro. Verifica los datos.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form[field].label}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})

@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'estudiante':
        try:
            estudiante = Estudiante.objects.get(usuario=user)
            calificaciones = Calificacion.objects.filter(estudiante=estudiante)
            alertas = Alerta.objects.filter(estudiante=estudiante)
            # RF07: Métricas de rendimiento
            promedio = calificaciones.aggregate(Avg('nota'))['nota__avg'] or 0
            cursos_aprobados = calificaciones.filter(nota__gte=3.0).count()
            total_cursos = estudiante.cursos.count()
            # RF08: Recomendaciones personalizadas
            recomendaciones = []
            if promedio < 3.0:
                recomendaciones.append("Te recomendamos dedicar más tiempo a estudiar las materias con notas bajas.")
            if alertas.exists():
                recomendaciones.append("Revisa tus alertas activas y consulta con tu profesor.")
            if not calificaciones.exists():
                recomendaciones.append("Registra tus primeras calificaciones para comenzar a monitorear tu rendimiento.")
            # RF11: Predicción de riesgo (placeholder, ajusta según tu lógica)
            riesgo = "Bajo" if promedio >= 3.0 else "Alto"
            return render(request, 'dashboard_estudiante.html', {
                'calificaciones': calificaciones,
                'alertas': alertas,
                'promedio': promedio,
                'cursos_aprobados': cursos_aprobados,
                'total_cursos': total_cursos,
                'recomendaciones': recomendaciones,
                'riesgo': riesgo
            })
        except Estudiante.DoesNotExist:
            messages.error(request, 'No se encontró un perfil de estudiante asociado a tu cuenta. Contacta al administrador.')
            return render(request, 'dashboard_estudiante.html', {
                'calificaciones': [],
                'alertas': [],
                'promedio': 0,
                'cursos_aprobados': 0,
                'total_cursos': 0,
                'recomendaciones': ["Contacta al administrador para configurar tu perfil de estudiante."],
                'riesgo': "No disponible"
            })
    elif user.role == 'profesor':
        # Redirigir directamente a gestionar calificaciones para profesores
        return redirect('gestionar_calificaciones')
    elif user.role == 'admin':
        estudiantes = Estudiante.objects.all()
        cursos = Curso.objects.all()
        if not estudiantes.exists() and not cursos.exists():
            messages.warning(request, 'No hay estudiantes ni cursos registrados.')
        return render(request, 'dashboard_admin.html', {'estudiantes': estudiantes, 'cursos': cursos})
    else:
        messages.error(request, 'Rol no reconocido. Contacta al administrador.')
        return redirect('login')

@login_required
def registrar_calificacion(request):
    """Vista para registrar calificaciones (ahora con soporte para microservicio)"""
    if request.user.role != 'profesor':
        messages.error(request, 'Solo los profesores pueden registrar calificaciones.')
        return redirect('dashboard')
    
    # Configuración del microservicio
    use_micro = getattr(settings, 'USE_MICROSERVICE_CALIFICACIONES', False)
    mode = getattr(settings, 'MICROSERVICE_MODE', 'monolith')
    
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            # 1. Guardar en el monolito
            calificacion = form.save()
            logger.info(f"✅ Calificación guardada en monolito: ID={calificacion.id}")
            
            # 2. Sincronizar con microservicio si está habilitado
            if use_micro and mode in ['hybrid', 'proxy']:
                try:
                    micro_data = {
                        'estudiante_id': calificacion.estudiante.id,
                        'curso_id': calificacion.curso.id,
                        'nota': float(calificacion.nota),
                        'descripcion': calificacion.descripcion
                    }
                    
                    logger.info(f"🔄 Enviando calificación al microservicio: {micro_data}")
                    result = microservice_client.crear_calificacion(micro_data)
                    
                    if result:
                        logger.info(f"✅ Calificación creada en microservicio con ID: {result.get('id')}")
                        messages.success(request, 'Calificación registrada correctamente.')
                    else:
                        logger.error("❌ Error al crear calificación en microservicio (respuesta None)")
                        if mode == 'proxy':
                            messages.warning(request, 'Advertencia: Error al sincronizar con microservicio')
                        else:
                            messages.success(request, 'Calificación registrada (solo en base local)')
                
                except Exception as e:
                    logger.error(f"❌ Excepción al sincronizar con microservicio: {str(e)}")
                    if mode == 'proxy':
                        messages.error(request, f'Error al registrar en microservicio: {str(e)}')
                    else:
                        messages.success(request, 'Calificación registrada localmente (microservicio no disponible)')
            else:
                messages.success(request, 'Calificación registrada.')
            
            # 3. Crear alerta si la nota es baja (solo en modo monolito o híbrido)
            if calificacion.nota < 3.0 and mode != 'proxy':
                # En modo proxy, el microservicio crea la alerta automáticamente
                Alerta.objects.create(
                    estudiante=calificacion.estudiante,
                    mensaje=f"Riesgo académico en {calificacion.curso.nombre}: Nota {calificacion.nota}",
                    nivel_riesgo='Medio'
                )
                logger.info(f"⚠️ Alerta de riesgo creada para estudiante {calificacion.estudiante.id}")
            
            return redirect('dashboard')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                field_name = 'Error general' if field == '__all__' else (form.fields[field].label or field)
                for error in errors:
                    messages.error(request, f'{field_name}: {error}')
    else:
        form = CalificacionForm()
    
    return render(request, 'dashboard_profesor.html', {'form': form})

@login_required
def editar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    usuario = estudiante.usuario  # Obtenemos el CustomUser asociado
    if request.method == 'POST':
        estudiante_form = EstudianteForm(request.POST, instance=estudiante)
        user_form = CustomUserEditForm(request.POST, instance=usuario)
        if estudiante_form.is_valid() and user_form.is_valid():
            try:
                estudiante_form.save()
                user_form.save()
                messages.success(request, 'Estudiante actualizado correctamente.')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar en la base de datos: {str(e)}')
        else:
            # Mostrar errores específicos de ambos formularios
            for form in [estudiante_form, user_form]:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{form.fields[field].label}: {error}')
            messages.error(request, 'Error al actualizar el estudiante. Verifica los datos.')
    else:
        estudiante_form = EstudianteForm(instance=estudiante)
        user_form = CustomUserEditForm(instance=usuario)
    return render(request, 'editar_estudiante.html', {'estudiante_form': estudiante_form, 'user_form': user_form})

@login_required
def eliminar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    if request.method == 'POST':
        estudiante.delete()
        messages.success(request, 'Estudiante eliminado.')
        return redirect('dashboard')
    return render(request, 'confirmar_eliminar_estudiante.html', {'estudiante': estudiante})

@login_required
def editar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Curso actualizado.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Error al actualizar el curso. Verifica los datos.')
    else:
        form = CursoForm(instance=curso)
    return render(request, 'editar_curso.html', {'form': form})

@login_required
def eliminar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if request.method == 'POST':
        curso.delete()
        messages.success(request, 'Curso eliminado.')
        return redirect('dashboard')
    return render(request, 'confirmar_eliminar_curso.html', {'curso': curso})

@login_required
def alertas_view(request):
    if request.user.role != 'estudiante':
        return redirect('dashboard')
    
    estudiante = Estudiante.objects.get(usuario=request.user)
    use_micro = getattr(settings, 'USE_MICROSERVICE_CALIFICACIONES', False)
    mode = getattr(settings, 'MICROSERVICE_MODE', 'monolith')
    
    if use_micro and mode in ['hybrid', 'proxy']:
        try:
            # Obtener alertas del microservicio
            alertas_data = microservice_client.obtener_alertas(estudiante_id=estudiante.id)
            
            if alertas_data is not None:
                # Convertir a objetos tipo Django
                from types import SimpleNamespace
                alertas = [SimpleNamespace(**alerta) for alerta in alertas_data]
                logger.info(f"✅ Alertas obtenidas del microservicio: {len(alertas)}")
            else:
                raise Exception("Microservicio no disponible")
        except Exception as e:
            logger.error(f"❌ Error al obtener alertas del microservicio: {str(e)}")
            # Fallback al monolito
            alertas = Alerta.objects.filter(estudiante=estudiante)
            messages.warning(request, 'Usando datos locales (microservicio no disponible)')
    else:
        alertas = Alerta.objects.filter(estudiante=estudiante)
    
    return render(request, 'alertas.html', {'alertas': alertas})

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=False,  # Cambia a True si usas HTTPS
                from_email='noreply@edutrack.com',  # Configura tu correo
                email_template_name='password_reset_email.html'
            )
            messages.success(request, 'Se ha enviado un correo con instrucciones para restablecer tu contraseña.')
            return redirect('password_reset_done')
        else:
            messages.error(request, 'Error: verifica el correo ingresado.')
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset.html', {'form': form})

@login_required
def perfil_view(request):
    # RF04
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
                update_session_auth_hash(request, user)  # Mantener la sesión activa
            user.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('perfil')  # Redirige a perfil para ver los cambios
        else:
            messages.error(request, 'Error al actualizar el perfil. Verifica los datos.')
            # Mostrar errores específicos de cada campo
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
            # Mostrar errores no asociados a campos
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para editar tu perfil.')
            return redirect('login')
        form = PerfilForm(instance=request.user)
    return render(request, 'perfil.html', {'form': form})

@login_required
def gestionar_calificaciones(request):
    """
    Vista híbrida que puede usar el monolito, el microservicio, o ambos.
    Modos:
    - 'monolith': Solo usa el monolito (comportamiento original)
    - 'hybrid': Usa el microservicio pero valida contra el monolito
    - 'proxy': Solo usa el microservicio (migración completa)
    """
    if request.user.role != 'profesor':
        messages.error(request, 'Solo los profesores pueden gestionar calificaciones.')
        return redirect('dashboard')

    mode = getattr(settings, 'MICROSERVICE_MODE', 'monolith')
    use_micro = getattr(settings, 'USE_MICROSERVICE_CALIFICACIONES', False)
    
    calificaciones = []
    show_form = request.GET.get('show_form', 'false').lower() == 'true'
    form = None
    micro_status = None

    # ========== OBTENER CALIFICACIONES ==========
    if use_micro and mode in ['hybrid', 'proxy']:
        logger.info(f"🔄 Modo {mode}: Intentando obtener calificaciones desde microservicio")
        
        # Intentar obtener desde microservicio
        try:
            micro_data = microservice_client.obtener_calificaciones()
            
            if micro_data is not None:
                # Convertir datos del micro a objetos tipo Django para el template
                # (Necesario porque el template espera objetos con atributos)
                from types import SimpleNamespace
                
                calificaciones_micro = []
                for cal in micro_data[:10]:  # Limitar a 10 como en el original
                    # Obtener estudiante y curso del monolito para mostrar nombres
                    estudiante = Estudiante.objects.filter(id=cal['estudiante_id']).first()
                    curso = Curso.objects.filter(id=cal['curso_id']).first()
                    
                    if estudiante and curso:
                        cal_obj = SimpleNamespace(
                            id=cal['id'],
                            estudiante=estudiante,
                            curso=curso,
                            nota=cal['nota'],
                            fecha=cal['fecha'],
                            descripcion=cal.get('descripcion', '')
                        )
                        calificaciones_micro.append(cal_obj)
                
                if mode == 'proxy':
                    # Modo proxy: solo usar microservicio
                    calificaciones = calificaciones_micro
                    micro_status = '✅ Microservicio (proxy mode)'
                    logger.info(f"✅ Calificaciones obtenidas del microservicio: {len(calificaciones)}")
                
                elif mode == 'hybrid':
                    # Modo híbrido: comparar con monolito
                    calificaciones_monolito = list(
                        Calificacion.objects.filter(curso__profesor=request.user).order_by('-fecha')[:10]
                    )
                    
                    # Usar datos del microservicio pero validar
                    calificaciones = calificaciones_micro
                    
                    # Comparar resultados
                    if len(calificaciones_micro) == len(calificaciones_monolito):
                        micro_status = f'✅ Microservicio + Monolito (coinciden: {len(calificaciones)} registros)'
                        logger.info("✅ Resultados coinciden entre microservicio y monolito")
                    else:
                        micro_status = f'⚠️ Microservicio ({len(calificaciones_micro)}) vs Monolito ({len(calificaciones_monolito)})'
                        logger.warning(f"⚠️ Discrepancia: Micro={len(calificaciones_micro)}, Monolito={len(calificaciones_monolito)}")
            else:
                raise Exception("Microservicio no disponible")
        
        except Exception as e:
            logger.error(f"❌ Error al obtener calificaciones del microservicio: {str(e)}")
            # Fallback al monolito
            calificaciones = Calificacion.objects.filter(curso__profesor=request.user).order_by('-fecha')[:10]
            micro_status = f'❌ Fallback a monolito (error: {str(e)[:50]})'
            messages.warning(request, 'El microservicio no está disponible. Usando base de datos local.')
    else:
        # Modo monolito tradicional
        calificaciones = Calificacion.objects.filter(curso__profesor=request.user).order_by('-fecha')[:10]
        micro_status = '🏛️ Solo monolito' if not use_micro else '🔴 Microservicio deshabilitado'

    # ========== MANEJAR POST (Crear/Actualizar) ==========
    if request.method == 'POST':
        if request.POST.get('update_id'):
            # ACTUALIZACIÓN
            cal_id = request.POST.get('update_id')
            calificacion = Calificacion.objects.filter(id=cal_id, curso__profesor=request.user).first()
            
            if calificacion:
                form = CalificacionForm(request.POST, instance=calificacion, user=request.user)
                if form.is_valid():
                    updated_cal = form.save()
                    
                    # Actualizar en microservicio si está habilitado
                    if use_micro and mode in ['hybrid', 'proxy']:
                        micro_data = {
                            'estudiante_id': updated_cal.estudiante.id,
                            'curso_id': updated_cal.curso.id,
                            'nota': float(updated_cal.nota),
                            'descripcion': updated_cal.descripcion
                        }
                        result = microservice_client.actualizar_calificacion(cal_id, micro_data)
                        
                        if result:
                            logger.info(f"✅ Calificación {cal_id} actualizada en microservicio")
                        else:
                            logger.error(f"❌ Error al actualizar calificación {cal_id} en microservicio")
                            if mode == 'proxy':
                                messages.warning(request, 'Advertencia: Error al sincronizar con microservicio')
                    
                    messages.success(request, 'Calificación actualizada.')
                    return redirect('gestionar_calificaciones')
                else:
                    for field, errors in form.errors.items():
                        field_name = 'Error general' if field == '__all__' else (form.fields[field].label or field)
                        for error in errors:
                            messages.error(request, f'{field_name}: {error}')
                    show_form = False
            else:
                messages.error(request, 'Calificación no encontrada.')
        
        else:
            # CREACIÓN NUEVA
            form = CalificacionForm(request.POST, user=request.user)
            if form.is_valid():
                calificacion = form.save()
                
                # Crear en microservicio si está habilitado
                if use_micro and mode in ['hybrid', 'proxy']:
                    micro_data = {
                        'estudiante_id': calificacion.estudiante.id,
                        'curso_id': calificacion.curso.id,
                        'nota': float(calificacion.nota),
                        'descripcion': calificacion.descripcion
                    }
                    result = microservice_client.crear_calificacion(micro_data)
                    
                    if result:
                        logger.info(f"✅ Calificación creada en microservicio con ID: {result.get('id')}")
                    else:
                        logger.error("❌ Error al crear calificación en microservicio")
                        if mode == 'proxy':
                            messages.warning(request, 'Advertencia: Error al sincronizar con microservicio')
                
                # Crear alerta si la nota es baja (esto lo hace el micro automáticamente)
                if calificacion.nota < 3.0 and mode != 'proxy':
                    # En modo proxy, el microservicio crea la alerta
                    Alerta.objects.create(
                        estudiante=calificacion.estudiante,
                        mensaje=f"Riesgo académico en {calificacion.curso.nombre}: Nota {calificacion.nota}",
                        nivel_riesgo='Medio'
                    )
                
                messages.success(request, 'Calificación registrada.')
                return redirect('gestionar_calificaciones')
            else:
                for field, errors in form.errors.items():
                    field_name = 'Error general' if field == '__all__' else (form.fields[field].label or field)
                    for error in errors:
                        messages.error(request, f'{field_name}: {error}')
                show_form = True

    # ========== MANEJAR ELIMINACIÓN ==========
    if request.method == 'GET' and 'delete' in request.GET:
        cal_id = request.GET.get('delete')
        calificacion = Calificacion.objects.filter(id=cal_id, curso__profesor=request.user).first()
        
        if calificacion:
            # Eliminar del microservicio primero
            if use_micro and mode in ['hybrid', 'proxy']:
                result = microservice_client.eliminar_calificacion(cal_id)
                if not result:
                    logger.error(f"❌ Error al eliminar calificación {cal_id} del microservicio")
                    if mode == 'proxy':
                        messages.error(request, 'Error al eliminar del microservicio')
                        return redirect('gestionar_calificaciones')
            
            # Eliminar del monolito
            calificacion.delete()
            messages.success(request, 'Calificación eliminada.')
            return redirect('gestionar_calificaciones')

    # ========== CREAR FORMULARIO SI SE SOLICITA ==========
    if show_form and not form:
        form = CalificacionForm(user=request.user)
        if not form.fields['estudiante'].queryset.exists():
            messages.warning(request, 'No hay estudiantes inscritos en tus cursos para registrar calificaciones.')
            form = None
        elif not form.fields['curso'].queryset.exists():
            messages.warning(request, 'No tienes cursos asignados para registrar calificaciones.')
            form = None

    return render(request, 'dashboard_profesor.html', {
        'calificaciones': calificaciones,
        'form': form,
        'show_form': show_form,
        'micro_status': micro_status,  # Mostrar estado del microservicio
        'use_microservice': use_micro,
        'microservice_mode': mode,
    })

@login_required
def gestionar_materias(request):
    # RF06
    if request.user.role != 'admin':
        messages.error(request, 'Solo los administradores pueden gestionar materias.')
        return redirect('dashboard')
    
    cursos = Curso.objects.all()
    profesores = CustomUser.objects.filter(role='profesor')
    
    # Verificar si hay profesores disponibles
    if not profesores.exists():
        messages.warning(request, 'No hay profesores registrados. Registra un profesor antes de crear materias.')
    
    show_form = request.GET.get('show_form', 'false').lower() == 'true'
    
    if request.method == 'POST':
        # Debug: Imprimir todos los datos POST
        print("POST data:", request.POST)
        
        # Verificar si es una actualización
        update_id = request.POST.get('update_id')
        print(f"Update ID: {update_id}")
        
        if update_id and update_id.strip():  # Verificar que no esté vacío
            # Es una actualización
            try:
                curso = get_object_or_404(Curso, id=int(update_id))
                form = CursoForm(request.POST, instance=curso)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Materia actualizada correctamente.')
                    return redirect('gestionar_materias')
                else:
                    messages.error(request, 'Error al actualizar la materia.')
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'{field}: {error}')
                    show_form = True
            except (ValueError, Curso.DoesNotExist):
                messages.error(request, 'Materia no encontrada.')
        else:
            # Es una nueva materia
            form = CursoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Materia creada correctamente.')
                return redirect('gestionar_materias')
            else:
                messages.error(request, 'Error al crear la materia.')
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                show_form = True
    
    # Manejar eliminación via GET
    elif request.method == 'GET' and 'delete' in request.GET:
        curso_id = request.GET.get('delete')
        if curso_id:
            try:
                curso = get_object_or_404(Curso, id=int(curso_id))
                curso.delete()
                messages.success(request, 'Materia eliminada correctamente.')
                return redirect('gestionar_materias')
            except (ValueError, Curso.DoesNotExist):
                messages.error(request, 'Materia no encontrada.')
    
    # Crear formulario vacío para mostrar
    form = CursoForm()
    
    return render(request, 'gestionar_materias.html', {
        'cursos': cursos, 
        'profesores': profesores,
        'form': form,
        'show_form': show_form
    })

@login_required
def generar_reportes(request):
    # RF09
    if request.user.role != 'admin':
        messages.error(request, 'Solo los administradores pueden generar reportes.')
        return redirect('dashboard')
    promedio_institucional = Calificacion.objects.aggregate(Avg('nota'))['nota__avg'] or 0
    total_estudiantes = Estudiante.objects.count()
    aprobados = Calificacion.objects.filter(nota__gte=3.0).values('estudiante').distinct().count()
    porcentaje_aprobados = (aprobados / total_estudiantes * 100) if total_estudiantes else 0
    return render(request, 'reportes_globales.html', {
        'promedio_institucional': promedio_institucional,
        'porcentaje_aprobados': porcentaje_aprobados,
        'total_estudiantes': total_estudiantes
    })

@login_required
def config_agente_view(request):
    if request.user.role != 'admin':
        messages.error(request, 'Solo los administradores pueden configurar el agente.')
        return redirect('dashboard')
    
    use_micro = getattr(settings, 'USE_MICROSERVICE_CALIFICACIONES', False)
    mode = getattr(settings, 'MICROSERVICE_MODE', 'monolith')
    
    config, created = ConfigAgente.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        from .forms import ConfigAgenteForm
        form = ConfigAgenteForm(request.POST, instance=config)
        
        if form.is_valid():
            config = form.save()
            
            # Sincronizar con microservicio
            if use_micro and mode in ['hybrid', 'proxy']:
                micro_data = {
                    'umbral_bajo': float(config.umbral_bajo),
                    'umbral_medio': float(config.umbral_medio),
                    'frecuencia_alertas': config.frecuencia_alertas,
                    'criterios_recomendacion': config.criterios_recomendacion
                }
                result = microservice_client.actualizar_config(1, micro_data)
                
                if result:
                    logger.info("✅ Configuración sincronizada con microservicio")
                else:
                    logger.error("❌ Error al sincronizar configuración con microservicio")
                    messages.warning(request, 'Configuración guardada localmente, pero no se pudo sincronizar con el microservicio')
            
            messages.success(request, 'Configuración actualizada.')
            return redirect('dashboard')
    else:
        from .forms import ConfigAgenteForm
        form = ConfigAgenteForm(instance=config)
    
    return render(request, 'config_agente.html', {'form': form})

@login_required
def predicciones_riesgo_view(request):
    torch.manual_seed(0)  # Semilla fija para reproducibilidad
    model = SimpleRiskModel()
    # RF11
    config = ConfigAgente.objects.first()
    umbral_bajo = config.umbral_bajo if config else 3.0
    umbral_medio = config.umbral_medio if config else 4.0

    # Modelo simple de IA con PyTorch
    model = SimpleRiskModel()
    # Placeholder para entrenamiento: usar datos dummy o reales
    # En producción, entrenar con datos históricos
    # Ejemplo simple: clasificar basado en promedio
    estudiantes = Estudiante.objects.all()
    riesgos = {}
    for estudiante in estudiantes:
        promedio = Calificacion.objects.filter(estudiante=estudiante).aggregate(Avg('nota'))['nota__avg'] or 0
        input_tensor = Variable(torch.tensor([[promedio]]).float())
        output = model(input_tensor)
        riesgo_idx = torch.argmax(output).item()
        riesgo = ['Bajo', 'Medio', 'Alto'][riesgo_idx]
        riesgos[estudiante] = riesgo
        # RF12: Enviar alerta si riesgo alto
        if riesgo == 'Alto':
            send_mail(
                'Alerta de Riesgo Académico',
                f'Estimado {estudiante.usuario.first_name} {estudiante.usuario.last_name}, se ha detectado un riesgo alto en tu rendimiento.',
                'your_email@gmail.com',
                [estudiante.usuario.email]
        )
    if request.user.role == 'admin':
        return render(request, 'dashboard_admin.html', {'riesgos': riesgos})
    elif request.user.role == 'estudiante':
        estudiante = Estudiante.objects.get(usuario=request.user)
        riesgo = riesgos.get(estudiante, 'Bajo')
        return render(request, 'dashboard_estudiante.html', {'riesgo': riesgo})
    return redirect('dashboard')

@login_required
def comparativos_cohorte_view(request):
    # RF13
    if request.user.role != 'admin':
        messages.error(request, 'Solo los administradores pueden ver comparativos de cohorte.')
        return redirect('dashboard')
    
    # Comparativo por curso
    cursos = Curso.objects.annotate(
        promedio_curso=Avg('calificaciones__nota'),
        total_calificaciones=Count('calificaciones'),
        aprobados=Count('calificaciones', filter=Q(calificaciones__nota__gte=3.0))
    ).prefetch_related('calificaciones')
    
    # Comparativo por profesor
    profesores = CustomUser.objects.filter(role='profesor').annotate(
        promedio_profesor=Avg('curso__calificaciones__nota'),
        total_calificaciones=Count('curso__calificaciones'),
        aprobados=Count('curso__calificaciones', filter=Q(curso__calificaciones__nota__gte=3.0))
    ).prefetch_related('curso_set__calificaciones')
    
    # Cálculos adicionales
    for curso in cursos:
        curso.porcentaje_aprobacion = (curso.aprobados / curso.total_calificaciones * 100) if curso.total_calificaciones > 0 else 0
    
    for profesor in profesores:
        profesor.porcentaje_aprobacion = (profesor.aprobados / profesor.total_calificaciones * 100) if profesor.total_calificaciones > 0 else 0
    
    return render(request, 'comparativos_cohorte.html', {
        'cursos': cursos,
        'profesores': profesores,
    })

def healthz(request):
    """
    Healthcheck simple:
    - Devuelve 200 {"status": "ok"} si Django está arriba.
    - Intenta una conexión rápida a la DB; si falla, devuelve 500 y detalle.
    """
    db_ok = True
    db_error = None
    try:
        # Intento de conexión simple y rápida (no cursor.execute pesado)
        connection = connections['default']
        connection.cursor()
    except OperationalError as e:
        db_ok = False
        db_error = str(e)

    if not db_ok:
        return JsonResponse({"status": "error", "db": "unavailable", "detail": db_error}, status=500)

    return JsonResponse({"status": "ok"}, status=200)