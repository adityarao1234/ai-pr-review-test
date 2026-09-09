"""Doctor domain models and in-memory storage."""

from dataclasses import dataclass


class DoctorNotFoundError(LookupError):
    """Raised when a requested doctor does not exist."""


@dataclass(frozen=True)
class Doctor:
    id: int
    name: str
    specialty: str
    available: bool


class DoctorService:
    def __init__(self) -> None:
        self._doctors: dict[int, Doctor] = {}
        self._next_id = 1

    def create(self, name: str, specialty: str, available: bool) -> Doctor:
        doctor = Doctor(
            id=self._next_id,
            name=name,
            specialty=specialty,
            available=available,
        )
        self._doctors[doctor.id] = doctor
        self._next_id += 1
        return doctor

    def get(self, doctor_id: int) -> Doctor:
        try:
            return self._doctors[doctor_id]
        except KeyError as error:
            raise DoctorNotFoundError(f"Doctor {doctor_id} was not found") from error

    def reset(self) -> None:
        """Clear state; intended for test isolation."""
        self._doctors.clear()
        self._next_id = 1


doctor_service = DoctorService()
