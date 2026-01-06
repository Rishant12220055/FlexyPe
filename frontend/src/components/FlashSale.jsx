import React, { useState, useEffect } from 'react';
import api from '../services/api';
import CountdownTimer from './CountdownTimer';
import '../styles/FlashSale.css';

export default function FlashSale() {
    const [sku, setSku] = useState('FLASH-SALE-001');
    const [quantity, setQuantity] = useState(1);
    const [inventory, setInventory] = useState(null);
    const [reservation, setReservation] = useState(null);
    const [order, setOrder] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        loadInventory();
        const interval = setInterval(loadInventory, 5000); // Refresh every 5 seconds
        return () => clearInterval(interval);
    }, [sku]);

    const loadInventory = async () => {
        try {
            const data = await api.getInventoryStatus(sku);
            setInventory(data);
        } catch (err) {
            console.error('Failed to load inventory:', err);
        }
    };

    const handleInitInventory = async () => {
        setLoading(true);
        setError('');
        try {
            await api.initializeInventory(sku, 100);
            setSuccess('✅ Initialized 100 units for ' + sku);
            await loadInventory();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to initialize inventory');
        } finally {
            setLoading(false);
        }
    };

    const handleReserve = async () => {
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const data = await api.reserveInventory(sku, quantity);
            setReservation(data);
            setSuccess('🎉 Successfully reserved ' + quantity + ' item(s)!');
            await loadInventory();
        } catch (err) {
            const errorData = err.response?.data;

            if (errorData?.status === 409) {
                setError(`❌ Insufficient inventory! Only ${errorData.available} available.`);
            } else if (errorData?.status === 429) {
                setError(`⏱️ Rate limit exceeded. Try again in ${errorData.retry_after}s.`);
            } else {
                setError(errorData?.detail || 'Failed to reserve inventory');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleConfirmCheckout = async () => {
        setLoading(true);
        setError('');

        try {
            const data = await api.confirmCheckout(reservation.reservation_id);
            setOrder(data);
            setReservation(null);
            setSuccess(`🎊 Order confirmed! Order ID: ${data.order_id}`);
        } catch (err) {
            const errorData = err.response?.data;

            if (errorData?.status === 404) {
                setError('❌ Reservation expired. Please reserve again.');
                setReservation(null);
                await loadInventory();
            } else {
                setError(errorData?.detail || 'Failed to confirm checkout');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleCancelReservation = () => {
        setReservation(null);
        setSuccess('');
        setError('');
        loadInventory();
    };

    const handleReservationExpire = () => {
        setError('⏰ Your reservation has expired.');
        setReservation(null);
        loadInventory();
    };

    const currentUser = api.getCurrentUser();

    return (
        <div className="flash-sale-container">
            {/* Header */}
            <header className="flash-sale-header">
                <div className="header-content">
                    <h1 className="header-title">
                        <span className="gradient-text">⚡ Flash Sale</span>
                    </h1>
                    <div className="user-info">
                        <span className="badge badge-success">👤 {currentUser}</span>
                        <button className="btn btn-secondary" onClick={() => {
                            api.logout();
                            window.location.reload();
                        }}>
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="container">
                <div className="flash-sale-grid">
                    {/* Product Section */}
                    <div className="product-section">
                        <div className="card">
                            <div className="product-header">
                                <h2>Limited Edition Product</h2>
                                <span className="badge badge-warning">🔥 HOT DEAL</span>
                            </div>

                            <div className="product-details">
                                <div className="product-image">
                                    <div className="image-placeholder">
                                        <span className="image-icon">📦</span>
                                    </div>
                                </div>

                                <div className="product-info">
                                    <p className="product-sku">SKU: {sku}</p>
                                    <p className="product-price">
                                        <span className="price-old">$49.99</span>
                                        <span className="price-new">$29.99</span>
                                        <span className="price-discount">40% OFF</span>
                                    </p>

                                    {inventory && (
                                        <div className="inventory-status">
                                            <div className="status-bar">
                                                <div
                                                    className="status-fill"
                                                    style={{ width: `${Math.min((inventory.available / 100) * 100, 100)}%` }}
                                                />
                                            </div>
                                            <p className="status-text">
                                                {inventory.available > 0 ? (
                                                    <>
                                                        <span className="text-success">✓ {inventory.available} available</span>
                                                    </>
                                                ) : (
                                                    <span className="text-error">✗ Out of stock</span>
                                                )}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {!inventory && (
                                <div className="init-prompt">
                                    <p className="text-secondary">No inventory initialized yet</p>
                                    <button
                                        className="btn btn-primary"
                                        onClick={handleInitInventory}
                                        disabled={loading}
                                    >
                                        Initialize Inventory (100 units)
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Action Section */}
                    <div className="action-section">
                        {!reservation && !order && (
                            <div className="card">
                                <h3 className="section-title">Reserve Now</h3>

                                <div className="form-group">
                                    <label className="form-label">Quantity</label>
                                    <input
                                        type="number"
                                        className="input"
                                        min="1"
                                        max="5"
                                        value={quantity}
                                        onChange={(e) => setQuantity(Math.min(5, Math.max(1, parseInt(e.target.value) || 1)))}
                                        disabled={loading || !inventory || inventory.available === 0}
                                    />
                                    <p className="form-hint">Maximum 5 items per reservation</p>
                                </div>

                                <button
                                    className="btn btn-primary btn-lg"
                                    onClick={handleReserve}
                                    disabled={loading || !inventory || inventory.available === 0}
                                >
                                    {loading ? (
                                        <>
                                            <span className="spinner animate-spin">⭮</span>
                                            Reserving...
                                        </>
                                    ) : (
                                        <>🛒 Reserve {quantity} Item{quantity > 1 ? 's' : ''}</>
                                    )}
                                </button>
                            </div>
                        )}

                        {reservation && (
                            <div className="card reservation-card">
                                <h3 className="section-title text-success">✓ Reservation Active</h3>

                                <div className="reservation-details">
                                    <p className="reservation-id">
                                        ID: <code>{reservation.reservation_id}</code>
                                    </p>
                                    <p>Quantity: <strong>{reservation.quantity} item(s)</strong></p>
                                    <p>SKU: <strong>{reservation.sku}</strong></p>
                                </div>

                                <CountdownTimer
                                    expiresAt={reservation.expires_at}
                                    onExpire={handleReservationExpire}
                                />

                                <div className="reservation-actions">
                                    <button
                                        className="btn btn-success btn-lg"
                                        onClick={handleConfirmCheckout}
                                        disabled={loading}
                                    >
                                        {loading ? (
                                            <>
                                                <span className="spinner animate-spin">⭮</span>
                                                Processing...
                                            </>
                                        ) : (
                                            <>💳 Confirm Purchase</>
                                        )}
                                    </button>

                                    <button
                                        className="btn btn-secondary"
                                        onClick={handleCancelReservation}
                                        disabled={loading}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}

                        {order && (
                            <div className="card order-card">
                                <h3 className="section-title text-success">🎉 Order Confirmed!</h3>

                                <div className="order-details">
                                    <p className="order-id">
                                        Order ID: <code>{order.order_id}</code>
                                    </p>
                                    <p>Status: <span className="badge badge-success">{order.status}</span></p>
                                    <p>Total: <strong>${order.total.toFixed(2)}</strong></p>

                                    <div className="order-items">
                                        <h4>Items:</h4>
                                        <ul>
                                            {order.items.map((item, idx) => (
                                                <li key={idx}>
                                                    {item.quantity}x {item.sku} @ ${item.price_per_unit.toFixed(2)}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>

                                <button
                                    className="btn btn-primary"
                                    onClick={() => {
                                        setOrder(null);
                                        setSuccess('');
                                        loadInventory();
                                    }}
                                >
                                    Make Another Purchase
                                </button>
                            </div>
                        )}

                        {/* Messages */}
                        {error && (
                            <div className="message message-error animate-slideIn">
                                {error}
                            </div>
                        )}

                        {success && (
                            <div className="message message-success animate-slideIn">
                                {success}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
