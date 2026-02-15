import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import {
    ClipboardList, HeartPulse, Wind, CheckCircle, AlertTriangle,
    XCircle, Info, ChevronDown, ChevronUp, Search, Filter
} from 'lucide-react';

export default function Results() {
    const { data: history, loading } = useApi('/triage/history');
    const [expandedId, setExpandedId] = useState(null);
    const [filterType, setFilterType] = useState('all'); // all, heart, lung
    const [filterRisk, setFilterRisk] = useState('all'); // all, LOW, MEDIUM, HIGH

    const filtered = (history || []).filter(t => {
        if (filterType !== 'all' && t.type !== filterType) return false;
        if (filterRisk !== 'all' && t.riskLevel !== filterRisk) return false;
        return true;
    });

    const getRiskIcon = (level) => {
        switch (level) {
            case 'LOW': return <CheckCircle size={16} color="var(--success-green)" />;
            case 'MEDIUM': return <AlertTriangle size={16} color="var(--warning-amber)" />;
            case 'HIGH': return <XCircle size={16} color="var(--cardiac-red)" />;
            case 'CRITICAL': return <XCircle size={16} color="var(--critical-purple)" />;
            default: return <Info size={16} />;
        }
    };

    const classColors = {
        Normal: 'var(--success-green)',
        Abnormal: 'var(--cardiac-red)',
        Wheeze: 'var(--warning-amber)',
        Crackle: 'var(--cardiac-red)',
        Both: 'var(--critical-purple)',
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1><ClipboardList size={28} style={{ color: 'var(--accent-teal)', verticalAlign: 'middle', marginRight: 10 }} />Triage Results</h1>
                <p>Complete history of all examinations with detailed analysis</p>
            </div>

            {/* Filters */}
            <div className="card" style={{ marginBottom: 24 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        <Filter size={16} /> Filter:
                    </div>

                    <div className="tabs" style={{ flex: 'none' }}>
                        {[
                            { value: 'all', label: 'All Types' },
                            { value: 'heart', label: 'Heart' },
                            { value: 'lung', label: 'Lung' },
                        ].map(opt => (
                            <button
                                key={opt.value}
                                className={`tab ${filterType === opt.value ? 'active' : ''}`}
                                onClick={() => setFilterType(opt.value)}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>

                    <div className="tabs" style={{ flex: 'none' }}>
                        {[
                            { value: 'all', label: 'All Risk' },
                            { value: 'LOW', label: 'Low' },
                            { value: 'MEDIUM', label: 'Medium' },
                            { value: 'HIGH', label: 'High' },
                        ].map(opt => (
                            <button
                                key={opt.value}
                                className={`tab ${filterRisk === opt.value ? 'active' : ''}`}
                                onClick={() => setFilterRisk(opt.value)}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>

                    <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {filtered.length} result{filtered.length !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            {/* Results List */}
            {loading ? (
                <div className="empty-state"><p>Loading results...</p></div>
            ) : filtered.length === 0 ? (
                <div className="card">
                    <div className="empty-state">
                        <div className="empty-icon"><ClipboardList size={36} /></div>
                        <h3>No Results Found</h3>
                        <p>No triage results match your current filters. Try adjusting the filter criteria or perform a new examination.</p>
                    </div>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {filtered.map(triage => {
                        const isExpanded = expandedId === triage.id;
                        return (
                            <div key={triage.id} className="card" style={{ cursor: 'pointer' }} onClick={() => setExpandedId(isExpanded ? null : triage.id)}>
                                {/* Summary row */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                    <div style={{
                                        width: 44, height: 44, borderRadius: 'var(--radius-md)',
                                        background: triage.type === 'heart' ? 'var(--cardiac-red-glow)' : 'var(--respiratory-blue-glow)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                                    }}>
                                        {triage.type === 'heart'
                                            ? <HeartPulse size={22} color="var(--cardiac-red)" />
                                            : <Wind size={22} color="var(--respiratory-blue)" />
                                        }
                                    </div>

                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                            <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{triage.diagnosis}</span>
                                            <span className={`risk-badge ${triage.riskLevel.toLowerCase()}`}>
                                                <span className="badge-dot" />
                                                {triage.riskLevel}
                                            </span>
                                        </div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            {triage.type.charAt(0).toUpperCase() + triage.type.slice(1)} exam &middot; {new Date(triage.timestamp).toLocaleString()} &middot; {(triage.confidence * 100).toFixed(0)}% confidence
                                        </div>
                                    </div>

                                    <div style={{ color: 'var(--text-muted)' }}>
                                        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                    </div>
                                </div>

                                {/* Expanded details */}
                                {isExpanded && (
                                    <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border-default)' }}>
                                        <div className="grid-2" style={{ gap: 16 }}>
                                            {/* Classification */}
                                            <div className="result-panel">
                                                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 12 }}>Classification Scores</h4>
                                                {Object.entries(triage.details?.heartClassification || triage.details?.lungClassification || {}).map(([cls, conf]) => (
                                                    <div className="confidence-bar" key={cls}>
                                                        <span className="confidence-label">{cls}</span>
                                                        <div className="confidence-track">
                                                            <div className="confidence-fill" style={{
                                                                width: `${conf * 100}%`,
                                                                background: classColors[cls] || 'var(--accent-teal)',
                                                            }} />
                                                        </div>
                                                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', minWidth: 45 }}>
                                                            {(conf * 100).toFixed(1)}%
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Vital Signs */}
                                            <div className="result-panel">
                                                <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 12 }}>Recorded Vitals</h4>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                    {triage.details?.temperature != null && (
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                                                            <span style={{ color: 'var(--text-secondary)' }}>Temperature</span>
                                                            <span style={{ fontWeight: 600, color: triage.details.temperature > 38 ? 'var(--cardiac-red)' : 'var(--text-primary)' }}>
                                                                {triage.details.temperature}°C
                                                            </span>
                                                        </div>
                                                    )}
                                                    {triage.details?.heartRate != null && (
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                                                            <span style={{ color: 'var(--text-secondary)' }}>Heart Rate</span>
                                                            <span style={{ fontWeight: 600, color: triage.details.heartRate > 100 ? 'var(--cardiac-red)' : 'var(--text-primary)' }}>
                                                                {triage.details.heartRate} BPM
                                                            </span>
                                                        </div>
                                                    )}
                                                    {triage.details?.respiratoryRate != null && (
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                                                            <span style={{ color: 'var(--text-secondary)' }}>Respiratory Rate</span>
                                                            <span style={{ fontWeight: 600, color: triage.details.respiratoryRate > 25 ? 'var(--cardiac-red)' : 'var(--text-primary)' }}>
                                                                {triage.details.respiratoryRate}/min
                                                            </span>
                                                        </div>
                                                    )}
                                                    {triage.details?.audioLevel != null && (
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                                                            <span style={{ color: 'var(--text-secondary)' }}>Audio Level</span>
                                                            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                                                                {triage.details.audioLevel} dB
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* AI Explanation */}
                                        <div className="result-panel" style={{ marginTop: 12 }}>
                                            <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8 }}>
                                                <Info size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                                                AI Analysis
                                            </h4>
                                            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                {triage.details?.explanation}
                                            </p>
                                            {triage.details?.riskFactors?.length > 0 && (
                                                <div style={{ marginTop: 10 }}>
                                                    <p style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--warning-amber)', marginBottom: 6 }}>
                                                        Risk Factors:
                                                    </p>
                                                    <ul style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', paddingLeft: 16 }}>
                                                        {triage.details.riskFactors.map((f, i) => <li key={i}>{f}</li>)}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
