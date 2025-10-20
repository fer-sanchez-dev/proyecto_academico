import pytest
from app.forms import (
    CustomUserCreationForm, PerfilForm, CalificacionForm,
    EstudianteForm, CustomUserEditForm, CursoForm
)
from app.models import CustomUser, Estudiante, Curso, Calificacion
from django.core.exceptions import ValidationError

# ============================
# 🔹 CustomUserCreationForm
# ============================

@pytest.mark.django_db
def test_user_creation_form_valid():
    form = CustomUserCreationForm(data={
        "email": "nuevo@test.com",
        "first_name": "Nuevo",
        "last_name": "Usuario",
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "role": "estudiante",
    })
    assert form.is_valid()
    user = form.save()
    assert user.email == "nuevo@test.com"
    assert user.username is None


@pytest.mark.django_db
def test_user_creation_form_duplicate_email(normal_user):
    form = CustomUserCreationForm(data={
        "email": "user@test.com",
        "first_name": "Otro",
        "last_name": "Usuario",
        "password1": "AnotherPass123",
        "password2": "AnotherPass123",
        "role": "profesor",
    })
    assert not form.is_valid()
    assert "correo electrónico ya está registrado" in str(form.errors).lower()


# ============================
# 🔹 PerfilForm
# ============================

@pytest.mark.django_db
def test_perfil_form_valid(normal_user):
    form = PerfilForm(instance=normal_user, data={
        "first_name": "NuevoNombre",
        "last_name": "NuevoApellido",
        "email": "nuevo@test.com",
        "password": "Pass123A"
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_perfil_form_invalid_password(normal_user):
    form = PerfilForm(instance=normal_user, data={
        "first_name": "N",
        "last_name": "A",
        "email": "nuevo@test.com",
        "password": "abc"
    })
    assert not form.is_valid()
    assert "debe tener al menos" in str(form.errors).lower()


# ============================
# 🔹 EstudianteForm
# ============================

@pytest.mark.django_db
def test_estudiante_form_valid(normal_user):
    form = EstudianteForm(data={
        "usuario": normal_user.id,
        "matricula": "ABC123",
        "carrera": "Ingeniería"
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_estudiante_form_duplicate_user(normal_user):
    Estudiante.objects.create(usuario=normal_user, matricula="M1", carrera="Sistemas")
    form = EstudianteForm(data={
        "usuario": normal_user.id,
        "matricula": "M2",
        "carrera": "Informática"
    })
    assert not form.is_valid()
    assert "ya está asociado" in str(form.errors).lower()


# ============================
# 🔹 CursoForm
# ============================

@pytest.mark.django_db
def test_curso_form_filters_profesores(admin_user, normal_user):
    form = CursoForm()
    profesores = list(form.fields["profesor"].queryset)
    assert admin_user in profesores  # porque es superuser
    assert normal_user not in profesores


# ============================
# 🔹 CustomUserEditForm
# ============================

@pytest.mark.django_db
def test_user_edit_form_valid(normal_user):
    form = CustomUserEditForm(instance=normal_user, data={
        "first_name": "Juan",
        "last_name": "Perez",
        "email": "nuevoedit@test.com"
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_user_edit_form_duplicate_email(normal_user):
    otro = CustomUser.objects.create_user(
        email="dup@test.com", password="testpass123", first_name="A", last_name="B", role="profesor"
    )
    form = CustomUserEditForm(instance=normal_user, data={
        "first_name": "Test",
        "last_name": "User",
        "email": "dup@test.com"
    })
    assert not form.is_valid()
    assert "correo" in str(form.errors).lower()
