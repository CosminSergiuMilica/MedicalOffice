import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useParams, useNavigate } from 'react-router-dom';

const AppointmentsHistory = () => {
    const [appointments, setAppointments] = useState([]);
    const [doctorDetailsList, setDoctorDetailsList] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchAppointments = async () => {
            try {
                const token = localStorage.getItem('token');
                const id_patient = localStorage.getItem('userId');
                const response = await axios.get(`http://localhost:8000/api/medical_office/appointments/patient/${id_patient}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                setAppointments(response.data.appointments);

                const doctorDetailsPromises = response.data.appointments.map(appointment =>
                    fetchDoctorDetails(appointment.id_doctor)
                );

                const doctorDetailsResolved = await Promise.all(doctorDetailsPromises);
                setDoctorDetailsList(doctorDetailsResolved);
            } catch (error) {
                console.error('Error fetching appointments:', error);
                if (error.response && error.response.status == 401) {
                    localStorage.removeItem('token');
                    navigate('/login');
                }
            }
        };

        fetchAppointments();
    }, []);

    const fetchDoctorDetails = async (doctorId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`http://localhost:8000/api/medical_office/doctors/${doctorId}`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            return response.data.doctor;
        } catch (error) {
            console.error('Error fetching doctor details:', error);
            if (error.response && error.response.status == 401) {
                localStorage.removeItem('token');
                navigate('/login');
            }
        }
    };

    return (
        <div className="appointments-list-container">
            <h2>Lista de Programări</h2>
            <ul className="appointments-list">
                {appointments.map((appointment, index) => (
                    <li key={appointment.id_appointment}>
                        <div className="appointment-info">
                            <p >Data: {new Date(appointment.date).toLocaleDateString()}</p>
                            <p >Ora: {new Date(appointment.date).toLocaleTimeString()}</p>
                            <p >
                                Doctor:{' '}
                                {doctorDetailsList[index]
                                    ? `${doctorDetailsList[index].first_name} ${doctorDetailsList[index].last_name}`
                                    : 'Nedeterminat'}
                            </p>
                            <div>
                            <Link to={`/programari/consultation/${appointment.id_appointment}`}><button>Detalii Consultație</button></Link>
                        </div>
                        </div>
                        
                    </li>
                ))}
            </ul>

        </div>

    );
};

export default AppointmentsHistory;
