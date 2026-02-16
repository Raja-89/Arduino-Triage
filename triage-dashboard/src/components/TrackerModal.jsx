import { useState, useEffect, useRef, useCallback, memo } from 'react';
import { X, RotateCcw, HeartPulse, Wind, CheckCircle2, Circle, Loader, Camera } from 'lucide-react';
import { PoseLandmarker, HandLandmarker, FilesetResolver, DrawingUtils } from '@mediapipe/tasks-vision';
import {
    computeCardiacPoints,
    computeLungPoints,
    dist,
    COLORS,
    px
} from '../utils/trackerLogic';

/**
 * TrackerModal — Client-side real-time tracking using MediaPipe.
 * Now wrapped in memo and protected against race conditions.
 */
function TrackerModal({ isOpen, mode = 'heart', onClose, visited = {}, onUpdate }) {
    const [isLoading, setIsLoading] = useState(true);
    const [cameraError, setCameraError] = useState(null);

    // We use a ref for visited to avoid stale closures in the RequestAnimationFrame loop
    const visitedRef = useRef(visited);

    // Sync ref when prop changes
    useEffect(() => {
        visitedRef.current = visited;
    }, [visited]);

    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const requestRef = useRef(null);
    const poseLandmarkerRef = useRef(null);
    const handLandmarkerRef = useRef(null);
    const lastVideoTimeRef = useRef(-1);

    const isHeart = mode === 'heart';

    // Initialize MediaPipe Models
    useEffect(() => {
        if (!isOpen) return;

        let isMounted = true;

        // If models already loaded, just skip
        if (poseLandmarkerRef.current && handLandmarkerRef.current) {
            setIsLoading(false);
            return;
        }

        const initModels = async () => {
            setIsLoading(true);
            try {
                const vision = await FilesetResolver.forVisionTasks(
                    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
                );

                if (!isMounted) return;

                const pose = await PoseLandmarker.createFromOptions(vision, {
                    baseOptions: {
                        modelAssetPath: `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`,
                        delegate: "GPU"
                    },
                    runningMode: "VIDEO",
                    numPoses: 1,
                    minPoseDetectionConfidence: 0.5,
                    minPosePresenceConfidence: 0.5,
                    minTrackingConfidence: 0.5,
                });

                const hand = await HandLandmarker.createFromOptions(vision, {
                    baseOptions: {
                        modelAssetPath: `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`,
                        delegate: "GPU"
                    },
                    runningMode: "VIDEO",
                    numHands: 2,
                    minHandDetectionConfidence: 0.5,
                    minHandPresenceConfidence: 0.5,
                    minTrackingConfidence: 0.5,
                });

                if (isMounted) {
                    poseLandmarkerRef.current = pose;
                    handLandmarkerRef.current = hand;
                    setIsLoading(false);
                }
            } catch (err) {
                console.error("Error loading models:", err);
                if (isMounted) setCameraError("Failed to load AI models.");
            }
        };

        if (!poseLandmarkerRef.current || !handLandmarkerRef.current) {
            initModels();
        }

        return () => {
            isMounted = false;
        };
    }, [isOpen]);

    // Start Camera & Prediction Loop
    // Merged into one effect to ensure tight lifecycle control
    useEffect(() => {
        if (!isOpen || isLoading) return;

        let stream = null;
        let isMounted = true;
        let animationFrameId = null;

        const loop = () => {
            if (!isMounted) return;
            predictWebcam();
            animationFrameId = requestAnimationFrame(loop);
        };

        const startCamera = async () => {
            try {
                // Stop any existing tracks first to be safe
                if (videoRef.current && videoRef.current.srcObject) {
                    const oldStream = videoRef.current.srcObject;
                    oldStream.getTracks().forEach(t => t.stop());
                }

                stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480 }
                });

                if (!isMounted) {
                    stream.getTracks().forEach(track => track.stop());
                    return;
                }

                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    await videoRef.current.play();
                    // Start loop only after playing
                    loop();
                }
            } catch (err) {
                console.error("Error accessing camera:", err);
                if (isMounted) setCameraError("Camera access denied or unavailable.");
            }
        };

        startCamera();

        return () => {
            isMounted = false;
            if (animationFrameId) cancelAnimationFrame(animationFrameId);
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            if (videoRef.current) {
                videoRef.current.srcObject = null;
            }
        };
    }, [isOpen, isLoading, mode]); // Mode change restarts camera - acceptable

    // Logic for single frame prediction
    // No longer recursive, called by the effect loop
    const predictWebcam = () => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const pose = poseLandmarkerRef.current;
        const hand = handLandmarkerRef.current;

        if (!video || !canvas || !pose || !hand) return;
        if (video.readyState < 2) return; // Wait for video data

        const w = video.videoWidth || 640;
        const h = video.videoHeight || 480;

        // Resize canvas if needed
        if (canvas.width !== w || canvas.height !== h) {
            canvas.width = w;
            canvas.height = h;
        }

        const ctx = canvas.getContext('2d');
        const startTimeMs = performance.now();

        if (video.currentTime !== lastVideoTimeRef.current) {
            lastVideoTimeRef.current = video.currentTime;

            const poseResult = pose.detectForVideo(video, startTimeMs);
            const handResult = hand.detectForVideo(video, startTimeMs);

            ctx.clearRect(0, 0, w, h);
            ctx.drawImage(video, 0, 0, w, h);

            if (poseResult.landmarks && poseResult.landmarks.length > 0) {
                const plm = poseResult.landmarks[0];

                drawSkeleton(ctx, plm, w, h);

                let result;
                if (mode === 'heart') {
                    result = computeCardiacPoints(plm, w, h);
                } else {
                    result = computeLungPoints(plm, w, h);
                }

                const { points, anchors } = result;
                drawTorsoZone(ctx, anchors);

                // Use ref logic
                const currentVisited = visitedRef.current;

                // Determine active order
                let activeOrder = 0;
                const sortedPoints = [...points].sort((a, b) => a.order - b.order);
                for (let p of sortedPoints) {
                    if (!currentVisited[p.name]) {
                        activeOrder = p.order;
                        break;
                    }
                }

                if (isHeart) {
                    drawConnections(ctx, points);
                }

                const handPositions = [];
                if (handResult.landmarks) {
                    for (const hlm of handResult.landmarks) {
                        drawHand(ctx, hlm, w, h);
                        handPositions.push(px(hlm[9], w, h));
                    }
                }

                let newVisits = {};
                let hasChanges = false;

                for (let t of points) {
                    let aligned = false;
                    for (let hp of handPositions) {
                        if (dist(hp, t.pos) < 48) {
                            aligned = true;
                            break;
                        }
                    }

                    // Check if newly visited
                    if (aligned && !currentVisited[t.name]) {
                        newVisits[t.name] = true;
                        hasChanges = true;
                    }

                    const isDone = currentVisited[t.name] || newVisits[t.name];
                    drawTargetPoint(ctx, t, aligned, isDone, isHeart, startTimeMs, activeOrder);

                    if (aligned) {
                        for (let hp of handPositions) {
                            if (dist(hp, t.pos) < 48) {
                                ctx.strokeStyle = isHeart ? COLORS.GREEN_OK_RGB : COLORS.LUNG_ACTIVE_RGB;
                                ctx.lineWidth = 2;
                                ctx.beginPath();
                                ctx.moveTo(hp[0], hp[1]);
                                ctx.lineTo(t.pos[0], t.pos[1]);
                                ctx.stroke();
                                break;
                            }
                        }
                    }
                }

                if (hasChanges && onUpdate) {
                    onUpdate(newVisits);
                }

            } else {
                ctx.font = "bold 24px Inter, sans-serif";
                ctx.fillStyle = COLORS.WHITE;
                ctx.textAlign = "center";
                ctx.fillText("Step into frame", w / 2, h / 2);
                ctx.font = "16px Inter, sans-serif";
                ctx.fillStyle = COLORS.DIM_WHITE;
                ctx.fillText("Ensure upper body is visible", w / 2, h / 2 + 30);
            }
        }
    };

    if (!isOpen) return null;

    const totalCount = isHeart ? 5 : 7;
    const doneCount = Object.values(visited).filter(Boolean).length;
    const progress = Math.round((doneCount / totalCount) * 100);
    const allDone = doneCount >= totalCount;

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            background: 'rgba(0, 0, 0, 0.92)',
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
        }}>
            {/* Top Bar */}
            <div style={{
                position: 'absolute', top: 0, left: 0, right: 0,
                height: 56, display: 'flex', alignItems: 'center',
                justifyContent: 'space-between', padding: '0 20px',
                background: 'rgba(10, 10, 12, 0.85)',
                borderBottom: `1px solid rgba(255,255,255,0.06)`,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {isHeart ? <HeartPulse size={22} color={COLORS.CARDIAC_RED_RGB} /> : <Wind size={22} color={COLORS.ACCENT_CYAN_RGB} />}
                    <span style={{ fontSize: '1rem', fontWeight: 600, color: '#fff' }}>
                        {isHeart ? 'Heart Placement Tracker' : 'Lung Placement Tracker'}
                    </span>
                    <span style={{
                        fontSize: '0.75rem', padding: '3px 10px',
                        borderRadius: 20, fontWeight: 600,
                        background: allDone ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.06)',
                        color: allDone ? '#10B981' : 'rgba(255,255,255,0.5)',
                    }}>
                        {allDone ? 'COMPLETE' : `${doneCount}/${totalCount}`}
                    </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <button onClick={() => onUpdate && onUpdate('RESET')} style={btnStyle}>
                        <RotateCcw size={14} /> Reset
                    </button>
                    <button onClick={onClose} style={closeBtnStyle}>
                        <X size={18} />
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div style={{ position: 'relative', width: 640, height: 480, maxWidth: '100%', borderRadius: 8, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
                {isLoading && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
                        <Loader className="animate-spin" color="#fff" />
                        <span style={{ color: 'rgba(255,255,255,0.6)' }}>Loading AI Models...</span>
                    </div>
                )}

                {cameraError && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
                        <Camera size={32} color="#dc2626" />
                        <span style={{ color: '#dc2626' }}>{cameraError}</span>
                    </div>
                )}

                <video ref={videoRef} playsInline muted style={{ display: 'none' }} />
                <canvas ref={canvasRef} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            </div>

            {/* Bottom Bar */}
            <div style={{
                position: 'absolute', bottom: 0, left: 0, right: 0,
                height: 56, display: 'flex', alignItems: 'center',
                padding: '0 20px', gap: 16,
                background: 'rgba(10, 10, 12, 0.85)',
                borderTop: '1px solid rgba(255,255,255,0.06)',
            }}>
                <div style={{ display: 'flex', gap: 6, flex: 1, flexWrap: 'wrap' }}>
                    <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.9rem' }}>
                        {allDone
                            ? "All points checked. Great job!"
                            : "Align hand with displayed points."}
                    </span>
                </div>

                <div style={{ width: 160, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{
                        flex: 1, height: 6, borderRadius: 3,
                        background: 'rgba(255,255,255,0.08)',
                        overflow: 'hidden',
                    }}>
                        <div style={{
                            width: `${progress}%`, height: '100%',
                            borderRadius: 3, transition: 'width 0.5s ease',
                            background: allDone ? '#10B981' : (isHeart ? COLORS.CARDIAC_RED_RGB : COLORS.ACCENT_CYAN_RGB),
                        }} />
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', minWidth: 32 }}>
                        {progress}%
                    </span>
                </div>
            </div>
        </div>
    );
}

