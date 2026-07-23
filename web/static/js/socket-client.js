const socket = io();

socket.on("connect", () => {
    document.getElementById("conn-text").textContent = "Connecté";
    document.querySelector(".status-dot").className = "status-dot connected";
});

socket.on("disconnect", () => {
    document.getElementById("conn-text").textContent = "Déconnecté";
    document.querySelector(".status-dot").className = "status-dot disconnected";
});

socket.on("update", (data) => {
    if (window.updateDashboard) {
        window.updateDashboard(data);
    }
});

socket.on("event", (data) => {
    if (window.addEvent) {
        window.addEvent(data);
    }
});
