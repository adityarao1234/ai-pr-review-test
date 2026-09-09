def test_create_and_retrieve_patient(client):
    created = client.post(
        "/patients", json={"name": "Test Patient", "age": 34, "phone": "555-0101"}
    )

    assert created.status_code == 201
    assert created.json()["id"] == 1

    retrieved = client.get("/patients/1")
    assert retrieved.status_code == 200
    assert retrieved.json() == created.json()


def test_missing_patient_returns_not_found(client):
    response = client.get("/patients/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient 999 was not found"
