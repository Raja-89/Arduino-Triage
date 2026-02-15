import { useState, useEffect } from 'react';
import { useApi, apiPost } from '../hooks/useApi';
import {
    HeartPulse, Play, Square, RotateCcw, CheckCircle,
    AlertTriangle, XCircle, Info, Stethoscope, Radio
} from 'lucide-react';

export default function HeartExam({ status }) {
    const { data: sensorData } = useApi('/sensor-data', 1000);
    const { data: systemStatus, refetch: refetchStatus } = useApi('/status', 500);
    const [examState, setExamState] = useState('idle'); // idle, examining, result
    const [result, setResult] = useState(null);

    useEffect(() => {
        if (systemStatus?.mode === 'EXAMINING') {
            setExamState('examining');
        } else if (systemStatus?.mode === 'RESULT' && systemStatus?.examResult) {
            setExamState('result');
            setResult(systemStatus.examResult);
        }
    }, [systemStatus]);

    const startExam = async () => {
        await apiPost('/exam/start', { type: 'heart' });
        setExamState('examining');
        setResult(null);
    };

    const stopExam = async () => {
        await apiPost('/exam/stop');
        setExamState('idle');
        setResult(null);
    };

    const resetExam = async () => {
        await apiPost('/reset');
        setExamState('idle');
        setResult(null);
        refetchStatus();
    };

    const getRiskIcon = (level) => {
        switch (level) {
            case 'LOW': return <CheckCircle size={20} />;
            case 'MEDIUM': return <AlertTriangle size={20} />;
            case 'HIGH': return <XCircle size={20} />;
            default: return <Info size={20} />;
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1><HeartPulse size={28} style={{ color: 'var(--cardiac-red)', verticalAlign: 'middle', marginRight: 10 }} />Heart Examination</h1>
                <p>Cardiac auscultation with AI-powered heart sound classification</p>
            </div>

            <div className="grid-2">
                {/* Exam Control */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><HeartPulse size={16} color="var(--cardiac-red)" style={{ marginRight: 6 }} />Examination Control</h3>
                        <span className={`risk-badge ${examState === 'examining' ? 'high' : examState === 'result' ? 'low' : 'medium'}`}>
                            <span className="badge-dot" />
                            {examState === 'examining' ? 'Recording' : examState === 'result' ? 'Complete' : 'Ready'}
                        </span>
                    </div>
                    <div className="card-body">
                        {examState === 'idle' && (
                            <div className="exam-flow">
                                <div style={{
                                    width: 100, height: 100, borderRadius: '50%',
                                    background: 'var(--cardiac-red-glow)', display: 'flex',
                                    alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px',
                                }}>
                                    <HeartPulse size={48} color="var(--cardiac-red)" className="heartbeat" />
                                </div>
                                <h3 className="exam-status">Ready for Heart Examination</h3>
                                <p className="exam-progress-text">
                                    Ensure stethoscope is placed on one of the 5 cardiac auscultation points.
                                    Use the Placement Guide for assistance.
                                </p>
                                <button className="btn btn-danger btn-lg" onClick={startExam} disabled={status?.mode === 'EXAMINING'}>
                                    <Play size={18} /> Start Heart Exam
                                </button>
                            </div>
                        )}

                        {examState === 'examining' && (
                            <div className="exam-flow">
                                <div style={{
                                    width: 120, height: 120, borderRadius: '50%',
                                    background: 'var(--cardiac-red-glow)', display: 'flex',
                                    alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px',
                                    boxShadow: '0 0 40px rgba(255, 76, 106, 0.3)',
                                }}>
                                    <HeartPulse size={56} color="var(--cardiac-red)" className="heartbeat" />
                                </div>
                                <h3 className="exam-status" style={{ color: 'var(--cardiac-red)' }}>Recording Heart Sounds...</h3>
                                <p className="exam-progress-text">
                                    Keep the patient still. Recording audio for analysis.
                                </p>
                                <div className="progress-bar" style={{ maxWidth: 400, margin: '0 auto 20px' }}>
                                    <div className="progress-fill" style={{
                                        width: `${systemStatus?.examProgress || 0}%`,
                                        background: 'linear-gradient(90deg, var(--cardiac-red), var(--cardiac-red-dim))',
                                    }} />
                                </div>
                                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                                    {systemStatus?.examProgress || 0}% complete
                                </p>
                                <button className="btn btn-secondary" onClick={stopExam} style={{ marginTop: 12 }}>
                                    <Square size={16} /> Stop Examination
                                </button>
                            </div>
                        )}

                        {examState === 'result' && result && (
                            <div>
                                <div className="exam-flow" style={{ paddingBottom: 16 }}>
                                    <div style={{
                                        width: 80, height: 80, borderRadius: '50%',
                                        background: result.riskLevel === 'LOW' ? 'var(--success-green-glow)' : 'var(--cardiac-red-glow)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
                                    }}>
                                        {getRiskIcon(result.riskLevel)}
                                    </div>
                                    <h3 className="exam-status">{result.diagnosis}</h3>
                                    <span className={`risk-badge ${result.riskLevel.toLowerCase()}`} style={{ marginTop: 8 }}>
                                        <span className="badge-dot" />
                                        {result.riskLevel} Risk
                                    </span>
                                </div>

                                {/* Classification breakdown */}
                                <div className="result-panel">
                                    <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 12 }}>Classification Results</h4>
                                    {result.details?.heartClassification && Object.entries(result.details.heartClassification).map(([cls, conf]) => (
                                        <div className="confidence-bar" key={cls}>
                                            <span className="confidence-label">{cls}</span>
                                            <div className="confidence-track">
                                                <div className="confidence-fill" style={{
                                                    width: `${(conf * 100)}%`,
                                                    background: cls === 'Abnormal' ? 'var(--cardiac-red)' : 'var(--success-green)',
                                                }} />
                                            </div>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', minWidth: 45 }}>
                                                {(conf * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Explanation */}
                                <div className="result-panel" style={{ marginTop: 12 }}>
                                    <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8 }}>
                                        <Info size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                                        AI Explanation
                                    </h4>
                                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                        {result.details?.explanation}
                                    </p>
                                    {result.details?.riskFactors?.length > 0 && (
                                        <div style={{ marginTop: 12 }}>
                                            <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--warning-amber)', marginBottom: 6 }}>
                                                Risk Factors:
                                            </p>
                                            <ul style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', paddingLeft: 16 }}>
                                                {result.details.riskFactors.map((f, i) => <li key={i}>{f}</li>)}
                                            </ul>
                                        </div>
                                    )}
                                </div>

                                <button className="btn btn-primary" onClick={resetExam} style={{ marginTop: 20, width: '100%' }}>
                                    <RotateCcw size={16} /> New Examination
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Live Readings */}
                <div>
                    <div className="card" style={{ marginBottom: 20 }}>
                        <div className="card-header">
                            <h3 className="card-title"><Radio size={16} style={{ marginRight: 6 }} />Live Readings</h3>
                        </div>
                        <div className="card-body">
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                <div className="sensor-card red">
                                    <div className="sensor-header">
                                        <span className="sensor-name">Heart Rate</span>
                                        <HeartPulse size={16} color="var(--cardiac-red)" />
                                    </div>
                                    <div className="sensor-value">{sensorData?.heartRate || '--'} <span className="sensor-unit">BPM</span></div>
                                    <div className="sensor-bar">
                                        <div className="sensor-bar-fill" style={{
                                            width: `${Math.min(((sensorData?.heartRate || 60) - 40) / 120 * 100, 100)}%`,
                                            background: 'var(--cardiac-red)',
                                        }} />
                                    </div>
                                </div>
                                <div className="sensor-card amber">
                                    <div className="sensor-header">
                                        <span className="sensor-name">Temperature</span>
                                    </div>
                                    <div className="sensor-value">{sensorData?.temperature || '--'}<span className="sensor-unit">°C</span></div>
                                </div>
                                <div className="sensor-card teal">
                                    <div className="sensor-header">
                                        <span className="sensor-name">Audio Level</span>
                                    </div>
                                    <div className="sensor-value">{sensorData?.audioLevel || '0'}<span className="sensor-unit"> dB</span></div>
                                    <div className="sensor-bar">
                                        <div className="sensor-bar-fill" style={{
                                            width: `${Math.min((sensorData?.audioLevel || 0) / 60 * 100, 100)}%`,
                                            background: 'var(--accent-teal)',
                                        }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Positioning Guide */}
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title"><Stethoscope size={16} style={{ marginRight: 6 }} />Heart Auscultation Points</h3>
                        </div>
                        <div className="card-body" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {[
                                    { name: 'Aortic', desc: '2nd right intercostal space' },
                                    { name: 'Pulmonic', desc: '2nd left intercostal space' },
                                    { name: "Erb's Point", desc: '3rd left intercostal space' },
                                    { name: 'Tricuspid', desc: '4th left intercostal space' },
                                    { name: 'Mitral (Apex)', desc: '5th intercostal space, midclavicular' },
                                ].map((p, i) => (
                                    <div key={i} style={{
                                        padding: '8px 12px', background: 'var(--bg-elevated)',
                                        borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--cardiac-red)',
                                    }}>
                                        <strong style={{ color: 'var(--text-primary)' }}>{p.name}</strong> — {p.desc}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
