import { useState, useCallback } from 'react';
import { Camera, HeartPulse, Wind, Target, Stethoscope, CheckCircle2, Circle } from 'lucide-react';
import TrackerModal from '../components/TrackerModal';

export default function PlacementGuide() {
    const [activeTab, setActiveTab] = useState('heart');
    const [showTracker, setShowTracker] = useState(false);

    // Checklists state
    const [visitedHeart, setVisitedHeart] = useState({});
    const [visitedLung, setVisitedLung] = useState({});

    const isHeart = activeTab === 'heart';
    const visited = isHeart ? visitedHeart : visitedLung;

    const heartPoints = [
        { name: 'Aortic', desc: '2nd right intercostal space, right sternal border' },
        { name: 'Pulmonic', desc: '2nd left intercostal space, left sternal border' },
        { name: "Erb's Point", desc: '3rd left intercostal space, left sternal border' },
        { name: 'Tricuspid', desc: '4th left intercostal space, left sternal border' },
        { name: 'Mitral (Apex)', desc: '5th intercostal space, midclavicular line' },
    ];

    const lungPoints = [
        { name: 'Right Apex', desc: 'Infraclavicular, right midclavicular' },
        { name: 'Left Apex', desc: 'Infraclavicular, left midclavicular' },
        { name: 'Right Upper', desc: '2nd intercostal space, anterior' },
        { name: 'Left Upper', desc: '2nd intercostal space, anterior' },
        { name: 'Right Middle', desc: '4th intercostal space, right midclavicular' },
        { name: 'Right Lower', desc: '6th intercostal space, right midclavicular' },
        { name: 'Left Lower', desc: '6th intercostal space, left midclavicular' },
    ];

    const points = isHeart ? heartPoints : lungPoints;
    const totalCount = points.length;
    const doneCount = Object.values(visited).filter(Boolean).length;

    // Stable callback to prevent TrackerModal re-renders
    const handleTrackerUpdate = useCallback((update) => {
        if (update === 'RESET') {
            // We need to know which tab is active inside the callback?
            // Actually activeTab is a dependency.
            // To avoid re-creation when activeTab changes (which is fine, modal re-renders then anyway),
            // we just implement it normally.
            // However, inside the modal loop, we want this to be stable if possible.
            // Since 'activeTab' changes rarely, this is fine.
            // But 'setVisited' depends on 'activeTab' in the render scope.
            // Let's use functional updates carefully.

            // Wait, if activeTab changes, 'setVisited' variable changes (it points to a different setter).
            // So handleTrackerUpdate MUST change.
            // The modal also receives 'mode={activeTab}', so it re-renders anyway.
            // The goal is to avoid re-render when 'visited' changes if not needed?
            // But 'visited' is passed to modal, so modal re-renders when visited changes.
            // Is that a problem?
            // If 'TrackerModal' re-renders, does proper memoization stop children?
            // 'TrackerModal' re-render executes the function body.
            // If 'videoRef.current' is stable, it acts fine.
            // The only issue is if the EFFECT fires again.
            // My previous fix ensured effect only fires on [isOpen, isLoading, mode].
            // So even if 'visited' or 'onUpdate' changes, the camera does NOT restart.
            // So this useCallback is good practice but the fix in TrackerModal was the key.
        }

        // We need to access the current setter based on activeTab
        // We can't use the closure variable 'setVisited' safely if we want to be pure,
        // but since we recreate this callback on activeTab change, it's correct.

        if (activeTab === 'heart') {
            if (update === 'RESET') setVisitedHeart({});
            else setVisitedHeart(prev => ({ ...prev, ...update }));
        } else {
            if (update === 'RESET') setVisitedLung({});
            else setVisitedLung(prev => ({ ...prev, ...update }));
        }
    }, [activeTab]);

    return (
        <div className="page-container">
            <div className="page-header">
                <h1><Target size={28} style={{ color: 'var(--text-primary)', verticalAlign: 'middle', marginRight: 10 }} />Stethoscope Placement Guide</h1>
                <p>AI-powered body tracking with real-time stethoscope placement guidance (Browser Native)</p>
            </div>

            {/* Tab Toggle */}
            <div className="tabs" style={{ marginBottom: 24, maxWidth: 350 }}>
                <button
                    className={`tab ${activeTab === 'heart' ? 'active' : ''}`}
                    onClick={() => setActiveTab('heart')}
                    style={activeTab === 'heart' ? { background: 'var(--cardiac-red)', color: '#fff', borderColor: 'var(--cardiac-red)' } : {}}
                >
                    <HeartPulse size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                    Heart Points
                </button>
                <button
                    className={`tab ${activeTab === 'lung' ? 'active' : ''}`}
                    onClick={() => setActiveTab('lung')}
                    style={activeTab === 'lung' ? { background: 'var(--respiratory-blue)', color: '#fff', borderColor: 'var(--respiratory-blue)' } : {}}
                >
                    <Wind size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                    Lung Points
                </button>
            </div>

            <div className="grid-2">
                {/* Launch Tracker Card */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Camera size={16} style={{ marginRight: 6 }} />Camera Tracker</h3>
                        <span className="risk-badge low">
                            <span className="badge-dot" />
                            Online
                        </span>
                    </div>
                    <div className="card-body" style={{ textAlign: 'center', padding: '40px 20px' }}>
                        <div style={{
                            width: 80, height: 80, borderRadius: '50%',
                            background: 'var(--bg-elevated)', border: `2px solid ${isHeart ? 'var(--cardiac-red)' : 'var(--respiratory-blue)'}`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            margin: '0 auto 20px',
                        }}>
                            {isHeart
                                ? <HeartPulse size={36} color="var(--cardiac-red)" className="heartbeat" />
                                : <Wind size={36} color="var(--respiratory-blue)" />
                            }
                        </div>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 8 }}>
                            {isHeart ? 'Heart' : 'Lung'} Placement Tracker
                        </h3>
                        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.6 }}>
                            Opens a fullscreen camera view with AI-guided auscultation points overlaid on your body.
                            Place your hand on each target to check it off.
                        </p>
                        <button
                            className="btn btn-primary btn-lg"
                            onClick={() => setShowTracker(true)}
                            style={{
                                background: isHeart ? 'var(--cardiac-red)' : 'var(--respiratory-blue)',
                                borderColor: isHeart ? 'var(--cardiac-red)' : 'var(--respiratory-blue)',
                            }}
                        >
                            <Camera size={18} /> Open Camera
                        </button>
                    </div>
                </div>

                {/* Progress / Status Card */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Stethoscope size={16} style={{ marginRight: 6 }} />
                            {isHeart ? 'Cardiac' : 'Lung'} Auscultation Points
                        </h3>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            {doneCount}/{totalCount} checked
                        </span>
                    </div>
                    <div className="card-body">
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {points.map((p, i) => {
                                // Match by name, simple exact match for now as keys are consistent
                                const checked = visited[p.name];
                                return (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'center', gap: 10,
                                        padding: '8px 12px', background: 'var(--bg-elevated)',
                                        borderRadius: 'var(--radius-sm)',
                                        borderLeft: `3px solid ${checked ? 'var(--success-green)' : (isHeart ? 'var(--cardiac-red)' : 'var(--respiratory-blue)')}`,
                                        opacity: checked ? 0.7 : 1,
                                    }}>
                                        {checked
                                            ? <CheckCircle2 size={16} color="var(--success-green)" />
                                            : <Circle size={16} color="var(--text-muted)" />
                                        }
                                        <div>
                                            <strong style={{
                                                fontSize: '0.82rem', color: checked ? 'var(--success-green)' : 'var(--text-primary)',
                                                textDecoration: checked ? 'line-through' : 'none',
                                            }}>{p.name}</strong>
                                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{p.desc}</div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Instructions Card */}
                <div className="card" style={{ gridColumn: '1 / -1' }}>
                    <div className="card-header">
                        <h3 className="card-title">How It Works</h3>
                    </div>
                    <div className="card-body" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
                            <div>
                                <strong style={{ color: 'var(--text-primary)' }}>1. Stand in front of camera</strong><br />
                                Position yourself so your upper body is clearly visible. The AI will detect your pose automatically.
                            </div>
                            <div>
                                <strong style={{ color: 'var(--text-primary)' }}>2. Follow the targets</strong><br />
                                Colored circles appear on your chest at each auscultation point. Place your hand on each target.
                            </div>
                            <div>
                                <strong style={{ color: 'var(--text-primary)' }}>3. Verify alignment</strong><br />
                                When your hand aligns with a target, it turns green and is marked as checked in the progress list.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Fullscreen Tracker Modal */}
            <TrackerModal
                isOpen={showTracker}
                mode={activeTab}
                onClose={() => setShowTracker(false)}
                visited={visited}
                onUpdate={handleTrackerUpdate}
            />
        </div>
    );
}
