// Satyam WhatsApp Automation Dashboard JS (Multi-User Dynamic Research Engine)

let isFetching = false;

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.style.borderColor = type === "error" ? "var(--danger)" : "var(--primary)";
    toast.classList.remove("hidden");
    toast.style.opacity = "1";
    toast.style.transform = "translateY(0)";

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        setTimeout(() => toast.classList.add("hidden"), 300);
    }, 3500);
}

function togglePasswordVisibility(fieldId) {
    const input = document.getElementById(fieldId);
    if (input.type === "password") {
        input.type = "text";
    } else {
        input.type = "password";
    }
}

async function fetchStatus() {
    if (isFetching) return;
    isFetching = true;

    try {
        const res = await fetch("/api/status");
        if (!res.ok) throw new Error("Status network error");
        const data = await res.json();

        // 1. Connection State
        const connPill = document.getElementById("connectionPill");
        const connText = document.getElementById("connectionText");
        const qrBox = document.getElementById("qrBox");
        const connectedBox = document.getElementById("connectedBox");
        const qrImage = document.getElementById("qrImage");
        const qrLoading = document.getElementById("qrLoading");

        if (data.connected) {
            connPill.className = "status-pill status-connected";
            connText.textContent = "WhatsApp Connected";
            qrBox.classList.add("hidden");
            connectedBox.classList.remove("hidden");

            document.getElementById("connectedUser").textContent = data.push_name ? `Linked: ${data.push_name}` : "WhatsApp Linked";
            document.getElementById("connectedPhone").textContent = data.phone_number ? `+${data.phone_number}` : (data.connected_jid || "Device Online");
        } else if (data.pairing && data.qr_data_url) {
            connPill.className = "status-pill status-pairing";
            connText.textContent = "Ready to Scan";
            qrBox.classList.remove("hidden");
            connectedBox.classList.add("hidden");
            qrLoading.classList.add("hidden");
            qrImage.classList.remove("hidden");
            qrImage.src = data.qr_data_url;
        } else {
            connPill.className = "status-pill status-disconnected";
            connText.textContent = "Generating QR Code...";
            qrBox.classList.remove("hidden");
            connectedBox.classList.add("hidden");
            qrLoading.classList.remove("hidden");
            qrImage.classList.add("hidden");
        }

        // 2. Metrics & Engine Info
        document.getElementById("metricTotalUsers").textContent = data.users_count || 0;
        document.getElementById("metricActiveUsers").textContent = data.active_users_count || 0;
        document.getElementById("lblModel").textContent = data.config?.gemini_model || "Gemini 3.8 Flash";
        document.getElementById("usersCounterBadge").textContent = `${data.users_count || 0} users`;

        const botPasswordInput = document.getElementById("botPassword");
        if (!botPasswordInput.dataset.modified) {
            botPasswordInput.value = data.config?.bot_password || "satyam08052010";
        }

        const intervalMinutesInput = document.getElementById("intervalMinutes");
        if (intervalMinutesInput && !intervalMinutesInput.dataset.modified) {
            intervalMinutesInput.value = data.config?.interval_minutes || 5;
        }

        const publicUrlInput = document.getElementById("publicUrl");
        if (publicUrlInput && !publicUrlInput.dataset.modified) {
            publicUrlInput.value = data.config?.public_url || "";
        }

        // Cloudflare Tunnel Display
        const tunnelStatusText = document.getElementById("tunnelStatusText");
        const tunnelUrlCode = document.getElementById("tunnelUrlCode");
        const btnOpenTunnel = document.getElementById("btnOpenTunnel");

        if (data.tunnel_active && data.tunnel_url) {
            if (tunnelStatusText) tunnelStatusText.innerHTML = "🟢 <strong>Active</strong> (Public HTTPS for outside WiFi)";
            if (tunnelUrlCode) tunnelUrlCode.textContent = data.tunnel_url;
            if (btnOpenTunnel) btnOpenTunnel.href = `${data.tunnel_url}/watch`;
        } else if (data.config?.public_url) {
            if (tunnelStatusText) tunnelStatusText.innerHTML = "🌐 <strong>Custom URL</strong>";
            if (tunnelUrlCode) tunnelUrlCode.textContent = data.config.public_url;
            if (btnOpenTunnel) btnOpenTunnel.href = `${data.config.public_url}/watch`;
        } else {
            if (tunnelStatusText) tunnelStatusText.innerHTML = "⚪ Tunnel offline (Using LAN fallback)";
            if (tunnelUrlCode) tunnelUrlCode.textContent = data.server_url || "http://localhost:5000";
            if (btnOpenTunnel) btnOpenTunnel.href = "/watch";
        }

        // 3. Render Users List
        renderUsers(data.users || []);

    } catch (err) {
        console.error("Error fetching status:", err);
    } finally {
        isFetching = false;
    }
}

