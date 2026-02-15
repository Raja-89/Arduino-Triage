import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
    Bell, Wifi, WifiOff, Cpu, Clock, HeartPulse, Wind,
    AlertTriangle, CheckCircle, Info, X, Thermometer, Activity
} from 'lucide-react';

const pageNames = {
    '/': 'Dashboard',
    '/heart-exam': 'Heart Examination',
    '/lung-exam': 'Lung Examination',
    '/placement-guide': 'Stethoscope Placement Guide',
    '/results': 'Triage Results',
    '/settings': 'Settings & Calibration',
};

/**
 * Generate notifications — real-time analysis only shown when hardware is connected.
 * When in demo mode, only show connectivity status.
 */
function generateNotifications(systemStatus, apiOnline) {
    const notifications = [];
    const now = new Date();

    // API offline — show error
    if (!apiOnline) {
        notifications.push({
            id: 'api-offline',
            type: 'error',
            icon: WifiOff,
            title: 'Server Unreachable',
            message: 'Cannot connect to API server. Start with: npm run dev',
            time: 'Now',
            read: false,
        });
        return notifications;
    }

    // API online but no hardware — just show status
    if (!systemStatus?.hardwareConnected) {
        notifications.push({
            id: 'sys-online',
            type: 'info',
            icon: Wifi,
            title: 'System Online — Demo Mode',
            message: 'No Arduino hardware detected. Connect hardware for real-time analysis.',
            time: formatTimeAgo(now, 0),
            read: true,
        });
        return notifications; // No analysis notifications in demo mode
    }

    // ═══ Hardware connected — show full real-time analysis ═══

    notifications.push({
        id: 'hw-connected',
        type: 'success',
        icon: Cpu,
        title: 'Arduino Connected',
        message: `Port: ${systemStatus.connectedPort || 'auto-detected'} — Live data streaming`,
        time: formatTimeAgo(now, 0),
        read: false,
    });

    // Exam in progress
    if (systemStatus?.mode === 'EXAMINING') {
        notifications.push({
            id: 'exam-progress',
            type: 'warning',
            icon: Activity,
            title: 'Examination In Progress',
            message: `Recording audio... ${systemStatus.examProgress || 0}% complete`,
            time: 'Now',
            read: false,
        });
    }

    // Exam result available
    if (systemStatus?.mode === 'RESULT' && systemStatus?.examResult) {
        const result = systemStatus.examResult;
        notifications.push({
            id: 'exam-result',
            type: result.riskLevel === 'LOW' ? 'success' : result.riskLevel === 'HIGH' ? 'error' : 'warning',
            icon: result.type === 'heart' ? HeartPulse : Wind,
            title: `${result.type === 'heart' ? 'Heart' : 'Lung'} Exam Complete`,
            message: `${result.diagnosis} — ${result.riskLevel} risk (${(result.confidence * 100).toFixed(0)}%)`,
            time: 'Just now',
            read: false,
        });
    }

    // Temperature warning — only with real sensor data
    if (systemStatus?.examResult?.details?.temperature > 38) {
        notifications.push({
            id: 'temp-warning',
            type: 'error',
            icon: Thermometer,
            title: 'Elevated Temperature',
            message: `Patient temperature: ${systemStatus.examResult.details.temperature}°C`,
            time: 'Just now',
            read: false,
        });
    }

    // ML Models ready
    if (systemStatus?.modelsLoaded) {
        notifications.push({
            id: 'models-loaded',
            type: 'success',
            icon: CheckCircle,
            title: 'ML Models Ready',
            message: 'Heart & Lung classifiers loaded for inference',
            time: formatTimeAgo(now, 5),
            read: true,
        });
    }

    // Uptime
    if (systemStatus?.uptime) {
        const mins = Math.floor(systemStatus.uptime / 60);
        const secs = systemStatus.uptime % 60;
        notifications.push({
            id: 'uptime',
            type: 'info',
            icon: Clock,
            title: 'System Uptime',
            message: `Running for ${mins}m ${secs}s`,
            time: '',
            read: true,
        });
    }

    return notifications;
}

