FROM mariadb:latest

ENV MYSQL_ROOT_PASSWORD=pass
ENV MYSQL_DATABASE=userdb
ENV MYSQL_USER=cosmin
ENV MYSQL_PASSWORD=cosmin

RUN apt-get update && apt-get install -y mysql-client

EXPOSE 3306
