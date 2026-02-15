import React from 'react';
import { X, CheckCircle, Smartphone, ArrowRight } from 'lucide-react';

export default function ExamModal({ isOpen, mode, onClose, onViewResults }) {
    if (!isOpen) return null;

    const isResult = mode === 'RESULT';

    return (
        <div className="modal-overlay" style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)', backdropFilter: 'blur(5px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000
        }}>
            <div className="modal-content" style={{
                background: 'var(--bg-primary)', padding: 32, borderRadius: 'var(--radius-lg)',
                maxWidth: 400, width: '90%', textAlign: 'center',
                boxShadow: 'var(--shadow-lg)', border: '1px solid var(--border-default)',
                position: 'relative'
            }}>
                {/* Close button for "Background" dismissal */}
                {!isResult && (
                    <button
                        onClick={onClose}
                        style={{
                            position: 'absolute', top: 16, right: 16,
                            background: 'transparent', border: 'none', cursor: 'pointer',
                            color: 'var(--text-secondary)'
                        }}
                    >
                        <X size={20} />
                    </button>
                )}

                <div style={{
                    width: 80, height: 80, borderRadius: '50%',
                    background: isResult ? 'var(--success-green-glow)' : 'var(--bg-elevated)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 24px',
                    animation: isResult ? 'none' : 'pulse 2s infinite'
                }}>
                    {isResult ? (
                        <CheckCircle size={40} color="var(--success-green)" />
                    ) : (
                        <Smartphone size={40} color="var(--accent-teal)" />
                    )}
                </div>

                <h2 style={{ fontSize: '1.5rem', marginBottom: 12 }}>
                    {isResult ? 'Examination Complete' : 'Testing in Progress...'}
                </h2>

                <p style={{ color: 'var(--text-secondary)', marginBottom: 32, lineHeight: 1.6 }}>
                    {isResult
                        ? 'The hardware device has finished the analysis. You can now view the detailed results.'
                        : 'Please check the hardware OLED display for real-time signal monitoring and status.'
                    }
                </p>

                {isResult ? (
                    <button
                        className="btn btn-primary btn-lg"
                        onClick={onViewResults}
                        style={{ width: '100%', justifyContent: 'center' }}
                    >
                        View Results <ArrowRight size={18} style={{ marginLeft: 8 }} />
                    </button>
                ) : (
                    <button
                        className="btn btn-secondary"
                        onClick={onClose}
                        style={{ width: '100%' }}
                    >
                        Close Popup (Keep Testing)
                    </button>
                )}
            </div>
        </div>
    );
}
