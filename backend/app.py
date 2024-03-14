import json
from datetime import timedelta, datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import requests
import grpc
import jwt
from utile import idmService_pb2_grpc, idmService_pb2
from pydantic import BaseModel


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
    ,
)

SECRET_KEY = "GoSdJgsDEe343"
class SignUpRequest(BaseModel):
    username: str
    password: str
class LoginRequest(BaseModel):
    username: str
    password: str

class Link(BaseModel):
    mode: str
    href: str
    type: str

def grpc_client():
    channel = grpc.insecure_channel('proiect-api-users-service-1:50051')
    return idmService_pb2_grpc.IDMServiceStub(channel)

def handle_service_error(e: requests.RequestException):
    status_code = e.response.status_code if e.response is not None else 500
    content = {"success": False, "message": ""}
    if e.response is not None and e.response.status_code in [400, 404, 422, 409]:
        content["message"] = e.response.json().get('detail', e.response.text)
    else:
        content["message"] = "An unexpected error occurred"
    return JSONResponse(status_code=status_code, content=content)

@app.get('/api/medical_office')
def intro():
    return {'message': "Bine ati venit!"}

####################PATIENTS###############
@app.get('/api/medical_office/patients')
def patients_list(request: Request, first_name: Optional[str] = Query(None, description="First name of the patient"),
                 items_per_page: Optional[int] = Query(1, description="The number of elements on the page"),
                 page: Optional[int] = Query(None, description="Page number")):
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")

        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

        if response.is_valid == 'valid':

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')
            if user_type == 'admin' or user_type == 'doctor':

                params = {}
                if page is not None:
                    params['page'] = page
                if items_per_page != 1:
                    params['items_per_page'] = items_per_page
                if first_name is not None:
                    params['first_name'] = first_name

                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get("http://patient-service:8000/patients", params=params, headers=headers)
                response.raise_for_status()
                patient_json = response.json()

                return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                    content=patient_json)
            else:
                raise HTTPException(status_code=403, detail="neautorizat")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)


@app.get('/api/medical_office/patients/{patient_id}')
def read_patient(request: Request, patient_id: str):
    #utilizator autentificat, ar fi bine sa fie chiar utilizatorul insusi sa-si vada profilu si orice medic sau admin
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
             raise HTTPException(status_code=401, detail="Not access")
        token = authorization_header.split(" ")[1]
        headers = {"Authorization": f"Bearer {token}"}
        patient = requests.get(f"http://patient-service:8000/patients/{patient_id}", headers=headers)
        patient.raise_for_status()

        patient_json = patient.json()

        return JSONResponse(status_code=200, headers=headers, media_type="application/json", content=patient_json)
    except requests.RequestException as e:
        return handle_service_error(e)

@app.delete('/api/medical_office/patients/{patient_id}')
def delete_patient(request: Request, patient_id: str):
    #admin
    try:
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
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.delete(f"http://patient-service:8000/patients/{patient_id}", headers=headers)
                response.raise_for_status()

                if response.status_code == 204:
                    grpc_stub.DeleteUser(idmService_pb2.DeleteUserRequest(user_id=patient_id))

                return Response(status_code=204, headers=headers)
            else:
                raise HTTPException(status_code=403, detail="neautorizat")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)

@app.patch('/api/medical_office/patients/{patient_id}')
async def update_patient(patient_id: str, request: Request):
    #patientul insusi sa si update la date

    data = await request.json()
    try:
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
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.patch(f"http://patient-service:8000/patients/{patient_id}", json=data, headers=headers)
                response.raise_for_status()

                patient_json = response.json()
                links = [Link(mode="self", href=f"/api/medical_office/patients/{patient_id}", type="PATCH"),
                         Link(mode="parent", href=f"/api/medical_office/patients", type="GET")]
                patient_json["_links"] = {link.mode: {"type": link.type, "href": link.href} for link in links}


                return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                    content=patient_json)
            else:
                raise HTTPException(status_code=403, detail="neautorizat")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)


