import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './patients.css';

const PatientsList = () => {
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('http://localhost:8000/api/medical_office/patients', {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setPatients(response.data.patients);
      } catch (error) {
        console.error('Error fetching patients:', error);
      }
    };

    fetchPatients();
  }, []);

  const togglePatientStatus = async (id) => {
    try {
      const token = localStorage.getItem('token');
      const patientToUpdate = patients.find(patient => patient.id_user === id);
      const updatedPatient = { ...patientToUpdate, is_active: !patientToUpdate.is_active };

      const response = await axios.patch(`http://localhost:8000/api/medical_office/patients/${id}`, updatedPatient, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setPatients(patients.map(patient => {
        if (patient.id_user === id) {
          return updatedPatient;
        }
        return patient;
      }));
    } catch (error) {
      console.error('Error toggling patient status:', error);
    }
  };

  return (
    <div className="patients-list-container">
      <h2>Lista de Pacienți</h2>
      <ul className="patients-list">
        {patients.map(patient => (
          <li key={patient.id_user}>
            <div className="patient-info">
              <p>Nume: {patient.first_name} {patient.last_name}</p>
              <p>Email: {patient.email}</p>
              <p>Telefon: {patient.phone}</p>
              <p>Data nasterii: {patient.birth_date}</p>
              <p>Stare activa: {patient.is_active ? 'Da' : 'Nu'}</p>
            </div>
            <button onClick={() => togglePatientStatus(patient.id_user)}>
              {patient.is_active ? 'Dezactivează' : 'Activează'}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PatientsList;
