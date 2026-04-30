import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from tests.conftest import register_and_login, TEST_CODE

VALID_PATIENT = {"full_name": "Jane Doe", "birth_date": "1990-05-15"}


# ── Registration ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json={
        "email": "doc@example.com", "password": "password123", "role": "doctor",
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    data = {"email": "dup@example.com", "password": "password123", "role": "client"}
    await client.post("/auth/register", json=data)
    resp = await client.post("/auth/register", json=data)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_weak_password(client):
    resp = await client.post("/auth/register", json={
        "email": "x@example.com", "password": "short", "role": "client",
    })
    assert resp.status_code == 422


# ── Verification ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_correct_code(client):
    await client.post("/auth/register", json={
        "email": "v@example.com", "password": "password123", "role": "client",
    })
    resp = await client.post("/auth/verify", json={"email": "v@example.com", "code": TEST_CODE})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_verify_wrong_code(client):
    await client.post("/auth/register", json={
        "email": "w@example.com", "password": "password123", "role": "client",
    })
    resp = await client.post("/auth/verify", json={"email": "w@example.com", "code": "000000"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_before_verify_blocked(client):
    await client.post("/auth/register", json={
        "email": "unverified@example.com", "password": "password123", "role": "client",
    })
    resp = await client.post("/auth/login", json={
        "email": "unverified@example.com", "password": "password123",
    })
    assert resp.status_code == 403


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    token = await register_and_login(client, "login@example.com", "doctor")
    assert token  # non-empty JWT string


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await register_and_login(client, "lp@example.com", "client")
    resp = await client.post("/auth/login", json={
        "email": "lp@example.com", "password": "wrongpassword",
    })
    assert resp.status_code == 401


# ── Patient endpoints — role enforcement ──────────────────────────────────────

@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.get("/patients/")
    assert resp.status_code == 403  # HTTPBearer returns 403 when header is absent


@pytest.mark.asyncio
async def test_doctor_can_list_patients(client):
    token = await register_and_login(client, "dr@example.com", "doctor")
    resp = await client.get("/patients/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_client_cannot_list_patients(client):
    token = await register_and_login(client, "cl@example.com", "client")
    resp = await client.get("/patients/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_patient_as_doctor(client):
    token = await register_and_login(client, "dr2@example.com", "doctor")
    resp = await client.post("/patients/", json=VALID_PATIENT,
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert "id" in resp.json()


@pytest.mark.asyncio
async def test_create_patient_as_client(client):
    token = await register_and_login(client, "cl2@example.com", "client")
    resp = await client.post("/patients/", json=VALID_PATIENT,
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_client_can_get_own_patient(client):
    token = await register_and_login(client, "cl3@example.com", "client")
    auth = {"Authorization": f"Bearer {token}"}
    pid = (await client.post("/patients/", json=VALID_PATIENT, headers=auth)).json()["id"]
    resp = await client.get(f"/patients/{pid}", headers=auth)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_client_cannot_get_other_patient(client):
    doc_token = await register_and_login(client, "dr3@example.com", "doctor")
    cl_token  = await register_and_login(client, "cl4@example.com", "client")
    # Doctor creates a patient (owned by doctor, not the client)
    pid = (await client.post("/patients/", json=VALID_PATIENT,
                             headers={"Authorization": f"Bearer {doc_token}"})).json()["id"]
    resp = await client.get(f"/patients/{pid}",
                            headers={"Authorization": f"Bearer {cl_token}"})
    assert resp.status_code == 403


# ── Validation ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_future_birth_date_rejected(client):
    token = await register_and_login(client, "dr4@example.com", "doctor")
    resp = await client.post("/patients/",
                             json={"full_name": "X", "birth_date": "2099-01-01"},
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pagination(client):
    token = await register_and_login(client, "dr5@example.com", "doctor")
    auth = {"Authorization": f"Bearer {token}"}
    for i in range(3):
        await client.post("/patients/",
                          json={"full_name": f"P{i}", "birth_date": "1990-01-01"},
                          headers=auth)
    resp = await client.get("/patients/?limit=2&offset=0", headers=auth)
    assert resp.status_code == 200
    assert len(resp.json()) <= 2
