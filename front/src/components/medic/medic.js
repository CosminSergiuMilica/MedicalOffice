import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './medic.css';

const MedicProfile = () => {
    const { id_doctor } = useParams();
    const [doctorDetails, setDoctorDetails] = useState(null);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const [userRole, setUserRole] = useState(null);
    const [selectedDate, setSelectedDate] = useState('');
    const [selectedTime, setSelectedTime] = useState('');
    const [successNotification, setSuccessNotification] = useState(false);

    useEffect(() => {
        const fetchDoctorDetails = async () => {
            try {
                const token = localStorage.getItem('token');
                const response = await axios.get(`http://localhost:8000/api/medical_office/doctors/${id_doctor}`, {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });
                setDoctorDetails(response.data.doctor);
                setUserRole(localStorage.getItem('userRole'));
            } catch (error) {
                console.error('Error fetching doctor details:', error);
                if (error.response) {
                    if (error.response.status == 401) {
                        navigate('/login');
                    } else if (error.response.status == 403) {
                        setError(error.response.data.detail || 'Acces denied');
                    } else {
                        setError('An unknown error occurred.');
                    }
                } else {
                    setError('An unknown error occurred.');
                }
            }
        };

        fetchDoctorDetails();
    }, [id_doctor]);

    const createAppointment = async () => {
        try {
            const token = localStorage.getItem('token');
            const dateTimeString = `${selectedDate} ${selectedTime}`;
            const appointmentData = {
                id_doctor: doctorDetails.id_doctor, 
                id_patient: localStorage.getItem('userId'),
                date: dateTimeString,
                status: "neprezentat"
            };

            const response = await axios.post('http://localhost:8000/api/medical_office/appointments/', appointmentData, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            setSuccessNotification(true);
        } catch (error) {
            setError(error.response ? error.response.data.message : 'An unknown error occurred.');
        }
    };

//     if (error) {
//     return (
//         <div className="error-message">
//             <p>{error}</p>
//         </div>
//     );
// }

    if (!doctorDetails) {
        return <p>Loading...</p>;
    }

    const { last_name, first_name, email, phone, specialization } = doctorDetails;

    return (
        <div className="medic-profile">
            <h2>Alege servicii de calitate</h2>

            <p>Nume: {last_name}</p>
            <p>Prenume: {first_name}</p>
            <p>Email: {email}</p>
            <p>Telefon: {phone}</p>
            <p>Specializare: {specialization}</p>

            {userRole === 'patient' && (
                <>
                    <h3>Programare</h3>
                    <label>Data:</label>
                    <input type="date" onChange={(e) => setSelectedDate(e.target.value)} />

                    <label>Ora:</label>
                    <input type="time" onChange={(e) => setSelectedTime(e.target.value)} />

                    <button onClick={createAppointment}>Programează</button>
                    {error && <p className="error-message">{error}</p>}
                    {successNotification && (
                        <div className="success-notification">
                            <p>Programarea a fost creata cu succes!</p>
                            
                        </div>
                    )}
                    
                </>
            )}
        </div>
    );
};

export default MedicProfile;
