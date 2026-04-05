"""
ÐÐ¾Ð½ÑÐ¸Ð³ÑÑÐ°ÑÐ¸Ñ Ð´Ð»Ñ Telegram-Ð±Ð¾ÑÐ° ÑÑÑÑÐºÐ¾Ð³Ð¾ ÑÐ·ÑÐºÐ°
Configuration for Russian language tutor bot
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "student_bot.db")

# Subscription prices (Ð² Ð´Ð¾Ð»Ð»Ð°ÑÐ°Ñ USD, ÐºÐ¾Ð½Ð²ÐµÑÑÐ¸ÑÑÑÑÑÑ Ð² ÑÑÐ±Ð»Ð¸)
SUBSCRIPTION_PRICES = {
    "free": 0,
    "premium": 5,
    "pro": 10
}

# Features Ð¿Ð¾ Ð¿Ð¾Ð´Ð¿Ð¸ÑÐºÐµ
SUBSCRIPTION_FEATURES = {
    "free": {
        "daily_exercises": 1,
        "interactive_tests": True,
        "progress_tracking": True,
        "detailed_explanations": False,
        "homework_submission": False,
        "feedback_queue": False,
        "priority_support": False,
    },
    "premium": {
        "daily_exercises": 100,
        "interactive_tests": True,
        "progress_tracking": True,
        "detailed_explanations": True,
        "homework_submission": True,
        "feedback_queue": False,
        "priority_support": False,
    },
    "pro": {
        "daily_exercises": 100,
        "interactive_tests": True,
        "progress_tracking": True,
        "detailed_explanations": True,
        "homework_submission": True,
        "feedback_queue": True,
        "priority_support": True,
    }
}

# Time configuration for daily exercises
DAILY_EXERCISE_HOUR = int(os.getenv("DAILY_EXERCISE_HOUR", "9"))
DAILY_EXERCISE_MINUTE = int(os.getenv("DAILY_EXERCISE_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Admin IDs (ÑÐ¿Ð¸ÑÐ¾Ðº ID Ð°Ð´Ð¼Ð¸Ð½Ð¸ÑÑÑÐ°ÑÐ¾ÑÐ¾Ð²)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Referral system
REFERRAL_DAYS = 7  # Ð±ÐµÑÐ¿Ð»Ð°ÑÐ½ÑÑ Ð´Ð½ÐµÐ¹ Ð·Ð° ÑÐµÑÐµÑÐ°Ð»Ð°

# Database backup path
BACKUP_PATH = os.getenv("BACKUP_PATH", "backups/")