// ─── Drawing Helpers ─────────────────────────────────────────────────────────

function drawSkeleton(ctx, plm, w, h) {
    const skeletonConnections = [[11, 12], [11, 13], [13, 15], [12, 14], [14, 16], [11, 23], [12, 24], [23, 24], [23, 25], [24, 26], [25, 27], [26, 28]];
    ctx.lineWidth = 1;
    ctx.strokeStyle = COLORS.SKELETON;

    for (const [i, j] of skeletonConnections) {
        if (!plm[i] || !plm[j]) continue;
        const p1 = px(plm[i], w, h);
        const p2 = px(plm[j], w, h);
        ctx.beginPath();
        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
        ctx.stroke();
    }
}

function drawHand(ctx, hlm, w, h) {
    const handConnections = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12], [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [17, 18], [18, 19], [19, 20], [0, 17]];
    ctx.lineWidth = 1;
    ctx.strokeStyle = COLORS.HAND;

    for (const [i, j] of handConnections) {
        if (!hlm[i] || !hlm[j]) continue;
        const p1 = px(hlm[i], w, h);
        const p2 = px(hlm[j], w, h);
        ctx.beginPath();
        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
        ctx.stroke();
    }

    ctx.fillStyle = COLORS.HAND_POINT;
    for (let i = 0; i < 21; i++) {
        const p = px(hlm[i], w, h);
        ctx.beginPath();
        ctx.arc(p[0], p[1], 2, 0, 2 * Math.PI);
        ctx.fill();
    }
}

