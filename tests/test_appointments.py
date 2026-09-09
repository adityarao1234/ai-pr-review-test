from datetime import date, timedelta


def create_patient(client):
    return client.post(
        "/patients", json={"name": "Demo Patient", "age": 29, "phone": "555-0102"}
    ).json()


def create_doctor(client, available=True):
    return client.post(
        "/doctors",
        json={"name": "Dr. Demo", "specialty": "Family Medicine", "available": available},
    ).json()


def test_create_appointment(client):
    patient = create_patient(client)
    doctor = create_doctor(client)

    response = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "date": "2030-01-15",
            "time": "09:30:00",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "patient_id": 1,
        "doctor_id": 1,
        "date": "2030-01-15",
        "time": "09:30:00",
        "status": "scheduled",
    }


def test_create_appointment_for_future_date(client):
    patient = create_patient(client)
    doctor = create_doctor(client)
    future_date = date.today() + timedelta(days=1)

    response = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "date": future_date.isoformat(),
            "time": "09:30:00",
        },
    )

    assert response.status_code == 201
    assert response.json()["date"] == future_date.isoformat()


def test_create_appointment_rejects_past_date(client):
    patient = create_patient(client)
    doctor = create_doctor(client)
    past_date = date.today() - timedelta(days=1)

    response = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "date": past_date.isoformat(),
            "time": "09:30:00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Appointments cannot be created for a past date"


def test_appointment_requires_existing_patient(client):
    doctor = create_doctor(client)

    response = client.post(
        "/appointments",
        json={"patient_id": 999, "doctor_id": doctor["id"], "date": "2030-01-15", "time": "09:30:00"},
    )

    assert response.status_code == 404


def test_appointment_requires_existing_doctor(client):
    patient = create_patient(client)

    response = client.post(
        "/appointments",
        json={"patient_id": patient["id"], "doctor_id": 999, "date": "2030-01-15", "time": "09:30:00"},
    )

    assert response.status_code == 404


def test_appointment_rejects_unavailable_doctor(client):
    patient = create_patient(client)
    doctor = create_doctor(client, available=False)

    response = client.post(
        "/appointments",
        json={"patient_id": patient["id"], "doctor_id": doctor["id"], "date": "2030-01-15", "time": "09:30:00"},
    )

    assert response.status_code == 409


def test_cancel_appointment(client):
    patient = create_patient(client)
    doctor = create_doctor(client)
    appointment = client.post(
        "/appointments",
        json={"patient_id": patient["id"], "doctor_id": doctor["id"], "date": "2030-01-15", "time": "09:30:00"},
    ).json()

    response = client.patch(f"/appointments/{appointment['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert client.get(f"/appointments/{appointment['id']}").json()["status"] == "cancelled"


def test_cannot_cancel_appointment_twice(client):
    patient = create_patient(client)
    doctor = create_doctor(client)
    appointment = client.post(
        "/appointments",
        json={"patient_id": patient["id"], "doctor_id": doctor["id"], "date": "2030-01-15", "time": "09:30:00"},
    ).json()

    client.patch(f"/appointments/{appointment['id']}/cancel")
    response = client.patch(f"/appointments/{appointment['id']}/cancel")

    assert response.status_code == 409
    assert response.json()["detail"] == "Appointment 1 is already cancelled"


def test_reschedule_appointment_preserves_other_fields(client):
    patient = create_patient(client)
    doctor = create_doctor(client)
    appointment = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "date": "2030-01-15",
            "time": "09:30:00",
        },
    ).json()

    response = client.patch(
        f"/appointments/{appointment['id']}/reschedule",
        json={"date": "2030-02-20", "time": "14:45:00"},
    )

    assert response.status_code == 200
    assert response.json() == {
        **appointment,
        "date": "2030-02-20",
        "time": "14:45:00",
    }


def test_reschedule_nonexistent_appointment_returns_not_found(client):
    response = client.patch(
        "/appointments/999/reschedule",
        json={"date": "2030-02-20", "time": "14:45:00"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment 999 was not found"


def test_cannot_reschedule_cancelled_appointment(client):
    patient = create_patient(client)
    doctor = create_doctor(client)
    appointment = client.post(
        "/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "date": "2030-01-15",
            "time": "09:30:00",
        },
    ).json()
    client.patch(f"/appointments/{appointment['id']}/cancel")

    response = client.patch(
        f"/appointments/{appointment['id']}/reschedule",
        json={"date": "2030-02-20", "time": "14:45:00"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Appointment 1 is not scheduled"
