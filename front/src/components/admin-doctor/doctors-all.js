import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './admin.css';

const DoctorList = () => {
  const [doctors, setDoctors] = useState([]);

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/medical_office/doctors');
        setDoctors(response.data.doctors);
      } catch (error) {
        console.error('Error fetching doctors:', error);
      }
    };

    fetchDoctors();
  }, []);

  return (
    <div className="doctors-list-container">
      <h2>Lista de Doctori</h2>
      <ul className="doctors-list">
        {doctors.map(doctor => (
          <li key={doctor.id_doctor} className="doctor-item">
            <div className="doctor-info">
              <p>Nume: {`${doctor.last_name} ${doctor.first_name}`}</p>
              <p>Email: {doctor.email}</p>
              <p>Telefon: {doctor.phone}</p>
              <p>Specializare: {doctor.specialization || 'Nespecificat'}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DoctorList;
