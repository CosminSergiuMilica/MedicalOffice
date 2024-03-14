from datetime import datetime, time, date

import bleach
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from bdpos.Appointments import Appointments
from bdpos.database import db
from typing import List, Optional
from bdpos.Patients import Patients
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
import grpc
import jwt
from utile import idmService_pb2_grpc, idmService_pb2
app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"
def grpc_client():
    channel = grpc.insecure_channel('proiect-api-users-service-1:50051')
    return idmService_pb2_grpc.IDMServiceStub(channel)
def sanitize_input(data: str):
    sanitized_data = bleach.clean(data)
    return sanitized_data
@app.on_event("startup")
def startup():
    if db.is_closed():
        try:
            db.connect()
        except ConnectionError:
            raise HTTPException(status_code=500, detail="Database connection failed")

class Appointment(BaseModel):
    id_appointment:int
    id_doctor: int
    id_patient: str
    date: str
    status: str

class AppointmentCreate(BaseModel):
    id_doctor: int
    id_patient: str
    date: str
    status: str

class AppointmentsList(BaseModel):
    total_appointments: int
    appointments: List[Appointment]
    _links: dict

class AppointmentResponse(BaseModel):
    message: str
    appointment_id: int
    _links: dict

@app.on_event("shutdown")
def shutdown():
    if not db.is_closed():
        db.close()

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="API Title", version="1.0.0", routes=app.routes))

