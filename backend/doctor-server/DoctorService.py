from datetime import datetime

from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from utile import idmService_pb2_grpc, idmService_pb2
import bleach
from fastapi.responses import JSONResponse
from bdpos.Doctor import Doctors
from bdpos.database import db
from bdpos.Patients import Patients
from bdpos.Appointments import Appointments
from fastapi import FastAPI, HTTPException, Query, Request
from typing import List, Optional
import re
import grpc
import jwt

app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"
def grpc_client():
    channel = grpc.insecure_channel('proiect-api-users-service-1:50051')
    return idmService_pb2_grpc.IDMServiceStub(channel)

def validate_email(email):
    pattern = r"^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+\.[a-zA-Z]+$"
    if re.match(pattern, email):
        return True
    else:
        return False

@app.on_event("startup")
def startup():
    if db.is_closed():
        try:
            db.connect()
        except ConnectionError:
            raise HTTPException(status_code=503, detail="Database connection failed")

@app.on_event("shutdown")
def shutdown():
    if not db.is_closed():
        db.close()

def paginate(items: list, page: int, items_per_page: int):
    start = (page - 1) * items_per_page
    end = start + items_per_page
    return items[start:end]

def sanitize_input(data: str):
    sanitized_data = bleach.clean(data)
    return sanitized_data

class Doctor(BaseModel):
    id_doctor: int
    id_user: str
    last_name: str
    first_name: str
    email: str
    phone: str
    specialization: str

class DoctorInput(BaseModel):
    id_user: str
    last_name: str
    first_name: str
    email: str
    phone: str
    specialization: str

class DoctorsResponse(BaseModel):
    total_doctors: int
    doctors: List[Doctor]
    _links: dict

class DoctorResponseId(BaseModel):
    total_doctors: int
    doctor: Doctor
    _links: dict

class DoctorCreateResponse(BaseModel):
    message: str
    doctor_id: int
    _links: dict

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="API Title", version="1.0.0", routes=app.routes))

