
from datetime import datetime
from typing import List, Optional, Dict
import bleach
import grpc
import jwt
from peewee import DatabaseError
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from utile import idmService_pb2_grpc, idmService_pb2
from bdpos.database import db
from bdpos.Patients import Patients
from fastapi import FastAPI, HTTPException, Query, Request, Response
import requests
import re
from fastapi.openapi.utils import get_openapi

app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"

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

class PatientData(BaseModel):
    cnp: str
    id_user: str
    last_name: str
    first_name: str
    email: str
    phone: str
    birth_date: str
    is_active: bool


class PatientCreateResponse(BaseModel):
    message: str
    patient_id: str
    _links: dict

class PatientListResponse(BaseModel):
    total_patients: int
    patients: List[PatientData]
    _links: Dict[str, Dict[str, str]]

class PatientResponse(BaseModel):
    total_patients: Optional[int]
    patient: PatientData
    _links: dict


def sanitize_input(data: str):
    sanitized_data = bleach.clean(data)
    return sanitized_data

def validate_email(email):
    pattern = r"^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+\.[a-zA-Z]+$"
    if re.match(pattern, email):
        return True
    else:
        return False

def validate_cnp(cnp):
    pattern = r"^\d{13}$"
    if re.match(pattern, cnp):
        return True
    else:
        return False

def paginate(items: list, page: int, items_per_page: int):
    start = (page - 1) * items_per_page
    end = start + items_per_page
    return items[start:end]

def grpc_client():
    channel = grpc.insecure_channel('proiect-api-users-service-1:50051')
    return idmService_pb2_grpc.IDMServiceStub(channel)

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="API Title", version="1.0.0", routes=app.routes))

