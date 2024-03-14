FROM python:3.12.0
ENV APP_PORT=8000

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install pymongo
COPY . .

CMD sh -c 'uvicorn InvestigationService:app --host 0.0.0.0 --port $APP_PORT'