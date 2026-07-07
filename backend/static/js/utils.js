// js/utils.js - Utility Functions

// Format currency in Indian Rupees
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

// Get category icon
function getCategoryIcon(category) {
    const icons = {
        'Food & Dining': '🍽️',
        'Shopping': '🛍️',
        'Transportation': '🚗',
        'Entertainment': '🎬',
        'Utilities': '💡',
        'Healthcare': '🏥',
        'Education': '📚',
        'Travel': '✈️',
        'Income': '💰',
        'Other': '📌'
    };
    return icons[category] || '📌';
}

// Get category color
function getCategoryColor(category) {
    const colors = {
        'Food & Dining': '#10B981',
        'Shopping': '#8B5CF6',
        'Transportation': '#3B82F6',
        'Entertainment': '#F59E0B',
        'Utilities': '#6B7280',
        'Healthcare': '#EF4444',
        'Education': '#8B5CF6',
        'Travel': '#06B6D4',
        'Income': '#10B981',
        'Other': '#9CA3AF'
    };
    return colors[category] || '#9CA3AF';
}

// Show toast notification
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast-container');
    if (!existing) {
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-width: 360px;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const colors = {
        success: '#10B981',
        error: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6'
    };
    toast.style.cssText = `
        padding: 14px 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
        border-left: 4px solid ${colors[type] || colors.success};
        font-size: 14px;
        font-weight: 500;
        color: #1E293B;
        animation: slideUp 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    `;
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    toast.innerHTML = `${icons[type] || '✅'} ${message}`;
    document.querySelector('.toast-container').appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Add slideUp animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);