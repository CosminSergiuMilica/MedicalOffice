import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { v4 as uuidv4 } from 'uuid';
import './doctor.css';
function AppointmentDetails() {
  const [appointmentDetails, setAppointmentDetails] = useState(null);
  const [showConsultationForm, setShowConsultationForm] = useState(false);
  const [diagnostic, setDiagnostic] = useState('sanatos');
  const [name, setName] = useState('');
  const [result, setResult] = useState('');
  const { id_appointment } = useParams(); 
  const currentDateTime = format(new Date(), "yyyy-MM-dd'T'HH:mm:ss");
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAppointmentDetails = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`http://localhost:8000/api/medical_office/appointments/${id_appointment}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setAppointmentDetails(response.data.appointments[0]); 
      } catch (error) {
        console.error('Error fetching appointment details:', error);
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('token');
          navigate('/login');
        }
      }
    };

    fetchAppointmentDetails();
  }, [id_appointment]);

  const handleShowConsultationForm = () => {
    setShowConsultationForm(true);
  };

  const handleSubmitConsultation = async (event) => {
    event.preventDefault();
    if (!diagnostic || !name || !result) {
        setErrorMessage('Va rugam sa completati toate campurile.');
        setSuccessMessage('');
        return;
  }
    try {
      const token = localStorage.getItem('token');
      const consultationData = {
        id_consultation: uuidv4(), 
        id_patient: appointmentDetails.id_patient,
        id_appointment:appointmentDetails.id_appointment,
        id_doctor: appointmentDetails.id_doctor,
        date: currentDateTime, 
        diagnostic: diagnostic,
        id_investigation: uuidv4(), 
        name: name,
        processing_time: currentDateTime, 
        result: result
      };
      
      const response = await axios.post('http://localhost:8000/api/medical_office/consultations', consultationData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setSuccessMessage('Consultatia a fost creata cu succes!');
      setErrorMessage('');
      console.log('Consultation created:', response.data);
    } catch (error) {
      console.error('Error creating consultation:', error);
      if (error.response && error.response.status === 401) {
          setErrorMessage(error.response ? error.response.data.detail : 'An unknown error occurred.');
          setSuccessMessage('');
          navigate('/login')
          localStorage.removeItem('token');
          navigate('/login');
      }
    }
  };

  if (!appointmentDetails) {
    return <p>Loading appointment details...</p>;
  }

  const { id_doctor, id_patient, date, status } = appointmentDetails;

  return (
    <div className='AppointmentDetails'>
      <h2>Detalii Programare</h2>
      {/* <p><strong>ID Programare:</strong> {id_appointment}</p>
      <p><strong>ID Medic:</strong> {id_doctor}</p>
      <p><strong>ID Pacient:</strong> {id_patient}</p> */}
      <p><strong>Data:</strong> {date}</p>
      <p><strong>Status:</strong> {status}</p>
      
      <div>
        <Link to={`/programari/consultation/${id_appointment}`}><button>Detalii Consultație</button></Link>
      </div>
      
      {showConsultationForm ? (
        <form onSubmit={handleSubmitConsultation}>
          <label>
            Diagnostic:
            <select value={diagnostic} onChange={(event) => setDiagnostic(event.target.value)}>
              <option value="sanatos">Sanatos</option>
              <option value="bolnav">Bolnav</option>
            </select>
          </label>
          <label>
            Name:
            <input type="text" value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label>
            Result:
            <input type="text" value={result} onChange={(event) => setResult(event.target.value)} />
          </label>
          <button type="submit">Creează Consultație</button>
        </form>
        
      ) : (
        <button onClick={handleShowConsultationForm}>Creează Consultație</button>
      )}
      {successMessage && (
        <p className="success-message">{successMessage}</p>
      )}

      {errorMessage && (
        <p className="error-message">{errorMessage}</p>
      )}
    
    </div>
    
  );
}

export default AppointmentDetails;
