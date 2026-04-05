"""
Конфигурация для Telegram-бота русского языка
Configuration for Russian language tutor bot
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "student_bot.db")

# Subscription prices (в долларах USD)
SUBSCRIPTION_PRICES = {
    "free": 0,
    "premium": 5,
    "pro": 10
}

# Features по подписке
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

# Количество упражнений в ежедневной серии (можно менять в Railway → Variables)
DAILY_EXERCISE_COUNT = int(os.getenv("DAILY_EXERCISE_COUNT", "5"))

# Admin IDs (список ID администраторов)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Referral system
REFERRAL_DAYS = 7  # бесплатных дней за реферала

# Database backup path
BACKUP_PATH = os.getenv("BACKUP_PATH", "backups/")
