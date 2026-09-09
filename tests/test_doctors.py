def test_create_and_retrieve_doctor(client):
    created = client.post(
        "/doctors",
        json={"name": "Dr. Example", "specialty": "General Medicine", "available": True},
    )

    assert created.status_code == 201
    assert created.json()["id"] == 1

    retrieved = client.get("/doctors/1")
    assert retrieved.status_code == 200
    assert retrieved.json() == created.json()


def test_missing_doctor_returns_not_found(client):
    response = client.get("/doctors/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Doctor 999 was not found"
