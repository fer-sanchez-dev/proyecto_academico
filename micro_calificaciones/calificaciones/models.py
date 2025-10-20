from django.db import models

class Calificacion(models.Model):
    # Relación indirecta con estudiante (ID proveniente del monolito)
    estudiante_id = models.IntegerField()
    curso_id = models.IntegerField()

    nota = models.FloatField()
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Estudiante {self.estudiante_id} - Curso {self.curso_id} - Nota {self.nota}"


class Alerta(models.Model):
    estudiante_id = models.IntegerField()
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    nivel_riesgo = models.CharField(max_length=50, default='Bajo')

    def __str__(self):
        return f"Alerta para estudiante {self.estudiante_id}: {self.mensaje}"


class ConfigAgente(models.Model):
    umbral_bajo = models.FloatField(default=3.0)
    umbral_medio = models.FloatField(default=4.0)
    frecuencia_alertas = models.CharField(
        max_length=50,
        choices=[('diaria', 'Diaria'), ('semanal', 'Semanal')],
        default='semanal'
    )
    criterios_recomendacion = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Configuraciones del Agente"

