import React, { useState, useEffect, useRef } from 'react';

const GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"; // Replace with your key

function loadGoogleMaps(apiKey) {
  return new Promise((resolve) => {
    if (window.google && window.google.maps) return resolve();
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;
    script.onload = resolve;
    document.head.appendChild(script);
  });
}

const EVENT_COLORS = {
  CALL: "#3b82f6", OUTGOING: "#3b82f6", INCOMING: "#22c55e",
  WEBSITE_VISIT: "#a855f7", BLUETOOTH_PAIRING: "#f97316",
  WHATSAPP_MESSAGE: "#25d366", WHATSAPP_CALL: "#25d366",
  DEFAULT: "#ef4444"
};

export default function GeoMapTab({ caseId }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef([]);
  const polylineRef = useRef(null);

  const [locations, setLocations] = useState([]);
  const [entities, setEntities] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState("ALL");
  const [showRoute, setShowRoute] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    fetchData();
  }, [caseId]);

  useEffect(() => {
    if (locations.length > 0) initMap();
  }, [locations]);

  useEffect(() => {
    if (mapReady) renderMarkers();
  }, [mapReady, selectedEntity, showRoute]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [locRes, entRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/geo/locations/${caseId}`),
        fetch(`http://127.0.0.1:8000/geo/entities/${caseId}`)
      ]);
      const locData = await locRes.json();
      const entData = await entRes.json();
      setLocations(locData);
      // Unique entities from location events
      const uniqueEntities = [...new Set(locData.map(l => l.entity).filter(Boolean))];
      setEntities(uniqueEntities);
    } catch (err) {
      setError("Failed to load location data: " + err.message);
    }
    setLoading(false);
  };

  const initMap = async () => {
    await loadGoogleMaps(GOOGLE_MAPS_API_KEY);
    const validPoints = locations.filter(l => l.lat && l.lng);
    const center = validPoints.length > 0
      ? { lat: validPoints[0].lat, lng: validPoints[0].lng }
      : { lat: 17.385, lng: 78.4867 }; // Default: Hyderabad

    mapInstance.current = new window.google.maps.Map(mapRef.current, {
      center,
      zoom: 12,
      mapTypeId: "roadmap",
      styles: [
        { elementType: "geometry", stylers: [{ color: "#1d2535" }] },
        { elementType: "labels.text.stroke", stylers: [{ color: "#1d2535" }] },
        { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
        { featureType: "road", elementType: "geometry", stylers: [{ color: "#38414e" }] },
        { featureType: "water", elementType: "geometry", stylers: [{ color: "#17263c" }] },
      ]
    });
    setMapReady(true);
  };

  const clearMap = () => {
    markersRef.current.forEach(m => m.setMap(null));
    markersRef.current = [];
    if (polylineRef.current) { polylineRef.current.setMap(null); polylineRef.current = null; }
  };

  const renderMarkers = () => {
    if (!mapInstance.current) return;
    clearMap();

    const filtered = selectedEntity === "ALL"
      ? locations
      : locations.filter(l => l.entity === selectedEntity);

    const validPoints = filtered.filter(l => l.lat && l.lng);

    validPoints.forEach((point, i) => {
      const color = EVENT_COLORS[point.event_type] || EVENT_COLORS.DEFAULT;
      const marker = new window.google.maps.Marker({
        position: { lat: point.lat, lng: point.lng },
        map: mapInstance.current,
        title: point.label,
        label: { text: String(i + 1), color: "#fff", fontSize: "11px", fontWeight: "bold" },
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: color,
          fillOpacity: 0.9,
          strokeColor: "#fff",
          strokeWeight: 2
        }
      });

      const infoWindow = new window.google.maps.InfoWindow({
        content: `
          <div style="background:#1e2533;color:#e5e7eb;padding:10px;border-radius:6px;min-width:200px">
            <p style="font-weight:bold;margin:0 0 4px;color:${color}">${point.event_type}</p>
            <p style="margin:2px 0;font-size:13px">📍 ${point.location_name}</p>
            <p style="margin:2px 0;font-size:12px;color:#9ca3af">Entity: ${point.entity || "-"}</p>
            <p style="margin:2px 0;font-size:12px;color:#9ca3af">Time: ${point.timestamp}</p>
          </div>`
      });
      marker.addListener("click", () => infoWindow.open(mapInstance.current, marker));
      markersRef.current.push(marker);
    });

    // Draw route polyline if enabled
    if (showRoute && validPoints.length > 1) {
      const path = validPoints.map(p => ({ lat: p.lat, lng: p.lng }));
      polylineRef.current = new window.google.maps.Polyline({
        path,
        geodesic: true,
        strokeColor: "#3b82f6",
        strokeOpacity: 0.8,
        strokeWeight: 2,
        map: mapInstance.current
      });
    }

    // Fit map to markers
    if (validPoints.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      validPoints.forEach(p => bounds.extend({ lat: p.lat, lng: p.lng }));
      mapInstance.current.fitBounds(bounds);
    }
  };

  const nonGeoLocations = locations.filter(l => !l.lat && l.location_name);

  return (
    <div>
      {/* Controls */}
      <div style={{ display: "flex", gap: "12px", marginBottom: "16px", flexWrap: "wrap", alignItems: "center" }}>
        <select
          value={selectedEntity}
          onChange={e => setSelectedEntity(e.target.value)}
          style={{
            background: "#1e2533", color: "#e5e7eb", border: "1px solid #374151",
            borderRadius: "6px", padding: "8px 12px", fontSize: "13px"
          }}
        >
          <option value="ALL">All Entities</option>
          {entities.map(e => <option key={e} value={e}>{e}</option>)}
        </select>

        <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "#9ca3af", cursor: "pointer" }}>
          <input type="checkbox" checked={showRoute} onChange={e => setShowRoute(e.target.checked)} />
          Show Route
        </label>

        <button
          onClick={fetchData}
          style={{
            background: "#1e3a5f", color: "#93c5fd", border: "none",
            borderRadius: "6px", padding: "8px 14px", cursor: "pointer", fontSize: "13px"
          }}
        >
          🔄 Refresh
        </button>

        <div style={{ marginLeft: "auto", display: "flex", gap: "12px", fontSize: "12px", color: "#9ca3af" }}>
          {Object.entries(EVENT_COLORS).filter(([k]) => k !== "DEFAULT").map(([type, color]) => (
            <span key={type} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block" }} />
              {type.replace("_", " ")}
            </span>
          ))}
        </div>
      </div>

      {/* Map */}
      {loading ? (
        <div style={{ textAlign: "center", padding: "60px", color: "#9ca3af" }}>Loading map...</div>
      ) : error ? (
        <div style={{ background: "#450a0a", border: "1px solid #ef4444", borderRadius: "6px", padding: "16px", color: "#fca5a5" }}>{error}</div>
      ) : (
        <>
          <div ref={mapRef} style={{
            width: "100%", height: "500px", borderRadius: "8px",
            border: "1px solid #374151", marginBottom: "16px"
          }} />

          {/* Non-geo location events table */}
          {nonGeoLocations.length > 0 && (
            <div>
              <h3 style={{ fontSize: "15px", fontWeight: "bold", marginBottom: "10px", color: "#9ca3af" }}>
                📍 Location Events (no coordinates — cell tower / address)
              </h3>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                  <thead>
                    <tr style={{ background: "#1e2533" }}>
                      {["Entity", "Event", "Location", "Timestamp"].map(h => (
                        <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: "#9ca3af", borderBottom: "1px solid #374151" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {nonGeoLocations.map((l, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #1f2937" }}>
                        <td style={{ padding: "8px 12px", color: "#e5e7eb" }}>{l.entity}</td>
                        <td style={{ padding: "8px 12px" }}>
                          <span style={{
                            background: "#1e3a5f", color: "#93c5fd",
                            padding: "2px 8px", borderRadius: "4px", fontSize: "11px"
                          }}>{l.event_type}</span>
                        </td>
                        <td style={{ padding: "8px 12px", color: "#9ca3af" }}>{l.location_name}</td>
                        <td style={{ padding: "8px 12px", color: "#6b7280", fontSize: "12px" }}>{l.timestamp}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {locations.length === 0 && (
            <div style={{ textAlign: "center", padding: "32px", color: "#9ca3af" }}>
              No location data found. Parse GPS evidence first.
            </div>
          )}
        </>
      )}
    </div>
  );
}