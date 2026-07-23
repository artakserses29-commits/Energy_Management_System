let lastEvents = "";

function pollStatus() {
    fetch("/api/status")
        .then((r) => r.json())
        .then((data) => {
            document.getElementById("conn-text").textContent = "Connecte";
            document.querySelector(".status-dot").className = "status-dot connected";
            if (window.updateDashboard) window.updateDashboard(data);
        })
        .catch(() => {
            document.getElementById("conn-text").textContent = "Deconnecte";
            document.querySelector(".status-dot").className = "status-dot disconnected";
        });
}

function pollEvents() {
    fetch("/api/evenements?limit=5")
        .then((r) => r.json())
        .then((events) => {
            const key = JSON.stringify(events.map((e) => e.id));
            if (key !== lastEvents) {
                lastEvents = key;
                if (window.refreshEvents) window.refreshEvents(events);
            }
        })
        .catch(() => {});
}

setInterval(pollStatus, 2000);
setInterval(pollEvents, 5000);
pollStatus();
