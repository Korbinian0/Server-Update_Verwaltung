// Application State & Globals
let authToken = localStorage.getItem('token') || null;
let currentTerm = null;
let currentTermFitAddon = null;
let currentWs = null;

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    if (authToken) {
        showDashboard();
    } else {
        showLogin();
    }

    // Event Listeners
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('addServerForm').addEventListener('submit', handleSaveServer);
    document.getElementById('changePwForm').addEventListener('submit', handleChangePassword);
    
    // Auth type change toggle
    document.getElementById('serverAuthType').addEventListener('change', (e) => {
        const type = e.target.value;
        if (type === 'password') {
            document.getElementById('passwordGroup').classList.remove('hidden');
            document.getElementById('keyGroup').classList.add('hidden');
        } else {
            document.getElementById('passwordGroup').classList.add('hidden');
            document.getElementById('keyGroup').classList.remove('hidden');
        }
    });
}

function authHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
    };
}

// UI Switchers
function showLogin() {
    document.getElementById('authSection').classList.remove('hidden');
    document.getElementById('dashboardSection').classList.add('hidden');
    document.getElementById('navUser').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('authSection').classList.add('hidden');
    document.getElementById('dashboardSection').classList.remove('hidden');
    document.getElementById('navUser').classList.remove('hidden');
    loadServers();
}

