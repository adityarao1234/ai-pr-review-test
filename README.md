# Hospital Appointment API

A small FastAPI demonstration service for creating patients and doctors, scheduling appointments, rescheduling appointments, updating appointment statuses, and cancelling appointments. It uses in-memory storage only, so data is reset when the application restarts.

This is a test and demonstration project, not a production healthcare system. Do not use it to store real patient or medical information.

## Install

Use Python 3.10 or newer, then install the dependencies:

```bash
python -m venv .venv
.venv\\Scripts\\activate  # Windows PowerShell
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn src.appointments:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`.

## Run tests

```bash
pytest
```

## Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/patients` | Create a patient. |
| `GET` | `/patients/{patient_id}` | Retrieve a patient. |
| `POST` | `/doctors` | Create a doctor. |
| `GET` | `/doctors/{doctor_id}` | Retrieve a doctor. |
| `POST` | `/appointments` | Create an appointment for an available doctor. |
| `GET` | `/appointments/{appointment_id}` | Retrieve an appointment. |
| `PATCH` | `/appointments/{appointment_id}/reschedule` | Reschedule a scheduled appointment. |
| `PATCH` | `/appointments/{appointment_id}/status` | Update an appointment status. |
| `PATCH` | `/appointments/{appointment_id}/cancel` | Cancel a scheduled appointment. |

Patients accept `name`, `age`, and `phone`. Doctors accept `name`, `specialty`, and `available`. Appointments accept `patient_id`, `doctor_id`, `date` (`YYYY-MM-DD`), and `time` (`HH:MM:SS`); their initial status is `scheduled`. Rescheduling accepts a new `date` and `time` and is available only while an appointment is scheduled. Status updates accept `scheduled`, `completed`, or `cancelled`.
