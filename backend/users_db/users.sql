CREATE TABLE IF NOT EXISTS users (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    tip ENUM('admin', 'patient', 'doctor') NOT NULL,
    secret VARCHAR(10) NOT NULL
);
REVOKE CREATE, DROP ON database_name.* FROM 'cosmin'@'localhost';