###################DOCTORS########################
@app.get('/api/medical_office/doctors')
def doctors_list(request: Request, page: Optional[int] = None,
                 items_per_page: Optional[int] = None,
                 specialization: Optional[str] = None,
                 name: Optional[str] = None):
    #oricine
    try:
        params = {}
        if page is not None:
            params['page'] = page
        if items_per_page is not None:
            params['items_per_page'] = items_per_page
        if specialization is not None:
            params['specialization'] = specialization
        if name is not None:
            params['name'] = name

        response = requests.get("http://doctor-service:8000/doctors", params=params)
        response.raise_for_status()

        doctor_json = response.json()
        links = [Link(mode="self", href=f"/api/medical_office/doctors", type="GET"),
                 Link(mode="parent", href=f"/api/medical_office", type="GET")]
        doctor_json["_links"] = {link.mode: {"type": link.type, "href": link.href} for link in links}

        return JSONResponse(status_code=200, media_type="application/json",
                            content=doctor_json)
    except requests.RequestException as e:
        return handle_service_error(e)

@app.get('/api/medical_office/doctors/{doctor_id}')
def read_patient(request: Request, doctor_id: str):
    #oricine poate cauta un doctor, evetual limitam datele pe care le poate vizualiza de aici
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

        if response.is_valid == "valid":

            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"http://doctor-service:8000/doctors/{doctor_id}", headers=headers)
            response.raise_for_status()

            doctor_json = response.json()

            return JSONResponse(status_code=200,headers=headers, media_type="application/json", content=doctor_json)

        else:
            raise HTTPException(status_code=401, detail="Not auth")
    except requests.RequestException as e:
        return handle_service_error(e)

@app.post('/api/medical_office/doctors/')
async def create_doctor(request: Request):
    #admin
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    try:
        decode_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = decode_token.get('role')
        if user_type == 'admin':
            grpc_stub = grpc_client()
            response = grpc_stub.CreateDoctor(idmService_pb2.CreateDoctorRequest(username=data.get('username'), password=data.get('password')))
            if response.id_user != "NONE":
                id_user = response.id_user
                doctor_data = {
                    "id_user": id_user,
                    "last_name": data.get('last_name'),
                    "first_name": data.get('first_name'),
                    "email": data.get('email'),
                    "phone": data.get('phone'),
                    "specialization": data.get('specialization'),
                }
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    resp = requests.post("http://doctor-service:8000/doctors", headers=headers, json=doctor_data)
                    resp.raise_for_status()

                    doctor_json = resp.json()
                    return JSONResponse(status_code=201, headers=headers, media_type="application/json",
                                        content=doctor_json)

                except requests.RequestException as e:

                    grpc_stub.DeleteUser(idmService_pb2.DeleteUserRequest(user_id=response.id_user))
                    return handle_service_error(e)
            else:
                grpc_stub.DeleteUser(idmService_pb2.DeleteUserRequest(user_id=response.id_user))
                raise HTTPException(status_code=401, detail="Înregistrare eșuată "+str(response.code))
        else:
            raise HTTPException(status_code=403, detail="Acces denied")
    except requests.RequestException as e:
        return handle_service_error(e)

@app.delete('/api/medical_office/doctors/{doctor_id}')
def delete_doctor(request: Request, doctor_id: str):
    #admin
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")
        token = authorization_header.split(" ")[1]
        headers = {"Authorization": f"Bearer {token}"}
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

        if response.is_valid == "valid":
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')

            if user_type == 'admin':
                response = requests.delete(f"http://doctor-service:8000/doctors/{doctor_id}", headers=headers)
                response.raise_for_status()
                headers = {"Authorization": f"Bearer {token}"}
                doctor_json = response.json()

                return JSONResponse(status_code=204, headers=headers, media_type="application/json", content=doctor_json)
            else:
                raise HTTPException(status_code=403, detail="Not a")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)

@app.patch('/api/medical_office/doctors/{doctor_id}')
async def update_doctor(doctor_id: str, request: Request):
    #doctorul care este autentificat doar pt el
    data = await request.json()
    try:
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

            headers = {"Authorization": f"Bearer {token}"}
            if user_type == 'doctor' and user_id==doctor_id:
                response = requests.patch(f"http://doctor-service:8000/doctors/{doctor_id}",json=data, headers=headers)
                response.raise_for_status()

                doctor_json = response.json()

                return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                    content=doctor_json)
            else:
                raise HTTPException(status_code=403, detail="Acces denied")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)

