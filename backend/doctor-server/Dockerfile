FROM python:3.12.0
ENV APP_PORT=8000

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . . 

CMD sh -c 'uvicorn DoctorService:app --host 0.0.0.0 --port $APP_PORT'