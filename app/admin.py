from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Curso, Estudiante, Calificacion, Alerta

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'profesor', 'descripcion')
    list_filter = ('profesor',)

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    # ✅ AGREGAMOS: Mostrar cantidad de cursos en la lista
    list_display = ('usuario', 'matricula', 'carrera', 'get_cursos_count')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'matricula')
    list_filter = ('carrera',)
    # ✅ AGREGAMOS: Interface horizontal para seleccionar múltiples cursos fácilmente
    filter_horizontal = ('cursos',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['usuario'].required = True
        return form
    
    # ✅ AGREGAMOS: Método para mostrar cantidad de cursos
    def get_cursos_count(self, obj):
        return obj.cursos.count()
    get_cursos_count.short_description = 'Cursos Inscritos'

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'nota', 'fecha')
    list_filter = ('curso', 'fecha')
    list_editable = ('nota',)

@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'nivel_riesgo', 'fecha', 'mensaje')
    list_filter = ('nivel_riesgo', 'fecha')
    readonly_fields = ('fecha',)