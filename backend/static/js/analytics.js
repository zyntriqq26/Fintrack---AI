// js/analytics.js - Analytics & Insights

async function loadAnalytics() {
    await Promise.all([
        loadInsights(),
        loadPredictions(),
        loadRecommendations()
    ]);
}

async function loadInsights() {
    try {
        const data = await getInsights();
        const container = document.getElementById('insightsGrid');
        
        if (!data.insights || data.insights.length === 0) {
            container.innerHTML = '<div class="empty-state">No insights available</div>';
            return;
        }

        container.innerHTML = data.insights.map(insight => `
            <div class="insight-card">
                <div class="insight-icon">${insight.icon}</div>
                <div class="insight-content">
                    <h4>${insight.title}</h4>
                    <p>${insight.text}</p>
                </div>
            </div>
        `).join('');

        // Show anomalies if any
        if (data.anomalies && data.anomalies.length > 0) {
            const anomalySection = document.createElement('div');
            anomalySection.className = 'anomalies-section';
            anomalySection.innerHTML = `
                <h3>⚠️ Unusual Transactions Detected</h3>
                <div class="anomalies-list">
                    ${data.anomalies.map(a => `
                        <div class="anomaly-item">
                            <span>${formatDate(a.date)}</span>
                            <strong>${a.description}</strong>
                            <span style="color:#EF4444;">${formatCurrency(a.amount)}</span>
                            <small>${a.reason}</small>
                        </div>
                    `).join('')}
                </div>
            `;
            container.parentNode.appendChild(anomalySection);
        }
    } catch (error) {
        console.error('Failed to load insights:', error);
    }
}

async function loadPredictions() {
    try {
        const data = await getPredictions();
        const container = document.getElementById('predictionsContainer');
        
        if (!data.predictions || data.predictions.length === 0) {
            container.innerHTML = '<div class="empty-state">Not enough data for predictions</div>';
            return;
        }

        container.innerHTML = `
            <div class="predictions-summary">
                <div class="prediction-total">
                    <span>Next Month's Predicted Spending</span>
                    <strong>${formatCurrency(data.total_predicted_next_month)}</strong>
                </div>
            </div>
            <div class="predictions-grid">
                ${data.predictions.slice(0, 8).map(p => `
                    <div class="prediction-card">
                        <div class="prediction-header">
                            <span>${getCategoryIcon(p.category)} ${p.category}</span>
                            <span class="trend-${p.trend.includes('Rising') ? 'up' : p.trend.includes('Falling') ? 'down' : 'stable'}">
                                ${p.trend}
                            </span>
                        </div>
                        <div class="prediction-amount">
                            Avg: ${formatCurrency(p.avg_monthly)}/month
                        </div>
                        <div class="prediction-next">
                            Next: ${formatCurrency(p.next_months[0]?.predicted || 0)}
                        </div>
                        <div class="prediction-confidence">
                            Confidence: ${p.confidence}%
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Failed to load predictions:', error);
    }
}

async function loadRecommendations() {
    try {
        const data = await getRecommendations();
        const container = document.getElementById('recommendationsContainer');
        
        if (!data.recommendations || data.recommendations.length === 0) {
            container.innerHTML = '<div class="empty-state">No recommendations available</div>';
            return;
        }

        // Priority badge colors
        const priorityColors = {
            high: '#EF4444',
            medium: '#F59E0B',
            low: '#3B82F6'
        };

        container.innerHTML = `
            <div class="recommendations-stats">
                <span>Potential Savings: ${formatCurrency(data.potential_savings)}</span>
                <span>Current Savings Rate: ${data.savings_rate}%</span>
            </div>
            <div class="recommendations-list">
                ${data.recommendations.map(rec => `
                    <div class="recommendation-item" style="border-left-color: ${priorityColors[rec.priority]};">
                        <div class="rec-icon">${rec.icon}</div>
                        <div class="rec-content">
                            <div class="rec-header">
                                <h4>${rec.title}</h4>
                                <span class="rec-priority ${rec.priority}">${rec.priority}</span>
                            </div>
                            <p>${rec.detail}</p>
                            ${rec.saving > 0 ? `<div class="rec-saving">💰 Save ${formatCurrency(rec.saving)}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (error) {
        console.error('Failed to load recommendations:', error);
    }
}

// Load analytics on page show
document.addEventListener('DOMContentLoaded', () => {
    // Load when analytics tab is clicked
    const analyticsNav = document.querySelector('[data-page="analytics"]');
    if (analyticsNav) {
        analyticsNav.addEventListener('click', loadAnalytics);
    }
});