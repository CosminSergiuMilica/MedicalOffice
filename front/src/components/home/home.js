import React, { useState, useEffect } from 'react';
import './home.css';
import { Link } from 'react-router-dom';
function Home() {
 return (
    <div >
      <div className="text">
        <h1 className="main-header">Welcome to CodeHealth</h1>
        <p className="description">Oferim servicii medicale de înaltă calitate pentru sănătatea dumneavoastră.</p>
        {/* <img src="homee.jpg" alt="homeimg" width={1458}/> */}
        <h1 className='second-header'>Descoperiți Calitatea Înaltă a Serviciilor Noastre de Sănătate</h1>

        <div className="categories">
          <Link to="/medici?specialization=pediatru" className="category-link">
            <img src="./pediatru.jpg" alt="Pediatru" height={256} width={160}/>
            <span>Pediatrie</span>
          </Link>

          <Link to="/medici?specialization=chirurg" className="category-link">
            <img src="./chirurg.jpg" alt="Nutritie" height={256} width={160} />
            <span>Chirurgie</span>
          </Link>
          <Link to="/medici?specialization=nutritionist" className="category-link">
            <img src="./nutritionist.jpg" alt="Nutritie" height={256} width={160} />
            <span>Nutritie</span>
          </Link>
          <Link to="/medici?specialization=oftalmolog" className="category-link">
            <img src="./oftalmolog.jpg" alt="oftalmolog" height={256} width={160} />
            <span>Oftalmologie</span>
          </Link>
          <Link to="/medici?specialization=dentist" className="category-link">
            <img src="./dent.jpg" alt="dentist" height={256} width={160} />
            <span>Stomatologie</span>
          </Link>
          <Link to="/medici?specialization=ortoped" className="category-link">
            <img src="./ortoped.jpg" alt="ortoped" height={256} width={160} />
            <span>Ortopedie</span>
          </Link>
          <Link to="/medici" className="category-link">
            <img src="./all.png" alt="allmed" height={256} width={160} />
            <span>Toti Medicii</span>
          </Link>
          {/* Adaugă link-uri pentru celelalte categorii de medici aici */}
        </div>
      </div>
    </div>
  );
}

export default Home;