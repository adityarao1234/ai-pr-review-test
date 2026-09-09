"""Appointment business rules and FastAPI endpoints."""

from dataclasses import dataclass, replace
from datetime import date, time

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from src.doctors import Doctor, DoctorNotFoundError, doctor_service
from src.patients import Patient, PatientNotFoundError, patient_service

ALLOWED_APPOINTMENT_STATUSES = {"scheduled", "completed", "cancelled"}


class DoctorUnavailableError(ValueError):
    """Raised when an appointment is requested with an unavailable doctor."""


class AppointmentNotFoundError(LookupError):
    """Raised when a requested appointment does not exist."""


class AppointmentAlreadyCancelledError(ValueError):
    """Raised when cancellation is requested twice."""


class AppointmentNotScheduledError(ValueError):
    """Raised when an operation requires a scheduled appointment."""


class InvalidAppointmentStatusError(ValueError):
    """Raised when an unsupported appointment status is requested."""


@dataclass(frozen=True)
class Appointment:
    id: int
    patient_id: int
    doctor_id: int
    date: date
    time: time
    status: str = "scheduled"


class AppointmentService:
    def __init__(self) -> None:
        self._appointments: dict[int, Appointment] = {}
        self._next_id = 1

    def create(self, patient_id: int, doctor_id: int, appointment_date: date, appointment_time: time) -> Appointment:
        patient_service.get(patient_id)
        doctor = doctor_service.get(doctor_id)
        if not doctor.available:
            raise DoctorUnavailableError(f"Doctor {doctor_id} is not available")

        appointment = Appointment(
            id=self._next_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
        )
        self._appointments[appointment.id] = appointment
        self._next_id += 1
        return appointment

    def get(self, appointment_id: int) -> Appointment:
        try:
            return self._appointments[appointment_id]
        except KeyError as error:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} was not found") from error

    def cancel(self, appointment_id: int) -> Appointment:
        appointment = self.get(appointment_id)
        if appointment.status == "cancelled":
            raise AppointmentAlreadyCancelledError(
                f"Appointment {appointment_id} is already cancelled"
            )
        cancelled = replace(appointment, status="cancelled")
        self._appointments[appointment_id] = cancelled
        return cancelled

    def reschedule(
        self,
        appointment_id: int,
        appointment_date: date,
        appointment_time: time,
    ) -> Appointment:
        appointment = self.get(appointment_id)
        if appointment.status == "completed":
            raise AppointmentNotScheduledError(
                f"Appointment {appointment_id} is completed"
            )
        rescheduled = replace(
            appointment,
            date=appointment_date,
            time=appointment_time,
        )
        self._appointments[appointment_id] = rescheduled
        return rescheduled

    def update_status(self, appointment_id: int, appointment_status: str) -> Appointment:
        appointment = self.get(appointment_id)
        if appointment_status not in ALLOWED_APPOINTMENT_STATUSES:
            raise InvalidAppointmentStatusError(
                f"Unsupported appointment status: {appointment_status}"
            )
        updated_appointment = replace(appointment, status=appointment_status)
        self._appointments[appointment_id] = updated_appointment
        return updated_appointment

    def reset(self) -> None:
        """Clear state; intended for test isolation."""
        self._appointments.clear()
        self._next_id = 1


appointment_service = AppointmentService()


class PatientCreate(BaseModel):
    name: str = Field(min_length=1)
    age: int = Field(ge=0, le=130)
    phone: str = Field(min_length=1)


class DoctorCreate(BaseModel):
    name: str = Field(min_length=1)
    specialty: str = Field(min_length=1)
    available: bool


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    date: date
    time: time


class AppointmentReschedule(BaseModel):
    date: date
    time: time


class AppointmentStatusUpdate(BaseModel):
    status: str


app = FastAPI(title="Hospital Appointment API")


def not_found(error: LookupError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@app.post("/patients", status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate) -> Patient:
    return patient_service.create(**payload.model_dump())


@app.get("/patients/{patient_id}")
def get_patient(patient_id: int) -> Patient:
    try:
        return patient_service.get(patient_id)
    except PatientNotFoundError as error:
        raise not_found(error) from error


@app.post("/doctors", status_code=status.HTTP_201_CREATED)
def create_doctor(payload: DoctorCreate) -> Doctor:
    return doctor_service.create(**payload.model_dump())


@app.get("/doctors/{doctor_id}")
def get_doctor(doctor_id: int) -> Doctor:
    try:
        return doctor_service.get(doctor_id)
    except DoctorNotFoundError as error:
        raise not_found(error) from error


@app.post("/appointments", status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate) -> Appointment:
    try:
        return appointment_service.create(
            patient_id=payload.patient_id,
            doctor_id=payload.doctor_id,
            appointment_date=payload.date,
            appointment_time=payload.time,
        )
    except (PatientNotFoundError, DoctorNotFoundError) as error:
        raise not_found(error) from error
    except DoctorUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: int) -> Appointment:
    try:
        return appointment_service.get(appointment_id)
    except AppointmentNotFoundError as error:
        raise not_found(error) from error


@app.patch("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int) -> Appointment:
    try:
        return appointment_service.cancel(appointment_id)
    except AppointmentNotFoundError as error:
        raise not_found(error) from error
    except AppointmentAlreadyCancelledError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@app.patch("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: int, payload: AppointmentReschedule
) -> Appointment:
    try:
        return appointment_service.reschedule(
            appointment_id=appointment_id,
            appointment_date=payload.date,
            appointment_time=payload.time,
        )
    except AppointmentNotFoundError as error:
        raise not_found(error) from error
    except AppointmentNotScheduledError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@app.patch("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int, payload: AppointmentStatusUpdate
) -> Appointment:
    try:
        return appointment_service.update_status(appointment_id, payload.status)
    except AppointmentNotFoundError as error:
        raise not_found(error) from error
    except InvalidAppointmentStatusError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
