// js/dashboard.js - Dashboard Logic

let categoryChartInstance = null;
let trendChartInstance = null;

async function loadDashboard() {
    try {
        const data = await getDashboardData();
        console.log('Dashboard data:', data); // Debug log
        
        if (data) {
            updateSummaryCards(data);
            updateCategoryChart(data.categories || []);
            updateTrendChart(data.monthly_trend || []);
            updateRecentTransactions(data.recent_transactions || []);
            updateBudgetOverview(data.budgets || []);
        }
    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showToast('Failed to load dashboard data', 'error');
        
        // Show error states
        document.getElementById('recentTransactions').innerHTML = 
            '<div class="empty-state">Failed to load transactions</div>';
        document.getElementById('budgetOverview').innerHTML = 
            '<div class="empty-state">Failed to load budgets</div>';
    }
}

function updateSummaryCards(data) {
    document.getElementById('totalIncome').textContent = formatCurrency(data.income || 0);
    document.getElementById('totalExpenses').textContent = formatCurrency(data.expenses || 0);
    document.getElementById('netSavings').textContent = formatCurrency(data.savings || 0);
    document.getElementById('savingsRate').textContent = `${data.savings_rate || 0}%`;
}

function updateCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    const context = ctx.getContext('2d');
    if (categoryChartInstance) {
        categoryChartInstance.destroy();
        categoryChartInstance = null;
    }
    
    if (!categories || categories.length === 0) {
        // Show empty state
        categoryChartInstance = new Chart(context, {
            type: 'doughnut',
            data: {
                labels: ['No Data'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#E2E8F0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '60%'
            }
        });
        return;
    }

    const labels = categories.map(c => c.category || 'Other');
    const values = categories.map(c => c.total || 0);
    const colors = labels.map(getCategoryColor);

    categoryChartInstance = new Chart(context, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12 }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

function updateTrendChart(trendData) {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;
    
    const context = ctx.getContext('2d');
    if (trendChartInstance) {
        trendChartInstance.destroy();
        trendChartInstance = null;
    }

    if (!trendData || trendData.length === 0) {
        trendChartInstance = new Chart(context, {
            type: 'line',
            data: {
                labels: ['No Data'],
                datasets: [
                    {
                        label: 'Income',
                        data: [0],
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true
                    },
                    {
                        label: 'Expenses',
                        data: [0],
                        borderColor: '#EF4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => formatCurrency(value)
                        }
                    }
                }
            }
        });
        return;
    }

    const labels = trendData.map(d => d.month || '');
    const income = trendData.map(d => d.income || 0);
    const expenses = trendData.map(d => d.expenses || 0);

    trendChartInstance = new Chart(context, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: income,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4
                },
                {
                    label: 'Expenses',
                    data: expenses,
                    borderColor: '#EF4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => formatCurrency(value)
                    }
                }
            }
        }
    });
}

function updateRecentTransactions(transactions) {
    const container = document.getElementById('recentTransactions');
    if (!transactions || transactions.length === 0) {
        container.innerHTML = '<div class="empty-state">No recent transactions</div>';
        return;
    }

    container.innerHTML = transactions.map(txn => {
        const amount = txn.amount || 0;
        const type = txn.type || 'expense';
        const category = txn.category || 'Uncategorized';
        const description = txn.description || 'Unknown';
        
        return `
            <div class="transaction-item">
                <div class="txn-left">
                    <div class="txn-icon ${type}">
                        ${type === 'income' ? '📈' : '📉'}
                    </div>
                    <div class="txn-info">
                        <div class="txn-desc">${description}</div>
                        <div class="txn-category">${category}</div>
                    </div>
                </div>
                <div class="txn-amount ${type === 'income' ? 'positive' : 'negative'}">
                    ${type === 'income' ? '+' : '-'} ${formatCurrency(amount)}
                </div>
            </div>
        `;
    }).join('');
}

function updateBudgetOverview(budgets) {
    const container = document.getElementById('budgetOverview');
    if (!budgets || budgets.length === 0) {
        container.innerHTML = '<div class="empty-state">No budgets set</div>';
        return;
    }

    container.innerHTML = budgets.map(b => {
        const spent = b.spent || 0;
        const limit = b.limit || 0;
        const pct = limit > 0 ? Math.min((spent / limit) * 100, 100) : 0;
        let statusClass = 'safe';
        if (pct > 90) statusClass = 'danger';
        else if (pct > 70) statusClass = 'warning';

        return `
            <div class="budget-item">
                <div class="budget-header">
                    <span class="budget-name">${b.category || 'Uncategorized'}</span>
                    <span class="budget-amounts">
                        ${formatCurrency(spent)} / ${formatCurrency(limit)}
                    </span>
                </div>
                <div class="budget-bar">
                    <div class="budget-bar-fill ${statusClass}" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

// Load dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    loadDashboard();
});

// Also reload dashboard when navigating to it
document.addEventListener('navigate', function(e) {
    if (e.detail && e.detail.page === 'dashboard') {
        loadDashboard();
    }
});

window.loadDashboard = loadDashboard;