function formatTimeAgo(now, minutesAgo) {
    if (minutesAgo === 0) return 'Just now';
    if (minutesAgo < 60) return `${minutesAgo}m ago`;
    return `${Math.floor(minutesAgo / 60)}h ago`;
}

const typeColors = {
    success: 'var(--success-green)',
    warning: 'var(--warning-amber)',
    error: 'var(--cardiac-red)',
    info: 'var(--accent-teal)',
};

export default function Navbar({ systemStatus }) {
    const location = useLocation();
    const pageName = pageNames[location.pathname] || 'Dashboard';
    const [showNotifications, setShowNotifications] = useState(false);
    const [apiOnline, setApiOnline] = useState(false);
    const dropdownRef = useRef(null);

    // Real-time connectivity — ping API every 3s
    useEffect(() => {
        let mounted = true;
        const check = async () => {
            try {
                const ctrl = new AbortController();
                const t = setTimeout(() => ctrl.abort(), 2000);
                const res = await fetch('http://localhost:3001/api/status', { signal: ctrl.signal });
                clearTimeout(t);
                if (mounted) setApiOnline(res.ok);
            } catch {
                if (mounted) setApiOnline(false);
            }
        };
        check();
        const id = setInterval(check, 3000);
        return () => { mounted = false; clearInterval(id); };
    }, []);

    useEffect(() => {
        if (systemStatus) setApiOnline(true);
    }, [systemStatus]);

    const isOnline = apiOnline && systemStatus?.connected;
    const hwConnected = systemStatus?.hardwareConnected;
    const notifications = generateNotifications(systemStatus, apiOnline);
    const unreadCount = notifications.filter(n => !n.read).length;

    // Close dropdown on outside click
    useEffect(() => {
        const handle = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setShowNotifications(false);
            }
        };
        document.addEventListener('mousedown', handle);
        return () => document.removeEventListener('mousedown', handle);
    }, []);

    const connectionLabel = !apiOnline
        ? 'Offline'
        : hwConnected
            ? 'Hardware'
            : 'Online';

    return (
        <header className="navbar">
            <div className="navbar-left">
                <div className="navbar-breadcrumb">
                    Smart Triage Station / <span>{pageName}</span>
                </div>
            </div>

            <div className="navbar-right">
                {systemStatus?.mode === 'EXAMINING' && (
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        background: 'rgba(255, 76, 106, 0.15)',
                        padding: '6px 14px', borderRadius: 'var(--radius-full)',
                        fontSize: '0.8rem', fontWeight: 600, color: 'var(--cardiac-red)',
                    }}>
                        <div className="status-dot" style={{ background: 'var(--cardiac-red)', width: 6, height: 6, boxShadow: '0 0 8px rgba(255,76,106,0.5)' }} />
                        Exam in Progress
                    </div>
                )}

                {/* Notification Bell */}
                <div ref={dropdownRef} style={{ position: 'relative' }}>
                    <button
                        className="btn btn-icon btn-ghost tooltip"
                        data-tip="Notifications"
                        onClick={() => setShowNotifications(!showNotifications)}
                        style={{ position: 'relative' }}
                    >
                        <Bell size={18} />
                        {unreadCount > 0 && (
                            <span style={{
                                position: 'absolute', top: 4, right: 4,
                                width: 16, height: 16, borderRadius: '50%',
                                background: 'var(--cardiac-red)', color: '#fff',
                                fontSize: '0.6rem', fontWeight: 700,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                lineHeight: 1,
                            }}>
                                {unreadCount}
                            </span>
                        )}
                    </button>

                    {showNotifications && (
                        <div style={{
                            position: 'absolute', top: '100%', right: 0,
                            marginTop: 8, width: 380,
                            background: 'var(--bg-primary)',
                            border: '1px solid var(--border-default)',
                            borderRadius: 'var(--radius-lg)',
                            boxShadow: 'var(--shadow-xl)',
                            zIndex: 1000,
                            overflow: 'hidden',
                        }}>
                            {/* Header */}
                            <div style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                padding: '14px 16px',
                                borderBottom: '1px solid var(--border-default)',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                                        Notifications
                                    </span>
                                    {unreadCount > 0 && (
                                        <span style={{
                                            padding: '1px 7px', borderRadius: 'var(--radius-full)',
                                            background: 'var(--cardiac-red)', color: '#fff',
                                            fontSize: '0.7rem', fontWeight: 600,
                                        }}>
                                            {unreadCount}
                                        </span>
                                    )}
                                </div>
                                <button
                                    className="btn btn-icon btn-ghost"
                                    onClick={() => setShowNotifications(false)}
                                    style={{ padding: 4 }}
                                >
                                    <X size={16} />
                                </button>
                            </div>

                            {/* System Meta — only show full details when hardware connected */}
                            <div style={{
                                padding: '10px 16px',
                                background: 'var(--bg-secondary)',
                                borderBottom: '1px solid var(--border-default)',
                                display: 'flex', gap: 16, flexWrap: 'wrap',
                                fontSize: '0.72rem', color: 'var(--text-muted)',
                            }}>
                                <span>
                                    <Cpu size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                                    Mode: <strong style={{ color: 'var(--text-primary)' }}>{systemStatus?.mode || 'IDLE'}</strong>
                                </span>
                                <span>
                                    <Activity size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                                    HW: <strong style={{ color: hwConnected ? 'var(--success-green)' : 'var(--text-muted)' }}>
                                        {hwConnected ? 'Connected' : 'Not Connected'}
                                    </strong>
                                </span>
                                {hwConnected && systemStatus?.uptime && (
                                    <span>
                                        <Clock size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                                        {Math.floor(systemStatus.uptime / 60)}m {systemStatus.uptime % 60}s
                                    </span>
                                )}
                            </div>

                            {/* Notification List */}
                            <div style={{ maxHeight: 360, overflowY: 'auto' }}>
                                {notifications.map(notif => (
                                    <div
                                        key={notif.id}
                                        style={{
                                            display: 'flex', gap: 12, padding: '12px 16px',
                                            borderBottom: '1px solid var(--border-subtle)',
                                            background: notif.read ? 'transparent' : 'var(--bg-secondary)',
                                        }}
                                    >
                                        <div style={{
                                            width: 32, height: 32, borderRadius: 'var(--radius-sm)',
                                            background: `${typeColors[notif.type]}15`,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            flexShrink: 0,
                                        }}>
                                            <notif.icon size={16} color={typeColors[notif.type]} />
                                        </div>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{
                                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                                marginBottom: 2,
                                            }}>
                                                <span style={{
                                                    fontWeight: notif.read ? 500 : 600,
                                                    fontSize: '0.82rem', color: 'var(--text-primary)',
                                                }}>
                                                    {notif.title}
                                                </span>
                                                {notif.time && (
                                                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', flexShrink: 0, marginLeft: 8 }}>
                                                        {notif.time}
                                                    </span>
                                                )}
                                            </div>
                                            <p style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
                                                {notif.message}
                                            </p>
                                        </div>
                                        {!notif.read && (
                                            <div style={{ width: 6, height: 6, borderRadius: '50%', background: typeColors[notif.type], flexShrink: 0, marginTop: 6 }} />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Connection Status */}
                <div style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '6px 12px', borderRadius: 'var(--radius-full)',
                    background: isOnline ? 'rgba(102, 187, 106, 0.1)' : 'rgba(255, 76, 106, 0.1)',
                    fontSize: '0.78rem', fontWeight: 600,
                    color: isOnline ? 'var(--success-green)' : 'var(--cardiac-red)',
                    transition: 'all 0.3s ease',
                }}>
                    {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
                    {connectionLabel}
                </div>
            </div>
        </header>
    );
}
