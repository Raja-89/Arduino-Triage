import { HEART_POSITIONS, LUNG_POSITIONS_ANTERIOR } from './constants';

/**
 * OpenCV.js-based body tracking for stethoscope placement guidance.
 *
 * Detects:
 *  1. Face (Haar cascade) — anchor for estimating chest/torso region
 *  2. Hands (skin-color segmentation + contour analysis) — tracks hand
 *     position to guide stethoscope placement
 *
 * Draws overlay showing face box, chest region, hand contours,
 * and proximity indicators between hand and auscultation targets.
 */

let cvReady = false;
let cvLoading = false;
let classifierLoaded = false;
let faceCascade = null;

// ── Load OpenCV.js from CDN ──────────────────────────────────

export async function loadOpenCV() {
    if (cvReady) return true;
    if (cvLoading) {
        return new Promise((resolve) => {
            const check = setInterval(() => {
                if (cvReady) { clearInterval(check); resolve(true); }
            }, 200);
            setTimeout(() => { clearInterval(check); resolve(false); }, 15000);
        });
    }

    cvLoading = true;

    return new Promise((resolve) => {
        window.Module = {
            onRuntimeInitialized: () => {
                cvReady = true;
                cvLoading = false;
                console.log('OpenCV.js loaded successfully');
                resolve(true);
            }
        };

        const script = document.createElement('script');
        script.src = 'https://docs.opencv.org/4.9.0/opencv.js';
        script.async = true;
        script.onerror = () => {
            cvLoading = false;
            console.warn('Failed to load OpenCV.js');
            resolve(false);
        };
        document.head.appendChild(script);
    });
}

// ── Classifier setup ──────────────────────────────────────────

function initClassifiers() {
    if (classifierLoaded || !cvReady || !window.cv) return false;

    try {
        const cv = window.cv;
        faceCascade = new cv.CascadeClassifier();
        faceCascade.load('haarcascade_frontalface_default');
        classifierLoaded = true;
        return true;
    } catch (err) {
        console.warn('Classifier init failed, using fallback mode:', err.message);
        return false;
    }
}

// ── Skin-color hand detection helper ──────────────────────────

function detectHands(cv, frame) {
    const hands = [];
    try {
        // Convert to HSV for skin detection
        const hsv = new cv.Mat();
        cv.cvtColor(frame, hsv, cv.COLOR_RGBA2RGB);
        const rgb = hsv.clone();
        cv.cvtColor(rgb, hsv, cv.COLOR_RGB2HSV);
        rgb.delete();

        // Skin-color range in HSV (covers most skin tones)
        const low = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [0, 30, 60, 0]);
        const high = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [25, 180, 255, 255]);
        const mask = new cv.Mat();
        cv.inRange(hsv, low, high, mask);

        // Morphological cleanup — remove noise, fill gaps
        const kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, new cv.Size(7, 7));
        cv.morphologyEx(mask, mask, cv.MORPH_OPEN, kernel);
        cv.morphologyEx(mask, mask, cv.MORPH_CLOSE, kernel);
        cv.dilate(mask, mask, kernel, new cv.Point(-1, -1), 2);

        // Find contours
        const contours = new cv.MatVector();
        const hierarchy = new cv.Mat();
        cv.findContours(mask, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);

        // Filter for hand-sized contours (skip face-sized ones)
        const frameArea = frame.rows * frame.cols;
        for (let i = 0; i < contours.size(); i++) {
            const contour = contours.get(i);
            const area = cv.contourArea(contour);
            const areaRatio = area / frameArea;

            // Hands are typically 1-8% of frame area
            if (areaRatio > 0.008 && areaRatio < 0.08) {
                const rect = cv.boundingRect(contour);
                const aspectRatio = rect.width / rect.height;
                // Hands have relatively square-ish bounding boxes or slightly tall
                if (aspectRatio > 0.3 && aspectRatio < 3.0) {
                    hands.push({
                        x: rect.x,
                        y: rect.y,
                        w: rect.width,
                        h: rect.height,
                        centerX: rect.x + rect.width / 2,
                        centerY: rect.y + rect.height / 2,
                        area: area,
                        contourIdx: i,
                    });
                }
            }
        }

        // Sort by area descending, keep top 2 (two hands max)
        hands.sort((a, b) => b.area - a.area);
        if (hands.length > 2) hands.length = 2;

        // Cleanup
        hsv.delete(); low.delete(); high.delete();
        mask.delete(); kernel.delete();
        contours.delete(); hierarchy.delete();
    } catch (err) {
        console.warn('Hand detection error:', err.message);
    }
    return hands;
}

