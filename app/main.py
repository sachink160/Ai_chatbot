from fastapi import FastAPI, Depends
from app.routes import user_routes, rag_rout, tools_rout, hr_rout, video_to_audio_rout, subscription_rout, dynamic_prompt_routes, logs_routes, crm_routes, resume_routes
from app.routes import image_routes, master_settings_routes
from app.database import Base, engine
from app.auth import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
from apscheduler.triggers.interval import IntervalTrigger # type: ignore

from app.Agent.news import run_news_agent
from app.logger import get_logger
from app.middleware import LoggingMiddleware, ErrorHandlingMiddleware
logger = get_logger(__name__)

scheduler = AsyncIOScheduler()

# def print_hello():
#     print("Hello from cron job!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    scheduler.add_job(run_news_agent, 'interval', hours=10, max_instances=2)
    # scheduler.add_job(run_news_agent, 'interval', hours=10, max_instances=2)
    scheduler.start()
    logger.info("Scheduler started.")
    
    # Initialize subscription plans
    try:
        from app.subscription_service import SubscriptionService
        from app.database import SessionLocal
        db = SessionLocal()
        SubscriptionService.create_subscription_plans(db)
        db.close()
        logger.info("Subscription plans initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize subscription plans: {e}")
    
    yield  # App is running
    # Shutdown tasks
    scheduler.shutdown()
    logger.info("Scheduler stopped.")


Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)

# Add middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(user_routes.router)
app.include_router(rag_rout.router)
app.include_router(tools_rout.router)
app.include_router(hr_rout.router)
app.include_router(video_to_audio_rout.router)
app.include_router(subscription_rout.router)
app.include_router(dynamic_prompt_routes.router)
app.include_router(logs_routes.router)
app.include_router(crm_routes.router)
app.include_router(resume_routes.router)
app.include_router(image_routes.router)
app.include_router(master_settings_routes.router)
# app.include_router(social_media_rout.router)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace with your frontend's origin, like "http://localhost:5500"
    allow_credentials=True,
    allow_methods=["*"],  # Or ["GET", "POST", "OPTIONS", "PUT", "DELETE"]
    allow_headers=["*"],  # Or ["Authorization", "Content-Type"]
)

# Profile endpoint moved to user_routes.py