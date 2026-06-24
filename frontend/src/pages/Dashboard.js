import React, { useState, useEffect } from 'react';
import { casesAPI } from '../api';

export default function Dashboard() {
  const [cases, setCases] = useState([]);
  const [showNewCase, setShowNewCase] = useState(false);
  const [formData, setFormData] = useState({
    case_number: '',
    title: '',
    description: '',
    officer_name: 'Aditi',
    officer_badge: 'CID-001',
    department: 'Cyber Crime Division'
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    try {
      const res = await casesAPI.getAll();
      setCases(res.data);
    } catch (err) {
      console.error('Error fetching cases:', err);
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCreateCase = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await casesAPI.create(formData);
      setFormData({
        case_number: '',
        title: '',
        description: '',
        officer_name: 'Aditi',
        officer_badge: 'CID-001',
        department: 'Cyber Crime Division'
      });
      setShowNewCase(false);
      fetchCases();
    } catch (err) {
      console.error('Error creating case:', err);
    }
    setLoading(false);
  };

  return (
    <div style={{maxWidth:'1280px', margin:'0 auto', padding:'32px 16px'}}>
      <div style={{marginBottom:'32px', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h1 style={{fontSize:'36px', fontWeight:'bold', margin:0}}>Investigation Cases</h1>
        <button onClick={() => setShowNewCase(!showNewCase)} className="btn-primary">
          {showNewCase ? 'Cancel' : '+ New Case'}
        </button>
      </div>

      {showNewCase && (
        <div className="card" style={{marginBottom:'32px'}}>
          <h2 style={{fontSize:'20px', fontWeight:'bold', marginBottom:'16px'}}>Create New Investigation Case</h2>
          <form onSubmit={handleCreateCase} style={{display:'flex', flexDirection:'column', gap:'12px'}}>
            <input type="text" name="case_number" placeholder="Case Number (e.g., CASE-2024-001)" value={formData.case_number} onChange={handleInputChange} required />
            <input type="text" name="title" placeholder="Case Title" value={formData.title} onChange={handleInputChange} required />
            <textarea name="description" placeholder="Case Description" value={formData.description} onChange={handleInputChange} rows="3" />
            <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'12px'}}>
              <input type="text" name="officer_name" placeholder="Officer Name" value={formData.officer_name} onChange={handleInputChange} />
              <input type="text" name="officer_badge" placeholder="Badge Number" value={formData.officer_badge} onChange={handleInputChange} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Creating...' : 'Create Case'}
            </button>
          </form>
        </div>
      )}

      {cases.length === 0 ? (
        <div className="card" style={{textAlign:'center', padding:'48px'}}>
          <p style={{color:'#9ca3af'}}>No cases yet. Create your first investigation.</p>
        </div>
      ) : (
        <div className="grid-3">
          {cases.map(caseItem => (
            <div
              key={caseItem.id}
              onClick={() => window.location.href = `/case/${caseItem.id}`}
              className="card"
              style={{cursor:'pointer'}}
            >
              <h3 style={{color:'#60a5fa', marginBottom:'8px', fontWeight:'bold'}}>{caseItem.case_number}</h3>
              <p style={{fontWeight:'600', marginBottom:'8px'}}>{caseItem.title}</p>
              <p style={{fontSize:'14px', color:'#9ca3af', marginBottom:'12px'}}>{caseItem.description}</p>
              <div style={{display:'flex', justifyContent:'space-between', fontSize:'12px'}}>
                <span className={caseItem.status === 'open' ? 'badge-open' : 'badge-closed'}>{caseItem.status}</span>
                <span style={{color:'#6b7280'}}>{new Date(caseItem.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
