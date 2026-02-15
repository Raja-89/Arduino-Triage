import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import {
    HeartPulse, Wind, Thermometer, Activity, Volume2,
    Move, Gauge, ArrowRight, ShieldCheck, AlertTriangle, Zap,
    Hospital, BarChart3, Microscope, ClipboardList, TrendingUp,
    Brain, Cpu, CheckCircle
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useState, useEffect } from 'react';

export default function Dashboard({ status }) {
    const { data: sensorData } = useApi('/sensor-data', 1000);
    const { data: history } = useApi('/triage/history');
    const { data: models } = useApi('/models');
    const navigate = useNavigate();
    const [waveData, setWaveData] = useState([]);

    // Live waveform data — uses real sensor data when available
    useEffect(() => {
        const interval = setInterval(() => {
            setWaveData(prev => {
                const now = Date.now();
                // Use real heart rate from hardware if available, else simulate
                const hr = sensorData?.heartRate || 72;
                const baseHeart = hr + Math.sin(now / 300) * 8 + Math.random() * 3;
                const baseLung = (sensorData?.respiratoryRate || 16) + Math.sin(now / 500) * 4 + Math.random() * 2;
                const newPoint = {
                    time: now,
                    heart: baseHeart,
                    lung: baseLung,
                    audio: sensorData?.audioLevel ?? Math.random() * 40,
                };
                const updated = [...prev, newPoint].slice(-40);
                return updated;
            });
        }, 200);
        return () => clearInterval(interval);
    }, [sensorData]);

    const recentTriages = history?.slice(0, 5) || [];

    return (
        <div className="page-container">
            <div className="page-header">
                <h1><Hospital size={28} style={{ verticalAlign: 'middle', marginRight: 10, color: 'var(--accent-teal)' }} />Triage Dashboard</h1>
                <p>Real-time monitoring and quick-start examinations</p>
            </div>

            {/* Quick Stats */}
            <div className="grid-4" style={{ marginBottom: 24 }}>
                <div className="stat-card">
                    <div className="stat-icon teal"><Activity size={22} /></div>
                    <div className="stat-info">
                        <div className="stat-label">System Mode</div>
                        <div className="stat-value" style={{ fontSize: '1.2rem' }}>{status?.mode || 'IDLE'}</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon red"><HeartPulse size={22} /></div>
                    <div className="stat-info">
                        <div className="stat-label">Heart Rate</div>
                        <div className="stat-value">{sensorData?.heartRate || '--'} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>BPM</span></div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon blue"><Wind size={22} /></div>
                    <div className="stat-info">
                        <div className="stat-label">Respiratory Rate</div>
                        <div className="stat-value">{sensorData?.respiratoryRate || '--'} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>/min</span></div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon amber"><Thermometer size={22} /></div>
                    <div className="stat-info">
                        <div className="stat-label">Temperature</div>
                        <div className="stat-value">{sensorData?.temperature || '--'}°C</div>
                    </div>
                </div>
            </div>

            {/* Quick Actions + Live Waveform */}
            <div className="grid-2" style={{ marginBottom: 24 }}>
                {/* Quick Actions */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Zap size={16} style={{ marginRight: 6, color: 'var(--warning-amber)' }} />Quick Start Examination</h3>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <button
                                className="btn btn-primary btn-lg"
                                style={{ width: '100%', justifyContent: 'space-between' }}
                                onClick={() => navigate('/heart-exam')}
                            >
                                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <HeartPulse size={20} className="heartbeat" />
                                    Start Heart Examination
                                </span>
                                <ArrowRight size={18} />
                            </button>
                            <button
                                className="btn btn-secondary btn-lg"
                                style={{
                                    width: '100%', justifyContent: 'space-between',
                                    background: 'linear-gradient(135deg, var(--respiratory-blue), var(--respiratory-blue-dim))',
                                    color: 'white', borderColor: 'transparent',
                                }}
                                onClick={() => navigate('/lung-exam')}
                            >
                                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Wind size={20} className="breathe" />
                                    Start Lung Examination
                                </span>
                                <ArrowRight size={18} />
                            </button>
                            <button
                                className="btn btn-secondary btn-lg"
                                style={{ width: '100%', justifyContent: 'space-between' }}
                                onClick={() => navigate('/placement-guide')}
                            >
                                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <Gauge size={20} />
                                    Stethoscope Placement Guide
                                </span>
                                <ArrowRight size={18} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Live Waveform */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><BarChart3 size={16} style={{ marginRight: 6, color: 'var(--accent-teal)' }} />Live Signal Monitor</h3>
                        <div className="status-indicator" style={{ fontSize: '0.75rem' }}>
                            <div className="status-dot" /> Live
                        </div>
                    </div>
                    <div className="card-body" style={{ height: 200 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={waveData}>
                                <defs>
                                    <linearGradient id="heartGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#FF4C6A" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#FF4C6A" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="lungGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#4FC3F7" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#4FC3F7" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="time" hide />
                                <YAxis hide domain={[0, 100]} />
                                <Tooltip
                                    contentStyle={{
                                        background: 'var(--bg-secondary)', border: '1px solid var(--border-default)',
                                        borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', color: 'var(--text-primary)'
                                    }}
                                    labelFormatter={() => ''}
                                />
                                <Area type="monotone" dataKey="heart" stroke="#FF4C6A" fill="url(#heartGradient)" strokeWidth={2} dot={false} name="Heart" />
                                <Area type="monotone" dataKey="lung" stroke="#4FC3F7" fill="url(#lungGradient)" strokeWidth={2} dot={false} name="Lung" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Sensor Details + Recent Triages */}
            <div className="grid-2">
                {/* Sensor Cards */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Microscope size={16} style={{ marginRight: 6, color: 'var(--accent-teal)' }} />Sensor Readings</h3>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            <div className="sensor-card amber">
                                <div className="sensor-header">
                                    <span className="sensor-name">Temperature</span>
                                    <Thermometer size={16} color="var(--warning-amber)" />
                                </div>
                                <div className="sensor-value">{sensorData?.temperature || '--'}<span className="sensor-unit">°C</span></div>
                                <div className="sensor-bar">
                                    <div className="sensor-bar-fill" style={{
                                        width: `${((sensorData?.temperature || 36) - 35) / 5 * 100}%`,
                                        background: (sensorData?.temperature || 36) > 38 ? 'var(--cardiac-red)' : 'var(--warning-amber)',
                                    }} />
                                </div>
                            </div>
                            <div className="sensor-card teal">
                                <div className="sensor-header">
                                    <span className="sensor-name">Audio Level</span>
                                    <Volume2 size={16} color="var(--accent-teal)" />
                                </div>
                                <div className="sensor-value">{sensorData?.audioLevel || '0'}<span className="sensor-unit"> dB</span></div>
                                <div className="sensor-bar">
                                    <div className="sensor-bar-fill" style={{
                                        width: `${Math.min((sensorData?.audioLevel || 0) / 60 * 100, 100)}%`,
                                        background: 'var(--accent-teal)',
                                    }} />
                                </div>
                            </div>
                            <div className="sensor-card blue">
                                <div className="sensor-header">
                                    <span className="sensor-name">SpO₂</span>
                                    <Zap size={16} color="var(--respiratory-blue)" />
                                </div>
                                <div className="sensor-value">{sensorData?.spO2 || '--'}<span className="sensor-unit">%</span></div>
                                <div className="sensor-bar">
                                    <div className="sensor-bar-fill" style={{
                                        width: `${(sensorData?.spO2 || 96)}%`,
                                        background: 'var(--respiratory-blue)',
                                    }} />
                                </div>
                            </div>
                            <div className="sensor-card red">
                                <div className="sensor-header">
                                    <span className="sensor-name">Movement</span>
                                    <Move size={16} color="var(--cardiac-red)" />
                                </div>
                                <div className="sensor-value">{sensorData?.movement ? 'Detected' : 'Stable'}</div>
                                <div className="sensor-bar">
                                    <div className="sensor-bar-fill" style={{
                                        width: sensorData?.movement ? '80%' : '10%',
                                        background: sensorData?.movement ? 'var(--cardiac-red)' : 'var(--success-green)',
                                    }} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recent Triages */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><ClipboardList size={16} style={{ marginRight: 6, color: 'var(--accent-teal)' }} />Recent Triage Results</h3>
                        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/results')}>View All</button>
                    </div>
                    <div className="card-body">
                        {recentTriages.length === 0 ? (
                            <div className="empty-state" style={{ padding: '30px 10px' }}>
                                <p>No triage results yet</p>
                            </div>
                        ) : (
                            <div className="timeline">
                                {recentTriages.map(triage => (
                                    <div
                                        key={triage.id}
                                        className={`timeline-item ${triage.riskLevel.toLowerCase()}`}
                                        onClick={() => navigate('/results')}
                                    >
                                        <div className="timeline-time">{new Date(triage.timestamp).toLocaleString()}</div>
                                        <div className="timeline-title">
                                            {triage.type === 'heart' ? <HeartPulse size={14} color="var(--cardiac-red)" style={{ marginRight: 4, verticalAlign: 'middle' }} /> : <Wind size={14} color="var(--respiratory-blue)" style={{ marginRight: 4, verticalAlign: 'middle' }} />} {triage.diagnosis}
                                            <span className={`risk-badge ${triage.riskLevel.toLowerCase()}`} style={{ marginLeft: 8 }}>
                                                <span className="badge-dot" />
                                                {triage.riskLevel}
                                            </span>
                                        </div>
                                        <div className="timeline-desc">Confidence: {(triage.confidence * 100).toFixed(0)}%</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Risk Summary Bar */}
            {status?.riskBreakdown && (
                <div className="card" style={{ marginTop: 24 }}>
                    <div className="card-header">
                        <h3 className="card-title"><TrendingUp size={16} style={{ marginRight: 6, color: 'var(--accent-teal)' }} />Risk Distribution</h3>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                            {[
                                { label: 'Low Risk', count: status.riskBreakdown.low, color: 'var(--success-green)', icon: ShieldCheck },
                                { label: 'Medium Risk', count: status.riskBreakdown.medium, color: 'var(--warning-amber)', icon: AlertTriangle },
                                { label: 'High Risk', count: status.riskBreakdown.high, color: 'var(--cardiac-red)', icon: AlertTriangle },
                                { label: 'Critical', count: status.riskBreakdown.critical, color: 'var(--critical-purple)', icon: Zap },
                            ].map(item => (
                                <div key={item.label} style={{
                                    flex: 1, minWidth: 140, textAlign: 'center', padding: 16,
                                    background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)',
                                    border: `1px solid var(--border-default)`,
                                }}>
                                    <item.icon size={20} color={item.color} style={{ marginBottom: 8 }} />
                                    <div style={{ fontSize: '1.5rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: item.color }}>
                                        {item.count}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>{item.label}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* ML Models Info */}
            {models && (
                <div className="card" style={{ marginTop: 24 }}>
                    <div className="card-header">
                        <h3 className="card-title"><Brain size={16} style={{ marginRight: 6, color: 'var(--accent-teal)' }} />ML Models</h3>
                        <span className="risk-badge low"><span className="badge-dot" />All Loaded</span>
                    </div>
                    <div className="card-body">
                        <div className="model-info-grid">
                            {Object.entries(models).map(([key, model]) => (
                                <div key={key} className="model-card">
                                    <div className="model-card-header">
                                        <h4>
                                            {key === 'heart'
                                                ? <HeartPulse size={16} color="var(--cardiac-red)" />
                                                : <Wind size={16} color="var(--respiratory-blue)" />
                                            }
                                            {model.name}
                                        </h4>
                                        <span className="risk-badge low" style={{ fontSize: '0.68rem' }}>
                                            <span className="badge-dot" />{model.status}
                                        </span>
                                    </div>
                                    <div className="model-card-stats">
                                        {[
                                            { label: 'Version', value: model.version },
                                            { label: 'Accuracy', value: model.accuracy },
                                            { label: 'Model Size', value: model.size },
                                            { label: 'Input Shape', value: model.inputShape },
                                            { label: 'Inference Time', value: model.inferenceTime },
                                            { label: 'Classes', value: model.classes?.join(', ') },
                                        ].map((stat, i) => (
                                            <div key={i} className="model-stat">
                                                <span className="model-stat-label">{stat.label}</span>
                                                <span className="model-stat-value">{stat.value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
