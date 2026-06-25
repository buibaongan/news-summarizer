from app.main import app
from tests.api_client import ASGITestClient


def test_sources_endpoint_lists_configured_sources():
    response = ASGITestClient(app).get('/sources')

    assert response.status_code == 200
    names = [source['name'] for source in response.json()]
    assert 'BBC' in names
    assert 'Reuters' in names
