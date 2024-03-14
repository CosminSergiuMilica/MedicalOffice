import React from 'react';
import './header.css';
import { Link } from 'react-router-dom';

function Header() {
    const isLoggedIn = localStorage.getItem('token') !== null;
    const userRole = localStorage.getItem('userRole');
    return (
        <div class="navbar">
            <div class="container">
                <a class="logo" href="/">
                    <img src="./logo.png" alt="Logo" />
                </a>
                <ul class="menu">
                    {!isLoggedIn && (
                        <>
                            <li><Link className='underline' to="/login">Login</Link></li>
                            <li><Link className='underline' to="/signup">Signup</Link></li>
                        </>
                    )}
                    {isLoggedIn && userRole == 'patient'  && (
                        <>
                            <li><Link className='underline' to="/programari">Programari</Link></li>
                            <li><Link className='underline' to="/logout">LogOut</Link></li>
                            <li><Link className='underline' to="/profile"><img src="./user.png" alt="Logo" height={20} /></Link></li>
                            
                        </>
                    )}
                    {isLoggedIn && userRole=='doctor' && (
                        <>
                            <li><Link className='underline' to="/programari">Programari</Link></li>
                            <li><Link className='underline' to="/logout">LogOut</Link></li>
                            <li><Link className='underline' to="/profile-doctor"><img src="./user.png" alt="Logo" height={20} /></Link></li>
                        </>
                    )}
                    {isLoggedIn && userRole == 'admin' && (
                        <>
                            <li><Link className='underline' to='/admin/create-doctor'>Adauga Medic</Link></li>
                            <li><Link className='underline' to="/admin/all-patients">Patients</Link></li>
                            <li><Link className='underline' to='/admin/all-doctors'>Doctors</Link></li>
                            <li><Link className='underline' to="/programari">Programari</Link></li>
                            <li><Link className='underline' to="/logout">LogOut</Link></li>


                        </>
                    )}
                    
                </ul>
            </div>
        </div>
    );
};

export default Header;
