import { useState } from 'react';
import { useApi, apiPost } from '../hooks/useApi';
import {
    Settings as SettingsIcon, Cpu, Database, Sliders, RefreshCw,
    CheckCircle, Loader, Server, HardDrive, Clock, Wifi, Brain
} from 'lucide-react';

export default function SettingsPage() {
    const { data: status } = useApi('/status', 3000);
    const { data: models } = useApi('/models');
    const { data: config } = useApi('/config');
    const { data: calStatus, refetch: refetchCal } = useApi('/calibration/status', 1000);
    const [calibrating, setCalibrating] = useState(false);

    const startCalibration = async () => {
        setCalibrating(true);
        await apiPost('/calibration/start');
        // Calibration will be tracked by polling calStatus
    };

    // Reset calibration button when complete
    if (calStatus?.status === 'complete' && calibrating) {
        setTimeout(() => setCalibrating(false), 2000);
    }

    return (
        <div className="page-container">
            <div className="page-header">
                <h1><SettingsIcon size={28} style={{ color: 'var(--accent-teal)', verticalAlign: 'middle', marginRight: 10 }} />Settings & Calibration</h1>
                <p>System configuration, calibration, and model management</p>
            </div>

            <div className="grid-2">
                {/* System Status Panel */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Server size={16} style={{ marginRight: 6 }} />System Status</h3>
                        <span className={`risk-badge ${status?.connected ? 'low' : 'high'}`}>
                            <span className="badge-dot" />
                            {status?.connected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                            {[
                                { icon: Wifi, label: 'Connection', value: status?.connectedPort || 'N/A' },
                                { icon: Cpu, label: 'System Mode', value: status?.mode || 'IDLE' },
                                { icon: Clock, label: 'Uptime', value: status?.uptime ? `${Math.floor(status.uptime / 60)}m ${status.uptime % 60}s` : '--' },
                                { icon: Database, label: 'Total Triages', value: status?.totalTriages || 0 },
                                { icon: Clock, label: 'Last Calibration', value: status?.lastCalibration ? new Date(status.lastCalibration).toLocaleString() : 'Never' },
                            ].map((item, i) => (
                                <div key={i} style={{
                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                    padding: '10px 14px', background: 'var(--bg-secondary)',
                                    borderRadius: 'var(--radius-sm)',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <item.icon size={16} color="var(--text-muted)" />
                                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{item.label}</span>
                                    </div>
                                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{item.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Calibration Panel */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Sliders size={16} style={{ marginRight: 6 }} />Calibration</h3>
                        {calStatus?.status === 'complete' && (
                            <span className="risk-badge low"><span className="badge-dot" />Complete</span>
                        )}
                    </div>
                    <div className="card-body">
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>
                            Calibrate audio sensors and hardware for optimal performance. This process measures
                            ambient noise levels and adjusts sensitivity thresholds.
                        </p>

                        {calStatus?.status === 'running' ? (
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                                    <Loader size={16} className="breathe" color="var(--accent-teal)" />
                                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-teal)' }}>
                                        Calibrating... {calStatus.progress}%
                                    </span>
                                </div>
                                <div className="progress-bar">
                                    <div className="progress-fill" style={{ width: `${calStatus.progress}%` }} />
                                </div>
                            </div>
                        ) : calStatus?.status === 'complete' ? (
                            <div style={{
                                padding: 20, background: 'var(--success-green-glow)',
                                borderRadius: 'var(--radius-md)', textAlign: 'center',
                            }}>
                                <CheckCircle size={32} color="var(--success-green)" style={{ marginBottom: 8 }} />
                                <p style={{ fontWeight: 600, color: 'var(--success-green)' }}>Calibration Complete!</p>
                                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                                    System is calibrated and ready for examinations.
                                </p>
                                <button className="btn btn-secondary btn-sm" onClick={startCalibration} style={{ marginTop: 12 }}>
                                    <RefreshCw size={14} /> Recalibrate
                                </button>
                            </div>
                        ) : (
                            <button className="btn btn-primary btn-lg" onClick={startCalibration} style={{ width: '100%' }}>
                                <Sliders size={18} /> Start Calibration
                            </button>
                        )}

                        <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Calibration Steps:</h4>
                            {[
                                'Ambient noise measurement',
                                'Microphone sensitivity adjustment',
                                'Frequency response calibration',
                                'Sensor baseline establishment',
                                'Validation test',
                            ].map((step, i) => (
                                <div key={i} style={{
                                    display: 'flex', alignItems: 'center', gap: 8,
                                    fontSize: '0.8rem', color: 'var(--text-secondary)',
                                }}>
                                    <span style={{
                                        width: 20, height: 20, borderRadius: '50%',
                                        background: calStatus?.progress > (i + 1) * 20 ? 'var(--success-green-glow)' : 'var(--bg-elevated)',
                                        color: calStatus?.progress > (i + 1) * 20 ? 'var(--success-green)' : 'var(--text-muted)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '0.7rem', fontWeight: 600,
                                    }}>
                                        {calStatus?.progress > (i + 1) * 20 ? '✓' : i + 1}
                                    </span>
                                    {step}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Models Section */}
            <div className="card" style={{ marginTop: 24 }}>
                <div className="card-header">
                    <h3 className="card-title"><Brain size={16} style={{ marginRight: 6 }} />ML Models</h3>
                </div>
                <div className="card-body">
                    <div className="grid-2">
                        {models && Object.entries(models).map(([key, model]) => (
                            <div key={key} style={{
                                padding: 20, background: 'var(--bg-secondary)',
                                borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                                    <h4 style={{ fontSize: '0.9rem', fontWeight: 600 }}>{model.name}</h4>
                                    <span className="risk-badge low"><span className="badge-dot" />{model.status}</span>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                    {[
                                        { label: 'Version', value: model.version },
                                        { label: 'Size', value: model.size },
                                        { label: 'Accuracy', value: model.accuracy },
                                        { label: 'Input', value: model.inputShape },
                                        { label: 'Inference', value: model.inferenceTime },
                                        { label: 'Classes', value: model.classes?.join(', ') },
                                    ].map((item, i) => (
                                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                                            <span style={{ color: 'var(--text-muted)' }}>{item.label}</span>
                                            <span style={{ color: 'var(--text-primary)', fontWeight: 500, textAlign: 'right', maxWidth: '60%' }}>{item.value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Configuration */}
            {config && (
                <div className="card" style={{ marginTop: 24 }}>
                    <div className="card-header">
                        <h3 className="card-title"><HardDrive size={16} style={{ marginRight: 6 }} />Configuration</h3>
                    </div>
                    <div className="card-body">
                        <div className="grid-3">
                            {[
                                {
                                    title: 'Triage Thresholds',
                                    items: Object.entries(config.triage || {}).map(([k, v]) => ({
                                        label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                                        value: v,
                                    })),
                                },
                                {
                                    title: 'Fusion Weights',
                                    items: Object.entries(config.fusionWeights || {}).map(([k, v]) => ({
                                        label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                                        value: `${(v * 100).toFixed(0)}%`,
                                    })),
                                },
                                {
                                    title: 'Audio Settings',
                                    items: Object.entries(config.audio || {}).map(([k, v]) => ({
                                        label: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                                        value: v,
                                    })),
                                },
                            ].map((section, i) => (
                                <div key={i} style={{
                                    padding: 16, background: 'var(--bg-secondary)',
                                    borderRadius: 'var(--radius-md)', border: '1px solid var(--border-default)',
                                }}>
                                    <h4 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 12, color: 'var(--accent-teal)' }}>
                                        {section.title}
                                    </h4>
                                    {section.items.map((item, j) => (
                                        <div key={j} style={{
                                            display: 'flex', justifyContent: 'space-between',
                                            fontSize: '0.8rem', padding: '4px 0',
                                        }}>
                                            <span style={{ color: 'var(--text-muted)' }}>{item.label}</span>
                                            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{String(item.value)}</span>
                                        </div>
                                    ))}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
