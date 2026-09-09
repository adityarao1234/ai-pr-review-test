"""Patient domain models and in-memory storage."""

from dataclasses import dataclass


class PatientNotFoundError(LookupError):
    """Raised when a requested patient does not exist."""


@dataclass(frozen=True)
class Patient:
    id: int
    name: str
    age: int
    phone: str


class PatientService:
    def __init__(self) -> None:
        self._patients: dict[int, Patient] = {}
        self._next_id = 1

    def create(self, name: str, age: int, phone: str) -> Patient:
        patient = Patient(id=self._next_id, name=name, age=age, phone=phone)
        self._patients[patient.id] = patient
        self._next_id += 1
        return patient

    def get(self, patient_id: int) -> Patient:
        try:
            return self._patients[patient_id]
        except KeyError as error:
            raise PatientNotFoundError(f"Patient {patient_id} was not found") from error

    def reset(self) -> None:
        """Clear state; intended for test isolation."""
        self._patients.clear()
        self._next_id = 1


patient_service = PatientService()
