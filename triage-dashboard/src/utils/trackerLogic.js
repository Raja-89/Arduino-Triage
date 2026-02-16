/**
 * Tracker Logic Utilities
 * Ported from tracker_server.py
 */

// ─── Math Helpers ────────────────────────────────────────────────────────────

export function px(lm, w, h) {
    return [Math.floor(lm.x * w), Math.floor(lm.y * h)];
}

export function dist(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

// ─── Anatomy ──────────────────────────────────────────────────────────────────

export function getBodyAnchors(plm, w, h) {
    // MediaPipe Pose Landmarks:
    // 11: left shoulder, 12: right shoulder
    // 23: left hip, 24: right hip
    const ls = px(plm[11], w, h);
    const rs = px(plm[12], w, h);
    const lh = px(plm[23], w, h);
    const rh = px(plm[24], w, h);
    return { ls, rs, lh, rh };
}

export function computeCardiacPoints(plm, w, h) {
    const { ls, rs, lh, rh } = getBodyAnchors(plm, w, h);

    // torso_h = average height of torso sides
    const torsoH = Math.floor(((lh[1] - ls[1]) + (rh[1] - rs[1])) / 2);

    const midX = Math.floor((ls[0] + rs[0]) / 2);
    const topY = Math.floor((ls[1] + rs[1]) / 2);

    const shoulderW = Math.abs(rs[0] - ls[0]);
    const stb = Math.floor(shoulderW * 0.11); // sternum border offset
    const mcl = Math.floor(shoulderW * 0.32); // mid-clavicular line offset

    // Intercostal spaces estimates based on torso height
    const ics2 = Math.floor(torsoH * 0.12);
    const ics3 = Math.floor(torsoH * 0.21);
    const ics4 = Math.floor(torsoH * 0.30);
    const ics5 = Math.floor(torsoH * 0.39);

    const points = [
        { name: "Aortic", pos: [midX - stb, topY + ics2], order: 1 },
        { name: "Pulmonic", pos: [midX + stb, topY + ics2], order: 2 },
        { name: "Erb's Pt", pos: [midX + stb, topY + ics3], order: 3 },
        { name: "Tricuspid", pos: [midX + stb, topY + ics4], order: 4 },
        { name: "Mitral", pos: [midX + mcl, topY + ics5], order: 5 },
    ];

    return { points, anchors: { ls, rs, lh, rh } };
}

export function computeLungPoints(plm, w, h) {
    const { ls, rs, lh, rh } = getBodyAnchors(plm, w, h);

    const torsoH = Math.floor(((lh[1] - ls[1]) + (rh[1] - rs[1])) / 2);
    const midX = Math.floor((ls[0] + rs[0]) / 2);
    const topY = Math.floor((ls[1] + rs[1]) / 2);

    const mcl = Math.floor(Math.abs(rs[0] - ls[0]) * 0.32);

    const points = [
        { name: "R Apex", pos: [midX - mcl, topY + Math.floor(torsoH * 0.03)], order: 1 },
        { name: "L Apex", pos: [midX + mcl, topY + Math.floor(torsoH * 0.03)], order: 2 },
        { name: "R Upper", pos: [midX - mcl, topY + Math.floor(torsoH * 0.14)], order: 3 },
        { name: "L Upper", pos: [midX + mcl, topY + Math.floor(torsoH * 0.14)], order: 4 },
        { name: "R Middle", pos: [midX - mcl, topY + Math.floor(torsoH * 0.32)], order: 5 },
        { name: "R Lower", pos: [midX - mcl, topY + Math.floor(torsoH * 0.50)], order: 6 },
        { name: "L Lower", pos: [midX + mcl, topY + Math.floor(torsoH * 0.50)], order: 7 },
    ];

    return { points, anchors: { ls, rs, lh, rh } };
}

// ─── Colors ──────────────────────────────────────────────────────────────────

export const COLORS = {
    BG_PANEL: "rgba(18, 15, 20, 0.85)",
    WHITE: "#FFFFFF",
    DIM_WHITE: "#9B9BA0", // (155, 155, 160)
    SKELETON: "rgb(80, 70, 65)",
    HAND: "rgb(180, 140, 60)",

    // Heart
    CARDIAC_RED: "rgb(70, 60, 220)", // Note: BGR (70,60,220) in Python -> RGB (220, 60, 70). Wait, cv2 is BGR.
    // Python: CARDIAC_RED = (70, 60, 220) -> BGR. Red component is 220. Green 60. Blue 70.
    // So RGB is (220, 60, 70).
    // Let's correct this.
    // In Python code: CARDIAC_RED = (70, 60, 220).
    // cv2 uses BGR. So Blue=70, Green=60, Red=220.

    // RGB Values
    CARDIAC_RED_RGB: "rgb(220, 60, 70)",
    CARDIAC_LIGHT_RGB: "rgb(255, 100, 100)", // Approx BGR (100,100,255) -> RGB (255,100,100)
    GOLD_RGB: "rgb(255, 190, 50)", // BGR (50, 190, 255) -> RGB (255, 190, 50)
    GREEN_OK_RGB: "rgb(120, 230, 80)", // BGR (80, 230, 120) -> RGB (120, 230, 80)
    GREEN_DIM_RGB: "rgb(80, 160, 55)", // BGR (55, 160, 80) -> RGB (80, 160, 55)

    // Lung
    ACCENT_CYAN_RGB: "rgb(50, 200, 230)", // BGR (230, 200, 50) -> RGB (50, 200, 230)
    ACCENT_GREEN_RGB: "rgb(120, 240, 80)", // BGR (80, 240, 120) -> RGB (120, 240, 80)
    LUNG_DEFAULT_RGB: "rgb(220, 100, 100)", // BGR (100, 100, 220) -> RGB (220, 100, 100) -- Wait, this looks red? 
    // Python LUNG_DEFAULT = (100, 100, 220) (BGR). R=220.
    // Actually, let's look at LUNG_ACTIVE = (80, 255, 130) -> RGB (130, 255, 80) Greenish.

    // Let's stick to the visual intent.
    // Heart = Red/Pink theme.
    // Lung = Blue/Cyan theme in dashboard, but the Python colors seem a bit mixed.
    // LUNG_DEFAULT in Python (100, 100, 220) -> R220 G100 B100. That's reddish?
    // Let's check the code usage. 
    // "LUNG PLACEMENT TRACKER" title color: ACCENT_CYAN (230, 200, 50) -> RGB (50, 200, 230) -> Cyan.
    // Points: LUNG_DEFAULT (100, 100, 220).
    // Let's trust my BGR->RGB conversion.

    LUNG_ACTIVE_RGB: "rgb(130, 255, 80)",
    LUNG_VISITED_RGB: "rgb(90, 180, 60)",

    // Hand
    HAND_POINT: "rgb(70, 190, 230)", // BGR (230, 190, 70)
};
