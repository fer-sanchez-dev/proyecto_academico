import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_admin_login(client, admin_user):
    login = client.login(email='admin@test.com', password='adminpass123')
    assert login is True

    url = reverse('admin:index')
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"<title" in resp.content  # Solo valida que haya cargado una página HTML
