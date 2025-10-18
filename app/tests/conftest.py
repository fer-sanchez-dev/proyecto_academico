import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

@pytest.fixture
def admin_user(db):
    """Crea y devuelve un superusuario."""
    return User.objects.create_superuser(
        email="admin@test.com",
        password="adminpass123",
        first_name="Admin",
        last_name="Test",
        role="admin"
    )

@pytest.fixture
def normal_user(db):
    """Usuario normal."""
    return User.objects.create_user(
        email="user@test.com",
        password="userpass123",
        first_name="User",
        last_name="Test",
        role="estudiante"
    )
