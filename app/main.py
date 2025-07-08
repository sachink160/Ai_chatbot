from fastapi import FastAPI, Depends
from app.routes import user_routes, rag_rout, tools_rout, hr_rout, video_to_audio_rout
from app.database import Base, engine
from app.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.Agent.news import run_news_agent

scheduler = AsyncIOScheduler()

# def print_hello():
#     print("Hello from cron job!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    # scheduler.add_job(run_news_agent, 'interval', seconds=40, max_instances=2)
    # scheduler.add_job(run_news_agent, 'interval', minutes=1, max_instances=2)
    scheduler.add_job(run_news_agent, 'interval', hours=10, max_instances=2)

    scheduler.start()

    print("Scheduler started.")
    
    yield  # App is running

    # Shutdown tasks
    scheduler.shutdown()
    print("Scheduler stopped.")


Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)
app.include_router(user_routes.router)
app.include_router(rag_rout.router)
app.include_router(tools_rout.router)
app.include_router(hr_rout.router)
app.include_router(video_to_audio_rout.router)
# app.include_router(social_media_rout.router)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace with your frontend's origin, like "http://localhost:5500"
    allow_credentials=True,
    allow_methods=["*"],  # Or ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
    allow_headers=["*"],  # Or ["Authorization", "Content-Type"]
)

@app.get("/profile", tags=["Profile"])
def get_profile(current_user: str = Depends(get_current_user)):
    return {"message": "Welcome", "user": current_user}
