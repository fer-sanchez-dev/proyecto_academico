from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico válido.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrador'),
        ('profesor', 'Profesor'),
        ('estudiante', 'Estudiante'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='estudiante')
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=30, blank=False, null=False)
    
    # Redefinir username para que sea opcional
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        default=None
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    class Meta:
        swappable = 'AUTH_USER_MODEL'

class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    profesor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'profesor'})

    def __str__(self):
        return self.nombre

class Estudiante(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='estudiante')
    matricula = models.CharField(max_length=20, unique=True, blank=True, null=True)
    carrera = models.CharField(max_length=100, blank=True, null=True)
    # ✅ NUEVA LÍNEA: Relación Many-to-Many con Curso
    cursos = models.ManyToManyField(Curso, blank=True, related_name='estudiantes')

    def __str__(self):
        if self.usuario:  # Cambiar user por usuario
            first_name = self.usuario.first_name or 'Sin nombre'
            last_name = self.usuario.last_name or 'Sin apellido'
            return f"{first_name} {last_name}"
        return f"Estudiante {self.id or 'sin ID'}"

class Calificacion(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="calificaciones")
    nota = models.FloatField()
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.estudiante} - {self.curso} - {self.nota}"

class Alerta(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    nivel_riesgo = models.CharField(max_length=50, default='Bajo')

    def __str__(self):
        return f"Alerta para {self.estudiante}: {self.mensaje}"
    
class ConfigAgente(models.Model):
    umbral_bajo = models.FloatField(default=3.0)
    umbral_medio = models.FloatField(default=4.0)
    frecuencia_alertas = models.CharField(max_length=50, choices=[('diaria', 'Diaria'), ('semanal', 'Semanal')], default='semanal')
    criterios_recomendacion = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Configuraciones del Agente"