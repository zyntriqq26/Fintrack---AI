// js/reports.js - Report Management

async function loadReports() {
    // Set default month to current
    const now = new Date();
    const monthInput = document.getElementById('reportMonth');
    if (monthInput) {
        monthInput.value = now.toISOString().slice(0, 7);
    }

    // Load previous reports from backend
    try {
        const response = await fetch('/reports');
        if (response.ok) {
            const files = await response.json();
            renderReportList(files);
        } else {
            console.error('Failed to fetch reports:', response.status);
            document.getElementById('reportList').innerHTML = 
                '<li class="empty-state">Could not load reports</li>';
        }
    } catch (error) {
        console.error('Failed to load reports:', error);
        document.getElementById('reportList').innerHTML = 
            '<li class="empty-state">Error loading reports</li>';
    }
}

function renderReportList(files) {
    const list = document.getElementById('reportList');
    if (!files || files.length === 0) {
        list.innerHTML = '<li class="empty-state">No reports generated yet</li>';
        return;
    }

    list.innerHTML = files.map(file => `
        <li>
            <span>📄 ${file}</span>
            <a href="/reports/${file}" download class="btn btn-sm btn-primary">
                <i class="fas fa-download"></i> Download
            </a>
        </li>
    `).join('');
}

async function handleGenerateReport(e) {
    e.preventDefault();
    const month = document.getElementById('reportMonth').value;
    
    if (!month) {
        showToast('Please select a month', 'error');
        return;
    }

    try {
        const url = await generateReport(month);
        // Open in new tab for download
        window.open(url, '_blank');
        showToast('Report generated successfully!');
        
        // Refresh report list after a delay
        setTimeout(loadReports, 2000);
    } catch (error) {
        console.error('Failed to generate report:', error);
        showToast('Failed to generate report', 'error');
    }
}

// ─── Event Listeners ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadReports();
    document.getElementById('generateReportBtn').addEventListener('click', handleGenerateReport);
});