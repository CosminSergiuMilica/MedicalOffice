import logo from './logo.svg';
import './components/header/header.css'

import { BrowserRouter as Router, Route,Routes } from 'react-router-dom';
import Header from './components/header/header';
import Login from './components/login/login';
import Signup from './components/signup/signup';
import Patient from './components/patient/patient';
import Home from './components/home/home'
import Footer from './components/footer/footer';
import MedicProfile from './components/medic/medic';
import Medici from './components/medici/medici';
import Logout from './components/logout';
import AppointmentsList from './components/programari/programari';
import AppointmentsHistory from './components/medica-history/medical_history';
import CreateDoctorForm from './components/admin-doctor/add_doctor';
import PatientsList from './components/admin-patient/patient-all';
import DoctorList from './components/admin-doctor/doctors-all';
import Doctor from './components/doctor/profile-doctor';
import AppointmentDetails from './components/doctor/appointment-details';
import Appointments from './components/doctor/apointment-doctor';
import ConsultationDetails from './components/doctor/consultation-details';
function App() {
  return (
    <Router>
      <div>
        <Header />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup/>} />
          <Route path="/" element={<Home/>} />
          <Route path="/profile" element={<Patient/>} />
          <Route path="/medic/:id_doctor" element={<MedicProfile />} />
          <Route path='/medici' element={<Medici/>}/>
          <Route path='/logout' element={<Logout/>}/>
          <Route path='/programari' element={<AppointmentsList/>}/>
          <Route path='/medical-history' element={<AppointmentsHistory/>}/>
          <Route path='/admin/create-doctor' element={<CreateDoctorForm/>}/>
          <Route path='/admin/all-patients' element={<PatientsList/>}/>
          <Route path='/admin/all-doctors' element={<DoctorList/>}/>
          <Route path='/profile-doctor' element={<Doctor />}/>
          <Route path='/programari/:id_appointment' element={<AppointmentDetails />}/>
          <Route path='/doctor/programari/:id_doctor' element={<Appointments/>}/>
          <Route path="/programari/consultation/:id_consultation" element={<ConsultationDetails/>} />

        </Routes>
        <Footer/>
      </div>
    </Router>
  );
}

export default App;
