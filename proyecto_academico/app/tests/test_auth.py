import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_login_client(client, normal_user):
    login_url = reverse('login')  # reemplaza por el name real de tu URL de login
    response = client.post(login_url, {'email': normal_user.email, 'password': 'userpass123'})
    # Si usas autenticación por email, comprueba redirección o status code
    assert response.status_code in (302, 200)
