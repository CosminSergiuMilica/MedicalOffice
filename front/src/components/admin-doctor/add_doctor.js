import React, { useState } from 'react';
import axios from 'axios';
import './admin.css';

const CreateDoctorForm = () => {
  const [formData, setFormData] = useState({
   username:'',
   password:'' ,
    last_name: '',
    first_name: '',
    email: '',
    phone: '',
    specialization: '',
  });
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const requiredFields = ['username', 'password', 'last_name', 'first_name', 'email', 'phone', 'specialization'];
    const isFormValid = requiredFields.every(field => formData[field]);

    if (!isFormValid) {
      setError('Please fill in all fields.');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post('http://localhost:8000/api/medical_office/doctors/', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      console.log('Doctor created:', response.data);
    } catch (error) {
      //console.error('Error creating doctor:', error);
      setError(error.response ? error.response.data.message : 'An unknown error occurred.');
    }
  };

  return (
    <div className="create-doctor-form">
      <h2>Create Doctor</h2>
      
      <form onSubmit={handleSubmit}>
        <label>
          Username:
          <input type="text" name="username" value={formData.username} onChange={handleChange} />
        </label>
        <label>
          password:
          <input type="password" name="password" value={formData.password} onChange={handleChange} />
        </label>
        <label>
          Last Name:
          <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} />
        </label>
   
        <label>
          First Name:
          <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} />
        </label>

        <label>
          Email:
          <input type="email" name="email" value={formData.email} onChange={handleChange} />
        </label>

        <label>
          Phone:
          <input type="text" name="phone" value={formData.phone} onChange={handleChange} />
        </label>

        <label>
          Specialization:
          <select name="specialization" value={formData.specialization} onChange={handleChange}>
            <option value="">Selectează o specializare</option>
            <option value="chirurg">Chirurg</option>
            <option value="dentist">Dentist</option>
            <option value="pediatru">Pediatru</option>
            <option value="nutritionist">Nutritionist</option>
            <option value="oftalmolog">Oftalmolog</option>
            <option value="ortoped">Ortoped</option>
          </select>
        </label>

        <button type="submit">Create Doctor</button>
      </form>
      {error && (
        <p className="server-error">{error}</p>
      )}
    </div>
  );
};

export default CreateDoctorForm;
