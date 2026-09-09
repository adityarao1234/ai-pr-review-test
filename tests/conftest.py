import pytest
from fastapi.testclient import TestClient

from src.appointments import app, appointment_service
from src.doctors import doctor_service
from src.patients import patient_service


@pytest.fixture(autouse=True)
def reset_in_memory_data():
    patient_service.reset()
    doctor_service.reset()
    appointment_service.reset()


@pytest.fixture
def client():
    return TestClient(app)
