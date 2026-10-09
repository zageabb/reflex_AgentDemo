"""UDA prefix smoke test with existing page routes."""
from app import create_app

def test_prefix_and_lan():
    app=create_app()
    client=app.test_client()
    headers={"X-Forwarded-Prefix":"/apps/reflex-agent-demo","X-Forwarded-Host":"tanyaanne.ddns.net","X-Forwarded-Proto":"https"}
    # Redirects are permitted for authentication.
    for h in ({},headers):
        r=client.get("/")
        assert r.status_code in (200,301,302,303,307,308)
        assert app.wsgi_app is not None
    with app.test_request_context("/",headers=headers):
        from flask import url_for
        assert url_for("static",filename="css/styles.css").startswith("/apps/reflex-agent-demo/")
    with app.test_request_context("/"):
        from flask import url_for
        assert url_for("static",filename="css/styles.css")=="/static/css/styles.css"
