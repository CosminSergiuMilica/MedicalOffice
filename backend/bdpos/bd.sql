CREATE DATABASE IF NOT EXISTS `pos-bd`;
USE `pos-bd`;
-- Crearea tabelului pentru pacienți (patients)
CREATE TABLE IF NOT EXISTS `patients` (
  `cnp` CHAR(13) NOT NULL PRIMARY KEY,
  `id_user` INT NOT NULL,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `email` VARCHAR(70) NOT NULL UNIQUE,
  `phone` CHAR(10) NOT NULL CHECK (phone REGEXP '^07[0-9]{8}$'),
  `birth_date` DATE NOT NULL,
  `is_active` BOOLEAN NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Crearea tabelului pentru doctori (doctors)
CREATE TABLE IF NOT EXISTS `doctors` (
  `id_doctor` INT AUTO_INCREMENT PRIMARY KEY,
  `id_user` INT NOT NULL,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `email` VARCHAR(70) NOT NULL UNIQUE,
  `phone` CHAR(10) NOT NULL CHECK (phone REGEXP '^[0-9]{10}$'),
  `specialization` ENUM('pediatru', 'chirurg', 'nutritionist', 'ortoped', 'dentist', 'oftalmolog') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Crearea tabelului pentru programari (appointments)
CREATE TABLE IF NOT EXISTS `appointments` (
  `id_appointment` INT AUTO_INCREMENT PRIMARY KEY,
  `id_patient` CHAR(13) NOT NULL,
  `id_doctor` INT NOT NULL,
  `date` DATETIME NOT NULL,
  `status` ENUM('onorată', 'neprezentat', 'anulată') NOT NULL,
  CONSTRAINT `fk_appointment_patient` FOREIGN KEY (`id_patient`) REFERENCES `patients` (`cnp`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_appointment_doctor` FOREIGN KEY (`id_doctor`) REFERENCES `doctors` (`id_doctor`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
