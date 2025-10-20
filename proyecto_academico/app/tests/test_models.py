import pytest
from app.models import Estudiante  # ajusta import según tu modelo

@pytest.mark.django_db
def test_estudiante_creation(normal_user):
    e = Estudiante.objects.create(usuario=normal_user, matricula='2025-001', carrera='Ingenieria')
    assert e.matricula == '2025-001'
    assert str(e.usuario).startswith(normal_user.first_name)
