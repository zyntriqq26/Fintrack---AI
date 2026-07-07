// js/transactions.js - Transaction Management

let currentPage = 1;
const perPage = 20;
let totalTransactions = 0;
let currentFilters = {};

async function loadTransactions(page = 1) {
    currentPage = page;
    const params = {
        page: page,
        per_page: perPage,
        ...currentFilters
    };

    try {
        const data = await getTransactions(params);
        totalTransactions = data.total;
        renderTransactions(data.transactions);
        updatePagination(data.page, data.total);
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

function renderTransactions(transactions) {
    const tbody = document.getElementById('transactionsBody');
    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No transactions found</td></tr>';
        return;
    }

    tbody.innerHTML = transactions.map(txn => `
        <tr>
            <td>${formatDate(txn.date)}</td>
            <td><strong>${txn.description}</strong></td>
            <td>
                <span style="display:flex;align-items:center;gap:4px;">
                    ${getCategoryIcon(txn.category)} ${txn.category || 'Uncategorized'}
                </span>
            </td>
            <td>
                <span class="txn-type-badge ${txn.type}">${txn.type.toUpperCase()}</span>
            </td>
            <td style="font-weight:600;color:${txn.type === 'income' ? '#10B981' : '#EF4444'}">
                ${txn.type === 'income' ? '+' : '-'} ${formatCurrency(txn.amount)}
            </td>
            <td>
                <div class="txn-actions">
                    <button class="delete-btn" data-id="${txn.id}" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

    // Add delete handlers
    tbody.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => handleDelete(parseInt(btn.dataset.id)));
    });
}

function updatePagination(page, total) {
    const totalPages = Math.ceil(total / perPage);
    document.getElementById('pageInfo').textContent = `Page ${page} of ${totalPages || 1}`;
    document.getElementById('prevPage').disabled = page <= 1;
    document.getElementById('nextPage').disabled = page >= totalPages;
}

async function handleDelete(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) return;
    try {
        await deleteTransaction(id);
        showToast('Transaction deleted successfully');
        loadTransactions(currentPage);
        loadDashboard();
    } catch (error) {
        console.error('Failed to delete:', error);
    }
}

// ─── Transaction Form ──────────────────────────────────────────────────────
async function handleAddTransaction(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        description: document.getElementById('txnDescription').value.trim(),
        amount: parseFloat(document.getElementById('txnAmount').value),
        type: document.getElementById('txnType').value,
        category: document.getElementById('txnCategory').value || null,
        date: document.getElementById('txnDate').value,
        notes: document.getElementById('txnNotes').value.trim()
    };

    if (!data.description || !data.amount || !data.date) {
        showToast('Please fill in all required fields', 'error');
        return;
    }

    try {
        await addTransaction(data);
        showToast('Transaction added successfully!');
        closeModal('transactionModal');
        form.reset();
        document.getElementById('txnDate').value = new Date().toISOString().split('T')[0];
        loadTransactions(currentPage);
        loadDashboard();
    } catch (error) {
        console.error('Failed to add transaction:', error);
    }
}

// ─── Event Listeners ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Load transactions
    loadTransactions(1);

    // Load categories for filter
    getCategories().then(categories => {
        const filter = document.getElementById('categoryFilter');
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            filter.appendChild(opt);
        });
        // Also populate category dropdown in form
        const formSelect = document.getElementById('txnCategory');
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            formSelect.appendChild(opt);
        });
    }).catch(console.error);

    // Set default date
    document.getElementById('txnDate').value = new Date().toISOString().split('T')[0];

    // Filters
    document.getElementById('searchInput').addEventListener('input', debounce(() => {
        currentFilters.search = document.getElementById('searchInput').value;
        loadTransactions(1);
    }, 300));

    document.getElementById('typeFilter').addEventListener('change', () => {
        currentFilters.type = document.getElementById('typeFilter').value;
        loadTransactions(1);
    });

    document.getElementById('categoryFilter').addEventListener('change', () => {
        currentFilters.category = document.getElementById('categoryFilter').value;
        loadTransactions(1);
    });

    // Pagination
    document.getElementById('prevPage').addEventListener('click', () => {
        if (currentPage > 1) loadTransactions(currentPage - 1);
    });
    document.getElementById('nextPage').addEventListener('click', () => {
        const totalPages = Math.ceil(totalTransactions / perPage);
        if (currentPage < totalPages) loadTransactions(currentPage + 1);
    });

    // Form submit
    document.getElementById('transactionForm').addEventListener('submit', handleAddTransaction);

    // Type toggle for category
    document.getElementById('txnType').addEventListener('change', function() {
        const group = document.getElementById('categoryGroup');
        if (this.value === 'income') {
            group.style.display = 'none';
            document.getElementById('txnCategory').value = 'Income';
        } else {
            group.style.display = 'block';
            document.getElementById('txnCategory').value = '';
        }
    });

    // Export
    document.getElementById('exportBtn').addEventListener('click', () => {
        showToast('Export functionality coming soon!', 'info');
    });
});

// Debounce helper
function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}