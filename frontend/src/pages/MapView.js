import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, Circle } from 'react-leaflet';
import L from 'leaflet';
import { graphAPI } from '../api';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const COLORS = ['#ef4444','#3b82f6','#22c55e','#f97316','#a855f7','#06b6d4','#eab308','#ec4899'];

const KNOWN_LOCATIONS = {
  'Hyderabad Ameerpet': [17.3850, 78.4867],
  'Hyderabad Ameerpet ZINKIT Hub': [17.3850, 78.4867],
  'Hyderabad Banjara Hills': [17.4156, 78.4483],
  'Hyderabad Jubilee Hills': [17.4239, 78.4738],
  'Hyderabad Old City': [17.3616, 78.4747],
  'Bangalore Majestic': [12.9716, 77.5946],
  'Bangalore Majestic ZINKIT Hub': [12.9716, 77.5946],
  'Bangalore RT Nagar': [13.0120, 77.5765],
  'Bangalore Koramangala': [12.9352, 77.6245],
  'Bangalore Whitefield': [12.9698, 77.7499],
  'Bangalore Indiranagar': [12.9719, 77.6412],
  'Bangalore Hebbal': [13.0450, 77.5920],
};

function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export default function MapView() {
  const { caseId } = useParams();
  const [events, setEvents] = useState([]);
  const [entities, setEntities] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState('all');
  const [showRoute, setShowRoute] = useState(true);
  const [showProximity, setShowProximity] = useState(true);
  const [proximityRadius, setProximityRadius] = useState(200);
  const [loading, setLoading] = useState(false);
  const [proximityAlerts, setProximityAlerts] = useState([]);

  useEffect(() => { loadMapData(); }, [caseId]);

  const loadMapData = async () => {
    setLoading(true);
    try {
      const eventsRes = await graphAPI.getEvents(caseId);
      const allEvents = eventsRes.data || [];
      setEvents(allEvents);
      const entitiesRes = await graphAPI.getEntities(caseId);
      setEntities(entitiesRes.data || []);
      detectProximity(allEvents, proximityRadius);
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  const detectProximity = (allEvents, radius) => {
    const gpsEvents = allEvents.filter(e => e.type === 'GPS_MOVEMENT');
    const alerts = [];
    for (let i = 0; i < gpsEvents.length; i++) {
      for (let j = i + 1; j < gpsEvents.length; j++) {
        const e1 = gpsEvents[i];
        const e2 = gpsEvents[j];
        if (e1.source === e2.source) continue;
        const c1 = parseCoord(e1.target);
        const c2 = parseCoord(e2.target);
        if (!c1 || !c2) continue;
        const dist = haversineDistance(c1[0], c1[1], c2[0], c2[1]);
        if (dist <= radius) {
          const timeDiff = Math.abs(
            new Date(e1.timestamp).getTime() - new Date(e2.timestamp).getTime()
          ) / (1000 * 60 * 60);
          if (timeDiff <= 2) {
            alerts.push({
              entity1: e1.source,
              entity2: e2.source,
              distance: Math.round(dist),
              location1: e1.location,
              time1: e1.timestamp,
              time2: e2.timestamp,
              coord: c1
            });
          }
        }
      }
    }
    setProximityAlerts(alerts);
  };

  const parseCoord = (str) => {
    if (!str) return null;
    const parts = str.split(',');
    if (parts.length === 2) {
      const lat = parseFloat(parts[0]);
      const lng = parseFloat(parts[1]);
      if (!isNaN(lat) && !isNaN(lng)) return [lat, lng];
    }
    return null;
  };

  const getColor = (entityValue) => {
    const phone = entities.filter(e => e.type === 'phone_number');
    const idx = phone.findIndex(e => e.value === entityValue);
    return COLORS[idx % COLORS.length] || '#ffffff';
  };

  const gpsEvents = events.filter(e =>
    e.type === 'GPS_MOVEMENT' &&
    (selectedEntity === 'all' || e.source === selectedEntity)
  );

  const cellEvents = events.filter(e =>
    ['PHONE_CALL','SMS','WHATSAPP_MESSAGE','WHATSAPP_CALL','INTERNET_SESSION'].includes(e.type) &&
    e.location && e.location.trim() !== '' &&
    (selectedEntity === 'all' || e.source === selectedEntity || e.target === selectedEntity)
  );

  const routePoints = [...gpsEvents]
    .sort((a, b) => (a.timestamp || '').localeCompare(b.timestamp || ''))
    .map(e => parseCoord(e.target))
    .filter(Boolean);

  const locationGroups = {};
  cellEvents.forEach(e => {
    const loc = e.location.trim();
    if (!locationGroups[loc]) locationGroups[loc] = { count: 0, types: new Set(), entities: new Set() };
    locationGroups[loc].count++;
    locationGroups[loc].types.add(e.type);
    if (e.source) locationGroups[loc].entities.add(e.source);
  });

  const phoneEntities = entities.filter(e => e.type === 'phone_number');
  const mapCenter = gpsEvents.length > 0
    ? parseCoord(gpsEvents[0].target) || [20.5937, 78.9629]
    : [20.5937, 78.9629];

  return (
    <div style={{ minHeight: '100vh', background: '#0f1419' }}>

      {/* HEADER */}
      <div style={{ padding: '12px 16px', background: '#1a2332', borderBottom: '1px solid #262d38' }}>
        <a href={`/case/${caseId}`} style={{ color: '#9ca3af', fontSize: '13px' }}>← Back to Case</a>
        <h2 style={{ margin: '4px 0 12px', fontSize: '18px', fontWeight: 'bold' }}>🗺 Geospatial Intelligence Map</h2>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <select value={selectedEntity} onChange={e => setSelectedEntity(e.target.value)}
            style={{ background: '#0f1419', color: 'white', border: '1px solid #262d38', borderRadius: '6px', padding: '6px 12px', fontSize: '13px' }}>
            <option value="all">All Entities</option>
            {phoneEntities.map(e => <option key={e.value} value={e.value}>{e.value}</option>)}
          </select>

          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
            <input type="checkbox" checked={showRoute} onChange={e => setShowRoute(e.target.checked)} />
            Show Route
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
            <input type="checkbox" checked={showProximity} onChange={e => setShowProximity(e.target.checked)} />
            Proximity Zones
          </label>

          <select value={proximityRadius} onChange={e => {
            const r = Number(e.target.value);
            setProximityRadius(r);
            detectProximity(events, r);
          }} style={{ background: '#0f1419', color: 'white', border: '1px solid #262d38', borderRadius: '6px', padding: '6px 12px', fontSize: '13px' }}>
            <option value={80}>80m radius</option>
            <option value={200}>200m radius</option>
            <option value={500}>500m radius</option>
          </select>

          <button onClick={loadMapData} disabled={loading} className="btn-primary" style={{ padding: '6px 16px', fontSize: '13px' }}>
            {loading ? 'Loading...' : '🔄 Refresh'}
          </button>

          <div style={{ marginLeft: 'auto', fontSize: '12px', color: '#9ca3af' }}>
            {gpsEvents.length} GPS • {Object.keys(locationGroups).length} towers • {proximityAlerts.length} proximity alerts
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginTop: '10px', flexWrap: 'wrap' }}>
          {phoneEntities.map((e, i) => (
            <span key={e.value} style={{
              fontSize: '11px', padding: '2px 8px', borderRadius: '4px',
              background: COLORS[i % COLORS.length] + '33',
              border: `1px solid ${COLORS[i % COLORS.length]}`,
              color: COLORS[i % COLORS.length]
            }}>● {e.value}</span>
          ))}
          <span style={{ fontSize: '11px', color: '#9ca3af' }}>● GPS Point &nbsp; 🔵 Cell Tower &nbsp; 🟠 Proximity Zone</span>
        </div>
      </div>

      {/* PROXIMITY ALERTS BANNER */}
      {proximityAlerts.length > 0 && (
        <div style={{ padding: '10px 16px', background: '#450a0a', borderBottom: '1px solid #ef4444' }}>
          <p style={{ margin: '0 0 6px', fontWeight: 'bold', color: '#fca5a5', fontSize: '13px' }}>
            ⚠ {proximityAlerts.length} PROXIMITY ALERT{proximityAlerts.length > 1 ? 'S' : ''} — Entities within {proximityRadius}m:
          </p>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {proximityAlerts.map((a, i) => (
              <span key={i} style={{
                fontSize: '11px', padding: '3px 10px', borderRadius: '4px',
                background: '#7f1d1d', color: '#fca5a5', border: '1px solid #ef4444'
              }}>
                {a.entity1} ↔ {a.entity2} ({a.distance}m) @ {a.location1}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* MAP */}
      <MapContainer center={mapCenter} zoom={gpsEvents.length > 0 ? 12 : 5}
        style={{ height: 'calc(100vh - 200px)', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* GPS POINTS */}
        {gpsEvents.map((event, i) => {
          const coord = parseCoord(event.target);
          if (!coord) return null;
          const color = getColor(event.source);
          return (
            <CircleMarker key={`gps-${i}`} center={coord} radius={9}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.85, weight: 2 }}>
              <Popup>
                <b>📍 GPS Location</b><br />
                <b>Entity:</b> {event.source}<br />
                <b>Location:</b> {event.location}<br />
                <b>Time:</b> {event.timestamp}<br />
                <b>Coordinates:</b> {event.target}
              </Popup>
            </CircleMarker>
          );
        })}

        {/* ROUTE LINE */}
        {showRoute && routePoints.length > 1 && (
          <Polyline positions={routePoints} pathOptions={{
            color: selectedEntity !== 'all' ? getColor(selectedEntity) : '#ef4444',
            weight: 3, opacity: 0.8, dashArray: '8,4'
          }} />
        )}

        {/* CELL TOWER MARKERS */}
        {Object.entries(locationGroups).map(([location, data], i) => {
          const coord = KNOWN_LOCATIONS[location];
          if (!coord) return null;
          return (
            <CircleMarker key={`cell-${i}`} center={coord} radius={14}
              pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.25, weight: 2 }}>
              <Popup>
                <b>📡 Cell Tower Activity</b><br />
                <b>Location:</b> {location}<br />
                <b>Events:</b> {data.count}<br />
                <b>Types:</b> {[...data.types].join(', ')}<br />
                <b>Entities:</b> {[...data.entities].join(', ')}
              </Popup>
            </CircleMarker>
          );
        })}

        {/* PROXIMITY ZONES */}
        {showProximity && proximityAlerts.map((alert, i) => (
          <Circle key={`prox-${i}`} center={alert.coord} radius={proximityRadius}
            pathOptions={{ color: '#f97316', fillColor: '#f97316', fillOpacity: 0.1, weight: 2, dashArray: '5,5' }}>
            <Popup>
              <b>⚠ Proximity Alert</b><br />
              <b>{alert.entity1}</b> and <b>{alert.entity2}</b><br />
              within <b>{alert.distance}m</b> of each other<br />
              <b>Location:</b> {alert.location1}<br />
              <b>Time 1:</b> {alert.time1}<br />
              <b>Time 2:</b> {alert.time2}
            </Popup>
          </Circle>
        ))}
      </MapContainer>
    </div>
  );
}