import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './doctor.css';
import { useParams, useNavigate } from 'react-router-dom';

function ConsultationDetails() {
  const [consultationDetails, setConsultationDetails] = useState([]);
  const [investigationDetails, setInvestigationDetails] = useState([]);
  const [updatedConsultations, setUpdatedConsultations] = useState([]);
  const [updatedInvestigations, setUpdatedInvestigations] = useState([]);
  const { id_consultation } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchConsultationDetails = async () => {
      try {
        const token = localStorage.getItem('token');
        const consultationResponse = await axios.get(`http://localhost:8000/api/medical_office/consultations/${id_consultation}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setConsultationDetails(consultationResponse.data.consultations);
        setUpdatedConsultations(consultationResponse.data.consultations.map(consultation => ({ ...consultation })));
        
        const investigations = await Promise.all(consultationResponse.data.consultations.map(async consultation => {
          if (consultation.investigation) {
            const investigationId = consultation.investigation;
            const investigationResponse = await axios.get(`http://localhost:8000/api/medical_office/investigations/${investigationId}`, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            });
            return investigationResponse.data.investigations[0];
          }
          return null;
        }));
        setInvestigationDetails(investigations);
        setUpdatedInvestigations(investigations.map(investigation => ({ ...investigation })));
      } catch (error) {
        if (error.response && error.response.status === 401) {
          localStorage.removeItem('token');
          navigate('/login');
        }
      }
    };

    fetchConsultationDetails();
  }, [id_consultation, navigate]);

  const handleUpdateConsultation = async (consultationId) => {
    try {
      const token = localStorage.getItem('token');
      const updatedConsultation = updatedConsultations.find(consultation => consultation.id_consultation === consultationId);
      await axios.patch(`http://localhost:8000/api/medical_office/consultations/${consultationId}`, updatedConsultation, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Error updating consultation:', error);
      if (error.response && error.response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    }
  };

  const handleUpdateInvestigation = async (investigationId) => {
    try {
      const token = localStorage.getItem('token');
      const updatedInvestigation = updatedInvestigations.find(investigation => investigation.id_investigation === investigationId);
      await axios.patch(`http://localhost:8000/api/medical_office/investigations/${investigationId}`, updatedInvestigation, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Error updating investigation:', error);
      if (error.response && error.response.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    }
  };

  const userRole = localStorage.getItem('userRole');

  if (!consultationDetails.length || !investigationDetails.length) {
    return <p>Loading consultation details...</p>;
  }

  return (
    <div className="consultation-details-container"> 
      {consultationDetails.map((consultation, index) => (
        <div key={index}>
          <h2>Detalii Consultație</h2>
          <div className="details-section"> 
            {/* <p><strong>ID Pacient:</strong> {consultation.id_patient}</p>
            <p><strong>ID Doctor:</strong> {consultation.id_doctor}</p> */}
            <p><strong>Data:</strong> {consultation.date}</p>
            <p><strong>Diagnostic:</strong> {consultation.diagnostic}</p>

            {userRole === 'doctor' && (
              <>
                <h3>Diagnostic actualizat</h3>
                <select
                  value={updatedConsultations[index]?.diagnostic || consultation.diagnostic}
                  onChange={(e) => {
                    const updatedConsultationsCopy = [...updatedConsultations];
                    updatedConsultationsCopy[index] = { ...updatedConsultationsCopy[index], diagnostic: e.target.value };
                    setUpdatedConsultations(updatedConsultationsCopy);
                  }}
                >
                  <option value="sanatos">Sanatos</option>
                  <option value="bolnav">Bolnav</option>
                </select>

                <button onClick={() => handleUpdateConsultation(consultation.id_consultation)}>Actualizează Consultația</button>
              </>
            )}
          </div>

          <h2>Detalii Investigație</h2>
          <div className="details-section"> 
            <p><strong>Nume Investigație:</strong> {investigationDetails[index]?.name}</p>
            <p><strong>Data Procesării:</strong> {investigationDetails[index]?.processing_time}</p>
            <p><strong>Rezultat:</strong> {investigationDetails[index]?.result}</p>

            {userRole === 'doctor' && (
              <>
                <h3>Rezultat actualizat</h3>
                <input
                  type="text"
                  value={updatedInvestigations[index]?.result || ''}
                  onChange={(e) => {
                    const updatedInvestigationsCopy = [...updatedInvestigations];
                    updatedInvestigationsCopy[index] = { ...updatedInvestigationsCopy[index], result: e.target.value };
                    setUpdatedInvestigations(updatedInvestigationsCopy);
                  }}
                />
                <button onClick={() => handleUpdateInvestigation(investigationDetails[index]?.id_investigation)}>Actualizează Investigația</button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default ConsultationDetails;