function drawTorsoZone(ctx, { ls, rs, lh, rh }) {
    ctx.fillStyle = "rgba(35, 25, 30, 0.4)";
    ctx.strokeStyle = "rgba(65, 55, 55, 0.8)";
    ctx.lineWidth = 1;

    ctx.beginPath();
    ctx.moveTo(rs[0], rs[1]);
    ctx.lineTo(ls[0], ls[1]);
    ctx.lineTo(lh[0], lh[1]);
    ctx.lineTo(rh[0], rh[1]);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
}

function drawConnections(ctx, points) {
    const sorted = [...points].sort((a, b) => a.order - b.order);
    ctx.strokeStyle = "rgba(50, 40, 40, 0.5)";
    ctx.lineWidth = 1;

    for (let i = 0; i < sorted.length - 1; i++) {
        const p1 = sorted[i].pos;
        const p2 = sorted[i + 1].pos;
        ctx.beginPath();
        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
        ctx.stroke();
    }
}

function drawTargetPoint(ctx, t, aligned, isDone, isHeart, time, activeOrder) {
    const [cx, cy] = t.pos;
    const isActive = t.order === activeOrder;
    const r = 10;

    let color = isHeart ? COLORS.CARDIAC_RED_RGB : COLORS.LUNG_DEFAULT_RGB;

    if (aligned) {
        color = isHeart ? COLORS.GREEN_OK_RGB : COLORS.LUNG_ACTIVE_RGB;
    } else if (isDone) {
        color = isHeart ? COLORS.GREEN_DIM_RGB : COLORS.LUNG_VISITED_RGB;
    } else if (isActive) {
        color = isHeart ? COLORS.CARDIAC_RED_RGB : COLORS.LUNG_DEFAULT_RGB;
    }

    let outerR = r;
    if (aligned) {
        outerR += 3 + Math.abs(Math.sin(time / 200) * 4);
    } else if (isActive) {
        outerR += Math.abs(Math.sin(time / 500) * 3);
    }

    ctx.beginPath();
    ctx.arc(cx, cy, outerR, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(cx, cy, r + 1, 0, 2 * Math.PI);
    ctx.strokeStyle = COLORS.WHITE;
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.strokeStyle = COLORS.DIM_WHITE;
    ctx.beginPath();
    ctx.moveTo(cx - r - 4, cy); ctx.lineTo(cx - r, cy);
    ctx.moveTo(cx + r, cy); ctx.lineTo(cx + r + 4, cy);
    ctx.moveTo(cx, cy - r - 4); ctx.lineTo(cx, cy - r);
    ctx.moveTo(cx, cy + r); ctx.lineTo(cx, cy + r + 4);
    ctx.stroke();

    // Text Label
    ctx.font = "12px Inter, sans-serif";
    ctx.textAlign = "center";

    const text = t.name;
    const metrics = ctx.measureText(text);
    const th = 12;
    const tw = metrics.width;
    const lx = cx;
    const ly = cy - r - 12;

    ctx.fillStyle = COLORS.BG_PANEL;
    roundRect(ctx, lx - tw / 2 - 4, ly - th - 2, tw + 8, th + 6, 4);
    ctx.fill();

    ctx.fillStyle = COLORS.WHITE;
    ctx.fillText(text, lx, ly);

    if (isHeart) {
        ctx.fillStyle = COLORS.WHITE;
        ctx.font = "11px Inter, sans-serif";
        ctx.textBaseline = "middle";
        ctx.fillText(t.order, cx, cy);
        ctx.textBaseline = "alphabetic";
    }
}

function roundRect(ctx, x, y, w, h, r) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
}

const btnStyle = {
    background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)',
    color: '#fff', padding: '6px 14px', borderRadius: 6,
    cursor: 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 6,
};

const closeBtnStyle = {
    background: 'rgba(255,60,60,0.1)', border: '1px solid rgba(255,60,60,0.2)',
    color: '#ff6b6b', padding: '6px 10px', borderRadius: 6,
    cursor: 'pointer', display: 'flex', alignItems: 'center',
};

// Export memoized component to prevent parent re-renders from triggering expensive updates
export default memo(TrackerModal);
