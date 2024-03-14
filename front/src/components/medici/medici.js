import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import './medici.css';

const Medici = () => {
  const [medici, setMedici] = useState([]);
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const specialization = query.get('specialization') ;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const url = specialization
          ? `http://localhost:8000/api/medical_office/doctors?specialization=${specialization}`
          : 'http://localhost:8000/api/medical_office/doctors';

        const response = await axios.get(url, {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem('token')}`
                    }
                });
        setMedici(response.data.doctors);
      } catch (error) {
        console.error('Error fetching doctors:', error);
      }
    };

    fetchData();
  }, [specialization]);

  return (
    <div className="medici-list-container">
      <h2>Lista medici</h2>
      <ul className="medici-list">
        {Array.isArray(medici) && medici.map((medic) => (
          <li key={medic.id_doctor} className="medic-item">
            <Link to={`/medic/${medic.id_user}`} className="medic-link">
              <p className="medic-name">
                {medic.first_name} {medic.last_name}
              </p>
              <p>
                Specialezare: {medic.specialization}
              </p>
              
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Medici;
