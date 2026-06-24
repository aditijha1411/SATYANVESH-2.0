import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import CaseDetail from './pages/CaseDetail';
import MapView from './pages/MapView';
import './App.css';

function App() {
  return (
    <Router>
      <div className="bg-dark min-h-screen">
        <nav style={{
          background:'#08090c', borderBottom:'1px solid #262d38',
          position:'sticky', top:0, zIndex:50, padding:'0 24px'
        }}>
          <div style={{
            maxWidth:'1280px', margin:'0 auto',
            display:'flex', justifyContent:'space-between',
            alignItems:'center', height:'64px'
          }}>
            <Link to="/" style={{display:'flex', alignItems:'center', gap:'8px', textDecoration:'none'}}>
              <span style={{fontSize:'22px', fontWeight:'bold', color:'#3b82f6'}}>SATYANVESH</span>
              <span style={{fontSize:'12px', color:'#6b7280'}}>v2.0</span>
            </Link>
            <div style={{display:'flex', gap:'20px', fontSize:'14px'}}>
              <Link to="/" style={{color:'#9ca3af', textDecoration:'none'}}>Dashboard</Link>
            </div>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/case/:caseId" element={<CaseDetail />} />
          <Route path="/case/:caseId/map" element={<MapView />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;