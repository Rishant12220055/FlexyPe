import React, { useState, useEffect } from 'react';
import AuthForm from './components/AuthForm';
import FlashSale from './components/FlashSale';
import api from './services/api';
import './index.css';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        setIsAuthenticated(api.isAuthenticated());
    }, []);

    const handleAuthSuccess = () => {
        setIsAuthenticated(true);
    };

    return (
        <div className="app">
            {isAuthenticated ? (
                <FlashSale />
            ) : (
                <AuthForm onAuthSuccess={handleAuthSuccess} />
            )}
        </div>
    );
}

export default App;
