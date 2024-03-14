FROM mariadb:latest
ENV MYSQL_ROOT_PASSWORD=pass
ENV MYSQL_DATABASE=pos-bd
ENV MYSQL_USER=cosmin
ENV MYSQL_PASSWORD=cosmin

RUN apt-get update && apt-get install -y mysql-client

WORKDIR /bazadate
COPY bd.sql /bazadate/bd.sql
COPY insert.sql /bazadate/insert.sql
COPY configure-permissions.sql /bazadate/configure-permissions.sql
EXPOSE 3306