let currentLang = "fr";
let locales = {};

async function setLang(lang) {
    currentLang = lang;
    try {
        const resp = await fetch(`/lang/${lang}`);
        locales = await resp.json();
        applyLocale();
    } catch (e) {
        console.error("Lang error:", e);
    }
}

function applyLocale() {
    document.querySelector(".nav-brand").textContent = locales.app_title || "Energy";
}

function changeMode(mode) {
    const sourceSelect = document.getElementById("source-select");
    sourceSelect.disabled = mode === "auto";
    fetch("/api/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
    });
}

function forceSource(source) {
    fetch("/api/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "manuel", source }),
    });
}

window.updateDashboard = function (data) {
    const m = data.mesures || {};
    const s = data.status || {};

    updateCard("solaire", m.solaire);
    updateCard("batterie", m.batterie);
    updateCard("jirama", m.jirama);
    updateCard("groupe", m.groupe);
    updateCard("consommation", m.consommation);

    document.querySelectorAll(".source-card").forEach((el) => el.classList.remove("active"));
    if (s.current_state) {
        const activeCard = document.getElementById(`card-${s.current_state}`);
        if (activeCard) activeCard.classList.add("active");
    }

    const modeLabel = document.getElementById("mode-label");
    modeLabel.textContent = s.mode === "auto" ? "Auto" : `Manuel: ${s.manual_source}`;

    updateCharts(data);
};

function updateCard(name, data) {
    if (!data) return;
    const powerEl = document.getElementById(`${name}-power`);
    const voltageEl = document.getElementById(`${name}-voltage`);
    const currentEl = document.getElementById(`${name}-current`);

    if (powerEl) powerEl.textContent = `${data.power || 0} W`;
    if (voltageEl) voltageEl.textContent = data.voltage || 0;
    if (currentEl) currentEl.textContent = data.current || 0;

    if (name === "batterie") {
        const soc = data.soc || 0;
        const socFill = document.getElementById("batterie-soc-fill");
        const socText = document.getElementById("batterie-soc-text");
        const flowEl = document.getElementById("batterie-flow");

        if (socFill) {
            socFill.style.width = `${Math.min(soc, 100)}%`;
            socFill.className = "soc-fill";
            if (soc < 30) socFill.classList.add("low");
            else if (soc < 70) socFill.classList.add("medium");
            else socFill.classList.add("high");
        }
        if (socText) socText.textContent = `${soc}%`;

        if (flowEl) {
            if (data.power < -5) flowEl.textContent = "🔋 Charge";
            else if (data.power > 5) flowEl.textContent = "⚡ Décharge";
            else flowEl.textContent = "○ Inactif";
        }
    }

    if (name === "jirama") {
        const statusEl = document.getElementById("jirama-status");
        if (statusEl) {
            const active = data.power > 1;
            statusEl.textContent = active ? "Actif" : "Inactif";
            statusEl.className = `status-badge ${active ? "active" : "inactive"}`;
        }
    }

    if (name === "groupe") {
        const statusEl = document.getElementById("groupe-status");
        if (statusEl) {
            const active = data.power > 1;
            statusEl.textContent = active ? "Actif" : "Inactif";
            statusEl.className = `status-badge ${active ? "active" : "inactive"}`;
        }
    }
}

window.addEvent = function (event) {
    const list = document.getElementById("events-list");
    if (!list) return;
    const item = document.createElement("div");
    item.className = `event-item event-level-${event.level || "info"}`;
    const ts = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
    item.innerHTML = `<span>${event.message || ""}</span><span class="event-time">${ts}</span>`;
    list.prepend(item);
    while (list.children.length > 50) {
        list.removeChild(list.lastChild);
    }
};

async function loadInitialData() {
    try {
        const resp = await fetch("/api/status");
        const data = await resp.json();
        window.updateDashboard(data);

        const eventsResp = await fetch("/api/evenements?limit=20");
        const events = await eventsResp.json();
        const list = document.getElementById("events-list");
        if (list) {
            list.innerHTML = "";
            events.forEach((e) => window.addEvent(e));
        }

        const forecastResp = await fetch("/api/previsions");
        const forecasts = await forecastResp.json();
        const forecastList = document.getElementById("forecast-list");
        if (forecastList) {
            forecastList.innerHTML = forecasts.map((f) => `
                <div class="forecast-item">
                    <div class="forecast-date">${f.date_prev || ""}</div>
                    <div>Nuages: ${f.couverture_nuageuse || 0}% | Prod: ${f.production_estimee || 0}W</div>
                    <div style="color:#94a3b8;font-size:0.8rem">${f.recommandation || ""}</div>
                </div>
            `).join("");
        }
    } catch (e) {
        console.error("Load error:", e);
    }
}

window.refreshEvents = function (events) {
    const list = document.getElementById("events-list");
    if (!list) return;
    if (events.length === 0) return;
    events.reverse();
    events.forEach((e) => {
        const existing = list.querySelector(`[data-id="${e.id}"]`);
        if (!existing) {
            const item = document.createElement("div");
            item.className = `event-item event-level-${e.level || "info"}`;
            item.setAttribute("data-id", e.id);
            const ts = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : "";
            item.innerHTML = `<span>${e.message || ""}</span><span class="event-time">${ts}</span>`;
            list.prepend(item);
            while (list.children.length > 50) {
                list.removeChild(list.lastChild);
            }
        }
    });
};

document.addEventListener("DOMContentLoaded", loadInitialData);
