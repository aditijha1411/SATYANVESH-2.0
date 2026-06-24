from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database.postgres import engine, Base
import models.case
import models.evidence
import models.entity
import models.event
import models.relationship
import models.notebook
from api.routes import cases, evidence, graph, timeline, leads, reports, notebook
from api.routes import entities, events, geo

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Assisted Case-Centric Digital Investigation Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(graph.router)
app.include_router(timeline.router)
app.include_router(leads.router)
app.include_router(reports.router)
app.include_router(notebook.router)
app.include_router(entities.router)
app.include_router(events.router)
app.include_router(geo.router)

@app.get("/")
def root():
    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "ok"}