let powerChart = null;
let socChart = null;

const CHART_COLORS = {
    solaire: { border: "#eab308", bg: "rgba(234, 179, 8, 0.1)" },
    batterie: { border: "#22c55e", bg: "rgba(34, 197, 94, 0.1)" },
    jirama: { border: "#3b82f6", bg: "rgba(59, 130, 246, 0.1)" },
    groupe: { border: "#f97316", bg: "rgba(249, 115, 22, 0.1)" },
    consommation: { border: "#ec4899", bg: "rgba(236, 72, 153, 0.1)" },
};

function initCharts() {
    const powerCtx = document.getElementById("chart-power");
    const socCtx = document.getElementById("chart-soc");
    if (!powerCtx || !socCtx) return;

    powerChart = new Chart(powerCtx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "Solaire", data: [], borderColor: CHART_COLORS.solaire.border, backgroundColor: CHART_COLORS.solaire.bg, fill: true, tension: 0.3, pointRadius: 0 },
                { label: "Consommation", data: [], borderColor: CHART_COLORS.consommation.border, backgroundColor: CHART_COLORS.consommation.bg, fill: true, tension: 0.3, pointRadius: 0 },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: "#94a3b8" } } },
            scales: {
                x: { ticks: { color: "#64748b", maxTicksLimit: 10 }, grid: { color: "#1e293b" } },
                y: { beginAtZero: true, ticks: { color: "#64748b" }, grid: { color: "#1e293b" } },
            },
        },
    });

    socChart = new Chart(socCtx, {
        type: "line",
        data: {
            labels: [],
            datasets: [
                { label: "SOC Batterie", data: [], borderColor: "#22c55e", backgroundColor: "rgba(34, 197, 94, 0.1)", fill: true, tension: 0.3, pointRadius: 0 },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: "#94a3b8" } } },
            scales: {
                x: { ticks: { color: "#64748b", maxTicksLimit: 10 }, grid: { color: "#1e293b" } },
                y: { min: 0, max: 100, ticks: { color: "#64748b" }, grid: { color: "#1e293b" } },
            },
        },
    });
}

function updateCharts(data) {
    if (!powerChart || !socChart) return;

    const now = new Date().toLocaleTimeString();
    const maxPoints = 50;

    const solarPower = data.mesures?.solaire?.power || 0;
    const consoPower = data.mesures?.consommation?.power || 0;
    const batterySoc = data.mesures?.batterie?.soc || 0;

    powerChart.data.labels.push(now);
    powerChart.data.datasets[0].data.push(solarPower);
    powerChart.data.datasets[1].data.push(consoPower);

    socChart.data.labels.push(now);
    socChart.data.datasets[0].data.push(batterySoc);

    if (powerChart.data.labels.length > maxPoints) {
        powerChart.data.labels.shift();
        powerChart.data.datasets.forEach((ds) => ds.data.shift());
        socChart.data.labels.shift();
        socChart.data.datasets.forEach((ds) => ds.data.shift());
    }

    powerChart.update("none");
    socChart.update("none");
}

document.addEventListener("DOMContentLoaded", initCharts);