function renderUsers(users) {
    const container = document.getElementById("usersList");
    if (!users || users.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📡</span>
                <p>No users have configured automations yet.<br>Any user can simply send <strong>hillo</strong> on WhatsApp to configure their own custom topic and timer!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = users.map(user => {
        const jid = user.jid || "";
        const cleanPhone = jid.split("@")[0].split(":")[0];
        const topic = user.custom_prompt || "<em>Waiting for user to choose topic...</em>";
        const interval = user.interval_minutes ? `Every ${user.interval_minutes} min` : "Timer not set";
        const isActive = !!user.is_active;
        const count = user.discovery_count || 0;
        const hasCustomKey = !!user.custom_gemini_key;
        const aiQueries = user.ai_query_count || 0;
        const keyBadge = hasCustomKey 
            ? `<span style="color: #10b981; font-size: 0.8rem; font-weight: 600;">🔑 Custom Key (Unlimited)</span>`
            : `<span style="color: #f59e0b; font-size: 0.8rem;">🔑 Free (${Math.min(aiQueries, 3)}/3 used)</span>`;

        return `
            <div class="user-card">
                <div class="user-card-header">
                    <span class="user-phone">📱 ${escapeHtml(cleanPhone)}</span>
                    <span class="badge-status ${isActive ? 'badge-active' : 'badge-stopped'}">
                        ${isActive ? 'Active 🟢' : 'Stopped 🔴'}
                    </span>
                </div>

                <div class="user-topic-box">
                    <span class="user-topic-label">User's Custom Topic</span>
                    <div class="user-topic-text">${escapeHtml(topic)}</div>
                </div>

                <div class="user-meta-row" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 8px 0;">
                    ${keyBadge}
                    <span>📊 ${count} updates</span>
                </div>

                <div class="user-meta-row" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 10px 0;">
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span>⏱️ <strong>Timer:</strong></span>
                        <select class="form-control" style="width: auto; padding: 2px 8px; font-size: 0.85rem; border-radius: 6px; background: rgba(255,255,255,0.08); color: var(--text-primary); border: 1px solid var(--border-color);" onchange="handleSetInterval('${escapeJs(jid)}', this.value)">
                            <option value="1" ${user.interval_minutes == 1 ? 'selected' : ''}>1 min</option>
                            <option value="2" ${user.interval_minutes == 2 ? 'selected' : ''}>2 min</option>
                            <option value="3" ${user.interval_minutes == 3 ? 'selected' : ''}>3 min</option>
                            <option value="5" ${user.interval_minutes == 5 ? 'selected' : ''}>5 min</option>
                            <option value="10" ${user.interval_minutes == 10 ? 'selected' : ''}>10 min</option>
                            <option value="15" ${user.interval_minutes == 15 ? 'selected' : ''}>15 min</option>
                            <option value="30" ${user.interval_minutes == 30 ? 'selected' : ''}>30 min</option>
                            <option value="60" ${user.interval_minutes == 60 ? 'selected' : ''}>60 min</option>
                        </select>
                    </div>
                </div>

                <div class="user-actions">
                    ${isActive ? `
                        <button class="btn btn-danger btn-sm" onclick="handleUserAction('${escapeJs(jid)}', 'stop')">⏹ Stop</button>
                    ` : `
                        <button class="btn btn-primary btn-sm" onclick="handleUserAction('${escapeJs(jid)}', 'start')">▶ Start</button>
                    `}
                    <button class="btn btn-secondary btn-sm" onclick="handleUserAction('${escapeJs(jid)}', 'trigger_now')">⚡ Send Now</button>
                </div>
            </div>
        `;
    }).join("");
}

async function handleSetInterval(jid, interval) {
    try {
        const res = await fetch("/api/user_action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jid, action: "set_interval", interval: parseInt(interval) })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            fetchStatus();
        } else {
            showToast(data.error || "Failed to update timer", "error");
        }
    } catch (e) {
        showToast("Network error: " + e.message, "error");
    }
}

async function handleUserAction(jid, action) {
    try {
        const res = await fetch("/api/user_action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jid, action })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            fetchStatus();
        } else {
            showToast(data.error || "Action failed", "error");
        }
    } catch (e) {
        showToast("Error communicating with server", "error");
    }
}

document.getElementById("btnSaveSettings").addEventListener("click", async () => {
    const payload = {
        gemini_api_key: document.getElementById("geminiApiKey").value,
        bot_password: document.getElementById("botPassword").value,
        interval_minutes: document.getElementById("intervalMinutes") ? parseInt(document.getElementById("intervalMinutes").value) || 5 : 5,
        public_url: document.getElementById("publicUrl") ? document.getElementById("publicUrl").value : ""
    };

    try {
        const res = await fetch("/api/update_settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast("✅ Admin settings saved successfully!");
            document.getElementById("geminiApiKey").value = "";
            fetchStatus();
        } else {
            showToast(data.message || "Failed to save settings", "error");
        }
    } catch (e) {
        showToast("Error saving settings", "error");
    }
});

document.getElementById("btnCleanStorage").addEventListener("click", async () => {
    try {
        const res = await fetch("/api/cleanup_storage", { method: "POST" });
        const data = await res.json();
        showToast(data.message || "Storage cleaned!");
    } catch (e) {
        showToast("Error cleaning storage", "error");
    }
});

const btnRestartTunnel = document.getElementById("btnRestartTunnel");
if (btnRestartTunnel) {
    btnRestartTunnel.addEventListener("click", async () => {
        btnRestartTunnel.disabled = true;
        btnRestartTunnel.textContent = "⏳";
        showToast("Restarting Cloudflare Tunnel...");
        try {
            const res = await fetch("/api/tunnel_action", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "restart" })
            });
            const data = await res.json();
            if (data.success && data.tunnel_url) {
                showToast("Cloudflare Tunnel Online!");
            } else {
                showToast("Failed to reconnect tunnel", "error");
            }
            await fetchStatus();
        } catch (e) {
            showToast("Error restarting tunnel", "error");
        } finally {
            btnRestartTunnel.disabled = false;
            btnRestartTunnel.textContent = "🔄";
        }
    });
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[m]);
}

function escapeJs(text) {
    if (!text) return "";
    return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// Mark inputs as user-edited so polling doesn't overwrite while user is typing
const passInput = document.getElementById("botPassword");
passInput.addEventListener("input", () => {
    passInput.dataset.modified = "true";
});

// Initialize polling
fetchStatus();
setInterval(fetchStatus, 3000);
