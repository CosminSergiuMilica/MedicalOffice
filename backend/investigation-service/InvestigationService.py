from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.openapi.utils import get_openapi
import jwt
from pymongo import MongoClient
from typing import List
import requests
from pymongo.errors import ConnectionFailure
from utile import idmService_pb2_grpc, idmService_pb2
import grpc
from fastapi.responses import JSONResponse
def grpc_client():
    channel = grpc.insecure_channel('proiect-api-users-service-1:50051')
    return idmService_pb2_grpc.IDMServiceStub(channel)

try:
    client = MongoClient("mongodb://cosmin:cosmin@mongo-pos:27017")
    db = client["mongodb-pos"]
    investigation = db["investigations"]
except ConnectionFailure:
    raise HTTPException(status_code=503, detail="Failed to connect to the database. Please make sure MongoDB is running")

app = FastAPI()
SECRET_KEY = "GoSdJgsDEe343"
@app.on_event("shutdown")
def shutdown():
    if not client.is_closed():
        client.close()


def transform_investigation_data(investigation_data):
    return {
        "id_investigation": investigation_data.get("id_investigation"),
        "name": investigation_data.get("name"),
        "id_consultation": investigation_data.get("id_consultation"),
        "processing_time": investigation_data.get("processing_time"),
        "result": investigation_data.get("result")
    }

@app.get("/docs")
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="API Title", version="1.0.0", routes=app.routes))
@app.get("/investigations")
def read_consultation(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        investigations = investigation.find({})
        investigations_list = [transform_investigation_data(i) for i in investigations]

        links = [
            {"mode": "self", "href": f"/api/medical_office/investigations", "type": "GET"},
            {"mode": "parent", "href": f"/api/medical_office", "type": "GET"}
        ]

        response_data = {
            "investigations": investigations_list,
            "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
        }

        return JSONResponse(status_code=200, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.get("/investigations/{id_investigation}")
def get_investigation_by_id(request: Request, id_investigation:str):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        inv = db.investigations.find({'id_investigation': id_investigation})
        if not inv:
            raise HTTPException(status_code=404, detail=f"Investigation with id {id_investigation} does not exist!")

        investigations_list = [transform_investigation_data(i) for i in inv]

        links = [
            {"mode": "self", "href": f"/api/medical_office/investigations/{id_investigation}", "type": "GET"},
            {"mode": "parent", "href": f"/api/medical_office/investigations", "type": "GET"}
        ]

        response_data = {
            "investigations": investigations_list,
            "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
        }

        return JSONResponse(status_code=200, content=response_data)
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.post("/investigations")
async def create_investigation(request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == 'doctor':
            investigation_data = await request.json()

            investigation_dict = {
                "id_investigation": investigation_data.get("id_investigation"),
                "name": investigation_data.get("name"),
                "id_consultation": investigation_data.get("id_consultation"),
                "processing_time": investigation_data.get("processing_time"),
                "result": investigation_data.get("result")
            }

            try:
                inserted_id = investigation.insert_one(investigation_dict).inserted_id
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to insert investigation: {str(e)}")

            links = [
                {"mode": "self", "href": f"/api/medical_office/investigations", "type": "POST"},
                {"mode": "parent", "href": f"/api/medical_office/investigations", "type": "GET"}
            ]

            response_data = {
                "message": "Investigation created successfully",
                "id": str(inserted_id),
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }

            return JSONResponse(status_code=201, content=response_data)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.patch("/investigations/{id_investigation}")
async def update_investigation(id_investigation: str, request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == 'doctor':
            existing_investigation = investigation.find_one({"id_investigation": id_investigation})
            if not existing_investigation:
                raise HTTPException(status_code=404, detail=f"Investigation with id {id_investigation} not found")

            investigation_data = await request.json()

            try:
                updated_result = investigation.update_one({"id_investigation": id_investigation}, {"$set": investigation_data})
                if updated_result.modified_count == 0:
                    raise HTTPException(status_code=404, detail=f"Investigation with id {id_investigation} not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update investigation: {str(e)}")

            links = [
                {"mode": "self", "href": f"/api/medical_office/investigations/{id_investigation}", "type": "PATCH"},
                {"mode": "parent", "href": f"/api/medical_office/investigations", "type": "GET"}
            ]

            response_data = {
                "message": "Investigation updated successfully",
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }

            return JSONResponse(status_code=200, content=response_data)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")

@app.delete('/investigations/{id_investigation}')
def delete_investigation(request: Request, id_investigation):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == 'doctor':
            existing_investigation = investigation.find_one({"id_investigation": id_investigation})
            if not existing_investigation:
                raise HTTPException(status_code=404, detail=f'Investigation with id: {id_investigation} not found')

            try:
                deleted_result = investigation.delete_one({"id_investigation": id_investigation})
                if deleted_result.delete_count == 0:
                    raise HTTPException(status_code=404, detail=f"Failed to delete investigation {id_investigation}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete investigation {id_investigation}")

            links = [
                {"mode": "self", "href": f"/api/medical_office/investigations/{id_investigation}", "type": "DELETE"},
                {"mode": "parent", "href": f"/api/medical_office/investigations", "type": "GET"}
            ]

            response_data = {
                "message": "Investigation deleted successfully",
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }

            return JSONResponse(status_code=204, content=response_data)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@app.put("/investigations/{id_investigation}")
async def update_full_investigation(id_investigation: str, request: Request):
    authorization_header = request.headers.get('Authorization')
    if authorization_header is None or not authorization_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Unauthorized access")

    token = authorization_header.split(" ")[1]
    grpc_stub = grpc_client()
    response = grpc_stub.VerifyToken(idmService_pb2.TokenRequest(token=token))
    if response.is_valid == 'valid':
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_type = payload.get('role')

        if user_type == 'doctor':
            investigation_data = await request.json()

            existing_investigation = investigation.find_one({"id_investigation": id_investigation})

            if existing_investigation:
                try:
                    investigation.update_one({"id_investigation": id_investigation}, {"$set": investigation_data})
                    message = "The investigation has been updated successfully"
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error updating investigation")
            else:
                try:
                    investigation_data["id_investigation"] = id_investigation
                    investigation.insert_one(investigation_data)
                    message = "A new investigation has been created successfully"
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Error creating investigation")

            links = [
                {"mode": "self", "href": f"/api/medical_office/investigations/{id_investigation}", "type": "PUT"},
                {"mode": "parent", "href": f"/api/medical_office/investigations", "type": "GET"}
            ]

            response_data = {
                "message": message,
                "_links": {link["mode"]: {"type": link["type"], "href": link["href"]} for link in links}
            }

            return JSONResponse(status_code=201, content=response_data)
        else:
            raise HTTPException(status_code=403, detail="Forbidden access")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")