@app.get("/appointments", response_model=AppointmentsList, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_appointments": 5, "appointments": [], "_links": {}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}}
})
def get_all_appointments(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        appointments = Appointments.select()
        total_appointments = appointments.count()
        appointment_list = [Appointment(
            id_appointment=appointment.id_appointment,
            id_doctor=appointment.id_doctor,
            id_patient=appointment.id_patient,
            date=appointment.date.strftime("%Y-%m-%d %H:%M"),
            status=appointment.status
        ) for appointment in appointments]

        links = [
            {"mode": "self", "href": f"/api/medical_office/appointments", "type": "GET"},
            {"mode": "parent", "href": f"/api/medical_office", "type": "GET"}
        ]
        appointments_response = AppointmentsList(
            total_appointments=total_appointments,
            appointments=appointment_list,
            _links={link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
        )

        return appointments_response
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.get("/appointments/patient-cnp/{id_patient}", response_model=AppointmentsList, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_appointments": 5, "appointments": [], "_links": {}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
})
def get_patient_by_cnp_appointments(request: Request, id_patient: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type in ['patient', 'doctor']:
            appointments = Appointments.select().where(Appointments.id_patient == id_patient)
            total_appointments = appointments.count()

            appointment_list = [Appointment(
                id_appointment=appointment.id_appointment,
                id_doctor=appointment.id_doctor,
                id_patient=appointment.id_patient,
                date=appointment.date.strftime("%Y-%m-%d %H:%M"),
                status=appointment.status
            ) for appointment in appointments]

            links = {
                "self": {"href": f"/api/medical_office/appointments/patient-cnp/{id_patient}", "type": "GET"},
                "parent": {"href": "/api/medical_office/appointments", "type": "GET"}
            }

            appointments_response = AppointmentsList(
                total_appointments=total_appointments,
                appointments=appointment_list,
                _links=links
            )

            headers = {"Authorization": f"Bearer {token}"}
            return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                content=appointments_response.dict())
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.get("/appointments/patient/{id_patient}", response_model=AppointmentsList, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_appointments": 0, "appointments": [], "_links": {}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
})
def get_patient_appointments(request: Request, id_patient: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type in ['patient', 'doctor']:
            patient = Patients.get_or_none(Patients.id_user == id_patient)
            if not patient:
                raise HTTPException(status_code=404, detail="The patient was not found")

            appointments = Appointments.select().where(Appointments.id_patient == patient.cnp)
            total_appointments = appointments.count()

            appointment_list = [Appointment(
                id_appointment=appointment.id_appointment,
                id_doctor=appointment.id_doctor,
                id_patient=appointment.id_patient,
                date=appointment.date.strftime("%Y-%m-%d %H:%M"),
                status=appointment.status
            ) for appointment in appointments]

            links = {
                "self": {"href": f"/api/medical_office/appointments/patient/{id_patient}", "type": "GET"},
                "parent": {"href": "/api/medical_office/appointments", "type": "GET"}
            }

            appointments_response = AppointmentsList(
                total_appointments=total_appointments,
                appointments=appointment_list,
                _links=links
            )

            headers = {"Authorization": f"Bearer {token}"}
            return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                content=appointments_response.dict())
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.get("/appointments/doctor/{id_doctor}", response_model=AppointmentsList, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_appointments": 0, "appointments": [], "_links": {}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
})
def get_doctor_appointments(request: Request, id_doctor: int):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        user_id = payload.get('sub')

        if user_type == 'doctor':
            appointments = Appointments.select().where(Appointments.id_doctor == id_doctor)
            total_appointments = appointments.count()

            appointment_list = [Appointment(
                id_appointment=appointment.id_appointment,
                id_doctor=appointment.id_doctor,
                id_patient=appointment.id_patient,
                date=appointment.date.strftime("%Y-%m-%d %H:%M"),
                status=appointment.status
            ) for appointment in appointments]

            links = {
                "self": {"href": f"/api/medical_office/appointments/doctor/{id_doctor}", "type": "GET"},
                "parent": {"href": "/api/medical_office/appointments", "type": "GET"}
            }

            appointments_response = AppointmentsList(
                total_appointments=total_appointments,
                appointments=appointment_list,
                _links=links
            )

            headers = {"Authorization": f"Bearer {token}"}
            return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                content=appointments_response.dict())
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.get('/appointments/{id_app}', response_model=AppointmentsList , responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_appointments": 5, "appointments": [], "_links": {}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
})
def read_appointments(request:Request, id_app):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        user_id = payload.get('sub')
        # de facut un get pe appointmntul respectiv si verificat id_user ului cu cel al patientului
        if user_type == 'patient' or user_type =='doctor':
            appointments = Appointments.select().where(Appointments.id_appointment == id_app)
            total_appointments = appointments.count()
            if not appointments:
                raise HTTPException(status_code=404, detail='Appointment not found')
            headers = {"Authorization": f"Bearer {token}"}
            links = [
                {"mode": "self", "href": f"/api/medical_office/appointments/{id_app}", "type": "GET"},
                {"mode": "parent", "href": f"/api/medical_office/appointments", "type": "GET"}
            ]
            appointment_json = {
                "total_appointments": total_appointments,
                "appointments": [{
                    "id_appointment": appointment.id_appointment,
                    "id_doctor": appointment.id_doctor,
                    "id_patient": appointment.id_patient,
                    "date": appointment.date.strftime("%Y-%m-%d %H:%M"),
                    "status": appointment.status} for appointment in appointments],
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }
            return JSONResponse(status_code=200, headers=headers, media_type="application/json", content=appointment_json)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.post('/appointments/', response_model=AppointmentResponse , responses={
    201: {"description": "Created", "content": {"application/json": {"example": {"message": "Appointment created successfully", "appointment_id": 1234, "_links": {"self": {"type": "POST", "href": "/api/medical_office/appointments/"}, "parent": {"type": "GET", "href": "/api/medical_office/appointments"}}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    409: {"description": "Conflict", "content": {"application/json": {"example": {"detail": "The doctor already has appointments on this date."}}}},
    422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "Some required data is missing"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error. Please try again later."}}}}
})
async def create_appointment(request: Request, appointment: AppointmentCreate):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        id_doctor = appointment.id_doctor
        id_patient = appointment.id_patient
        date = appointment.date
        status = appointment.status

        if not all([id_doctor, id_patient, date, status]):
            raise HTTPException(status_code=422, detail="Some required data is missing")

        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d %H:%M")
            if appointment_date < datetime.now():
                raise HTTPException(status_code=422, detail="The appointment date must be in the future")
            if not (time(8, 0) <= appointment_date.time() <= time(20, 0)):
                raise HTTPException(status_code=422, detail="Appointments must be between 8:00 AM and 8:00 PM")
        except ValueError:
            raise HTTPException(status_code=422, detail="The date format is invalid")

        existing_appointments = Appointments.select().where(
            (Appointments.id_doctor == id_doctor) & (Appointments.date == appointment_date)
        )
        if existing_appointments.exists():
            raise HTTPException(status_code=409, detail="The doctor already has appointments on this date.")

        try:
            patient = Patients.get_or_none(Patients.id_user == id_patient)
            new_appointment = Appointments.create(
                id_doctor=id_doctor,
                id_patient=patient.cnp,
                date=appointment_date,
                status=status
            )
            new_appointment.save()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later.")

        headers = {"Authorization": f"Bearer {token}"}
        links = [
            {"mode": "self", "href": f"/api/medical_office/appointments/", "type": "POST"},
            {"mode": "parent", "href": f"/api/medical_office/appointments", "type": "GET"}
        ]
        appointment_json = {
            "message": "Appointment created successfully",
            "appointment_id": new_appointment.id_appointment,
            "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
        }
        return JSONResponse(status_code=201, content=appointment_json)

    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.delete('/appointments/{appointment_id}' , responses={
    204: {"description": "No Content", "content": {"application/json": {"example": {"message": "Appointment deleted successfully", "appointment_id": 1234, "_links": {"self": {"type": "DELETE", "href": "/api/medical_office/appointments/{appointment_id}"}, "parent": {"type": "GET", "href": "/api/medical_office/appointments"}}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "The appointment was not found"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error. Please try again later."}}}}
})
def delete_appointment(appointment_id: int, request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        if user_type == 'doctor' or user_type=='patient':
            try:
                appointment = Appointments.get(Appointments.id_appointment == appointment_id)
            except Appointments.DoesNotExist:
                raise HTTPException(status_code=404, detail="The appointment was not found")

            appointment.delete_instance()
            links = [
                {"mode": "self", "href": f"/api/medical_office/appointments/{appointment_id}", "type": "DELETE"},
                {"mode": "parent", "href": f"/api/medical_office/appointments", "type": "GET"}
            ]

            patient_json = {
                "message": "Appointment deleted successfully",
                "appointment_id": appointment_id,
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }
            return JSONResponse(status_code=204, content=patient_json)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.patch('/appointments/{appointment_id}', responses={
    200: {"description": "Success", "content": {"application/json": { "example": {"message": "Appointment updated successfully", "appointment_id": 123, "_links": {}}}}},
    400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "The date format is invalid"}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Not access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "The appointment was not found"}}}},
    409: {"description": "Conflict", "content": { "application/json": {"example": {"detail": "The doctor already has an appointment at this date and time."}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error. Please try again later."}}}}
})
async def update_appointment(appointment_id: int, request: Request):

    data = await request.json()
    new_date = data.get('date')
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        user_id = payload.get('sub')

        if user_type == 'patient':
            try:
                appointment = Appointments.get(Appointments.id_appointment == appointment_id)
            except Appointments.DoesNotExist:
                raise HTTPException(status_code=404, detail="The appointment was not found")

            try:
                new_appointment_datetime = datetime.strptime(new_date, "%Y-%m-%d %H:%M")
                if not (time(8, 0) <= new_appointment_datetime.time() <= time(20, 0)):
                    raise HTTPException(status_code=409, detail="Appointments must be between 8:00 AM and 8:00 PM")
            except ValueError:
                raise HTTPException(status_code=400, detail="The date format is invalid")

            overlapping_appointments = Appointments.select().where(
                (Appointments.id_doctor == appointment.id_doctor) &
                (Appointments.date == new_appointment_datetime.date()) &
                (Appointments.id_appointment != appointment_id)
            )
            if overlapping_appointments.exists():
                raise HTTPException(status_code=409, detail="The doctor already has an appointment at this date and time.")

            appointment.date = new_appointment_datetime.date()
            appointment.time = new_appointment_datetime.time()
            try:
                appointment.save()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating appointment:")
            links = [
                {"mode": "self", "href": f"/api/medical_office/appointments/{appointment_id}", "type": "PATCH"},
                {"mode": "parent", "href": f"/api/medical_office/appointments", "type": "GET"}
            ]

            patient_json = {
                "message": "Appointment updated successfully",
                "appointment_id": appointment_id,
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }
            return JSONResponse(status_code=200, content=patient_json)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

