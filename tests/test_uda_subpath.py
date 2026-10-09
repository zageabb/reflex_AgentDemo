"""Verify proxy-derived URL generation using the full WSGI stack."""
from app import create_app

def test_prefix_and_lan():
    app = create_app()
    client = app.test_client()
    headers = {
        "X-Forwarded-Prefix": "/apps/reflex-agent-demo",
        "X-Forwarded-Host": "tanyaanne.ddns.net",
        "X-Forwarded-Proto": "https",
    }
    local = client.get("/", follow_redirects=True)
    proxied = client.get("/", headers=headers, follow_redirects=True)
    assert local.status_code == 200
    assert proxied.status_code == 200
    assert b'/static/css/styles.css' in local.data
    assert b'/apps/reflex-agent-demo/static/css/styles.css' in proxied.data
