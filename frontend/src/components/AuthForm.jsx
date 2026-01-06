import React, { useState } from 'react';
import api from '../services/api';
import '../styles/AuthForm.css';

export default function AuthForm({ onAuthSuccess }) {
    const [userId, setUserId] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e, isRegister = false) => {
        e.preventDefault();

        if (!userId.trim()) {
            setError('Please enter a user ID');
            return;
        }

        setLoading(true);
        setError('');

        try {
            if (isRegister) {
                await api.register(userId);
            } else {
                await api.login(userId);
            }
            onAuthSuccess();
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card card glass">
                <div className="auth-header">
                    <h1 className="auth-title">
                        <span className="gradient-text">FlexyPe</span> Flash Sale
                    </h1>
                    <p className="auth-subtitle">Smart Inventory Reservation System</p>
                </div>

                <form className="auth-form" onSubmit={(e) => handleSubmit(e, false)}>
                    <div className="form-group">
                        <label htmlFor="userId" className="form-label">
                            User ID
                        </label>
                        <input
                            id="userId"
                            type="text"
                            className="input"
                            placeholder="Enter your user ID (e.g., user_123)"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    {error && (
                        <div className="error-message animate-slideIn">
                            ⚠️ {error}
                        </div>
                    )}

                    <div className="auth-actions">
                        <button
                            type="submit"
                            className="btn btn-primary btn-lg"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner animate-spin">⭮</span>
                                    Logging in...
                                </>
                            ) : (
                                'Login'
                            )}
                        </button>

                        <button
                            type="button"
                            className="btn btn-secondary btn-lg"
                            onClick={(e) => handleSubmit(e, true)}
                            disabled={loading}
                        >
                            Register
                        </button>
                    </div>

                    <div className="auth-info">
                        <p className="text-secondary text-center">
                            💡 This is a simplified auth for the hackathon demo
                        </p>
                    </div>
                </form>
            </div>
        </div>
    );
}
