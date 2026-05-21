from sqlalchemy import select

from app.models import AuditLog


async def test_create_patient(client):
    response = await client.post(
        "/patients",
        json={"full_name": "Ada Lovelace", "birth_date": "1815-12-10"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["full_name"] == "Ada Lovelace"
    assert body["birth_date"] == "1815-12-10"
    assert "created_at" in body


async def test_create_patient_rejects_invalid_input(client):
    response = await client.post(
        "/patients",
        json={"full_name": "", "birth_date": "not-a-date"},
    )

    assert response.status_code == 422


async def test_create_patient_rejects_blank_name(client):
    response = await client.post(
        "/patients",
        json={"full_name": "   ", "birth_date": "1990-01-01"},
    )

    assert response.status_code == 422


async def test_create_patient_writes_audit_log(client):
    await client.post(
        "/patients",
        json={"full_name": "Grace Hopper", "birth_date": "1906-12-09"},
    )

    Session = client._transport.app.state.session_factory
    async with Session() as session:
        result = await session.execute(select(AuditLog))
        audit_log = result.scalar_one()
        assert audit_log.action == "patient_created"
        assert audit_log.patient_id == 1
        assert audit_log.details["full_name"] == "Grace Hopper"


async def test_health_check(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_frontend_page_is_served(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert "Patient registration" in response.text
    assert 'id="patient-form"' in response.text


async def test_frontend_assets_are_served(client):
    script_response = await client.get("/app.js")
    styles_response = await client.get("/styles.css")

    assert script_response.status_code == 200
    assert 'fetch("/patients"' in script_response.text
    assert styles_response.status_code == 200
    assert ".panel" in styles_response.text
