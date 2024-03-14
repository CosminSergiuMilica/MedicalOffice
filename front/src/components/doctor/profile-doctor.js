import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './doctor.css';
import { useNavigate } from 'react-router-dom';

function Doctor() {
  const [doctorDetails, setDoctorDetails] = useState(null);
  const navigate = useNavigate(); // Hook-ul useNavigate pentru a naviga între pagini

  useEffect(() => {
    const fetchDoctorDetails = async () => {
      try {
        const token = localStorage.getItem('token');
        const id = localStorage.getItem('userId');
        const response = await axios.get(`http://localhost:8000/api/medical_office/doctors/${id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const doctorData = response.data.doctor;
        setDoctorDetails(doctorData);
      } catch (error) {
        console.error('Error fetching doctor details:', error);
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('token');
          navigate('/login');
      }
      }
    };

    fetchDoctorDetails();
  }, []);

  const handleAppointments = async (id_doctor) => {
  
    navigate(`/doctor/programari/${id_doctor}`); 
  };

  if (!doctorDetails) {
    return <p>Loading...</p>;
  }

  const { id_doctor, last_name, first_name, email, phone, specialization } = doctorDetails;

  return (
    <div className="doctor-details">
      <h2>Detalii Medic</h2>
      <p><strong>Nume:</strong> {last_name}</p>
      <p><strong>Prenume:</strong> {first_name}</p>
      <p><strong>Email:</strong> {email}</p>
      <p><strong>Telefon:</strong> {phone}</p>
      <p><strong>Specializare:</strong> {specialization}</p>

      <button onClick={() => handleAppointments(id_doctor)}>Programările Mele</button>
    </div>
  );
}

export default Doctor;
