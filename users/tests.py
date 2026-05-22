import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


User = get_user_model()


@pytest.mark.django_db
def test_register_and_login_flow():
    client = APIClient()
    register_response = client.post(
        '/api/users/register/',
        {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'subscription_tier': 'free',
        },
        format='json',
    )
    assert register_response.status_code == 201

    login_response = client.post(
        '/api/users/login/',
        {'username': 'newuser', 'password': 'StrongPass123!'},
        format='json',
    )
    assert login_response.status_code == 200
    assert 'access' in login_response.data
    assert 'refresh' in login_response.data


@pytest.mark.django_db
def test_me_endpoint_returns_profile():
    user = User.objects.create_user(username='meuser', password='StrongPass123!')
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get('/api/users/me/')

    assert response.status_code == 200
    assert response.data['username'] == 'meuser'


@pytest.mark.django_db
def test_refresh_token_returns_new_access_token():
    client = APIClient()
    User.objects.create_user(username='tokenuser', password='StrongPass123!')

    login_response = client.post(
        '/api/users/login/',
        {'username': 'tokenuser', 'password': 'StrongPass123!'},
        format='json',
    )
    refresh_response = client.post(
        '/api/users/token/refresh/',
        {'refresh': login_response.data['refresh']},
        format='json',
    )

    assert refresh_response.status_code == 200
    assert 'access' in refresh_response.data
