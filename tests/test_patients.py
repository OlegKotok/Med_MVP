"""
Full MVP test suite.
Covers: registration, email sending (mocked), verification (+ expiry),
login, password reset, doctor listing, patient CRUD + roles,
appointment booking + doctor email notification, role enforcement.
"""
import pytest
from unittest.mock import patch, call
from httpx import AsyncClient, ASGITransport
from app.main import app
from tests.conftest import register_and_login, TEST_CODE

VALID_PATIENT = {"full_name": "Jane Doe", "birth_date": "1990-05-15"}
FUTURE_DT = "2099-01-15T10:00:00+00:00"


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — Registration
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_register_sends_verification_email(client):
    """Registration must trigger send_verification_email with the user's address."""
    with patch("app.auth_service.send_verification_email") as mock_send:
        resp = await client.post("/auth/register", json={
            "email": "new@example.com", "password": "password123", "role": "client",
        })
    assert resp.status_code == 201
    mock_send.assert_called_once_with("new@example.com", TEST_CODE)


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


@pytest.mark.asyncio
async def test_register_invalid_role(client):
    resp = await client.post("/auth/register", json={
        "email": "x@example.com", "password": "password123", "role": "admin",
    })
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — Verification
# ═══════════════════════════════════════════════════════════════════════════════

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
async def test_verify_expired_code(client, monkeypatch):
    """Simulate an expired code by patching _is_expired to always return True."""
    import app.auth_service as svc

    await client.post("/auth/register", json={
        "email": "exp@example.com", "password": "password123", "role": "client",
    })
    monkeypatch.setattr(svc, "_is_expired", lambda dt: True)
    resp = await client.post("/auth/verify", json={"email": "exp@example.com", "code": TEST_CODE})
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


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — Login
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_login_success(client):
    token = await register_and_login(client, "login@example.com", "doctor")
    assert token


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await register_and_login(client, "lp@example.com", "client")
    resp = await client.post("/auth/login", json={
        "email": "lp@example.com", "password": "wrongpassword",
    })
    assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH — Password reset
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_forgot_password_sends_email(client):
    await register_and_login(client, "reset@example.com", "client")
    with patch("app.auth_service.send_password_reset_email") as mock_send:
        resp = await client.post("/auth/forgot-password", json={"email": "reset@example.com"})
    assert resp.status_code == 200
    mock_send.assert_called_once_with("reset@example.com", TEST_CODE)


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_no_leak(client):
    """Must return 200 even for unknown emails — don't reveal account existence."""
    resp = await client.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_flow(client):
    await register_and_login(client, "pw@example.com", "client")
    await client.post("/auth/forgot-password", json={"email": "pw@example.com"})
    resp = await client.post("/auth/reset-password", json={
        "email": "pw@example.com", "code": TEST_CODE, "new_password": "newpassword99",
    })
    assert resp.status_code == 200
    # Can now log in with new password
    login_resp = await client.post("/auth/login", json={
        "email": "pw@example.com", "password": "newpassword99",
    })
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_wrong_code(client):
    await register_and_login(client, "pw2@example.com", "client")
    await client.post("/auth/forgot-password", json={"email": "pw2@example.com"})
    resp = await client.post("/auth/reset-password", json={
        "email": "pw2@example.com", "code": "000000", "new_password": "newpassword99",
    })
    assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# Doctors listing
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_list_doctors_public(client):
    """GET /auth/doctors is public — no token required."""
    await register_and_login(client, "dr_list@example.com", "doctor")
    resp = await client.get("/auth/doctors")
    assert resp.status_code == 200
    emails = [d["email"] for d in resp.json()]
    assert "dr_list@example.com" in emails


@pytest.mark.asyncio
async def test_list_doctors_excludes_clients(client):
    await register_and_login(client, "cl_excl@example.com", "client")
    resp = await client.get("/auth/doctors")
    emails = [d["email"] for d in resp.json()]
    assert "cl_excl@example.com" not in emails


