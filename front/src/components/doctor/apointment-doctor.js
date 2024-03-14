import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useParams, useNavigate } from 'react-router-dom';
import './appoint.css';

function Appointments() {
  const [appointments, setAppointments] = useState([]);
  const { id_doctor } = useParams(); 
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`http://localhost:8000/api/medical_office/appointments/doctor/${id_doctor}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setAppointments(response.data.appointments);
      } catch (error) {
        console.error('Error fetching appointments:', error);
        if (error.response && error.response.status == 401) {
          localStorage.removeItem('token');
          navigate('/login');
      }
      }
    };

    fetchAppointments();
  }, [id_doctor]);

  return (
    <div className='Appointments'>
      <h2>Programări mele</h2>
      <ul>
        {appointments.length > 0 ? (
          appointments.map(appointment => (
            <li key={appointment.id_appointment}>
             
              {/* <p>ID Medic: {appointment.id_doctor}</p> */}
              {/* <p>ID Pacient: {appointment.id_patient}</p> */}
              <p>Data și Ora: {appointment.date}</p>
              <p>Status: {appointment.status}</p>
              <Link to={`/programari/${appointment.id_appointment}`}>Vezi detalii</Link>
            </li>
          ))
        ) : (
          <li>Nu există programari pentru acest medic.</li>
        )}
      </ul>
    </div>
  );
}

export default Appointments;
