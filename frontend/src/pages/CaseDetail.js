import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { casesAPI, evidenceAPI, graphAPI, timelineAPI, aiAPI, notebookAPI } from '../api';

export default function CaseDetail() {
  const { caseId } = useParams();
  const [activeTab, setActiveTab] = useState('overview');
  const [caseData, setCaseData] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [entities, setEntities] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [leads, setLeads] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState({ title: '', content: '', entry_type: 'NOTE' });
  const [savingNote, setSavingNote] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('success');

  useEffect(() => { fetchCaseData(); }, [caseId]);

  const fetchCaseData = async () => {
    try {
      const caseRes = await casesAPI.get(caseId);
      setCaseData(caseRes.data);
      const evidenceRes = await evidenceAPI.getByCase(caseId);
      setEvidence(evidenceRes.data);
    } catch (err) { console.error('Error fetching case:', err); }
  };

  const showMessage = (msg, type = 'success') => {
    setMessage(msg); setMessageType(type);
    setTimeout(() => setMessage(''), 4000);
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('case_id', caseId);
    formData.append('file', selectedFile);
    formData.append('uploaded_by', 'Investigator');
    formData.append('source_description', 'Evidence file');
    try {
      await evidenceAPI.upload(caseId, formData);
      showMessage('Evidence uploaded successfully');
      setSelectedFile(null);
      fetchCaseData();
    } catch (err) {
      showMessage('Upload failed: ' + (err.response?.data?.detail || err.message), 'error');
    }
    setUploading(false);
  };

  const handleParseEvidence = async (evidenceId) => {
    setLoading(true);
    try {
      await evidenceAPI.parse(evidenceId);
      showMessage('Evidence parsed successfully');
      fetchCaseData();
      await loadGraphData();
    } catch (err) {
      showMessage('Parse failed: ' + (err.response?.data?.detail || err.message), 'error');
    }
    setLoading(false);
  };

  const handleDeleteEvidence = async (evidenceId, filename) => {
    if (!window.confirm(`Delete "${filename}"? This cannot be undone.`)) return;
    try {
      await evidenceAPI.delete(evidenceId);
      showMessage('Evidence deleted');
      fetchCaseData();
    } catch (err) {
      showMessage('Delete failed: ' + (err.response?.data?.detail || err.message), 'error');
    }
  };

  const loadGraphData = async () => {
    try {
      const entitiesRes = await graphAPI.getEntities(caseId);
      setEntities(entitiesRes.data);
      const relsRes = await graphAPI.getRelationships(caseId);
      setRelationships(relsRes.data);
    } catch (err) { console.error('Error loading graph:', err); }
  };

  const handleCorrelate = async () => {
    setLoading(true);
    try {
      await graphAPI.correlate(caseId);
      showMessage('Correlation complete');
      await loadGraphData();
    } catch (err) { showMessage('Correlation failed', 'error'); }
    setLoading(false);
  };

  const handleGetLeads = async () => {
    setLoading(true);
    try {
      const res = await aiAPI.getLeads(caseId);
      setLeads(res.data.leads || []);
      showMessage(`${res.data.leads?.length || 0} leads generated`);
    } catch (err) { showMessage('Failed to generate leads', 'error'); }
    setLoading(false);
  };

  const handleGetTimeline = async () => {
    setLoading(true);
    try {
      const res = await timelineAPI.getFullTimeline(caseId);
      setTimeline(res.data || []);
      const patternsRes = await timelineAPI.getPatterns(caseId);
      setPatterns(patternsRes.data || []);
      showMessage(`${res.data?.length || 0} events loaded`);
    } catch (err) { showMessage('Failed to load timeline', 'error'); }
    setLoading(false);
  };

  const handleLoadNotes = async () => {
    try {
      const res = await notebookAPI.getAll(caseId);
      setNotes(res.data || []);
    } catch (err) { showMessage('Failed to load notes', 'error'); }
  };

  const handleSaveNote = async (e) => {
    e.preventDefault();
    if (!newNote.title) return;
    setSavingNote(true);
    try {
      await notebookAPI.create(caseId, { ...newNote, created_by: 'Investigator' });
      showMessage('Note saved');
      setNewNote({ title: '', content: '', entry_type: 'NOTE' });
      handleLoadNotes();
    } catch (err) { showMessage('Failed to save note', 'error'); }
    setSavingNote(false);
  };

  const handleDeleteNote = async (entryId) => {
    if (!window.confirm('Delete this note?')) return;
    try {
      await notebookAPI.delete(caseId, entryId);
      showMessage('Note deleted');
      handleLoadNotes();
    } catch (err) { showMessage('Failed to delete note', 'error'); }
  };

  const handlePinNote = async (entryId, pin) => {
    try {
      if (pin) {
        await notebookAPI.pin(caseId, entryId);
      } else {
        await fetch(`http://127.0.0.1:8000/notebook/${caseId}/entry/${entryId}/unpin`, { method: 'POST' });
      }
      handleLoadNotes();
    } catch (err) { showMessage('Failed to update note', 'error'); }
  };

  const typeColors = {
    'PHONE_CALL': '#3b82f6',
    'SMS': '#06b6d4',
    'GPS_MOVEMENT': '#22c55e',
    'INTERNET_SESSION': '#8b5cf6',
    'WEBSITE_VISIT': '#8b5cf6',
    'FINANCIAL_TRANSACTION': '#f59e0b',
    'WHATSAPP_MESSAGE': '#25D366',
    'WHATSAPP_CALL': '#25D366',
    'BLUETOOTH_PAIRING': '#ec4899',
    'IOT_ACTIVITY': '#f97316',
  };

  const tabs = ['overview', 'evidence', 'entities', 'relationships', 'leads', 'timeline', 'notebook'];

  if (!caseData) return (
    <div style={{ textAlign: 'center', padding: '48px', color: '#9ca3af' }}>Loading case...</div>
  );

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '32px 16px' }}>

      {message && (
        <div style={{
          background: messageType === 'error' ? '#450a0a' : '#052e16',
          border: `1px solid ${messageType === 'error' ? '#ef4444' : '#22c55e'}`,
          borderRadius: '6px', padding: '12px 16px', marginBottom: '16px',
          color: messageType === 'error' ? '#fca5a5' : '#86efac'
        }}>{message}</div>
      )}

      <div style={{ marginBottom: '24px' }}>
        <a href="/" style={{ color: '#9ca3af', fontSize: '14px' }}>← Back to Cases</a>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', margin: '8px 0 4px' }}>{caseData.case_number}</h1>
        <p style={{ color: '#9ca3af', margin: 0 }}>{caseData.title}</p>
      </div>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '24px', borderBottom: '1px solid #262d38', overflowX: 'auto' }}>
        {tabs.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: '10px 16px', background: 'none', border: 'none', cursor: 'pointer',
            fontWeight: '600', fontSize: '14px',
            color: activeTab === tab ? '#3b82f6' : '#9ca3af',
            borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
            whiteSpace: 'nowrap'
          }}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
        <button onClick={() => window.location.href = `/case/${caseId}/map`} style={{
          padding: '10px 16px', background: 'none', border: 'none', cursor: 'pointer',
          fontWeight: '600', fontSize: '14px', color: '#22c55e',
          borderBottom: '2px solid transparent', whiteSpace: 'nowrap'
        }}>🗺 Map</button>
      </div>

      {/* OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="card">
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '20px' }}>Case Overview</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {[['Case Number', caseData.case_number], ['Status', caseData.status],
              ['Officer', caseData.officer_name], ['Badge', caseData.officer_badge],
              ['Department', caseData.department], ['Created', new Date(caseData.created_at).toLocaleString()]
            ].map(([label, value]) => (
              <div key={label}>
                <p style={{ color: '#9ca3af', fontSize: '12px', margin: '0 0 4px' }}>{label}</p>
                <p style={{ fontWeight: '600', margin: 0 }}>{value}</p>
              </div>
            ))}
          </div>
          {caseData.description && (
            <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid #262d38' }}>
              <p style={{ color: '#9ca3af', fontSize: '12px', margin: '0 0 8px' }}>Description</p>
              <p style={{ margin: 0 }}>{caseData.description}</p>
            </div>
          )}
        </div>
      )}

      {/* EVIDENCE */}
      {activeTab === 'evidence' && (
        <div>
          <div className="card" style={{ marginBottom: '20px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Upload Evidence</h2>
            <form onSubmit={handleFileUpload} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <input type="file" onChange={(e) => setSelectedFile(e.target.files[0])} style={{ flex: 1 }} />
              <button type="submit" disabled={uploading || !selectedFile} className="btn-primary" style={{ whiteSpace: 'nowrap' }}>
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </form>
          </div>
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>Evidence Files ({evidence.length})</h2>
          {evidence.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '32px', color: '#9ca3af' }}>No evidence uploaded yet.</div>
          ) : evidence.map(e => (
            <div key={e.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{ fontWeight: '600', margin: '0 0 4px' }}>{e.original_filename}</p>
                <p style={{ fontSize: '13px', color: '#9ca3af', margin: '0 0 2px' }}>{e.evidence_type} • {(e.file_size_bytes / 1024).toFixed(1)} KB</p>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>{new Date(e.uploaded_at).toLocaleString()} • by {e.uploaded_by}</p>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ padding: '4px 10px', borderRadius: '4px', fontSize: '12px', background: e.status === 'parsed' ? '#14532d' : '#1e3a5f', color: e.status === 'parsed' ? '#86efac' : '#93c5fd' }}>
                  {e.status}
                </span>
                {e.status !== 'parsed' && (
                  <button onClick={() => handleParseEvidence(e.id)} disabled={loading} className="btn-primary" style={{ padding: '6px 14px', fontSize: '13px' }}>
                    {loading ? '...' : 'Parse'}
                  </button>
                )}
                <button onClick={() => handleDeleteEvidence(e.id, e.original_filename)} style={{ padding: '6px 14px', fontSize: '13px', background: '#7f1d1d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ENTITIES */}
      {activeTab === 'entities' && (
        <div>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
            <button onClick={loadGraphData} disabled={loading} className="btn-primary">Load Entities</button>
            <button onClick={handleCorrelate} disabled={loading} className="btn-primary" style={{ background: '#7c3aed' }}>
              {loading ? 'Running...' : 'Run Correlation'}
            </button>
          </div>
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>Entities ({entities.length})</h2>
          {entities.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '32px', color: '#9ca3af' }}>Click Load Entities after parsing evidence.</div>
          ) : entities.map((e, i) => (
            <div key={i} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <p style={{ fontWeight: '600', margin: '0 0 4px' }}>{e.value}</p>
                <span style={{ fontSize: '12px', background: '#1e3a5f', color: '#93c5fd', padding: '2px 8px', borderRadius: '4px' }}>{e.type}</span>
              </div>
              <p style={{ fontSize: '13px', color: '#9ca3af', margin: '4px 0' }}>Activity count: {e.activity_count}</p>
              {e.locations?.length > 0 && <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>Locations: {e.locations.join(', ')}</p>}
            </div>
          ))}
        </div>
      )}

      {/* RELATIONSHIPS */}
      {activeTab === 'relationships' && (
        <div>
          <button onClick={handleCorrelate} disabled={loading} className="btn-primary" style={{ background: '#7c3aed', marginBottom: '20px' }}>
            {loading ? 'Running...' : 'Run Correlation'}
          </button>
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>Relationships ({relationships.length})</h2>
          {relationships.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '32px', color: '#9ca3af' }}>Click Run Correlation to find connections.</div>
          ) : relationships.map((r, i) => (
            <div key={i} className="card" style={{ borderLeft: `4px solid ${r.weight >= 10 ? '#ef4444' : r.weight >= 5 ? '#f97316' : '#7c3aed'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <p style={{ fontWeight: '600', margin: 0 }}>{r.source} ↔ {r.target}</p>
                <span style={{ fontSize: '12px', background: '#1a2332', padding: '2px 8px', borderRadius: '4px', color: r.weight >= 10 ? '#ef4444' : r.weight >= 5 ? '#f97316' : '#a78bfa' }}>
                  strength: {r.weight}
                </span>
              </div>
              <p style={{ fontSize: '13px', color: '#a78bfa', margin: '0 0 4px' }}>{r.type}</p>
              {r.evidence?.length > 0 && <p style={{ fontSize: '11px', color: '#6b7280', margin: 0 }}>Evidence refs: {r.evidence.slice(0, 2).join(', ')}</p>}
            </div>
          ))}
        </div>
      )}

      {/* LEADS */}
      {activeTab === 'leads' && (
        <div>
          <button onClick={handleGetLeads} disabled={loading} className="btn-primary" style={{ marginBottom: '20px', background: '#dc2626' }}>
            {loading ? 'Analyzing...' : '🔍 Generate AI Leads'}
          </button>
          {leads.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '32px', color: '#9ca3af' }}>Click Generate AI Leads to analyze the case.</div>
          ) : leads.map((lead, i) => (
            <div key={i} className="card" style={{ borderLeft: '4px solid #dc2626', marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', background: '#450a0a', color: '#fca5a5', padding: '2px 8px', borderRadius: '4px' }}>{lead.lead_type}</span>
                <span style={{ fontSize: '13px', fontWeight: '600', color: lead.confidence > 0.8 ? '#ef4444' : lead.confidence > 0.6 ? '#f97316' : '#eab308' }}>
                  {(lead.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <p style={{ fontWeight: '600', margin: '0 0 6px' }}>{lead.title}</p>
              <p style={{ fontSize: '13px', color: '#9ca3af', margin: '0 0 8px' }}>{lead.description}</p>
              <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>➤ {lead.recommended_action}</p>
            </div>
          ))}
        </div>
      )}

      {/* TIMELINE */}
      {activeTab === 'timeline' && (
        <div>
          <button onClick={handleGetTimeline} disabled={loading} className="btn-primary" style={{ marginBottom: '20px', background: '#059669' }}>
            {loading ? 'Loading...' : '📅 Load Timeline'}
          </button>

          {patterns.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '12px', color: '#f97316' }}>
                ⚠ Suspicious Patterns Detected ({patterns.length})
              </h3>
              {patterns.map((p, i) => (
                <div key={i} className="card" style={{
                  borderLeft: `4px solid ${p.severity >= 9 ? '#ef4444' : p.severity >= 7 ? '#f97316' : '#eab308'}`,
                  marginBottom: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{
                      fontSize: '11px', padding: '2px 8px', borderRadius: '4px',
                      background: p.severity >= 9 ? '#450a0a' : p.severity >= 7 ? '#431407' : '#422006',
                      color: p.severity >= 9 ? '#fca5a5' : p.severity >= 7 ? '#fed7aa' : '#fef08a'
                    }}>{p.pattern_type}</span>
                    <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                      Severity: {p.severity}/10 • {p.event_count} events
                    </span>
                  </div>
                  <p style={{ fontWeight: '600', margin: '0 0 6px', fontSize: '14px' }}>{p.description}</p>
                  <p style={{ fontSize: '12px', color: '#60a5fa', margin: '0 0 4px' }}>💡 {p.what_this_means}</p>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>➤ {p.recommended_action}</p>
                </div>
              ))}
            </div>
          )}

          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>Chronological Events ({timeline.length})</h2>
          {timeline.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '32px', color: '#9ca3af' }}>Click Load Timeline to view all events.</div>
          ) : (
            <div style={{ position: 'relative', paddingLeft: '24px', borderLeft: '2px solid #262d38' }}>
              {timeline.map((event, i) => {
                const isLateNight = event.time_flag === 'LATE_NIGHT';
                const color = typeColors[event.event_type] || '#6b7280';
                return (
                  <div key={i} style={{ position: 'relative', marginBottom: '12px' }}>
                    <div style={{
                      position: 'absolute', left: '-30px', top: '12px',
                      width: '12px', height: '12px', borderRadius: '50%',
                      background: color, border: '2px solid #0f1419'
                    }} />
                    <div style={{
                      background: isLateNight ? '#1a0a0a' : '#1a2332',
                      border: `1px solid ${isLateNight ? '#7f1d1d' : '#262d38'}`,
                      borderRadius: '8px', padding: '12px 16px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                          <span style={{
                            fontSize: '11px', padding: '2px 8px', borderRadius: '4px',
                            background: color + '33', color: color, border: `1px solid ${color}55`
                          }}>{event.event_type}</span>
                          {isLateNight && (
                            <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: '#450a0a', color: '#fca5a5' }}>
                              🌙 LATE NIGHT
                            </span>
                          )}
                        </div>
                        <span style={{ fontSize: '11px', color: '#6b7280', whiteSpace: 'nowrap', marginLeft: '8px' }}>{event.timestamp}</span>
                      </div>
                      <p style={{ fontWeight: '600', margin: '0 0 4px', fontSize: '13px' }}>{event.summary}</p>
                      {event.location && (
                        <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                          📍 {event.location}{event.duration_seconds > 0 ? ` • ${event.duration_seconds}s` : ''}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* NOTEBOOK */}
      {activeTab === 'notebook' && (
        <div>
          <div className="card" style={{ marginBottom: '20px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Add Investigation Note</h2>
            <form onSubmit={handleSaveNote} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <input type="text" placeholder="Title" value={newNote.title} onChange={e => setNewNote({ ...newNote, title: e.target.value })} required />
                <select value={newNote.entry_type} onChange={e => setNewNote({ ...newNote, entry_type: e.target.value })}
                  style={{ background: '#08090c', border: '1px solid #262d38', borderRadius: '6px', padding: '10px 12px', color: 'white' }}>
                  <option value="NOTE">NOTE</option>
                  <option value="HYPOTHESIS">HYPOTHESIS</option>
                  <option value="OBSERVATION">OBSERVATION</option>
                  <option value="LEAD">LEAD</option>
                  <option value="SUSPECT_PROFILE">SUSPECT PROFILE</option>
                </select>
              </div>
              <textarea placeholder="Write your investigation note, hypothesis or observation..." value={newNote.content} onChange={e => setNewNote({ ...newNote, content: e.target.value })} rows="4" />
              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="submit" disabled={savingNote} className="btn-primary">{savingNote ? 'Saving...' : 'Save Note'}</button>
                <button type="button" onClick={handleLoadNotes} className="btn-primary" style={{ background: '#374151' }}>Load Notes</button>
              </div>
            </form>
          </div>

          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px' }}>Investigation Notes ({notes.length})</h2>
          {notes.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '32px', color: '#9ca3af' }}>No notes yet. Add your first investigation note above.</div>
          ) : notes.map((note, i) => (
            <div key={i} className="card" style={{ borderLeft: `4px solid ${note.is_pinned ? '#f59e0b' : '#374151'}`, marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {note.is_pinned && <span>📌</span>}
                  <p style={{ fontWeight: '600', margin: 0 }}>{note.title}</p>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: '#1e3a5f', color: '#93c5fd' }}>{note.entry_type}</span>
                  <button onClick={() => handlePinNote(note.id, !note.is_pinned)}
                    style={{ padding: '2px 8px', fontSize: '11px', borderRadius: '4px', background: note.is_pinned ? '#78350f' : '#374151', color: 'white', border: 'none', cursor: 'pointer' }}>
                    {note.is_pinned ? 'Unpin' : 'Pin'}
                  </button>
                  <button onClick={() => handleDeleteNote(note.id)}
                    style={{ padding: '2px 8px', fontSize: '11px', borderRadius: '4px', background: '#7f1d1d', color: 'white', border: 'none', cursor: 'pointer' }}>
                    Delete
                  </button>
                </div>
              </div>
              {note.content && <p style={{ fontSize: '13px', color: '#9ca3af', margin: '0 0 8px', lineHeight: '1.6' }}>{note.content}</p>}
              <p style={{ fontSize: '11px', color: '#6b7280', margin: 0 }}>{new Date(note.created_at).toLocaleString()} • by {note.created_by}</p>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}