# ═══════════════════════════════════════════════════════════════════════════════
# Patients — role enforcement
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_unauthenticated_rejected(client):
    resp = await client.get("/patients/")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_doctor_can_list_patients(client):
    token = await register_and_login(client, "dr_p@example.com", "doctor")
    resp = await client.get("/patients/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_client_cannot_list_patients(client):
    token = await register_and_login(client, "cl_p@example.com", "client")
    resp = await client.get("/patients/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_patient_as_doctor(client):
    token = await register_and_login(client, "dr2@example.com", "doctor")
    resp = await client.post("/patients/", json=VALID_PATIENT,
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201


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
    assert (await client.get(f"/patients/{pid}", headers=auth)).status_code == 200


@pytest.mark.asyncio
async def test_client_cannot_get_other_patient(client):
    doc_token = await register_and_login(client, "dr3@example.com", "doctor")
    cl_token  = await register_and_login(client, "cl4@example.com", "client")
    pid = (await client.post("/patients/", json=VALID_PATIENT,
                             headers={"Authorization": f"Bearer {doc_token}"})).json()["id"]
    resp = await client.get(f"/patients/{pid}", headers={"Authorization": f"Bearer {cl_token}"})
    assert resp.status_code == 403


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
        await client.post("/patients/", json={"full_name": f"P{i}", "birth_date": "1990-01-01"}, headers=auth)
    resp = await client.get("/patients/?limit=2&offset=0", headers=auth)
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


# ═══════════════════════════════════════════════════════════════════════════════
# Appointments
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_book_appointment_sends_doctor_email(client):
    """Booking must trigger send_appointment_notification to the doctor."""
    doc_token = await register_and_login(client, "dr_appt@example.com", "doctor")
    cl_token  = await register_and_login(client, "cl_appt@example.com", "client")

    # Get doctor's id from the public doctors list
    doctors = (await client.get("/auth/doctors")).json()
    doctor_id = next(d["id"] for d in doctors if d["email"] == "dr_appt@example.com")

    with patch("app.appointment_service.send_appointment_notification") as mock_notify:
        resp = await client.post("/appointments/", json={
            "doctor_id": doctor_id,
            "scheduled_at": FUTURE_DT,
            "notes": "First visit",
        }, headers={"Authorization": f"Bearer {cl_token}"})

    assert resp.status_code == 201
    mock_notify.assert_called_once()
    args = mock_notify.call_args
    assert args.kwargs["doctor_email"] == "dr_appt@example.com"
    assert args.kwargs["client_email"] == "cl_appt@example.com"


@pytest.mark.asyncio
async def test_book_appointment_nonexistent_doctor(client):
    cl_token = await register_and_login(client, "cl_bad@example.com", "client")
    resp = await client.post("/appointments/", json={
        "doctor_id": "00000000-0000-0000-0000-000000000000",
        "scheduled_at": FUTURE_DT,
    }, headers={"Authorization": f"Bearer {cl_token}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_book_appointment_past_time_rejected(client):
    doc_token = await register_and_login(client, "dr_past@example.com", "doctor")
    cl_token  = await register_and_login(client, "cl_past@example.com", "client")
    doctors = (await client.get("/auth/doctors")).json()
    doctor_id = next(d["id"] for d in doctors if d["email"] == "dr_past@example.com")

    resp = await client.post("/appointments/", json={
        "doctor_id": doctor_id,
        "scheduled_at": "2000-01-01T10:00:00+00:00",
    }, headers={"Authorization": f"Bearer {cl_token}"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_client_sees_own_appointments(client):
    doc_token = await register_and_login(client, "dr_mine@example.com", "doctor")
    cl_token  = await register_and_login(client, "cl_mine@example.com", "client")
    doctors = (await client.get("/auth/doctors")).json()
    doctor_id = next(d["id"] for d in doctors if d["email"] == "dr_mine@example.com")

    with patch("app.appointment_service.send_appointment_notification"):
        await client.post("/appointments/", json={
            "doctor_id": doctor_id, "scheduled_at": FUTURE_DT,
        }, headers={"Authorization": f"Bearer {cl_token}"})

    resp = await client.get("/appointments/", headers={"Authorization": f"Bearer {cl_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_doctor_sees_incoming_appointments(client):
    doc_token = await register_and_login(client, "dr_inc@example.com", "doctor")
    cl_token  = await register_and_login(client, "cl_inc@example.com", "client")
    doctors = (await client.get("/auth/doctors")).json()
    doctor_id = next(d["id"] for d in doctors if d["email"] == "dr_inc@example.com")

    with patch("app.appointment_service.send_appointment_notification"):
        await client.post("/appointments/", json={
            "doctor_id": doctor_id, "scheduled_at": FUTURE_DT,
        }, headers={"Authorization": f"Bearer {cl_token}"})

    resp = await client.get("/appointments/", headers={"Authorization": f"Bearer {doc_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_unauthenticated_cannot_book(client):
    resp = await client.post("/appointments/", json={
        "doctor_id": "00000000-0000-0000-0000-000000000000",
        "scheduled_at": FUTURE_DT,
    })
    assert resp.status_code == 403
