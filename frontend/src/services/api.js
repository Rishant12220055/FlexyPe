import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class APIClient {
    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Add auth token to requests
        this.client.interceptors.request.use((config) => {
            const token = localStorage.getItem('authToken');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });
    }

    // Auth
    async login(userId) {
        const response = await this.client.post('/auth/login', { user_id: userId });
        const { access_token } = response.data;
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('userId', userId);
        return response.data;
    }

    async register(userId) {
        const response = await this.client.post('/auth/register', { user_id: userId });
        const { access_token } = response.data;
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('userId', userId);
        return response.data;
    }

    logout() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userId');
    }

    isAuthenticated() {
        return !!localStorage.getItem('authToken');
    }

    getCurrentUser() {
        return localStorage.getItem('userId');
    }

    // Inventory
    async getInventoryStatus(sku) {
        const response = await this.client.get(`/inventory/${sku}`);
        return response.data;
    }

    async reserveInventory(sku, quantity, idempotencyKey = null) {
        const headers = {};
        if (idempotencyKey) {
            headers['X-Idempotency-Key'] = idempotencyKey;
        }

        const response = await this.client.post(
            '/inventory/reserve',
            { sku, quantity },
            { headers }
        );
        return response.data;
    }

    async initializeInventory(sku, quantity) {
        const response = await this.client.post(`/inventory/${sku}/initialize`, null, {
            params: { quantity },
        });
        return response.data;
    }

    // Checkout
    async confirmCheckout(reservationId) {
        const response = await this.client.post('/checkout/confirm', {
            reservation_id: reservationId,
        });
        return response.data;
    }

    async cancelReservation(reservationId) {
        const response = await this.client.post('/checkout/cancel', {
            reservation_id: reservationId,
        });
        return response.data;
    }

    async getOrder(orderId) {
        const response = await this.client.get(`/checkout/orders/${orderId}`);
        return response.data;
    }

    // Health
    async healthCheck() {
        const response = await this.client.get('/health', {
            baseURL: '/',
        });
        return response.data;
    }
}

export default new APIClient();
