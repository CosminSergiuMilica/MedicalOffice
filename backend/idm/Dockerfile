FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install grpcio grpcio-tools bcrypt pyjwt peewee requests~=2.31.0
RUN pip install pymysql

CMD ["python", "UserService.py"]