#################APPOINTMENTS################
@app.get("/api/medical_office/appointments")
def get_appointments(request:Request):
    #doctorul si patientul
    try:
        authorization_header = request.headers.get('Authorization')

        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))

        if response.is_valid == "valid":
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get("http://appointment-service:8000/appointments", headers=headers)
            resp.raise_for_status()

            jsn = resp.json()

            return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                content=jsn)
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)

@app.get("/api/medical_office/appointments/patient/{id_patient}")
def get_appointment_patient(request: Request, id_patient: str):
    try:
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

            if user_type == 'patient' and user_id == id_patient:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"http://appointment-service:8000/appointments/patient/{id_patient}", headers=headers)
                response.raise_for_status()
                # headers = {"Authorization": f"Bearer {token}"}
                appointment_json = response.json()
                links = [Link(mode="self", href=f"/api/medical_office/appointments/patient/{id_patient}", type="GET"),
                         Link(mode="parent", href=f"/api/medical_office/appointments", type="GET")]
                appointment_json["_links"] = {link.mode: {"type": link.type, "href": link.href} for link in links}

                return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                    content=appointment_json)
            else:
                raise HTTPException(status_code=403, detail="Acces denied")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)

@app.get("/api/medical_office/appointments/doctor/{id_doctor}")
def get_appointment_doctor(request:Request, id_doctor: str):
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
        if response.is_valid == "valid":
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')

            if user_type == 'doctor':
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"http://appointment-service:8000/appointments/doctor/{id_doctor}", headers=headers)
                response.raise_for_status()

                appointment_json = response.json()

                return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                    content=appointment_json)
            else:
                raise HTTPException(status_code=403, detail="Acces denied")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except requests.RequestException as e:
        return handle_service_error(e)
@app.get("/api/medical_office/appointments/{id_app}")
def get_appointments_by_id(request: Request, id_app: int):
    #doctor, patient
    if int(id_app) <= 0:
        raise HTTPException(status_code=400, detail="Appointment ID is invalid.")
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
        if response.is_valid == "valid":
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"http://appointment-service:8000/appointments/{id_app}", headers=headers)
            response.raise_for_status()

            appointment_json = response.json()

            return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                content=appointment_json)
        else:
            raise HTTPException(status_code=401, detail="Not auth")
    except requests.RequestException as e:
        return handle_service_error(e)


@app.post('/api/medical_office/appointments/')
async def create_appointment(request: Request):
    #patient, doctor
    data = await request.json()
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")
        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
        headers = {"Authorization": f"Bearer {token}"}
        if response.is_valid == "valid":
            response = requests.post("http://appointment-service:8000/appointments/",headers=headers, json=data)
            response.raise_for_status()

            appointment_json = response.json()

            return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                content=appointment_json)
        else:
            raise HTTPException(status_code=401)
    except requests.RequestException as e:
        return handle_service_error(e)


@app.delete('/api/medical_office/appointments/{appointment_id}')
def delete_appointment(appointment_id: int, request: Request):
    #admin
    if int(appointment_id) <= 0:
        raise HTTPException(status_code=400, detail="Appointment ID is invalid.")
    try:
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
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.delete(f"http://appointment-service:8000/appointments/{appointment_id}", headers=headers)
                response.raise_for_status()

                appointment_json = response.json()

                return JSONResponse(status_code=204, headers=headers, media_type="application/json",
                                    content=appointment_json)
            else:
                raise HTTPException(status_code=403)
        else:
            raise HTTPException(status_code=401)
    except requests.RequestException as e:
        return handle_service_error(e)

@app.patch('/api/medical_office/appointments/{appointment_id}')
async def update_appointment(appointment_id: int, request: Request):
    #patientul sa modifice data sau doctorul
    if int(appointment_id) <= 0:
        raise HTTPException(status_code=400, detail="Appointment ID is invalid.")
    data = await request.json()
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header is None or not authorization_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Not access")

        token = authorization_header.split(" ")[1]
        grpc_stub = grpc_client()
        headers = {"Authorization": f"Bearer {token}"}
        response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
        if response.is_valid == "valid":
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_type = payload.get('role')

            if user_type == 'patient' or user_type == 'doctor':
                response = requests.patch(f"http://appointment-service:8000/appointments/{appointment_id}", headers=headers, json=data)
                response.raise_for_status()

                appointment_json = response.json()

                return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                                    content=appointment_json)
            else:
                raise HTTPException(status_code=403)
        else:
            raise HTTPException(status_code=401)

    except requests.RequestException as e:
        return handle_service_error(e)