@app.get('/patients', response_model=PatientListResponse, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_patients": 0, "patients": [], "_links": []}}}},
    400: {"description": "Bad Request", "content": {"application/json": {"example": {"detail": "Invalid request"}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "Patients not found"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error"}}}}
})
def read_patient(request: Request, first_name: Optional[str] = Query(None, description="First name of the patient"),
                 items_per_page: Optional[int] = Query(1, description="The number of elements on the page"),
                 page: Optional[int] = Query(None, description="Page number")):
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Unauthorized access")

        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
        if response.is_valid == 'valid':

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')

            if user_type == 'admin' or user_type == 'doctor':
                patients = Patients.select()

                if first_name is not None:
                    patients = Patients.select().where(Patients.first_name == first_name)
                    if not patients.exists():
                        raise HTTPException(status_code=404, detail="Patients not found")

                total_patients = patients.count()

                if page is not None:
                    if page < 1:
                        raise HTTPException(status_code=400, detail='The page number must be at least 1')
                    if items_per_page < 1:
                        raise HTTPException(status_code=400,
                                            detail='The number of elements on the page must be at least 1')
                    if items_per_page > total_patients or page > total_patients:
                        items_per_page = total_patients
                        page = 1
                    patients = patients.paginate(page, items_per_page)

                patient_list = list(patients)

                links = [
                    {"mode": "self", "href": f"/api/medical_office/patients", "type": "GET"},
                    {"mode": "parent", "href": f"/api/medical_office", "type": "GET"}
                ]

                patient_data = [
                    PatientData(
                        cnp=patient.cnp,
                        id_user=patient.id_user,
                        last_name=patient.last_name,
                        first_name=patient.first_name,
                        email=patient.email,
                        phone=patient.phone,
                        birth_date=patient.birth_date.strftime("%Y-%m-%d"),
                        is_active=patient.is_active
                    ) for patient in patient_list
                ]

                patient_list_response = PatientListResponse(
                    total_patients=total_patients,
                    patients=patient_data,
                    _links={link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
                )

                headers = {"Authorization": f"Bearer {token}"}
                return JSONResponse(status_code=200, headers=headers, media_type="application/json", content=patient_list_response.dict())
            else:
                raise HTTPException(status_code=403, detail="Forbidden access")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except Exception as e:
         raise HTTPException(status_code=500)


@app.get('/patients/{patient_id}', response_model=PatientResponse, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_patients": 1, "patient": {}, "_links": []}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "Patient not found"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error"}}}}
})
def read_patient(request: Request, patient_id: str):

    authorization_header = request.headers.get('Authorization')

    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == 'valid':
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        user_id = payload.get('sub')

        if user_id == patient_id or user_type == 'admin' or user_type == 'doctor':
            try:
                patient = Patients.get_or_none(Patients.id_user == patient_id)
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
            if patient is None:
                patient = Patients.get_or_none(Patients.cnp == patient_id)
                if patient is None:
                    raise HTTPException(status_code=404, detail="Patient not found")

            links = [
                {"mode": "self", "href": f"/api/medical_office/patients/{patient_id}", "type": "GET"},
                {"mode": "parent", "href": f"/api/medical_office/patients", "type": "GET"}
            ]

            patient_data = PatientData(
                cnp=patient.cnp,
                id_user=patient.id_user,
                last_name=patient.last_name,
                first_name=patient.first_name,
                email=patient.email,
                phone=patient.phone,
                birth_date=patient.birth_date.strftime("%Y-%m-%d"),
                is_active=patient.is_active
            )

            patient_response = PatientResponse(
                total_patients=1,
                patient=patient_data,
                _links={link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            )

            headers = {"Authorization": f"Bearer {token}"}
            return JSONResponse(status_code=200, headers=headers, media_type="application/json", content=patient_response.dict())
        else:
            raise HTTPException(status_code=403, detail="Unauthorized acces")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.post('/patients', response_model=PatientCreateResponse, responses={
    201: {"description": "Created", "content": {"application/json": {"example": {"message": "Patient created successfully", "patient_id": 1234, "_links": {"self": {"type": "POST", "href": "/api/medical_office/patients/"}, "parent": {"type": "GET", "href": "/api/medical_office"}}}}}},
    422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "The CNP is not in the correct format"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error. Please try again later"}}}}
} )
async def create_patient(patient_data: PatientData):
    try:
        if not validate_cnp(patient_data.cnp):
            raise HTTPException(status_code=422, detail="The CNP is not in the correct format")
        if not validate_email(patient_data.email):
            raise HTTPException(status_code=422, detail="Invalid email: " + patient_data.email)
        if Patients.select().where(Patients.email == patient_data.email).exists():
            raise HTTPException(status_code=422, detail="Email already exists in the database")
        if Patients.select().where(Patients.phone == patient_data.phone).exists():
            raise HTTPException(status_code=422, detail="Phone number already exists in the database")

        birth_date_obj = datetime.strptime(patient_data.birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))
        if age < 18:
            raise HTTPException(status_code=422, detail="The patient is not at least 18 years old and cannot be created")

        new_patient = Patients.create(
            cnp=patient_data.cnp,
            id_user=patient_data.id_user,
            last_name=patient_data.last_name,
            first_name=patient_data.first_name,
            email=patient_data.email,
            phone=patient_data.phone,
            birth_date=patient_data.birth_date,
            is_active=patient_data.is_active
        )
        new_patient.save()

        links = [
            {"mode": "self", "href": f"/api/medical_office/patients/", "type": "POST"},
            {"mode": "parent", "href": f"/api/medical_office", "type": "GET"}
        ]
        patient_json = {
            "message": "Patient created successfully",
            "patient_id": new_patient.id_user,
            "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
        }

        return JSONResponse(status_code=201, media_type="application/json", content=patient_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error. Please try again later")

@app.delete('/patients/{patient_id}', responses={
    204: {"description": "No Content", "content": {"application/json": { "example": {"message": "Patient deleted successfully", "patient_id": "123", "_links": []}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Not access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Not authenticated"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "Patient not found"}}}},
    409: {"description": "Conflict", "content": {"application/json": {"example": {"detail": "Cannot delete patient with future appointments"}}}},
} )
def delete_patient(request: Request, patient_id: str):

    authorization_header = request.headers.get('Authorization')

    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == 'admin':
            try:
                patient = Patients.get(Patients.id_user == patient_id)
                #patient.delete_instance()
            except Patients.DoesNotExist:
                raise HTTPException(status_code=404, detail="Patient not found")

            try:
                response = requests.get(f"http://appointment-service:8000/appointments/patients/{patient_id}")
                response.raise_for_status()

                if response.status_code == 404:
                    patient.delete_instance()
                else:
                    appointments = response.json()
                    current_datetime = datetime.now().isoformat()
                    future_appointments = [appointment for appointment in appointments if appointment['date'] > current_datetime]

                    if future_appointments:
                        raise HTTPException(status_code=409, detail="Cannot delete patient with future appointments")

                    patient.delete_instance()
                links = [
                    {"mode": "self", "href": f"/api/medical_office/patients/{patient_id}", "type": "DELETE"},
                    {"mode": "parent", "href": f"/api/medical_office/patients", "type": "GET"}
                ]

                patient_json = {
                    "message": "Patient deleted successfully",
                    "patient_id": patient_id,
                    "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
                }
                return JSONResponse(status_code=204, content=patient_json)

            except requests.RequestException as e:
                if e.response.status_code == 404:
                    pass
                else:
                    raise e
        else:
            raise HTTPException(status_code=403, detail="Unauthorized acces")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.patch('/patients/{patient_id}', response_model=PatientResponse, responses={
    200: {"description": "Success", "content": {"application/json": {"example": {"total_patients": 1, "patient": {}, "_links": []}}}},
    401: {"description": "Unauthorized", "content": {"application/json": {"example": {"detail": "Unauthorized access"}}}},
    403: {"description": "Forbidden", "content": {"application/json": {"example": {"detail": "Forbidden access"}}}},
    404: {"description": "Not Found", "content": {"application/json": {"example": {"detail": "Patient not found"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error"}}}}
})
async def update_patient(patient_id: str, request: Request, patient_data: PatientData):
    data = await request.json()
    authorization_header = request.headers.get('Authorization')

    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == "admin":
            try:
                patient = Patients.get(Patients.id_user == patient_id)
            except Patients.DoesNotExist:
                raise HTTPException(status_code=404, detail="Patient not found")

            for key, value in data.items():
                if hasattr(patient, key):
                    setattr(patient, key, value)

            try:
                patient.save()
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error. Please try again later")

            links = [
                    {"mode": "self", "href": f"/api/medical_office/patients/{patient_id}", "type": "PATCH"},
                    {"mode": "parent", "href": f"/api/medical_office/patients", "type": "GET"}
            ]

            patient_response = PatientResponse(
                total_patients=1,
                patient=PatientData(
                    cnp=patient.cnp,
                    id_user=patient.id_user,
                    last_name=patient.last_name,
                    first_name=patient.first_name,
                    email=patient.email,
                    phone=patient.phone,
                    birth_date=patient.birth_date,
                    is_active=patient.is_active
                ),
                _links={link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            )
            return patient_response
        else:
            raise HTTPException(status_code=403, detail="Unauthorized acces")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.put('/patients/{patient_id}', response_model=PatientCreateResponse , responses={
    201: {"description": "Created", "content": {"application/json": {"example": {"message": "Patient created successfully", "patient_id": 1234, "_links": {"self": {"type": "POST", "href": "/api/medical_office/patients/"}, "parent": {"type": "GET", "href": "/api/medical_office"}}}}}},
    422: {"description": "Unprocessable Entity", "content": {"application/json": {"example": {"detail": "The CNP is not in the correct format"}}}},
    500: {"description": "Internal Server Error", "content": {"application/json": {"example": {"detail": "Internal server error. Please try again later"}}}}
} )
async def update_patient(patient_id: str, request: Request, patient_data: PatientData):

    cnp = patient_data.cnp
    id_user = patient_data.id_user
    last_name = patient_data.last_name
    first_name = patient_data.first_name
    email = patient_data.email
    phone = patient_data.phone
    birth_date = patient_data.birth_date
    is_active = patient_data.is_active

    if not all([cnp, id_user, last_name, first_name, email, phone, birth_date, is_active]):
        raise HTTPException(status_code=422, detail="Some mandatory data is missing")

    if not validate_cnp(cnp):
        raise HTTPException(status_code=422, detail="The CNP is not in the correct format")

    if not validate_email(email):
        raise HTTPException(status_code=422, detail="Invalid email: " + email)

    try:
        birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Date of birth format is invalid")

    today = datetime.now()
    age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))

    if age < 18:
        raise HTTPException(status_code=422, detail="The patient is not at least 18 years old and cannot be created")

    try:
        existing_patient = Patients.get_or_none((Patients.id_user == patient_id) | (Patients.cnp == patient_id))

        if existing_patient is None:
            if Patients.select().where(Patients.email == email).exists():
                raise HTTPException(status_code=422, detail="Email already exists in the database")
            if Patients.select().where(Patients.phone == phone).exists():
                raise HTTPException(status_code=422, detail="Phone number already exists in the database")
            existing_patient = Patients.create(
                cnp=cnp,
                id_user=id_user,
                last_name=last_name,
                first_name=first_name,
                email=email,
                phone=phone,
                birth_date=birth_date,
                is_active=is_active
            )
        else:
            existing_patient.cnp = cnp
            existing_patient.id_user = id_user
            existing_patient.last_name = last_name
            existing_patient.first_name = first_name
            existing_patient.email = email
            existing_patient.phone = phone
            existing_patient.birth_date = birth_date
            existing_patient.is_active = is_active

        existing_patient.save()
    except DatabaseError:
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later")

    links = [
        {"mode": "self", "href": f"/api/medical_office/patients/{patient_id}", "type": "PUT"},
        {"mode": "parent", "href": f"/api/medical_office/patients", "type": "GET"}
    ]
    patient_json = {
        "message": "Patient updated successfully",
        "patient_id": existing_patient.id_user,
        "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
    }

    return JSONResponse(status_code=201, media_type="application/json", content=patient_json)