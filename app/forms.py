from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import CustomUser, Calificacion, Curso, ConfigAgente, Estudiante

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    email = forms.EmailField(required=True, label="Correo Electrónico")
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'role')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = None  # Dejar username como NULL
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')

class PerfilForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
            'password': 'Nueva Contraseña',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name').strip()
        if len(first_name) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name').strip()
        if len(last_name) < 2:
            raise forms.ValidationError('El apellido debe tener al menos 2 caracteres.')
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email').strip()
        if CustomUser.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
            if not any(c.isupper() for c in password):
                raise forms.ValidationError('La contraseña debe contener al menos una mayúscula.')
            if not any(c.islower() for c in password):
                raise forms.ValidationError('La contraseña debe contener al menos una minúscula.')
            if not any(c.isdigit() for c in password):
                raise forms.ValidationError('La contraseña debe contener al menos un número.')
        return password

class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ('estudiante', 'curso', 'nota', 'descripcion')
        widgets = {
            'estudiante': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'curso': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'nota': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '5',
                'step': '0.1',
                'placeholder': 'Ej: 4.5'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la evaluación...'
            })
        }
        labels = {
            'estudiante': 'Estudiante',
            'curso': 'Curso/Materia',
            'nota': 'Calificación (0-5)',
            'descripcion': 'Descripción'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extrae el argumento user
        super(CalificacionForm, self).__init__(*args, **kwargs)
        
        if user and hasattr(user, 'role') and user.role == 'profesor':
            if not self.instance.pk:  # Solo filtrar si es una nueva calificación
                # Mostrar todos los estudiantes (sin restricciones de inscripción)
                self.fields['estudiante'].queryset = Estudiante.objects.all()
                
                # Filtrar cursos del profesor
                self.fields['curso'].queryset = Curso.objects.filter(profesor=user)
                
                # Mejorar la visualización del nombre del estudiante
                def estudiante_label(obj):
                    return f"{obj.usuario.first_name} {obj.usuario.last_name}"
                
                self.fields['estudiante'].label_from_instance = estudiante_label
            
            # Añadir mensaje de ayuda si no hay opciones disponibles
            if not self.fields['estudiante'].queryset.exists():
                self.fields['estudiante'].help_text = "No hay estudiantes con calificaciones previas en tus cursos."
            if not self.fields['curso'].queryset.exists():
                self.fields['curso'].help_text = "No tienes cursos asignados."

    def clean_nota(self):
        nota = self.cleaned_data.get('nota')
        if nota is not None:
            if nota < 0 or nota > 5:
                raise forms.ValidationError('La calificación debe estar entre 0.0 y 5.0.')
        return nota

    def clean(self):
        cleaned_data = super().clean()
        estudiante = cleaned_data.get('estudiante')
        curso = cleaned_data.get('curso')
        
        if estudiante and curso:
            # SOLO validar duplicados si NO estamos editando una calificación existente
            if not self.instance.pk:  # Solo para nuevas calificaciones
                if Calificacion.objects.filter(estudiante=estudiante, curso=curso).exists():
                    raise forms.ValidationError(
                        f'Ya existe una calificación para {estudiante.usuario.first_name} {estudiante.usuario.last_name} en el curso {curso.nombre}.'
                    )
            else:
                # Si estamos editando, verificar que no exista OTRA calificación diferente para la misma combinación
                existing_calificaciones = Calificacion.objects.filter(
                    estudiante=estudiante, 
                    curso=curso
                ).exclude(pk=self.instance.pk)
                
                if existing_calificaciones.exists():
                    raise forms.ValidationError(
                        f'Ya existe otra calificación para {estudiante.usuario.first_name} {estudiante.usuario.last_name} en el curso {curso.nombre}.'
                    )
        
        return cleaned_data

class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ['usuario', 'matricula', 'carrera']  # ✅ Correcto: 'usuario'
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),  # ✅ Cambiado: era 'user'
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'carrera': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'usuario': 'Usuario',  # ✅ Cambiado: era 'user'
            'matricula': 'Matrícula',
            'carrera': 'Carrera',
        }

    def clean_usuario(self):  # ✅ Cambiado: era 'clean_user'
        usuario = self.cleaned_data.get('usuario')  # ✅ Cambiado: era 'user'
        if not usuario:
            raise forms.ValidationError('Debe seleccionar un usuario.')
        if Estudiante.objects.filter(usuario=usuario).exclude(id=self.instance.id).exists():  # ✅ Cambiado: era 'user=user'
            raise forms.ValidationError('Este usuario ya está asociado a otro estudiante.')
        return usuario  # ✅ Cambiado: era 'user'

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if matricula and len(matricula) < 3:
            raise forms.ValidationError('La matrícula debe tener al menos 3 caracteres.')
        return matricula

class CustomUserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name').strip()
        if len(first_name) < 2:
            raise forms.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name').strip()
        if len(last_name) < 2:
            raise forms.ValidationError('El apellido debe tener al menos 2 caracteres.')
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email').strip()
        if CustomUser.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Este correo ya está en uso por otro usuario.")
        return email

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre', 'descripcion', 'profesor']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profesor'].queryset = CustomUser.objects.filter(role='profesor')
        if not self.fields['profesor'].queryset.exists():
            self.fields['profesor'].queryset = CustomUser.objects.none()

class ConfigAgenteForm(forms.ModelForm):
    class Meta:
        model = ConfigAgente
        fields = ('umbral_bajo', 'umbral_medio', 'frecuencia_alertas', 'criterios_recomendacion')