###########CONSULTATIONS##################
@app.get("/api/medical_office/consultations")
async def get_consultations(request: Request, id_doctor: Optional[str] = None, id_patient: Optional[str] = None):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        headers = {"Authorization": f"Bearer {token}"}
        try:
            params = {}
            if id_doctor:
                params['id_doctor'] = id_doctor
            if id_patient:
                params['id_patient'] = id_patient

            response = requests.get("http://consultation-service:8000/consultations", params=params, headers=headers)
            response.raise_for_status()
            consultations = response.json()
            return consultations
        except requests.RequestException as e:
            return handle_service_error(e)

@app.get("/api/medical_office/consultations/{id_consultation}")
def get_consultation_by_id( request: Request ,id_consultation):
    #doctor si patientul al carui este consultatia
    try:
        authorization_header = request.headers.get('Authorization')
        token = authorization_header.split(" ")[1]
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"http://consultation-service:8000/consultations/{id_consultation}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return handle_service_error(e)

@app.post("/api/medical_office/consultations")
async def create_consultation(request: Request):
    data = await request.json()
    authorization_header = request.headers.get('Authorization')
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    consultation_data = {
        "id_consultation": data.get("id_consultation"),
        "id_appointment": data.get("id_appointment"),
        "id_patient": data.get("id_patient"),
        "id_doctor": data.get("id_doctor"),
        "date": data.get("date"),
        "diagnostic": data.get("diagnostic"),
        "investigation": data.get("id_investigation")
    }

    investigation_data = {
        "id_investigation": data.get("id_investigation"),
        "name": data.get("name"),
        "id_consultation": data.get("id_consultation"),
        "processing_time": data.get("processing_time"),
        "result": data.get("result")
    }

    try:
        consultation_response = requests.post("http://consultation-service:8000/consultations", json=consultation_data, headers=headers)
        consultation_response.raise_for_status()

        investigation_response = requests.post("http://investigation-service:8000/investigations", json=investigation_data, headers=headers)
        investigation_response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    print(consultation_response.json())
    return {"consultation_response": consultation_response.json(),
            "investigation_response": investigation_response.json()}

@app.patch("/api/medical_office/consultations/{id_consultation}")
async def update_consultation(request:Request, id_consultation):

    authorization_header = request.headers.get('Authorization')
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    data = await request.json()
    try:
        response = requests.patch(
            f"http://consultation-service:8000/consultations/{id_consultation}",
            json=data, headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return handle_service_error(e)

@app.delete('/api/medical_office/consultations/{id_consultation}')
def delete_consultation(request:Request, id_consultation):
    #vedem ce restrictii impunem pt metoda
    try:
        authorization_header = request.headers.get('Authorization')
        token = authorization_header.split(" ")[1]
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"http://consultation-service:8000/consultation/{id_consultation}", headers=headers)
        response.raise_for_status()
        return Response(status_code=204)

    except requests.RequestException as e:
        return handle_service_error(e)

#########INVESTIGATION#################

@app.get("/api/medical_office/investigation")
def list_investigation(request: Request):
    #doctor
    try:
        authorization_header = request.headers.get('Authorization')
        token = authorization_header.split(" ")[1]
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://investigation-service:8000/investigation", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return handle_service_error(e)

