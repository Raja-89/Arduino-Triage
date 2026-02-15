import { useState, useEffect, useRef, useCallback } from 'react';
import { useCamera } from '../hooks/useCamera';
import { loadOpenCV, initClassifiers, detectBodyRegion, mapTargetPositions, drawTargetOverlay, drawDetectionOverlay } from '../utils/bodyTracking';
import { Camera, CameraOff, HeartPulse, Wind, Target, Loader, Monitor, RefreshCw, Lightbulb, AlertCircle, CheckCircle2, Hand, Search } from 'lucide-react';

export default function PlacementGuide() {
    const [activeTab, setActiveTab] = useState('heart');
    const [activeTarget, setActiveTarget] = useState(null);
    const [cvLoaded, setCvLoaded] = useState(false);
    const [loadingCV, setLoadingCV] = useState(false);
    const [trackingActive, setTrackingActive] = useState(false);
    const { videoRef, isActive, error, devices, selectedDeviceId, startCamera, stopCamera, switchCamera } = useCamera();
    const canvasRef = useRef(null);
    const animFrameRef = useRef(null);
    const lastDetection = useRef(null);
    const frameCount = useRef(0);
    const [placementFeedback, setPlacementFeedback] = useState({ status: 'idle', message: 'Start camera for placement guidance' });

    // Load OpenCV.js
    const handleLoadCV = useCallback(async () => {
        setLoadingCV(true);
        const loaded = await loadOpenCV();
        if (loaded) {
            initClassifiers();
            setCvLoaded(true);
            setTrackingActive(true);
        }
        setLoadingCV(false);
    }, []);

    // Start camera and begin loading OpenCV
    const handleStartCamera = useCallback(async () => {
        await startCamera();
        if (!cvLoaded && !loadingCV) {
            handleLoadCV();
        }
    }, [startCamera, cvLoaded, loadingCV, handleLoadCV]);

    // Real-time tracking loop
    useEffect(() => {
        if (!isActive) return;

        let running = true;

        const loop = () => {
            if (!running) return;

            const canvas = canvasRef.current;
            const video = videoRef.current;
            if (!canvas || !video || !video.videoWidth) {
                animFrameRef.current = requestAnimationFrame(loop);
                return;
            }

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Run OpenCV detection every 5 frames (for performance)
            frameCount.current++;
            if (cvLoaded && trackingActive && frameCount.current % 5 === 0) {
                const detection = detectBodyRegion(video, canvas);
                if (detection) {
                    lastDetection.current = detection;
                }
            }

            // Draw detection overlay (face box, chest region)
            if (lastDetection.current) {
                drawDetectionOverlay(ctx, lastDetection.current);
            }

            // Map and draw auscultation targets
            const targets = mapTargetPositions(lastDetection.current, canvas.width, canvas.height, activeTab);
            const themeColor = activeTab === 'heart' ? '#E11D48' : '#0EA5E9';
            drawTargetOverlay(ctx, targets, activeTarget, lastDetection.current, themeColor);

            // Update placement feedback based on detection state
            if (lastDetection.current) {
                const det = lastDetection.current;
                const hasHands = det.hands && det.hands.length > 0;
                const activeTargetObj = targets?.find(t => t.id === activeTarget);

                if (hasHands && activeTargetObj) {
                    // Check if any hand is close to the active target
                    const handNearTarget = det.hands.some(hand => {
                        const handCX = hand.x + hand.width / 2;
                        const handCY = hand.y + hand.height / 2;
                        const dist = Math.sqrt((handCX - activeTargetObj.x) ** 2 + (handCY - activeTargetObj.y) ** 2);
                        return dist < 80;
                    });

                    if (handNearTarget) {
                        setPlacementFeedback({ status: 'good', message: `Perfect! Hold stethoscope steady at ${activeTargetObj.label || activeTarget} position` });
                    } else {
                        setPlacementFeedback({ status: 'adjust', message: `Move stethoscope toward the highlighted ${activeTargetObj.label || activeTarget} point` });
                    }
                } else if (det.face) {
                    setPlacementFeedback({ status: 'adjust', message: 'Body detected. Show your hands holding the stethoscope near the chest' });
                } else {
                    setPlacementFeedback({ status: 'searching', message: 'Position yourself facing the camera so your upper body is visible' });
                }
            } else if (isActive && cvLoaded) {
                setPlacementFeedback({ status: 'searching', message: 'Looking for body... Stand 2-3 feet from camera' });
            }

            animFrameRef.current = requestAnimationFrame(loop);
        };

        animFrameRef.current = requestAnimationFrame(loop);

        return () => {
            running = false;
            if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        };
    }, [isActive, cvLoaded, trackingActive, activeTab, activeTarget, videoRef]);

    // Cycle through targets automatically
    useEffect(() => {
        if (!isActive) return;
        const positions = activeTab === 'heart'
            ? ['aortic', 'pulmonic', 'erbs', 'tricuspid', 'mitral']
            : ['ant_r_upper', 'ant_l_upper', 'ant_r_middle', 'ant_l_middle', 'ant_r_lower', 'ant_l_lower'];

        let idx = 0;
        setActiveTarget(positions[0]);
        const interval = setInterval(() => {
            idx = (idx + 1) % positions.length;
            setActiveTarget(positions[idx]);
        }, 4000);
        return () => clearInterval(interval);
    }, [isActive, activeTab]);

    return (
        <div className="page-container">
            <div className="page-header">
                <h1><Target size={28} style={{ color: 'var(--text-primary)', verticalAlign: 'middle', marginRight: 10 }} />Stethoscope Placement Guide</h1>
                <p>Camera-guided positioning with real-time body tracking for accurate auscultation</p>
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
                {/* Camera View */}
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title"><Camera size={16} style={{ marginRight: 6 }} />Camera View</h3>
                        <div className="camera-controls">
                            {/* Camera device selector */}
                            {devices.length > 1 && (
                                <select
                                    className="camera-select"
                                    value={selectedDeviceId || ''}
                                    onChange={(e) => switchCamera(e.target.value)}
                                >
                                    {devices.map((device, i) => (
                                        <option key={device.deviceId} value={device.deviceId}>
                                            {device.label || `Camera ${i + 1}`}
                                        </option>
                                    ))}
                                </select>
                            )}

                            {!isActive ? (
                                <button className="btn btn-primary btn-sm" onClick={handleStartCamera}>
                                    <Camera size={14} /> Start Camera
                                </button>
                            ) : (
                                <button className="btn btn-danger btn-sm" onClick={stopCamera}>
                                    <CameraOff size={14} /> Stop
                                </button>
                            )}
                        </div>
                    </div>
                    <div className="card-body">
                        <div className="camera-container">
                            <video ref={videoRef} autoPlay playsInline muted style={{ display: isActive ? 'block' : 'none' }} />
                            <canvas ref={canvasRef} />

                            {!isActive && (
                                <div style={{
                                    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                                    background: 'var(--bg-elevated)',
                                }}>
                                    <Camera size={48} color="var(--text-muted)" style={{ marginBottom: 16 }} />
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center', padding: '0 20px' }}>
                                        Click "Start Camera" to begin guided stethoscope placement
                                    </p>
                                    {devices.length > 0 && (
                                        <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: 8 }}>
                                            <Monitor size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                                            {devices.length} camera{devices.length !== 1 ? 's' : ''} detected
                                        </p>
                                    )}
                                    {error && (
                                        <p style={{ color: 'var(--cardiac-red)', fontSize: '0.8rem', marginTop: 8, maxWidth: 300, textAlign: 'center' }}>
                                            <AlertCircle size={14} style={{ verticalAlign: 'middle', marginRight: 4, color: 'var(--cardiac-red)' }} />{error}
                                        </p>
                                    )}
                                </div>
                            )}

                            {isActive && (
                                <div className="camera-status">
                                    <div className="status-dot" style={cvLoaded ? {} : { background: 'var(--warning-amber)' }} />
                                    {loadingCV ? 'Loading OpenCV...' : cvLoaded ? 'Tracking Active' : 'Overlay Mode'}
                                </div>
                            )}
                        </div>

                        {/* Status bar under camera */}
                        {isActive && (
                            <div style={{
                                marginTop: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                padding: '10px 16px', background: 'var(--bg-elevated)',
                                borderRadius: 'var(--radius-sm)', fontSize: '0.8rem',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)' }}>
                                    {loadingCV ? (
                                        <>
                                            <Loader size={14} className="breathe" />
                                            Loading OpenCV.js real-time tracking...
                                        </>
                                    ) : cvLoaded ? (
                                        <>
                                            <RefreshCw size={14} style={{ color: 'var(--success-green)' }} />
                                            <span style={{ color: 'var(--success-green)' }}>OpenCV real-time body detection active</span>
                                        </>
                                    ) : (
                                        <>
                                            <Monitor size={14} />
                                            Static overlay mode — OpenCV not loaded
                                        </>
                                    )}
                                </div>
                                {devices.length > 1 && (
                                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                                        {devices.find(d => d.deviceId === selectedDeviceId)?.label || 'Camera'}
                                    </span>
                                )}
                            </div>
                        )}

                        {/* Real-time Placement Feedback */}
                        {isActive && cvLoaded && (
                            <div className={`placement-feedback ${placementFeedback.status}`} style={{ marginTop: 10 }}>
                                {placementFeedback.status === 'good' && <CheckCircle2 size={16} />}
                                {placementFeedback.status === 'adjust' && <Hand size={16} />}
                                {placementFeedback.status === 'searching' && <Search size={16} />}
                                {placementFeedback.message}
                            </div>
                        )}
                    </div>
                </div>

                {/* Instructions */}
                <div>
                    <div className="card" style={{ marginBottom: 20 }}>
                        <div className="card-header">
                            <h3 className="card-title">
                                {activeTab === 'heart'
                                    ? <><HeartPulse size={16} color="var(--cardiac-red)" style={{ marginRight: 6, verticalAlign: 'middle' }} />Heart Auscultation Points</>
                                    : <><Wind size={16} color="var(--respiratory-blue)" style={{ marginRight: 6, verticalAlign: 'middle' }} />Lung Auscultation Points</>}
                            </h3>
                        </div>
                        <div className="card-body">
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.7 }}>
                                {activeTab === 'heart'
                                    ? 'The 5 cardiac auscultation points are used to listen to heart sounds. Each point corresponds to a specific heart valve.'
                                    : 'The 6 anterior lung auscultation points are used to listen to breath sounds in both lungs symmetrically.'}
                            </p>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {(activeTab === 'heart'
                                    ? [
                                        { name: 'Aortic', id: 'aortic', desc: '2nd right intercostal space, right sternal border', color: '#F44336' },
                                        { name: 'Pulmonic', id: 'pulmonic', desc: '2nd left intercostal space, left sternal border', color: '#FFC107' },
                                        { name: "Erb's Point", id: 'erbs', desc: '3rd left intercostal space, left sternal border', color: '#4CAF50' },
                                        { name: 'Tricuspid', id: 'tricuspid', desc: '4th left intercostal space, lower left sternal border', color: '#2196F3' },
                                        { name: 'Mitral (Apex)', id: 'mitral', desc: '5th intercostal space, midclavicular line', color: '#9C27B0' },
                                    ]
                                    : [
                                        { name: 'Right Upper Lobe', id: 'ant_r_upper', desc: 'Above right clavicle, anterior chest', color: '#F44336' },
                                        { name: 'Left Upper Lobe', id: 'ant_l_upper', desc: 'Above left clavicle, anterior chest', color: '#FFC107' },
                                        { name: 'Right Middle', id: 'ant_r_middle', desc: '4th intercostal space, right anterior', color: '#4CAF50' },
                                        { name: 'Left Middle', id: 'ant_l_middle', desc: '4th intercostal space, left anterior', color: '#2196F3' },
                                        { name: 'Right Lower Lobe', id: 'ant_r_lower', desc: 'Below 6th rib, right midaxillary', color: '#9C27B0' },
                                        { name: 'Left Lower Lobe', id: 'ant_l_lower', desc: 'Below 6th rib, left midaxillary', color: '#795548' },
                                    ]
                                ).map(point => (
                                    <div
                                        key={point.id}
                                        onClick={() => setActiveTarget(point.id)}
                                        style={{
                                            padding: '12px 16px',
                                            background: activeTarget === point.id ? 'var(--accent-teal-glow)' : 'var(--bg-elevated)',
                                            borderRadius: 'var(--radius-sm)',
                                            borderLeft: `3px solid ${activeTarget === point.id
                                                ? (activeTab === 'heart' ? 'var(--cardiac-red)' : 'var(--respiratory-blue)')
                                                : 'var(--border-default)'}`,
                                            cursor: 'pointer',
                                            transition: 'all var(--transition-fast)',
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <span style={{ width: 12, height: 12, borderRadius: '50%', background: point.color, display: 'inline-block', flexShrink: 0 }} />
                                            <strong style={{ color: 'var(--text-primary)', fontSize: '0.85rem' }}>{point.name}</strong>
                                            {activeTarget === point.id && (
                                                <span style={{
                                                    marginLeft: 'auto', fontSize: '0.7rem', fontWeight: 600,
                                                    color: activeTab === 'heart' ? 'var(--cardiac-red)' : 'var(--respiratory-blue)',
                                                }}>
                                                    ACTIVE
                                                </span>
                                            )}
                                        </div>
                                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4, paddingLeft: 26 }}>
                                            {point.desc}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Tips */}
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title"><Lightbulb size={16} style={{ marginRight: 6, color: 'var(--warning-amber)' }} />Tips</h3>
                        </div>
                        <div className="card-body" style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                            <ul style={{ paddingLeft: 16 }}>
                                <li>Face the camera and stand at arm's length distance</li>
                                <li>Good lighting improves body detection accuracy</li>
                                <li>The blue dashed box shows face detection, green shows chest region</li>
                                <li>Green circles mark stethoscope placement positions</li>
                                <li>Each point cycles automatically — or click one to jump to it</li>
                                <li>Connect an external camera using the dropdown selector</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
