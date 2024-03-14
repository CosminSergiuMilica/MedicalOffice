from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.openapi.utils import get_openapi
from pymongo import MongoClient
from typing import List, Optional
from utile import idmService_pb2_grpc, idmService_pb2
import grpc
import jwt
from pymongo.errors import ConnectionFailure, OperationFailure, PyMongoError
from fastapi.responses import JSONResponse
def grpc_client():
    channel = grpc.insecure_channel('proiect-api-users-service-1:50051')
    return idmService_pb2_grpc.IDMServiceStub(channel)

try:
    client = MongoClient("mongodb://cosmin:cosmin@proiect-api-mongo-pos-1:27017")
    db = client["mongodb-pos"]
    consultation = db.consultations
except ConnectionFailure:
    raise HTTPException(status_code=503, detail="Failed to connect to the database. Please make sure MongoDB is running.")

app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"
def transform_consultation_data(consultation_data):
    return {
        "id_consultation": consultation_data.get("id_consultation"),
        "id_appointment": consultation_data.get("id_appointment"),
        "id_patient": consultation_data.get("id_patient"),
        "id_doctor": consultation_data.get("id_doctor"),
        "date": consultation_data.get("date"),
        "diagnostic": consultation_data.get("diagnostic"),
        "investigation": consultation_data.get("investigation")
    }

@app.on_event("shutdown")
def shutdown():
    if not client.is_closed():
        client.close()

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="API Title", version="1.0.0", routes=app.routes))

