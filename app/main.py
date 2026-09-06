import os
import time
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import OperationalError

from app.database import engine, Base, SessionLocal
from app.auth import init_default_user
from app.routers import auth, servers, updates, terminal

app = FastAPI(title="Server- & Update-Verwaltung", version="1.0.0")

# Mount Static & Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Include Routers
app.include_router(auth.router)
app.include_router(servers.router)
app.include_router(updates.router)
app.include_router(terminal.router)

@app.on_event("startup")
def startup_db():
    # Retries for MySQL connection during container startup
    max_retries = 30
    for i in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                init_default_user(db)
            finally:
                db.close()
            print("[Startup] Database tables initialized and default user verified.")
            break
        except OperationalError as e:
            print(f"[Startup] Waiting for MySQL database connection ({i+1}/{max_retries})...")
            time.sleep(2)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