@app.get("/doctors", response_model=DoctorsResponse, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_doctors": 0, "doctors": [], "_links": []}}}},
    400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "Invalid request"}}}},
})
def get_doctors(page: Optional[int] = Query(None, description="Page number"),
                items_per_page: Optional[int] = Query(1, description="The number of elements on the page"),
                specialization: Optional[str] = Query(None, description="Doctor's specialization"),
                name: Optional[str] = Query(None, description="Doctor's name")):

    query = Doctors.select()
    total_doctors = query.count()

    if specialization is not None:
        query = query.where(Doctors.specialization == specialization)

    if name is not None:
        query = query.where(Doctors.last_name == name)
        if not query.exists():
            raise HTTPException(status_code=404, detail="Doctors not found")

    if page is not None:
        if page < 1:
            raise HTTPException(status_code=400, detail='The page number must be at least 1')

        if items_per_page < 1:
            raise HTTPException(status_code=400, detail='The number of elements on the page must be at least 1')

        if items_per_page > total_doctors or page > total_doctors:
            items_per_page = total_doctors
            page=1
        query = query.paginate(page, items_per_page)

    links = [
        {"mode": "self", "href": f"/api/medical_office/doctors", "type": "GET"},
        {"mode": "parent", "href": f"/api/medical_office", "type": "GET"}
    ]

    doctors = list(query)
    doctor_data = [
        Doctor(
            id_doctor=doctor.id_doctor,
            id_user=doctor.id_user,
            last_name=doctor.last_name,
            first_name=doctor.first_name,
            email=doctor.email,
            phone=doctor.phone,
            specialization=doctor.specialization
        ) for doctor in doctors
    ]

    doctors_response = DoctorsResponse(
        total_doctors=total_doctors,
        doctors=doctor_data,
        _links={link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
    )

    return doctors_response


@app.get('/doctors/{doctor_id}', response_model=DoctorResponseId, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_doctors": 1, "doctor": {}, "_links": []}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "Doctor not found"}}}},
})
def read_doctor(request: Request, doctor_id: str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":

        try:
            doctor = Doctors.get_or_none(Doctors.id_user == doctor_id)
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
        if doctor is None:
            doctor = Doctors.get_or_none(Doctors.id_doctor == doctor_id)
            if doctor is None:
                raise HTTPException(status_code=404, detail="Doctor not found")

        links = [
            {"mode": "self", "href": f"/api/medical_office/doctors/{doctor_id}", "type": "GET"},
            {"mode": "parent", "href": f"/api/medical_office/doctors", "type": "GET"}
        ]

        doctor_json = {
            "total_doctors": 1,
            "doctor": {
                "id_doctor": doctor.id_doctor,
                "id_user": doctor.id_user,
                "last_name": doctor.last_name,
                "first_name": doctor.first_name,
                "email": doctor.email,
                "phone": doctor.phone,
                "specialization": doctor.specialization
            },
            "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
        }

        headers = {"Authorization": f"Bearer {token}"}
        return JSONResponse(status_code=200, headers=headers, media_type="application/json", content=doctor_json)
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.post('/doctors', response_model=DoctorCreateResponse, responses={
    201: {"description": "Success", "content": {"application/json": {"example": {"message": "Doctor created successfully", "doctor_id": "123", "_links": {}}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "Validation error"}}}},
})
async def create_doctor(request: Request, doctor: DoctorInput):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="nauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == 'admin':
            valid_specializations = {'pediatru', 'chirurg', 'nutritionist', 'ortoped', 'dentist', 'oftalmolog'}
            if doctor.specialization.lower() not in valid_specializations:
                raise HTTPException(status_code=422, detail="Specialization not valid")

            if not validate_email(doctor.email):
                raise HTTPException(status_code=422, detail='The email is in invalid format')

            if Doctors.select().where(Doctors.email == doctor.email).exists():
                raise HTTPException(status_code=422, detail="Email already exists in the database")
            if Doctors.select().where(Doctors.phone == doctor.phone).exists():
                raise HTTPException(status_code=422, detail="Phone number already exists in the database")

            new_doctor = Doctors.create(
                id_user=doctor.id_user,
                last_name=doctor.last_name,
                first_name=doctor.first_name,
                email=doctor.email,
                phone=doctor.phone,
                specialization=doctor.specialization
            )
            new_doctor.save()
            links = {
                "self": {"href": f"/api/medical_office/doctors", "type": "POST"},
                "parent": {"href": f"/api/medical_office/doctors", "type": "GET"},
                "doctor": {"href": f"/api/medical_office/doctors/{new_doctor.id_doctor}", "type": "GET"}
            }
            return JSONResponse(status_code=201, content={"message": "Doctor created successfully", "doctor_id": str(new_doctor.id_doctor), "_links": links})
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.delete('/doctors/{doctor_id}', responses={
    204: {"description": "No Content"},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "Doctor not found"}}}},
    409: {"description": "Conflict", "content": {"application/json": {"example": {"detail": "Doctor has future appointments and cannot be deleted."}}}},
})
def delete_doctor(request: Request, doctor_id: int):

    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == 'admin':
            try:
                doctor = Doctors.get(Doctors.id_user == doctor_id)
            except Doctors.DoesNotExist:
                raise HTTPException(status_code=404, detail="Doctor not found")

            future_appointments = Appointments.select().where((Appointments.doctor_id == doctor_id) & (Appointments.date > datetime.now()))
            if future_appointments.exists():
                raise HTTPException(status_code=409, detail="Doctor has future appointments and cannot be deleted.")

            doctor.delete_instance()
            links = [
                {"mode": "self", "href": f"/api/medical_office/doctors/{doctor_id}", "type": "DELETE"},
                {"mode": "parent", "href": f"/api/medical_office/doctors", "type": "GET"}
            ]
            patient_json = {
                "message": "Doctor deleted successfully",
                "patient_id": doctor_id,
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }
            return JSONResponse(status_code=204, content=patient_json)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.patch('/doctors/{doctor_id}', responses={
    204: {"description": "No Content"},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "Doctor not found"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error"}}}},
})
async def update_doctor(doctor_id: int, request: Request):

    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")
    token = authorization_header.split(" ")[1]

    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        user_id = payload.get('sub')

        if user_type == 'doctor' and user_id == doctor_id:
            try:
                doctor = Doctors.get(Doctors.id_doctor == doctor_id)
            except Doctors.DoesNotExist:
                raise HTTPException(status_code=404, detail="Doctor not found")

            for key, value in data.items():
                if hasattr(doctor, key):
                    setattr(doctor, key, sanitize_input(value))

            try:
                doctor.save()
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error. Please try again later")

            links = [
                {"mode": "self", "href": f"/api/medical_office/doctors/{doctor_id}", "type": "PATCH"},
                {"mode": "parent", "href": f"/api/medical_office/doctors", "type": "GET"}
            ]

            doctor_json ={
                "message": "Doctor updated successfully",
                "doctor_id": doctor_id,
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }
            return JSONResponse(status_code=204, content=doctor_json)
        else:
            raise HTTPException(status_code=403, detail="Forbidden acces")
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.put('/doctors/{doctor_id}', response_model=DoctorCreateResponse, responses={
    201: {"description": "Success", "content": {"application/json": {"example": {"message": "Doctor created/updated successfully", "doctor_id": "123", "_links": {}}}}},
    422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "Validation error"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error"}}}},
})
async def update_or_create_doctor(request: Request, doctor_id: int):
    data = await request.json()
    id_user = data.get('id_user')
    last_name = data.get('last_name')
    first_name = data.get('first_name')
    email = data.get('email')
    phone = data.get('phone')
    specialization = data.get('specialization')

    valid_specializations = {'pediatru', 'chirurg', 'nutritionist', 'ortoped', 'dentist', 'oftalmolog'}
    if specialization.lower() not in valid_specializations:
        raise HTTPException(status_code=422, detail="Specialization not valid")

    if not all([id_user, last_name, first_name, email, phone, specialization]):
        raise HTTPException(status_code=422, detail="Some mandatory data is missing")

    if validate_email(email) == False:
        raise HTTPException(status_code=422, detail='The email is in invalid format')

    try:
        existing_doctor = Doctors.get_or_none(Doctors.id_doctor == doctor_id)

        if existing_doctor:
            existing_doctor.id_user = id_user
            existing_doctor.last_name = last_name
            existing_doctor.first_name = first_name
            existing_doctor.email = email
            existing_doctor.phone = phone
            existing_doctor.specialization = specialization
            existing_doctor.save()
            message = "Doctor updated successfully"
            doctor_id = existing_doctor.id_doctor
        else:
            if Doctors.select().where(Doctors.email == email).exists():
                raise HTTPException(status_code=422, detail="Email number already exists in the database")
            if Doctors.select().where(Doctors.phone == phone).exists():
                raise HTTPException(status_code=422, detail="Phone number already exists in the database")
            new_doctor = Doctors.create(
                id_user=id_user,
                last_name=last_name,
                first_name=first_name,
                email=email,
                phone=phone,
                specialization=specialization
            )
            new_doctor.save()
            message = "Doctor created successfully"
            doctor_id = new_doctor.id_doctor

        links = {
            "self": {"href": f"/api/medical_office/doctors", "type": "POST"},
            "parent": {"href": f"/api/medical_office/doctors", "type": "GET"},
            "doctor": {"href": f"/api/medical_office/doctors/{doctor_id}", "type": "GET"}
        }
        return JSONResponse(status_code=201, content={"message": message, "doctor_id": doctor_id, "_links": links})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later")