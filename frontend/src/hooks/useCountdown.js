import { useState, useEffect } from 'react';

export function useCountdown(targetDate) {
    const [timeLeft, setTimeLeft] = useState(calculateTimeLeft(targetDate));

    useEffect(() => {
        if (!targetDate) {
            setTimeLeft(null);
            return;
        }

        const timer = setInterval(() => {
            const remaining = calculateTimeLeft(targetDate);
            setTimeLeft(remaining);

            if (remaining.total <= 0) {
                clearInterval(timer);
            }
        }, 1000);

        return () => clearInterval(timer);
    }, [targetDate]);

    return timeLeft;
}

function calculateTimeLeft(targetDate) {
    if (!targetDate) return null;

    const now = new Date().getTime();
    const target = new Date(targetDate).getTime();
    const total = target - now;

    if (total <= 0) {
        return { total: 0, minutes: 0, seconds: 0 };
    }

    const minutes = Math.floor((total % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((total % (1000 * 60)) / 1000);

    return { total, minutes, seconds };
}
