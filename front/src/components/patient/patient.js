import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './patient.css';
import { useNavigate } from 'react-router-dom';

function Patient() {
  const [patientDetails, setPatientDetails] = useState(null);
  const navigate = useNavigate();
  useEffect(() => {
    const fetchPatientDetails = async () => {
      try {
        const token = localStorage.getItem('token');
        const id_user = localStorage.getItem('userId');
        const response = await axios.get(`http://localhost:8000/api/medical_office/patients/${id_user}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setPatientDetails(response.data.patient);
      } catch (error) {
        console.error('Error fetching patient details:', error);
        if (error.response && error.response.status == 401) {
          localStorage.removeItem('token');
          navigate('/login');
      }
      }
    };

    fetchPatientDetails();
  }, []);

  if (!patientDetails) {
    return <p>Loading...</p>;
  }

  const { cnp,  last_name, first_name, email, phone, birth_date, is_active } = patientDetails;

  return (
    <div className="patient-details">
      <h2>Detalii Pacient</h2>
      <p><strong>CNP:</strong> {cnp}</p>
      
      <p><strong>Nume:</strong> {last_name}</p>
      <p><strong>Prenume:</strong> {first_name}</p>
      <p><strong>Email:</strong> {email}</p>
      <p><strong>Telefon:</strong> {phone}</p>
      <p><strong>Data nașterii:</strong> {birth_date}</p>
      
      
      <button onClick={() => navigate('/medical-history')}>Istoric Medical</button>
    </div>
  );
}

export default Patient;
