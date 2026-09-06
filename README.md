# Server- & Update-Verwaltung 🚀

Eine moderne Web-Software in Docker zur Verwaltung von Linux-Servern (Debian, Rocky Linux, Alpine Linux), inklusive Live-Web-Shell im Browser und automatischer Update-Verwaltung.

![Design](https://img.shields.io/badge/Theme-Orange%20%26%20Lila-8b5cf6?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)

---

## 🚀 Features

- **🔑 Authentifizierung**: Standard-Zugangsdaten `admin` / `admin` (Passwort-Hash in MySQL/MariaDB gespeichert, im Web-Interface änderbar).
- **🖥️ Server-Verwaltung**: Hinzufügen, Bearbeiten und Löschen von Linux-Servern mit SSH-Passwort oder SSH-Private-Key.
- **⚡ Web SSH Shell**: Direktes interaktives Terminal im Webbrowser via WebSockets & xterm.js.
- **📦 Update-Verwaltung**:
  - **Debian / Ubuntu**: Paketprüfungen und Upgrade via `apt-get`.
  - **Rocky Linux / RHEL**: Paketprüfungen und Upgrade via `dnf`.
  - **Alpine Linux**: Paketprüfungen und Upgrade via `apk`.
  - Einzelne sowie parallele System-Updates mit Protokollierung.
- **🎨 Design**: Dunkles Theme im **Orange & Lila** Farbverlauf.

---

## 🐳 Lokal mit Docker Compose ausführen

```bash
# Repository klonen
git clone https://github.com/Korbinian0/Server-Update_Verwaltung.git
cd Server-Update_Verwaltung

# Container starten
docker compose up -d --build
```

- **Web-Interface**: [http://localhost:8000](http://localhost:8000)
- **Standard-Login**: `admin` / `admin`

---

## 🤖 GitHub Actions Docker Workflow (CI/CD)

Ein fertiger GitHub Workflow ist in `.github/workflows/docker-ci-cd.yml` integriert:

- **Syntax & Docker Validate**: Prüft bei jedem `push` und `pull_request` den Code & Compose-Files.
- **Build & Push**: Baut das Docker-Image automatisch bei jedem Push auf `main`/`master` und lädt es auf die **GitHub Container Registry (`ghcr.io`)** hoch.
