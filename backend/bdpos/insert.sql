USE `idm-db`;

-- Inserarea datelor în tabelul `users`
INSERT INTO `users` (`username`, `password`) VALUES
('user1', 'password1'),
('user2', 'password2'),
('user3', 'password3'),
('user4', 'password4'),
('user5', 'password5');

USE `pos-db`;

-- Inserarea datelor în tabelul `patients`
INSERT INTO `patients` (`cnp`, `id_user`, `first_name`, `last_name`, `email`, `phone`, `birth_date`, `is_active`) VALUES
('1234567890123', 1, 'John', 'Doe', 'john.doe@example.com', '0712345678', '1980-01-01', TRUE),
('1234567890124', 2, 'Jane', 'Smith', 'jane.smith@example.com', '0723456789', '1985-02-02', TRUE),
('1234567890125', 3, 'Bob', 'Johnson', 'bob.johnson@example.com', '0734567890', '1990-03-03', FALSE),
('1234567890126', 4, 'Alice', 'Brown', 'alice.brown@example.com', '0745678901', '1995-04-04', TRUE),
('1234567890127', 5, 'Tom', 'Davis', 'tom.davis@example.com', '0756789012', '2000-05-05', FALSE);

-- Inserarea datelor în tabelul `doctors`
INSERT INTO `doctors` (`id_user`, `first_name`, `last_name`, `email`, `phone`, `specialization`) VALUES
(1, 'Dr. John', 'Doe', 'dr.john@example.com', '0765432109', 'pediatru'),
(2, 'Dr. Jane', 'Smith', 'dr.jane@example.com', '0765432110', 'chirurg'),
(3, 'Dr. Bob', 'Johnson', 'dr.bob@example.com', '0765432111', 'nutritionist'),
(4, 'Dr. Alice', 'Brown', 'dr.alice@example.com', '0765432112', 'ortoped'),
(5, 'Dr. Tom', 'Davis', 'dr.tom@example.com', '0765432113', 'dentist');

-- Inserarea datelor în tabelul `appointments`
INSERT INTO `appointments` (`id_patient`, `id_doctor`, `date`, `status`) VALUES
('1234567890123', 1, '2023-11-15', 'onorată'),
('1234567890124', 2, '2023-11-16', 'neprezentat'),
('1234567890125', 3, '2023-11-17', 'anulată'),
('1234567890126', 4, '2023-11-18', 'onorată'),
('1234567890127', 5, '2023-11-19', 'neprezentat');
