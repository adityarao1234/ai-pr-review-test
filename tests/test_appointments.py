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


def test_update_appointment_status(client):
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
        f"/appointments/{appointment['id']}/status",
        json={"status": "completed"},
    )

    assert response.status_code == 200
    assert response.json() == {**appointment, "status": "completed"}


def test_update_appointment_status_allows_each_supported_status(client):
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

    for appointment_status in ("cancelled", "scheduled", "completed"):
        response = client.patch(
            f"/appointments/{appointment['id']}/status",
            json={"status": appointment_status},
        )

        assert response.status_code == 200
        assert response.json()["status"] == appointment_status


def test_update_status_for_nonexistent_appointment_returns_not_found(client):
    response = client.patch("/appointments/999/status", json={"status": "completed"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment 999 was not found"


def test_update_status_rejects_unsupported_status(client):
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
        f"/appointments/{appointment['id']}/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Unsupported appointment status: in_progress"
