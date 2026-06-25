from app.main import app
from tests.api_client import ASGITestClient


def test_health_endpoint():
    response = ASGITestClient(app).get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
