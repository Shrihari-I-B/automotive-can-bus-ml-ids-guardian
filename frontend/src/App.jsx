import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Play, Square, AlertTriangle, Activity, Shield, Terminal, Zap, RefreshCw } from 'lucide-react';
import Tachometer from './components/Tachometer';
import Speedometer from './components/Speedometer';

const API_URL = 'http://localhost:8000/api';
const WS_URL = 'ws://localhost:8000/ws/dashboard';

function App() {
    const [data, setData] = useState({
        can: { RPM: 0, Gear: 0, Speed: 0, Brake: 0 },
        vehicle_state: "Unknown",
        alerts: [],
        status: { Simulator: false, IDS: false, Attacker: false },
        logs: [],
        dos_active: false
    });
    const [loading, setLoading] = useState({});
    const [activeAttack, setActiveAttack] = useState(null);
    const logsEndRef = useRef(null);

    // WebSocket Connection
    useEffect(() => {
        console.log("Connecting to WebSocket:", WS_URL);
        const ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log("WebSocket Connected");
        };

        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                setData(payload);
                // Sync active attack state if backend reports attacker is off
                if (!payload.status.Attacker && activeAttack) {
                    setActiveAttack(null);
                }
            } catch (e) {
                console.error("Error parsing WebSocket message:", e);
            }
        };

        ws.onerror = (error) => {
            console.error("WebSocket Error:", error);
        };

        ws.onclose = () => {
            console.log("WebSocket Disconnected");
        };

        return () => ws.close();
    }, [activeAttack]);

    // Auto-scroll logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [data.logs]);

    // Helper to toggle loading state
    const toggleLoading = (key, isLoading) => {
        setLoading(prev => ({ ...prev, [key]: isLoading }));
    };

    // Generic Control Handler (Start/Stop Simulator & IDS)
    const handleControl = async (endpoint, key) => {
        if (loading[key]) return;
        toggleLoading(key, true);
        console.log(`Triggering Control: ${endpoint}`);
        try {
            const response = await axios.post(`${API_URL}/${endpoint}`);
            console.log(`Control Success (${endpoint}):`, response.data);
        } catch (error) {
            console.error(`Control Error (${endpoint}):`, error);
            alert(`Failed to execute ${endpoint}: ${error.message}`);
        } finally {
            toggleLoading(key, false);
        }
    };

    // Attack Handler
    const handleAttack = async (type) => {
        if (loading[type] || activeAttack === type) return;
        toggleLoading(type, true);
        console.log(`Starting Attack: ${type}`);
        try {
            const response = await axios.post(`${API_URL}/start/attack`, { type });
            console.log(`Attack Started (${type}):`, response.data);
            setActiveAttack(type);
        } catch (error) {
            console.error(`Attack Error (${type}):`, error);
            alert(`Failed to start ${type} attack: ${error.message}`);
        } finally {
            toggleLoading(type, false);
        }
    };

    // Stop Attack Handler
    const stopAttack = async () => {
        if (loading['stopAttack']) return;
        toggleLoading('stopAttack', true);
        console.log("Stopping Attack");
        try {
            const response = await axios.post(`${API_URL}/stop/attack`);
            console.log("Attack Stopped:", response.data);
            setActiveAttack(null);
        } catch (error) {
            console.error("Stop Attack Error:", error);
            alert(`Failed to stop attack: ${error.message}`);
        } finally {
            toggleLoading('stopAttack', false);
        }
    };

    // Clear Logs Handler
    const clearLogs = async () => {
        console.log("Clearing Logs");
        try {
            const response = await axios.post(`${API_URL}/logs/clear`);
            console.log("Logs Cleared:", response.data);
        } catch (error) {
            console.error("Clear Logs Error:", error);
        }
    };

    return (
        <div className="dashboard-container">
            {/* Sidebar */}
            <div className="sidebar">
                <div className="logo">
                    <h1>CAN IDS</h1>
                    <p>Security Monitor</p>
                </div>

                <div className="controls-section">
                    <h3>Controls</h3>

                    {/* Simulator Controls */}
                    <div className="control-group">
                        <div className="control-header">
                            <span>Simulator</span>
                            <span className={`status-badge ${data.status.Simulator ? 'status-running' : 'status-stopped'}`}>
                                {data.status.Simulator ? 'RUNNING' : 'STOPPED'}
                            </span>
                        </div>
                        {!data.status.Simulator ? (
                            <button
                                className="btn btn-primary full-width"
                                onClick={() => handleControl('start/simulator', 'sim')}
                                disabled={loading['sim']}
                            >
                                {loading['sim'] ? 'Starting...' : <><Play size={16} /> Start Sim</>}
                            </button>
                        ) : (
                            <button
                                className="btn btn-danger full-width"
                                onClick={() => handleControl('stop/simulator', 'sim')}
                                disabled={loading['sim']}
                            >
                                {loading['sim'] ? 'Stopping...' : <><Square size={16} /> Stop Sim</>}
                            </button>
                        )}
                    </div>

                    {/* IDS Controls */}
                    <div className="control-group">
                        <div className="control-header">
                            <span>IDS Detector</span>
                            <span className={`status-badge ${data.status.IDS ? 'status-running' : 'status-stopped'}`}>
                                {data.status.IDS ? 'ACTIVE' : 'INACTIVE'}
                            </span>
                        </div>
                        {!data.status.IDS ? (
                            <button
                                className="btn btn-primary full-width"
                                onClick={() => handleControl('start/ids', 'ids')}
                                disabled={loading['ids']}
                            >
                                {loading['ids'] ? 'Enabling...' : <><Shield size={16} /> Enable IDS</>}
                            </button>
                        ) : (
                            <button
                                className="btn btn-danger full-width"
                                onClick={() => handleControl('stop/ids', 'ids')}
                                disabled={loading['ids']}
                            >
                                {loading['ids'] ? 'Disabling...' : <><Square size={16} /> Disable IDS</>}
                            </button>
                        )}
                    </div>
                </div>

                <div className="attacks-section">
                    <h3>Attack Injection</h3>
                    <div className="attack-buttons">
                        <button
                            className={`btn full-width ${activeAttack === 'replay' ? 'btn-danger' : 'btn-outline'}`}
                            onClick={() => handleAttack('replay')}
                            disabled={loading['replay'] || (activeAttack && activeAttack !== 'replay')}
                        >
                            {loading['replay'] ? 'Injecting...' : <><RefreshCw size={16} /> Replay Attack</>}
                        </button>
                        <button
                            className={`btn full-width ${activeAttack === 'spoof' ? 'btn-danger' : 'btn-outline'}`}
                            onClick={() => handleAttack('spoof')}
                            disabled={loading['spoof'] || (activeAttack && activeAttack !== 'spoof')}
                        >
                            {loading['spoof'] ? 'Injecting...' : <><Zap size={16} /> Spoof Attack</>}
                        </button>
                        <button
                            className={`btn full-width ${activeAttack === 'flood' ? 'btn-danger' : 'btn-outline'}`}
                            onClick={() => handleAttack('flood')}
                            disabled={loading['flood'] || (activeAttack && activeAttack !== 'flood')}
                        >
                            {loading['flood'] ? 'Injecting...' : <><AlertTriangle size={16} /> Flood Attack</>}
                        </button>
                        <button
                            className="btn btn-secondary full-width"
                            onClick={stopAttack}
                            disabled={!activeAttack || loading['stopAttack']}
                        >
                            {loading['stopAttack'] ? 'Stopping...' : 'Stop Attack'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="main-content">
                {/* Top Row: Gauges & Status */}
                <div className="grid-3">
                    <div className="card">
                        <div className="card-header">
                            <span className="card-title"><Activity size={20} /> RPM</span>
                        </div>
                        <div className="gauge-wrapper">
                            <Tachometer rpm={data.can.RPM} />
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <span className="card-title"><Activity size={20} /> Speed</span>
                        </div>
                        <div className="gauge-wrapper">
                            <Speedometer speed={data.can.Speed} gear={data.can.Gear} />
                        </div>
                        <div className="vehicle-state-badge">
                            {data.vehicle_state}
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <span className="card-title"><Shield size={20} /> IDS Status</span>
                        </div>
                        <div className="ids-status-content">
                            {data.alerts.length > 0 ? (
                                <div className="status-message danger">
                                    <AlertTriangle size={24} />
                                    <span>INTRUSION DETECTED</span>
                                </div>
                            ) : (
                                <div className="status-message success">
                                    <Shield size={24} />
                                    <span>SYSTEM SECURE</span>
                                </div>
                            )}
                            <div className="stat-label">
                                {data.alerts.length} alerts in last session
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom Row: Alerts & Logs */}
                <div className="grid-2 bottom-row">
                    <div className="card alerts-card">
                        <div className="card-header">
                            <span className="card-title"><AlertTriangle size={20} /> Recent Alerts</span>
                        </div>
                        <div className="alerts-list">
                            {data.alerts.length === 0 ? (
                                <div className="empty-state">No threats detected.</div>
                            ) : (
                                data.alerts.slice().reverse().map((alert, i) => (
                                    <div key={i} className="alert-item">
                                        <div className="alert-icon">
                                            <AlertTriangle size={20} />
                                        </div>
                                        <div className="alert-content">
                                            <div className="alert-title">{alert.type}</div>
                                            <div className="alert-meta">
                                                <span>Vol: {alert.volume}</span>
                                                <span className="alert-details">{alert.details}</span>
                                            </div>
                                        </div>
                                        <div className="alert-time">{alert.timestamp}</div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    <div className="card logs-card" style={data.dos_active ? { border: '1px solid #ef4444' } : {}}>
                        <div className="card-header">
                            <span className="card-title">
                                <Terminal size={20} /> System Logs
                                {data.dos_active && (
                                    <span style={{
                                        marginLeft: '10px',
                                        color: '#ef4444',
                                        fontWeight: 'bold',
                                        fontSize: '0.8rem',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '5px'
                                    }}>
                                        <AlertTriangle size={14} /> BUS OFF - FLOODING
                                    </span>
                                )}
                            </span>
                            <button className="btn btn-sm btn-outline" onClick={clearLogs}>Clear</button>
                        </div>
                        <div className="log-container">
                            {data.logs.map((log, i) => (
                                <div key={i} className="log-line">{log}</div>
                            ))}
                            <div ref={logsEndRef} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
