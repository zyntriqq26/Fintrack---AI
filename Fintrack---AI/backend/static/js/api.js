// js/api.js - API Communication Layer

const API_BASE = 'http://127.0.0.1:5000/api';

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Something went wrong');
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

// ─── Dashboard ──────────────────────────────────────────────────────────────
async function getDashboardData() {
    return apiRequest('/dashboard');
}

// ─── Transactions ────────────────────────────────────────────────────────────
async function getTransactions(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/transactions?${query}`);
}

async function addTransaction(data) {
    return apiRequest('/transactions', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function deleteTransaction(id) {
    return apiRequest(`/transactions/${id}`, {
        method: 'DELETE'
    });
}

// ─── Budgets ─────────────────────────────────────────────────────────────────
async function getBudgets() {
    return apiRequest('/budgets');
}

async function setBudget(data) {
    return apiRequest('/budgets', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

// ─── Analytics ──────────────────────────────────────────────────────────────
async function getPredictions() {
    return apiRequest('/predict');
}

async function getRecommendations() {
    return apiRequest('/recommendations');
}

async function getInsights() {
    return apiRequest('/insights');
}

// ─── Chat ────────────────────────────────────────────────────────────────────
async function sendChatMessage(message) {
    return apiRequest('/chat', {
        method: 'POST',
        body: JSON.stringify({ message })
    });
}

// ─── Reports ─────────────────────────────────────────────────────────────────
async function generateReport(month) {
    return `${API_BASE}/report?month=${month}`;
}

// ─── Categories ──────────────────────────────────────────────────────────────
async function getCategories() {
    return apiRequest('/categories');
}