@app.get("/api/medical_office/investigations/{id_investigation}")
def get_investigation_by_id(request:Request, id_investigation:str):
    #doctor si patientul al carui este investigatia
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == "valid":
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(f"http://investigation-service:8000/investigations/{id_investigation}", headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return handle_service_error(e)
    else:
        raise HTTPException(status_code=401)

@app.post('/api/medical_office/investigation')
async def create_investigation(request: Request):
    #doctor
    authorization_header = request.headers.get('Authorization')
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    data = await request.json()
    try:

        response = requests.post("http://investigation-service:8000/investigation", json=data, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return handle_service_error(e)
    return response.json()

@app.delete("/api/medical_office/investigation/{id_investigation}")
def delete_patient(request: Request, id_investigation: str):
    authorization_header = request.headers.get('Authorization')
    token = authorization_header.split(" ")[1]
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(f"http://investigation-service:8000/investigation/{id_investigation}", headers=headers)
        response.raise_for_status()
        return Response(status_code=204)
    except requests.RequestException as e:
        return handle_service_error(e)

@app.patch("/api/medical_office/investigations/{id_investigation}")
async def update_investigation(request: Request, id_investigation: str):
    authorization_header = request.headers.get('Authorization')
    token = authorization_header.split(" ")[1]
    data = await request.json()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(f"http://investigation-service:8000/investigations/{id_investigation}",json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return handle_service_error(e)

##########USERS###############
@app.post('/api/medical_office/login')
async def login(request: Request):
    data = await request.json()
    grpc_stub = grpc_client()
    response = grpc_stub.Login(idmService_pb2.LoginRequest(username=data['username'], password=data['password']))
    #print("AICIIIIII " + str(response.code))
    if response.access_token:
        print("Aicic"+response.access_token)
        payload = jwt.decode(response.access_token, SECRET_KEY, algorithms=["HS256"])

        user_type = payload.get('role')
        user_id = payload.get('sub')
        headers = {"Authorization": f"Bearer {response.access_token}"}
        links = [Link(mode="self", href=f"/api/medical_office/login", type="POST"),
                 Link(mode="parent", href=f"/api/medical_office", type="GET")]
        json = {"Authorization": f"Bearer {response.access_token}",'user_role':user_type , 'user_id': user_id, "_links":{link.mode: {"type": link.type, "href": link.href} for link in links}}

        return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                            content=json)
    else:
        raise HTTPException(status_code=response.code, detail=response.message)

@app.post('/api/medical_office/signup')
async def signup(request: Request):
    data = await request.json()
    # print("am intrat ")
    grpc_stub = grpc_client()
    response = grpc_stub.SignUp(idmService_pb2.SignUpRequest(username=data.get('username'), password=data.get('password')))

    #print("am iesit" + response.access_token)
    if response.access_token:
        id_user = response.id_user
        patient_data = {
            "cnp": data.get('cnp'),
            "id_user": id_user,
            "last_name": data.get('last_name'),
            "first_name": data.get('first_name'),
            "email": data.get('email'),
            "phone": data.get('phone'),
            "birth_date": data.get('birth_date'),
            "is_active": data.get('is_active')
        }
        try:
            patient_response = requests.post("http://patient-service:8000/patients", json=patient_data)
            patient_response.raise_for_status()

            headers = {"Authorization": f"Bearer {response.access_token}"}
            payload = jwt.decode(response.access_token, SECRET_KEY, algorithms=["HS256"])

            user_type = payload.get('role')
            user_id = payload.get('sub')
            json = patient_response.json()

            links = [Link(mode="self", href=f"/api/medical_office/signup", type="POST"),
                     Link(mode="parent", href=f"/api/medical_office", type="GET")]
            json["_links"] = {link.mode: {"type": link.type, "href": link.href} for link in links}
            json["Authorization"]= f"Bearer {response.access_token}"
            json['user_role'] = user_type
            json['user_id'] = user_id

            return JSONResponse(status_code=201, headers=headers, media_type="application/json",
                                content=json)
        except requests.RequestException as e:
            grpc_stub.DeleteUser(idmService_pb2.DeleteUserRequest(user_id=response.id_user))
            return handle_service_error(e)

    else:
        grpc_stub.DeleteUser(idmService_pb2.DeleteUserRequest(user_id=response.id_user))
        raise HTTPException(status_code=response.code, detail="Înregistrare eșuată")

@app.patch('/api/medical_office/update-data')
async def update_data_user(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Not access")
    token = authorization_header.split(" ")[1]

    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_id = payload.get('sub')
    data = await request.json()

    grpc_stub = grpc_client()
    response = grpc_stub.UpdateUser(idmService_pb2.UpdateUserRequest(username=data.get('username'), password=data.get('password'), user_id=user_id))

    if response.code == 200:
        headers = {"Authorization": f"Bearer {token}"}
        json = response.json()
        links = [Link(mode="self", href=f"/api/medical_office/update-data", type="PATCH"),
                 Link(mode="parent", href=f"/api/medical_office", type="GET")]
        json["_links"] = {link.mode: {"type": link.type, "href": link.href} for link in links}

        return JSONResponse(status_code=200, headers=headers, media_type="application/json",
                            content=json)
    else:
        raise HTTPException(status_code=response.code, detail=response.message)
