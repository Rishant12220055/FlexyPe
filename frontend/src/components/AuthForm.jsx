import React, { useState } from 'react';
import api from '../services/api';
import '../styles/AuthForm.css';

export default function AuthForm({ onAuthSuccess }) {
    const [isLoginMode, setIsLoginMode] = useState(true);
    const [userId, setUserId] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!userId.trim() || !password.trim()) {
            setError('Please enter both User ID and Password');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setLoading(true);
        setError('');
        setSuccessMsg('');

        try {
            if (isLoginMode) {
                await api.login(userId, password);
                onAuthSuccess();
            } else {
                await api.register(userId, password);
                setSuccessMsg('Registration successful! Logging you in...');
                setTimeout(() => {
                    onAuthSuccess();
                }, 1000);
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    const toggleMode = () => {
        setIsLoginMode(!isLoginMode);
        setError('');
        setSuccessMsg('');
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

                <form className="auth-form" onSubmit={handleSubmit}>
                    <h2 className="form-title" style={{ textAlign: 'center', marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 'bold' }}>
                        {isLoginMode ? 'Welcome Back' : 'Create Account'}
                    </h2>

                    <div className="form-group">
                        <label htmlFor="userId" className="form-label">
                            Username
                        </label>
                        <input
                            id="userId"
                            type="text"
                            className="input"
                            placeholder="Enter username"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password" className="form-label">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            className="input"
                            placeholder="Enter password (min 6 chars)"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            disabled={loading}
                        />
                    </div>

                    {error && (
                        <div className="error-message animate-slideIn">
                            ⚠️ {error}
                        </div>
                    )}

                    {successMsg && (
                        <div className="success-message animate-slideIn" style={{ color: '#4ade80', marginBottom: '1rem', textAlign: 'center' }}>
                            ✅ {successMsg}
                        </div>
                    )}

                    <div className="auth-actions">
                        <button
                            type="submit"
                            className="btn btn-primary btn-lg"
                            disabled={loading}
                            style={{ width: '100%' }}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner animate-spin">⭮</span>
                                    {isLoginMode ? 'Logging in...' : 'Creating Account...'}
                                </>
                            ) : (
                                isLoginMode ? 'Login' : 'Register'
                            )}
                        </button>
                    </div>

                    <div className="auth-footer" style={{ marginTop: '1.5rem', textAlign: 'center', color: '#94a3b8' }}>
                        {isLoginMode ? (
                            <p>
                                Don't have an account?{' '}
                                <button
                                    type="button"
                                    onClick={toggleMode}
                                    style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', textDecoration: 'underline', fontSize: 'inherit' }}
                                >
                                    Register
                                </button>
                            </p>
                        ) : (
                            <p>
                                Already have an account?{' '}
                                <button
                                    type="button"
                                    onClick={toggleMode}
                                    style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', textDecoration: 'underline', fontSize: 'inherit' }}
                                >
                                    Login
                                </button>
                            </p>
                        )}
                    </div>
                </form>
            </div>
        </div>
    );
}
