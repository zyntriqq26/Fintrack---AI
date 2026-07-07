// js/app.js - Main Application Controller

// ─── Modal Functions ──────────────────────────────────────────────────────
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// ─── Navigation ──────────────────────────────────────────────────────────
function navigateTo(page) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.toggle('active', section.id === `page-${page}`);
    });

    const titles = {
        dashboard: 'Dashboard',
        transactions: 'Transactions',
        budgets: 'Budgets',
        analytics: 'Analytics',
        chat: 'AI Assistant',
        reports: 'Reports'
    };
    document.getElementById('pageTitle').textContent = titles[page] || page;

    document.getElementById('sidebar').classList.remove('open');

    if (page === 'dashboard') {
        if (typeof loadDashboard === 'function') loadDashboard();
    } else if (page === 'transactions') {
        if (typeof loadTransactions === 'function') loadTransactions(1);
    } else if (page === 'budgets') {
        if (typeof loadBudgets === 'function') loadBudgets();
    } else if (page === 'analytics') {
        if (typeof loadAnalytics === 'function') loadAnalytics();
    } else if (page === 'reports') {
        if (typeof loadReports === 'function') loadReports();
    }
}

// ─── Modal Close Handlers ──────────────────────────────────────────────
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        const modal = btn.closest('.modal');
        if (modal) closeModal(modal.id);
    });
});

document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal(modal.id);
    });
});

// ─── Keyboard Shortcuts ────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.open').forEach(modal => {
            closeModal(modal.id);
        });
    }
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput')?.focus();
    }
});

// ─── Profile Button ──────────────────────────────────────────────────────
// ─── Profile Button ──────────────────────────────────────────────────────
const profileBtn = document.getElementById('profileBtn');
if (profileBtn) {
    profileBtn.addEventListener('click', function() {
        openModal('profileModal');  // Opens the modal
    });
}

// ─── Add Transaction Button ────────────────────────────────────────────
const addBtn = document.getElementById('addTransactionBtn');
if (addBtn) {
    addBtn.addEventListener('click', () => {
        openModal('transactionModal');
    });
}

// ─── Add Budget Button ─────────────────────────────────────────────────
const budgetBtn = document.getElementById('addBudgetBtn');
if (budgetBtn) {
    budgetBtn.addEventListener('click', () => {
        openModal('budgetModal');
    });
}

// ─── DARK MODE TOGGLE ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    console.log('App initializing...');
    
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            navigateTo(this.dataset.page);
        });
    });

    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            document.getElementById('sidebar').classList.toggle('open');
        });
    }

    // ─── DARK MODE ──────────────────────────────────────────────────
    const themeToggle = document.getElementById('themeToggle');
    console.log('Theme toggle button found:', themeToggle);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Theme toggle clicked!');
            
            // Toggle dark class
            document.body.classList.toggle('dark-theme');
            
            // Toggle icon
            const icon = this.querySelector('i');
            if (icon) {
                if (document.body.classList.contains('dark-theme')) {
                    icon.className = 'fas fa-sun';
                    console.log('Switched to Dark mode');
                } else {
                    icon.className = 'fas fa-moon';
                    console.log('Switched to Light mode');
                }
            }
            
            // Save preference
            if (document.body.classList.contains('dark-theme')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
        });
    } else {
        console.error('Theme toggle button NOT found!');
    }

    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    console.log('Saved theme:', savedTheme);
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        const icon = document.querySelector('#themeToggle i');
        if (icon) {
            icon.className = 'fas fa-sun';
        }
        console.log('Loaded Dark mode from storage');
    }

    // Initialize dashboard
    navigateTo('dashboard');
});

// Make functions globally available
window.navigateTo = navigateTo;
window.openModal = openModal;
window.closeModal = closeModal;