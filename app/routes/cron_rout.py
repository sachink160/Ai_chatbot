from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.logger import get_logger
logger = get_logger(__name__)

scheduler = AsyncIOScheduler()

def print_hello():
    print("Hello from cron job!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    scheduler.add_job(print_hello, IntervalTrigger(seconds=3))
    scheduler.start()

    print("Scheduler started.")
    
    yield  # App is running

    # Shutdown tasks
    scheduler.shutdown()
    print("Scheduler stopped.")

app = FastAPI(lifespan=lifespan)
