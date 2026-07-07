// js/budgets.js - Budget Management

async function loadBudgets() {
    try {
        const budgets = await getBudgets();
        renderBudgets(budgets);
    } catch (error) {
        console.error('Failed to load budgets:', error);
        document.getElementById('budgetsGrid').innerHTML = 
            '<div class="empty-state">Failed to load budgets</div>';
    }
}

function renderBudgets(budgets) {
    const container = document.getElementById('budgetsGrid');
    if (!budgets || budgets.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p style="font-size:40px;margin-bottom:12px;">📊</p>
                <h3>No Budgets Set</h3>
                <p style="color:var(--gray-400);">Start tracking your spending by setting monthly budgets</p>
                <button class="btn btn-primary" style="margin-top:16px;" onclick="openBudgetModal()">
                    <i class="fas fa-plus"></i> Set Your First Budget
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = budgets.map(b => {
        const spent = b.spent || 0;
        const limit = b.limit || 0;
        const pct = limit > 0 ? Math.min((spent / limit) * 100, 100) : 0;
        const statusClass = pct > 90 ? 'danger' : pct > 70 ? 'warning' : 'safe';

        return `
            <div class="budget-card">
                <div class="budget-card-header">
                    <span class="budget-card-icon">${getCategoryIcon(b.category)}</span>
                    <h4>${b.category || 'Uncategorized'}</h4>
                    <span class="budget-card-status ${spent > limit ? 'over' : 'under'}">
                        ${spent > limit ? '⚠️ Over' : '✅ On Track'}
                    </span>
                </div>
                <div class="budget-card-amounts">
                    <span>Spent: ${formatCurrency(spent)}</span>
                    <span>Limit: ${formatCurrency(limit)}</span>
                </div>
                <div class="budget-bar">
                    <div class="budget-bar-fill ${statusClass}" 
                         style="width: ${pct}%"></div>
                </div>
                <div class="budget-card-footer">
                    <span>${pct.toFixed(0)}% used</span>
                    <span>Remaining: ${formatCurrency(Math.max(0, limit - spent))}</span>
                </div>
            </div>
        `;
    }).join('');
}

async function handleSetBudget(e) {
    e.preventDefault();
    
    const category = document.getElementById('budgetCategory').value;
    const monthly_limit = parseFloat(document.getElementById('budgetLimit').value);

    if (!category) {
        showToast('Please select a category', 'error');
        return;
    }

    if (!monthly_limit || monthly_limit <= 0) {
        showToast('Please enter a valid budget amount', 'error');
        return;
    }

    const data = {
        category: category,
        monthly_limit: monthly_limit
    };

    try {
        await setBudget(data);
        showToast(`Budget set for ${category}`);
        closeModal('budgetModal');
        document.getElementById('budgetForm').reset();
        await loadBudgets();
    } catch (error) {
        console.error('Failed to set budget:', error);
        showToast('Failed to set budget: ' + error.message, 'error');
    }
}

// ─── Event Listeners ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadBudgets();
    document.getElementById('budgetForm').addEventListener('submit', handleSetBudget);
});

window.openBudgetModal = function() {
    openModal('budgetModal');
};

window.loadBudgets = loadBudgets;