// ── Main detection: face + hands ──────────────────────────────

export function detectBodyRegion(videoElement, canvasElement) {
    if (!cvReady || !window.cv || !videoElement || !canvasElement) return null;

    const cv = window.cv;

    try {
        const cap = new cv.VideoCapture(videoElement);
        const frame = new cv.Mat(videoElement.videoHeight, videoElement.videoWidth, cv.CV_8UC4);
        cap.read(frame);

        // ── Face detection ──
        const gray = new cv.Mat();
        cv.cvtColor(frame, gray, cv.COLOR_RGBA2GRAY);
        cv.equalizeHist(gray, gray);

        let bodyRegion = null;

        if (faceCascade && classifierLoaded) {
            const faces = new cv.RectVector();
            faceCascade.detectMultiScale(gray, faces, 1.1, 4, 0,
                new cv.Size(60, 60), new cv.Size(0, 0));

            if (faces.size() > 0) {
                let bestFace = faces.get(0);
                for (let i = 1; i < faces.size(); i++) {
                    const f = faces.get(i);
                    if (f.width * f.height > bestFace.width * bestFace.height) {
                        bestFace = f;
                    }
                }

                const chestY = bestFace.y + bestFace.height * 1.2;
                const chestH = bestFace.height * 2.5;
                const chestW = bestFace.width * 2.2;
                const chestX = bestFace.x + bestFace.width / 2 - chestW / 2;

                bodyRegion = {
                    faceX: bestFace.x,
                    faceY: bestFace.y,
                    faceW: bestFace.width,
                    faceH: bestFace.height,
                    chestX, chestY, chestW, chestH,
                    detected: true,
                };
            }
            faces.delete();
        }

        // ── Hand detection ──
        const hands = detectHands(cv, frame);

        // Cleanup
        frame.delete();
        gray.delete();

        // Attach hands to body region
        if (bodyRegion) {
            bodyRegion.hands = hands;
        } else if (hands.length > 0) {
            // Even without face, if we see hands, return partial detection
            bodyRegion = { detected: false, hands };
        }

        return bodyRegion;
    } catch (err) {
        console.warn('Detection frame error:', err.message);
        return null;
    }
}

// ── Map target positions ──────────────────────────────────────

export function mapTargetPositions(bodyRegion, canvasWidth, canvasHeight, type = 'heart') {
    const positions = type === 'heart' ? HEART_POSITIONS : LUNG_POSITIONS_ANTERIOR;

    if (bodyRegion && bodyRegion.detected) {
        const { chestX, chestY, chestW, chestH } = bodyRegion;

        return positions.map(pos => ({
            ...pos,
            screenX: chestX + pos.x * chestW,
            screenY: chestY + (pos.y - 0.25) * chestH,
            tracked: true,
        }));
    }

    // Fallback: static positions relative to canvas center
    return positions.map(pos => ({
        ...pos,
        screenX: pos.x * canvasWidth,
        screenY: pos.y * canvasHeight,
        tracked: false,
    }));
}

// ── Draw detection overlay (face + chest + hands) ─────────────