// Auth Actions
async function handleLogin(e) {
    e.preventDefault();
    const user = document.getElementById('loginUsername').value;
    const pass = document.getElementById('loginPassword').value;
    const errDiv = document.getElementById('loginError');

    errDiv.classList.add('hidden');

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Anmeldung fehlgeschlagen');
        }

        authToken = data.access_token;
        localStorage.setItem('token', authToken);
        showDashboard();
    } catch (err) {
        errDiv.textContent = err.message;
        errDiv.classList.remove('hidden');

// Server CRUD
async function loadServers() {
    try {
        const res = await fetch('/api/servers', { headers: authHeaders() });
        if (res.status === 401) { logout(); return; }
        const servers = await res.json();
        renderServers(servers);
        updateStats(servers);
    } catch (err) {
        console.error('Fehler beim Laden der Server:', err);
    }
}

function updateStats(servers) {
    document.getElementById('statTotalServers').textContent = servers.length;
    let pendingCount = 0;
    let okCount = 0;

    servers.forEach(s => {
        if (s.pending_updates_count > 0) pendingCount += s.pending_updates_count;
        if (s.status === 'ok') okCount++;
    });

    document.getElementById('statPendingUpdates').textContent = pendingCount;
    document.getElementById('statHealthyServers').textContent = okCount;
}

function renderServers(servers) {
    const grid = document.getElementById('serversGrid');
    grid.innerHTML = '';

    if (servers.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">
            Keine Linux Server registriert. Klicken Sie auf "Server hinzufügen", um zu beginnen.
        </div>`;
        return;
    }

    servers.forEach(s => {
        const card = document.createElement('div');
        card.className = 'server-card';

        let osClass = 'os-debian';
        let osName = 'Debian / Ubuntu';
        if (s.os_type === 'rocky') { osClass = 'os-rocky'; osName = 'Rocky Linux'; }
        if (s.os_type === 'alpine') { osClass = 'os-alpine'; osName = 'Alpine Linux'; }

        const lastCheck = s.last_checked ? new Date(s.last_checked).toLocaleString('de-DE') : 'Nie';

        card.innerHTML = `
            <div>
                <div class="server-head">
                    <div>
                        <div class="server-name">${escapeHtml(s.name)}</div>
                        <div class="server-host">${escapeHtml(s.username)}@${escapeHtml(s.hostname)}:${s.port}</div>
                    </div>
                    <span class="os-badge ${osClass}">${osName}</span>
                </div>
                <div class="server-info-list">
                    <div class="server-info-item">
                        <span>Status:</span>
                        <span class="status-badge status-${s.status}">${getStatusLabel(s.status)}</span>
                    </div>
                    <div class="server-info-item">
                        <span>Verfügbare Updates:</span>
                        <strong style="color: ${s.pending_updates_count > 0 ? 'var(--orange-primary)' : 'var(--success)'}">
                            ${s.pending_updates_count} Pakete
                        </strong>
                    </div>
                    <div class="server-info-item">
                        <span>Zuletzt geprüft:</span>
                        <span style="color: var(--text-muted);">${lastCheck}</span>
                    </div>
                </div>
            </div>
            <div class="server-actions">
                <button class="btn-gradient" onclick="openTerminal(${s.id}, '${escapeHtml(s.name)}')">
                    ⚡ Web Shell
                </button>
                <button class="btn-secondary" onclick="checkUpdates(${s.id})">
                    🔍 Prüfen
                </button>
                ${s.pending_updates_count > 0 ? `
                    <button class="btn-orange" onclick="runUpdates(${s.id})">
                        🚀 Updaten (${s.pending_updates_count})
                    </button>
                ` : ''}
                <button class="btn-secondary" onclick="openLogsModal(${s.id}, '${escapeHtml(s.name)}')">
                    📜 Logs
                </button>
                <button class="btn-danger" onclick="deleteServer(${s.id})">
                    🗑️
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}


function getStatusLabel(status) {
    const map = {
        'ok': 'Bereit / OK',
        'updates_available': 'Updates vorhanden',
        'checking': 'Prüfe...',
        'updating': 'Wird aktualisiert...',
        'error': 'Fehler',
        'unreachable': 'Unerreichbar'
    };
    return map[status] || status;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function openAddServerModal() {
    document.getElementById('serverId').value = '';
    document.getElementById('addServerForm').reset();
    document.getElementById('serverModalTitle').textContent = 'Neuen Linux Server hinzufügen';
    document.getElementById('passwordGroup').classList.remove('hidden');
    document.getElementById('keyGroup').classList.add('hidden');
    document.getElementById('serverModal').classList.remove('hidden');
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    if (id === 'terminalModal') {
        closeTerminal();
    }
}

async function handleSaveServer(e) {
    e.preventDefault();
    const id = document.getElementById('serverId').value;
    const body = {
        name: document.getElementById('serverName').value,
        hostname: document.getElementById('serverHost').value,
        port: parseInt(document.getElementById('serverPort').value),
        os_type: document.getElementById('serverOs').value,
        username: document.getElementById('serverUser').value,
        auth_type: document.getElementById('serverAuthType').value,
        password: document.getElementById('serverPassword').value || null,
        ssh_key: document.getElementById('serverKey').value || null
    };

    const url = id ? `/api/servers/${id}` : '/api/servers';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: authHeaders(),
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error('Fehler beim Speichern des Servers');
        closeModal('serverModal');
        loadServers();
    } catch (err) {
        alert(err.message);
    }
}

async function deleteServer(id) {
    if (!confirm('Möchten Sie diesen Server wirklich löschen?')) return;
    try {
        const res = await fetch(`/api/servers/${id}`, { method: 'DELETE', headers: authHeaders() });
        if (res.ok) loadServers();

// Updates Triggering
async function checkUpdates(id) {
    try {
        loadServers();
        const res = await fetch(`/api/updates/${id}/check`, { method: 'POST', headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            alert(`Prüfung abgeschlossen. ${data.count} Updates gefunden.`);
        } else {
            alert(`Fehler: ${data.error}`);
        }
        loadServers();
    } catch (err) {
        alert('Fehler bei Update-Prüfung');
    }
}

async function checkAllUpdates() {
    try {
        const btn = document.getElementById('btnCheckAll');
        btn.disabled = true;
        btn.textContent = '⏳ Prüfe alle...';
        
        await fetch('/api/updates/check-all', { method: 'POST', headers: authHeaders() });
        btn.disabled = false;
        btn.textContent = '🔍 Alle Server prüfen';
        loadServers();
    } catch (err) {
        alert('Fehler bei der Prüfung aller Server');
    }
}

async function runUpdates(id) {
    if (!confirm('Möchten Sie jetzt alle verfügbaren Updates auf diesem System installieren?')) return;
    try {
        loadServers();
        const res = await fetch(`/api/updates/${id}/run`, { method: 'POST', headers: authHeaders() });
        const data = await res.json();
        if (data.success) {
            alert('Updates erfolgreich installiert!');
        } else {
            alert(`Fehler bei der Update-Durchführung: ${data.error}`);
        }
        loadServers();
    } catch (err) {
        alert('Fehler beim Ausführen der Updates');
    }
}

// Logs Modal
async function openLogsModal(id, serverName) {
    document.getElementById('logsModalTitle').textContent = `Update-Logs für ${serverName}`;
    const logBox = document.getElementById('logContentBox');
    logBox.textContent = 'Lade Protokolle...';
    document.getElementById('logsModal').classList.remove('hidden');

    try {
        const res = await fetch(`/api/updates/${id}/logs`, { headers: authHeaders() });
        const logs = await res.json();

        if (logs.length === 0) {
            logBox.textContent = 'Noch keine Protokolle für diesen Server vorhanden.';
            return;
        }

        let html = '';

// Web Terminal Integration
function openTerminal(serverId, serverName) {
    document.getElementById('terminalServerTitle').textContent = `Web Shell - ${serverName}`;
    document.getElementById('terminalModal').classList.remove('hidden');

    const termContainer = document.getElementById('terminalContainer');
    termContainer.innerHTML = '';

    if (currentWs) { currentWs.close(); }
    if (currentTerm) { currentTerm.dispose(); }

    currentTerm = new Terminal({
        cursorBlink: true,
        fontFamily: 'Courier New, monospace',
        fontSize: 14,
        theme: {
            background: '#090611',
            foreground: '#f3f4f6',
            cursor: '#f97316',
            selectionBackground: 'rgba(139, 92, 246, 0.4)'
        }
    });

    if (window.FitAddon && window.FitAddon.FitAddon) {
        currentTermFitAddon = new window.FitAddon.FitAddon();
        currentTerm.loadAddon(currentTermFitAddon);
    }

    currentTerm.open(termContainer);
    if (currentTermFitAddon) {
        currentTermFitAddon.fit();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${serverId}?token=${authToken}`;
    currentWs = new WebSocket(wsUrl);

    currentWs.onopen = () => {
        if (currentTermFitAddon) currentTermFitAddon.fit();
    };

    currentWs.onmessage = (event) => {
        currentTerm.write(event.data);
    };

    currentWs.onclose = () => {
        currentTerm.write('\r\n\x1b[31m[SSH Session beendet]\x1b[0m\r\n');
    };

    currentWs.onerror = () => {
        currentTerm.write('\r\n\x1b[31m[WebSocket Fehler]\x1b[0m\r\n');
    };

    currentTerm.onData((data) => {
        if (currentWs && currentWs.readyState === WebSocket.OPEN) {
            currentWs.send(data);
        }
    });

    window.addEventListener('resize', handleTermResize);
}

function handleTermResize() {
    if (currentTermFitAddon) {
        currentTermFitAddon.fit();
        if (currentWs && currentWs.readyState === WebSocket.OPEN && currentTerm) {
            currentWs.send(JSON.stringify({
                type: 'resize',
                cols: currentTerm.cols,
                rows: currentTerm.rows
            }));
        }
    }
}

function closeTerminal() {
    window.removeEventListener('resize', handleTermResize);
    if (currentWs) { currentWs.close(); currentWs = null; }
    if (currentTerm) { currentTerm.dispose(); currentTerm = null; }
}

// Password Modal
function openChangePwModal() {
    document.getElementById('changePwForm').reset();
    document.getElementById('changePwError').classList.add('hidden');
    document.getElementById('changePwModal').classList.remove('hidden');
}

async function handleChangePassword(e) {
    e.preventDefault();
    const oldPass = document.getElementById('oldPw').value;
    const newPass = document.getElementById('newPw').value;
    const errDiv = document.getElementById('changePwError');

    errDiv.classList.add('hidden');

    try {
        const res = await fetch('/api/auth/password', {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ old_password: oldPass, new_password: newPass })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Fehler beim Ändern des Passworts');

        alert('Passwort erfolgreich geändert!');
        closeModal('changePwModal');
    } catch (err) {
        errDiv.textContent = err.message;
        errDiv.classList.remove('hidden');
    }
}

        logs.forEach(l => {
            const time = new Date(l.created_at).toLocaleString('de-DE');
            html += `=== [${time}] Aktion: ${l.action.toUpperCase()} | Status: ${l.status.toUpperCase()} ===\n`;
            html += `${l.output || 'Keine Konsolenausgabe'}\n\n`;
        });
        logBox.textContent = html;
    } catch (err) {
        logBox.textContent = 'Fehler beim Laden der Logs';
    }
}

    } catch (err) {
        alert('Fehler beim Löschen');
    }
}

    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('token');
    showLogin();
}
