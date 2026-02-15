import { useState, useEffect, useRef, useCallback } from 'react';

export function useCamera() {
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const [isActive, setIsActive] = useState(false);
    const [error, setError] = useState(null);
    const [devices, setDevices] = useState([]);
    const [selectedDeviceId, setSelectedDeviceId] = useState(null);

    // List available cameras — must request permission first to get labels
    const refreshDevices = useCallback(async () => {
        try {
            const allDevices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = allDevices.filter(d => d.kind === 'videoinput');
            setDevices(videoDevices);
            return videoDevices;
        } catch {
            return [];
        }
    }, []);

    // Try to enumerate on mount (labels won't be available until permission is granted)
    useEffect(() => {
        refreshDevices();
        // Re-enumerate when devices change (e.g. USB camera plugged in)
        navigator.mediaDevices?.addEventListener('devicechange', refreshDevices);
        return () => {
            navigator.mediaDevices?.removeEventListener('devicechange', refreshDevices);
        };
    }, [refreshDevices]);

    const startCamera = useCallback(async (deviceId = null) => {
        try {
            setError(null);

            // Stop any existing stream first
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }

            const targetDeviceId = deviceId || selectedDeviceId;
            const constraints = {
                video: targetDeviceId
                    ? { deviceId: { exact: targetDeviceId }, width: { ideal: 640 }, height: { ideal: 480 } }
                    : { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false,
            };

            const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
            streamRef.current = mediaStream;
            setIsActive(true);

            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
                await videoRef.current.play();
            }

            // After getting permission, refresh to get proper labels
            const updatedDevices = await refreshDevices();

            // Record which device we're actually using
            const activeTrack = mediaStream.getVideoTracks()[0];
            const activeSettings = activeTrack?.getSettings();
            if (activeSettings?.deviceId) {
                setSelectedDeviceId(activeSettings.deviceId);
            } else if (!targetDeviceId && updatedDevices.length > 0) {
                setSelectedDeviceId(updatedDevices[0].deviceId);
            }

        } catch (err) {
            console.error('Camera error:', err);
            if (err.name === 'NotAllowedError') {
                setError('Camera permission denied. Please allow camera access in browser settings.');
            } else if (err.name === 'NotFoundError') {
                setError('No camera found on this device.');
            } else if (err.name === 'NotReadableError') {
                setError('Camera is in use by another application.');
            } else {
                setError(err.message || 'Cannot access camera');
            }
            setIsActive(false);
        }
    }, [selectedDeviceId, refreshDevices]);

    const switchCamera = useCallback(async (deviceId) => {
        setSelectedDeviceId(deviceId);
        if (isActive) {
            await startCamera(deviceId);
        }
    }, [isActive, startCamera]);

    const stopCamera = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setIsActive(false);
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
    }, []);

    // Auto-detect the built-in camera on first mount and select it
    useEffect(() => {
        if (devices.length > 0 && !selectedDeviceId) {
            // Prefer built-in/integrated cameras first
            const builtIn = devices.find(d =>
                d.label.toLowerCase().includes('built-in') ||
                d.label.toLowerCase().includes('integrated') ||
                d.label.toLowerCase().includes('internal') ||
                d.label.toLowerCase().includes('facetime')
            );
            setSelectedDeviceId(builtIn ? builtIn.deviceId : devices[0].deviceId);
        }
    }, [devices, selectedDeviceId]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    return {
        videoRef,
        isActive,
        error,
        devices,
        selectedDeviceId,
        startCamera,
        stopCamera,
        switchCamera,
    };
}