export function drawDetectionOverlay(ctx, bodyRegion) {
    if (!bodyRegion) return;

    if (bodyRegion.detected) {
        // Face rectangle
        ctx.strokeStyle = 'rgba(30, 136, 229, 0.6)';
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);
        ctx.strokeRect(bodyRegion.faceX, bodyRegion.faceY, bodyRegion.faceW, bodyRegion.faceH);
        ctx.setLineDash([]);

        // Chest region outline
        ctx.strokeStyle = 'rgba(0, 150, 136, 0.4)';
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 4]);
        ctx.strokeRect(bodyRegion.chestX, bodyRegion.chestY, bodyRegion.chestW, bodyRegion.chestH);
        ctx.setLineDash([]);

        // Label — no emoji
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        const label = 'Body Tracked';
        const tw = ctx.measureText(label).width;
        ctx.fillRect(bodyRegion.faceX, bodyRegion.faceY - 22, tw + 12, 18);
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(label, bodyRegion.faceX + 6, bodyRegion.faceY - 8);
    }

    // Draw hands
    if (bodyRegion.hands && bodyRegion.hands.length > 0) {
        bodyRegion.hands.forEach((hand, idx) => {
            // Hand bounding box
            ctx.strokeStyle = idx === 0 ? 'rgba(255, 152, 0, 0.8)' : 'rgba(233, 30, 99, 0.8)';
            ctx.lineWidth = 2;
            ctx.setLineDash([4, 3]);
            ctx.strokeRect(hand.x, hand.y, hand.w, hand.h);
            ctx.setLineDash([]);

            // Hand center dot
            ctx.beginPath();
            ctx.arc(hand.centerX, hand.centerY, 6, 0, Math.PI * 2);
            ctx.fillStyle = idx === 0 ? 'rgba(255, 152, 0, 0.6)' : 'rgba(233, 30, 99, 0.6)';
            ctx.fill();
            ctx.strokeStyle = '#FFF';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Label
            ctx.font = 'bold 10px Inter, sans-serif';
            ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
            const hl = `Hand ${idx + 1}`;
            const htw = ctx.measureText(hl).width;
            ctx.fillRect(hand.x, hand.y - 16, htw + 8, 14);
            ctx.fillStyle = '#FFF';
            ctx.fillText(hl, hand.x + 4, hand.y - 5);
        });
    }
}

// ── Draw auscultation target overlay ──────────────────────────

export function drawTargetOverlay(ctx, targets, activeTargetId = null, bodyRegion = null) {
    // Get hand positions for proximity check
    const hands = bodyRegion?.hands || [];

    targets.forEach(target => {
        const isActive = target.id === activeTargetId;

        // Check if any hand is near this target
        let handNear = false;
        let handDistance = Infinity;
        hands.forEach(hand => {
            const dx = hand.centerX - target.screenX;
            const dy = hand.centerY - target.screenY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < handDistance) handDistance = dist;
            if (dist < 60) handNear = true;
        });

        const radius = isActive ? 28 : handNear ? 24 : 20;

        // Pulsing outer ring for active target or hand-near target
        if (isActive || handNear) {
            ctx.beginPath();
            ctx.arc(target.screenX, target.screenY, radius + 10, 0, Math.PI * 2);
            ctx.strokeStyle = handNear
                ? 'rgba(76, 175, 80, 0.5)'
                : 'rgba(67, 160, 71, 0.3)';
            ctx.lineWidth = handNear ? 3 : 2;
            ctx.stroke();
        }

        // Solid circle fill
        ctx.beginPath();
        ctx.arc(target.screenX, target.screenY, radius, 0, Math.PI * 2);
        ctx.fillStyle = handNear
            ? 'rgba(76, 175, 80, 0.35)'
            : isActive
                ? 'rgba(67, 160, 71, 0.25)'
                : 'rgba(0, 150, 136, 0.15)';
        ctx.fill();
        ctx.strokeStyle = handNear ? '#4CAF50' : isActive ? '#43A047' : '#009688';
        ctx.lineWidth = handNear ? 3 : isActive ? 3 : 2;
        ctx.stroke();

        // Crosshair
        ctx.beginPath();
        ctx.moveTo(target.screenX - 8, target.screenY);
        ctx.lineTo(target.screenX + 8, target.screenY);
        ctx.moveTo(target.screenX, target.screenY - 8);
        ctx.lineTo(target.screenX, target.screenY + 8);
        ctx.strokeStyle = handNear ? '#4CAF50' : isActive ? '#43A047' : '#009688';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Label background
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.textAlign = 'center';
        const labelY = target.screenY + radius + 18;
        const labelText = handNear ? `${target.label} ✓` : target.label;
        const textWidth = ctx.measureText(labelText).width;
        ctx.fillStyle = handNear ? 'rgba(76, 175, 80, 0.85)' : 'rgba(0, 0, 0, 0.75)';
        ctx.fillRect(target.screenX - textWidth / 2 - 6, labelY - 11, textWidth + 12, 16);

        // Label text
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(labelText, target.screenX, labelY);

        // Tracking indicator (small green dot)
        if (target.tracked) {
            ctx.beginPath();
            ctx.arc(target.screenX + radius - 2, target.screenY - radius + 2, 4, 0, Math.PI * 2);
            ctx.fillStyle = '#43A047';
            ctx.fill();
        }
    });
}

export { initClassifiers };