@app.get("/consultations" )
def read_consultation(request: Request, id_doctor: Optional[str] = None,
                      id_patient: Optional[str] = None):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

    if response.is_valid == "valid":
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')
        if user_type in ['patient', 'doctor']:
            query = {}
            if id_doctor:
                query["id_doctor"] = id_doctor
            if id_patient:
                query["id_patient"] = id_patient

            try:
                consultations = consultation.find(query)
            except ConnectionFailure as e:
                raise HTTPException(status_code=503, detail=f"Database connection error")
            except PyMongoError as e:
                raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")

            links = {
                "self": {"href": f"/api/medical_office/consultations", "type": "GET"},
                "parent": {"href": f"/api/medical_office/", "type": "GET"}
            }
            consultations_list = [transform_consultation_data(c) for c in consultations]

            response_data = {"consultations": consultations_list, "_links": links}
            return JSONResponse(status_code=200, content=response_data)
        else:
            raise HTTPException(status_code=403, detail="Forbidden acces")
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")
@app.get("/consultations/{id_consultation}")
def get_consultation_by_id(request: Request, id_consultation: int):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")
    token = authorization_header.split(" ")[1]

    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        consultations = db.consultations.find({'id_appointment': id_consultation})
        if not consultations:
            raise HTTPException(status_code=404, detail=f"The consultation with {id_consultation} does not exist!")

        links = {
            "self": {"href": f"/api/medical_office/consultations/{id_consultation}", "type": "GET"},
            "parent": {"href": f"/api/medical_office/consultations", "type": "GET"}
        }

        consultations_list = [transform_consultation_data(c) for c in consultations]
        response_data = {"consultations": consultations_list, "_links": links}
        return JSONResponse(status_code=200, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.post("/consultations")
async def create_consultation(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        consultation_data = await request.json()
        id_patient = consultation_data.get("id_patient")
        id_doctor = consultation_data.get("id_doctor")
        diagnostic = consultation_data.get("diagnostic")
        date = consultation_data.get("date")

        headers = {"Authorization": f"Bearer {token}"}

        patient_response = requests.get(f"http://patient-service:8000/patients/{id_patient}", headers=headers)
        if patient_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Patient with id {id_patient} not found")

        doctor_response = requests.get(f"http://doctor-service:8000/doctors/{id_doctor}", headers=headers)
        if doctor_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Doctor with id {id_doctor} not found")

        if diagnostic not in ["bolnav", "sanatos"]:
            raise HTTPException(status_code=422, detail="Invalid diagnostic. Must be 'bolnav' or 'sanatos'")

        consultation_dict = {
            "id_consultation": consultation_data.get("id_consultation"),
            "id_appointment": consultation_data.get("id_appointment"),
            "id_patient": id_patient,
            "id_doctor": id_doctor,
            "date": date,
            "diagnostic": diagnostic,
            "investigation": consultation_data.get("investigation")
        }

        try:
            inserted_id = consultation.insert_one(consultation_dict).inserted_id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to insert consultation")

        links = {
            "self": {"href": f"/api/medical_office/consultations", "type": "POST"},
            "parent": {"href": f"/api/medical_office/consultations", "type": "GET"}
        }

        response_data = {"message": "Consultation created successfully", "id": str(inserted_id), "_links": links}
        return JSONResponse(status_code=201, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")


@app.patch("/consultations/{id_consultation}")
async def update_consultation(id_consultation: str, request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        existing_consultation = consultation.find_one({"id_consultation": id_consultation})
        if not existing_consultation:
            raise HTTPException(status_code=404, detail=f"Consultation with id {id_consultation} not found")

        consultation_data = await request.json()
        id_patient = consultation_data.get("id_patient")
        id_doctor = consultation_data.get("id_doctor")
        diagnostic = consultation_data.get("diagnostic")
        new_id_doctor = consultation_data.get("id_doctor")
        new_date = consultation_data.get("date")
        headers = {"Authorization": f"Bearer {token}"}
        patient_response = requests.get(f"http://patient-service:8000/patients/{id_patient}", headers=headers)
        if patient_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Patient with id {id_patient} not found")

        doctor_response = requests.get(f"http://doctor-service:8000/doctors/{id_doctor}", headers=headers)
        if doctor_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Doctor with id {id_doctor} not found")

        if diagnostic not in ["bolnav", "sanatos"]:
            raise HTTPException(status_code=422, detail="Invalid diagnostic. Must be 'bolnav' or 'sanatos'")

        if "id_doctor" in consultation_data and existing_consultation["id_doctor"] != new_id_doctor:
            raise HTTPException(status_code=403, detail="Changing the doctor is not allowed")

        if "date" in consultation_data and existing_consultation["date"] != new_date:
            raise HTTPException(status_code=403, detail="Changing the date is not allowed")

        try:
            updated_result = consultation.update_one({"id_consultation": id_consultation}, {"$set": consultation_data})
            if updated_result.modified_count == 0:
                raise HTTPException(status_code=404, detail=f"Consultation with id {id_consultation} not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")

        links = {
            "self": {"href": f"/api/medical_office/consultations/{id_consultation}", "type": "PATCH"},
            "parent": {"href": f"/api/medical_office/consultations", "type": "GET"}
        }

        response_data = {"message": "Consultation updated successfully", "_links": links}
        return JSONResponse(status_code=200, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.delete('/consultations/{id_consultation}')
def delete_consultation(request: Request, id_consultation):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        existing_consultation = consultation.find_one({"id_consultation": id_consultation})
        if not existing_consultation:
            raise HTTPException(status_code=404, detail=f'Consultation with id: {id_consultation} not found')

        try:
            deleted_result = consultation.delete_one({"id_consultation": id_consultation})
            if deleted_result.deleted_count == 0:
                raise HTTPException(status_code=404, detail=f"Failed to delete consultation {id_consultation}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")

        links = {
            "self": {"href": f"/api/medical_office/consultations/{id_consultation}", "type": "DELETE"},
            "parent": {"href": f"/api/medical_office/consultations", "type": "GET"}
        }

        response_data = {'message': 'Consultation deleted successfully', "_links": links}
        return JSONResponse(status_code=200, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.put("/consultations/{id_consultation}")
async def update_or_create_consultation(id_consultation: str, request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        consultation_data = await request.json()
        id_patient = consultation_data.get("id_patient")
        id_doctor = consultation_data.get("id_doctor")
        diagnostic = consultation_data.get("diagnostic")
        new_date = consultation_data.get("date")

        patient_response = requests.get(f"http://patient-service:8000/patients/{id_patient}")
        if patient_response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Patient with id {id_patient} not found")

        doctor_response = requests.get(f"http://doctor-service:8000/doctors/{id_doctor}")
        if doctor_response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Doctor with id {id_doctor} not found")

        if diagnostic not in ["bolnav", "sanatos"]:
            raise HTTPException(status_code=422, detail="Invalid diagnostic. Must be 'bolnav' or 'sanatos'")

        existing_consultation = consultation.find_one({"id_consultation": id_consultation})

        if existing_consultation:
            try:
                if "id_doctor" in consultation_data and existing_consultation["id_doctor"] != id_doctor:
                    raise HTTPException(status_code=403, detail="Changing the doctor is not allowed")

                if "date" in consultation_data and existing_consultation["date"] != new_date:
                    raise HTTPException(status_code=403, detail="Changing the date is not allowed")

                consultation.update_one({"id_consultation": id_consultation}, {"$set": consultation_data})
                return {"message": "The consultation has been updated successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
        else:
            try:
                appointment_response = requests.get(f"http://appointment-service:8000/appointments/patients/{id_patient}")
                if appointment_response.status_code != 200:
                    raise HTTPException(status_code=404, detail=f"Failed to retrieve patient appointments")

                appointments = appointment_response.json()
                matching_appointments = [appointment for appointment in appointments if
                                         appointment["id_doctor"] == id_doctor and appointment["date"] == new_date]

                if not matching_appointments:
                    raise HTTPException(status_code=403,
                                        detail=f"Patient does not have an appointment with doctor {id_doctor} on {new_date}")

                consultation_data["id_consultation"] = id_consultation
                inserted_id = consultation.insert_one(consultation_data).inserted_id
                links = {
                    "self": {"href": f"/api/medical_office/consultations/{id_consultation}", "type": "PUT"},
                    "parent": {"href": f"/api/medical_office/consultations", "type": "GET"}
                }
                response_data = {"message": "A new consultation has been successfully created", "id": str(inserted_id),
                                 "_links": links}
                return JSONResponse(status_code=201, content=response_data)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal server error. Please try again")
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")