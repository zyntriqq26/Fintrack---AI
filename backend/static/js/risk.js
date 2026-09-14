/* static/js/risk.js — Renders the ML risk prediction card */
(function () {
    const ICONS = { safe: "🟢", high: "🟡", worst: "🟠", critical: "🔴" };

    async function loadRisk() {
        const body = document.getElementById("riskBody");
        const monthEl = document.getElementById("riskMonth");
        if (!body) return;

        try {
            const res = await fetch("/api/risk");
            const data = await res.json();

            if (!res.ok) {
                body.innerHTML =
                    `<div class="risk-empty">${data.error || "Unable to load risk assessment."}</div>`;
                return;
            }

            renderRisk(data, body, monthEl);
        } catch (err) {
            body.innerHTML =
                `<div class="risk-empty">Network error loading risk assessment.</div>`;
        }
    }

    function renderRisk(data, body, monthEl) {
        const label = (data.risk_label || "").toLowerCase();
        const icon = ICONS[label] || "⚪";
        const proba = data.probabilities || {};

        if (monthEl) monthEl.textContent = data.month ? `Month: ${data.month}` : "";

        const probaRows = Object.entries(proba)
            .sort((a, b) => b[1] - a[1])
            .map(([cls, p]) => `
                <div class="risk-proba-row">
                    <span class="risk-proba-label">${cls}</span>
                    <div class="risk-proba-bar">
                        <div class="risk-proba-fill risk-${cls}"
                             style="width:${(p * 100).toFixed(1)}%"></div>
                    </div>
                    <span class="risk-proba-value">${(p * 100).toFixed(1)}%</span>
                </div>
            `).join("");

        body.innerHTML = `
            <div class="risk-main">
                <div class="risk-badge risk-${label}">
                    <span class="risk-badge-icon">${icon}</span>
                    <span class="risk-badge-text">${(data.risk_label || "").toUpperCase()}</span>
                </div>
                <p class="risk-description">${data.description || ""}</p>
            </div>
            <div class="risk-probas">${probaRows}</div>
            <div class="risk-footer">
                <span>Model: ${data.model || "ML"}</span>
                <span>Month: ${data.month || ""}</span>
            </div>
        `;
    }

    document.addEventListener("DOMContentLoaded", () => {
    loadRisk();
    setInterval(loadRisk, 8000);   // re-fetch every 8 seconds
});
})();