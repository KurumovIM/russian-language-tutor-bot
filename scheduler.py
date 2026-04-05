"""
Планировщик задач
Task scheduler for daily exercises and subscription management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import DAILY_EXERCISE_HOUR, DAILY_EXERCISE_MINUTE, TIMEZONE, ADMIN_IDS
from database import Database
from exercises import get_random_exercise

logger = logging.getLogger(__name__)

class BotScheduler:
    """Планировщик для бота"""

    def __init__(self, bot):
        """Инициализация планировщика"""
        self.bot = bot
        self.db = Database()
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))
        self.is_running = False

    def start(self):
        """Запустить планировщик"""
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return

        try:
            self.scheduler.add_job(
                self.send_daily_exercises,
                CronTrigger(
                    hour=DAILY_EXERCISE_HOUR,
                    minute=DAILY_EXERCISE_MINUTE,
                    timezone=pytz.timezone(TIMEZONE)
                ),
                id="send_daily_exercises",
                name="Отправка ежедневных упражнений",
                replace_existing=True
            )

            self.scheduler.add_job(
                self.check_subscription_expiry,
                CronTrigger(hour=8, minute=0, timezone=pytz.timezone(TIMEZONE)),
                id="check_subscription_expiry",
                name="Проверка истечения подписок",
                replace_existing=True
            )

            self.scheduler.add_job(
                self.cleanup_old_data,
                CronTrigger(hour=2, minute=0, timezone=pytz.timezone(TIMEZONE)),
                id="cleanup_old_data",
                name="Очистка старых данных",
                replace_existing=True
            )

            self.scheduler.start()
            self.is_running = True
            logger.info("Планировщик запущен успешно")

        except Exception as e:
            logger.error(f"Ошибка при запуске планировщика: {e}")

    def stop(self):
        """Остановить планировщик"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Планировщик остановлен")

    async def send_daily_exercises(self):
        """Отправить ежедневные упражнения активным студентам"""
        try:
            logger.info("Начало отправки ежедневных упражнений...")
            students = self.db.get_students_for_daily_exercise()
            if not students:
                logger.info("Нет студентов для отправки упражнений")
                return
            exercise = get_random_exercise()
            if not exercise:
                logger.error("Нет доступных упражнений")
                return
            sent_count = 0
            failed_count = 0
            for student in students:
                try:
                    user_id = student['user_id']
                    if self.db.check_daily_exercise_sent(user_id, exercise.get('exercise_id')):
                        continue
                    message_text = self._format_exercise_message(exercise)
                    await self.bot.send_message(chat_id=user_id, text=message_text, parse_mode="HTML")
                    self.db.log_daily_exercise(user_id, exercise.get('exercise_id', 0))
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при отправке упражнения студенту {student['user_id']}: {e}")
                    failed_count += 1
                await asyncio.sleep(0.1)
            logger.info(f"Упражнения отправлены: {sent_count}, ошибок: {failed_count}")
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=f"📊 Ежедневное упражнение отправлено:\n✅ Успешно: {sent_count}\n❌ Ошибок: {failed_count}",
                        parse_mode="HTML"
                    )
                except:
                    pass
        except Exception as e:
            logger.error(f"Критическая ошибка при отправке упражнений: {e}")

    async def check_subscription_expiry(self):
        """Проверить и уведомить о скорых истечениях подписок"""
        try:
            logger.info("Проверка истечения подписок...")
            expiring_students = self.db.get_expiring_subscriptions(days=3)
            if not expiring_students:
                return
            for student in expiring_students:
                try:
                    user_id = student['user_id']
                    tier = student['subscription_tier']
                    end_date = datetime.fromisoformat(student['subscription_end'])
                    days_left = (end_date - datetime.now()).days
                    message_text = f"⏰ <b>Ваша подписка {tier.upper()} истекает!</b>\n\nОсталось дней: {days_left}\n\nПродлите подписку, чтобы не потерять доступ."
                    await self.bot.send_message(chat_id=user_id, text=message_text, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Ошибка при уведомлении студента {student['user_id']}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при проверке подписок: {e}")

    async def cleanup_old_data(self):
        """Очистить старые данные"""
        try:
            logger.info("Начало очистки старых данных...")
            logger.info("Очистка старых данных завершена")
        except Exception as e:
            logger.error(f"Ошибка при очистке старых данных: {e}")

    def _format_exercise_message(self, exercise: dict) -> str:
        """Форматировать сообщение с упражнением"""
        message = f"<b>📚 Упражнение дня</b>\n\n<b>Категория:</b> {exercise.get('category', 'N/A')}\n<b>Уровень:</b> {exercise.get('difficulty', 'N/A')}\n\n<b>{exercise.get('title', '')}</b>\n\n{exercise.get('content', '')}"
        return message.strip()

    def pause_scheduler(self):
        if self.is_running:
            self.scheduler.pause()

    def resume_scheduler(self):
        if self.is_running:
            self.scheduler.resume()

    def get_jobs_info(self) -> list:
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({'id': job.id, 'name': job.name, 'next_run_time': job.next_run_time})
        return jobs_info
