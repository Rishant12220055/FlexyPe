import React from 'react';
import { useCountdown } from '../hooks/useCountdown';
import '../styles/CountdownTimer.css';

export default function CountdownTimer({ expiresAt, onExpire }) {
    const timeLeft = useCountdown(expiresAt);

    React.useEffect(() => {
        if (timeLeft && timeLeft.total <= 0 && onExpire) {
            onExpire();
        }
    }, [timeLeft, onExpire]);

    if (!timeLeft || timeLeft.total <= 0) {
        return (
            <div className="countdown-timer expired">
                <span className="countdown-label">Expired</span>
            </div>
        );
    }

    const isLowTime = timeLeft.total < 60000; // Less than 1 minute

    return (
        <div className={`countdown-timer ${isLowTime ? 'low-time' : ''}`}>
            <div className="countdown-label">
                {isLowTime ? '⏰ Hurry! ' : '⏱️ '} Time Remaining
            </div>
            <div className="countdown-display">
                <div className="countdown-unit">
                    <span className="countdown-value">{String(timeLeft.minutes).padStart(2, '0')}</span>
                    <span className="countdown-text">min</span>
                </div>
                <span className="countdown-separator">:</span>
                <div className="countdown-unit">
                    <span className="countdown-value">{String(timeLeft.seconds).padStart(2, '0')}</span>
                    <span className="countdown-text">sec</span>
                </div>
            </div>
        </div>
    );
}
