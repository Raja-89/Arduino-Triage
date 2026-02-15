import { useState, useEffect } from 'react';
import { useApi, apiPost } from '../hooks/useApi';
import {
    Wind, Play, Square, RotateCcw, CheckCircle,
    AlertTriangle, XCircle, Info, Stethoscope, Radio
} from 'lucide-react';

export default function LungExam({ status }) {
    const { data: sensorData } = useApi('/sensor-data', 1000);
    const { data: systemStatus, refetch: refetchStatus } = useApi('/status', 500);
    const [examState, setExamState] = useState('idle');
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
        await apiPost('/exam/start', { type: 'lung' });
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

    const classColors = {
        Normal: 'var(--success-green)',
        Wheeze: 'var(--warning-amber)',
        Crackle: 'var(--cardiac-red)',
        Both: 'var(--critical-purple)',
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1><Wind size={28} style={{ color: 'var(--respiratory-blue)', verticalAlign: 'middle', marginRight: 10 }} />Lung Examination</h1>
                <p>Respiratory auscultation with AI-powered lung sound classification</p>
            </div>

            <div className="grid-2">
                {/* Exam Control */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Wind size={16} color="var(--respiratory-blue)" style={{ marginRight: 6 }} />Examination Control</h3>
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
                                    background: 'var(--respiratory-blue-glow)', display: 'flex',
                                    alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px',
                                }}>
                                    <Wind size={48} color="var(--respiratory-blue)" className="breathe" />
                                </div>
                                <h3 className="exam-status">Ready for Lung Examination</h3>
                                <p className="exam-progress-text">
                                    Ensure stethoscope is placed on one of the 6 anterior or posterior lung auscultation points.
                                </p>
                                <button
                                    className="btn btn-lg"
                                    onClick={startExam}
                                    disabled={status?.mode === 'EXAMINING'}
                                    style={{
                                        background: 'linear-gradient(135deg, var(--respiratory-blue), var(--respiratory-blue-dim))',
                                        color: 'white', border: 'none',
                                        boxShadow: '0 0 20px rgba(79, 195, 247, 0.3)',
                                    }}
                                >
                                    <Play size={18} /> Start Lung Exam
                                </button>
                            </div>
                        )}

                        {examState === 'examining' && (
                            <div className="exam-flow">
                                <div style={{
                                    width: 120, height: 120, borderRadius: '50%',
                                    background: 'var(--respiratory-blue-glow)', display: 'flex',
                                    alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px',
                                    boxShadow: '0 0 40px rgba(79, 195, 247, 0.3)',
                                }}>
                                    <Wind size={56} color="var(--respiratory-blue)" className="breathe" />
                                </div>
                                <h3 className="exam-status" style={{ color: 'var(--respiratory-blue)' }}>Recording Lung Sounds...</h3>
                                <p className="exam-progress-text">
                                    Ask patient to breathe deeply and normally.
                                </p>
                                <div className="progress-bar" style={{ maxWidth: 400, margin: '0 auto 20px' }}>
                                    <div className="progress-fill" style={{
                                        width: `${systemStatus?.examProgress || 0}%`,
                                        background: 'linear-gradient(90deg, var(--respiratory-blue), var(--respiratory-blue-dim))',
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
                                        background: result.riskLevel === 'LOW' ? 'var(--success-green-glow)' : 'var(--warning-amber-glow)',
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
                                    {result.details?.lungClassification && Object.entries(result.details.lungClassification).map(([cls, conf]) => (
                                        <div className="confidence-bar" key={cls}>
                                            <span className="confidence-label">{cls}</span>
                                            <div className="confidence-track">
                                                <div className="confidence-fill" style={{
                                                    width: `${(conf * 100)}%`,
                                                    background: classColors[cls] || 'var(--accent-teal)',
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
                                <div className="sensor-card blue">
                                    <div className="sensor-header">
                                        <span className="sensor-name">Respiratory Rate</span>
                                        <Wind size={16} color="var(--respiratory-blue)" />
                                    </div>
                                    <div className="sensor-value">{sensorData?.respiratoryRate || '--'} <span className="sensor-unit">/min</span></div>
                                    <div className="sensor-bar">
                                        <div className="sensor-bar-fill" style={{
                                            width: `${Math.min(((sensorData?.respiratoryRate || 16) - 8) / 32 * 100, 100)}%`,
                                            background: 'var(--respiratory-blue)',
                                        }} />
                                    </div>
                                </div>
                                <div className="sensor-card teal">
                                    <div className="sensor-header">
                                        <span className="sensor-name">SpO₂</span>
                                    </div>
                                    <div className="sensor-value">{sensorData?.spO2 || '--'}<span className="sensor-unit">%</span></div>
                                </div>
                                <div className="sensor-card amber">
                                    <div className="sensor-header">
                                        <span className="sensor-name">Audio Level</span>
                                    </div>
                                    <div className="sensor-value">{sensorData?.audioLevel || '0'}<span className="sensor-unit"> dB</span></div>
                                    <div className="sensor-bar">
                                        <div className="sensor-bar-fill" style={{
                                            width: `${Math.min((sensorData?.audioLevel || 0) / 60 * 100, 100)}%`,
                                            background: 'var(--warning-amber)',
                                        }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Lung Positioning Guide */}
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title"><Stethoscope size={16} style={{ marginRight: 6 }} />Lung Auscultation Points</h3>
                        </div>
                        <div className="card-body" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {[
                                    { name: 'Right Upper', desc: 'Above clavicle, anterior' },
                                    { name: 'Left Upper', desc: 'Above clavicle, anterior' },
                                    { name: 'Right Middle', desc: '4th intercostal space, anterior' },
                                    { name: 'Left Middle', desc: '4th intercostal space, anterior' },
                                    { name: 'Right Lower', desc: 'Below 6th rib, midaxillary' },
                                    { name: 'Left Lower', desc: 'Below 6th rib, midaxillary' },
                                ].map((p, i) => (
                                    <div key={i} style={{
                                        padding: '8px 12px', background: 'var(--bg-elevated)',
                                        borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--respiratory-blue)',
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
