from django.urls import path, include
from django.contrib import admin
from app.views import healthz
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_view, name='home'),  # Página de inicio redirige al login
    path('admin/', admin.site.urls),
    path("healthz/", views.healthz, name="healthz"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('calificaciones/registrar/', views.registrar_calificacion, name='registrar_calificacion'),
    path('alertas/', views.alertas_view, name='alertas'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'), name='password_reset_done'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('calificaciones/gestionar/', views.gestionar_calificaciones, name='gestionar_calificaciones'),
    path('materias/gestionar/', views.gestionar_materias, name='gestionar_materias'),
    path('reportes/', views.generar_reportes, name='generar_reportes'),  # RF09
    path('config_agente/', views.config_agente_view, name='config_agente'),  # RF10
    path('predicciones_riesgo/', views.predicciones_riesgo_view, name='predicciones_riesgo'),  # RF11
    path('comparativos_cohorte/', views.comparativos_cohorte_view, name='comparativos_cohorte'),  # RF13
    path('estudiantes/editar/<int:estudiante_id>/', views.editar_estudiante, name='editar_estudiante'),
    path('estudiantes/eliminar/<int:estudiante_id>/', views.eliminar_estudiante, name='eliminar_estudiante'),
    path('cursos/editar/<int:curso_id>/', views.editar_curso, name='editar_curso'),
    path('cursos/eliminar/<int:curso_id>/', views.eliminar_curso, name='eliminar_curso'),
]