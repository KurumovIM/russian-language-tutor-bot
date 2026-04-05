"""
Планировщик задач
Task scheduler for daily exercises and subscription management
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import DAILY_EXERCISE_HOUR, DAILY_EXERCISE_MINUTE, TIMEZONE, ADMIN_IDS, DAILY_EXERCISE_COUNT
from database import Database
from exercises import EXERCISES

logger = logging.getLogger(__name__)


class BotScheduler:
    """Планировщик для бота"""

    def __init__(self, bot):
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
            logger.info(f"Планировщик запущен. Серия: {DAILY_EXERCISE_COUNT} упражнений в {DAILY_EXERCISE_HOUR}:{DAILY_EXERCISE_MINUTE:02d} {TIMEZONE}")

        except Exception as e:
            logger.error(f"Ошибка при запуске планировщика: {e}")

    def stop(self):
        """Остановить планировщик"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Планировщик остановлен")

    def _pick_exercises(self, count: int) -> list:
        """Выбрать N случайных уникальных упражнений из банка"""
        count = min(count, len(EXERCISES))
        return random.sample(EXERCISES, count)

    async def send_daily_exercises(self):
        """Отправить ежедневную серию упражнений всем активным студентам"""
        try:
            logger.info(f"Начало отправки серии из {DAILY_EXERCISE_COUNT} упражнений...")

            students = self.db.get_students_for_daily_exercise()
            if not students:
                logger.info("Нет студентов для отправки упражнений")
                return

            # Выбираем одинаковый набор упражнений для всех студентов (за день)
            exercises = self._pick_exercises(DAILY_EXERCISE_COUNT)
            if not exercises:
                logger.error("Нет доступных упражнений в банке")
                return

            sent_count = 0
            failed_count = 0

            for student in students:
                try:
                    user_id = student['user_id']

                    # Вступительное сообщение серии
                    intro_text = (
                        f"📚 <b>Ежедневная серия упражнений</b>\n\n"
                        f"Сегодня вас ждёт <b>{len(exercises)} заданий</b> по русскому языку.\n"
                        f"Решайте в своём темпе — объяснения после каждого ответа!\n\n"
                        f"Начинаем 🚀"
                    )
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=intro_text,
                        parse_mode="HTML"
                    )
                    await asyncio.sleep(0.5)

                    # Отправляем каждое упражнение по очереди
                    for idx, exercise in enumerate(exercises, start=1):
                        message_text = self._format_exercise_message(exercise, idx, len(exercises))
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=message_text,
                            parse_mode="HTML"
                        )
                        # Пауза между заданиями в серии (чтобы не перегружать)
                        await asyncio.sleep(1.0)

                    # Итоговое сообщение серии
                    finish_text = (
                        f"✅ <b>Серия отправлена!</b>\n\n"
                        f"Ответьте на все {len(exercises)} вопроса в боте, "
                        f"чтобы увидеть объяснения и прокачать streak 🔥\n\n"
                        f"Удачи! Следующая серия завтра в "
                        f"{DAILY_EXERCISE_HOUR}:{DAILY_EXERCISE_MINUTE:02d} 🕘"
                    )
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=finish_text,
                        parse_mode="HTML"
                    )

                    sent_count += 1

                except Exception as e:
                    logger.error(f"Ошибка при отправке серии студенту {student['user_id']}: {e}")
                    failed_count += 1

                # Задержка между студентами (чтобы не получить flood limit)
                await asyncio.sleep(0.2)

            logger.info(f"Серии отправлены: {sent_count}, ошибок: {failed_count}")

            # Уведомить администраторов
            for admin_id in ADMIN_IDS:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f"📊 <b>Ежедневная рассылка завершена</b>\n\n"
                            f"📚 Упражнений в серии: {len(exercises)}\n"
                            f"✅ Студентов получило: {sent_count}\n"
                            f"❌ Ошибок: {failed_count}"
                        ),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Критическая ошибка при отправке упражнений: {e}")

    async def check_subscription_expiry(self):
        """Уведомить о скорых истечениях подписок"""
        try:
            logger.info("Проверка истечения подписок...")
            expiring_students = self.db.get_expiring_subscriptions(days=3)

            if not expiring_students:
                logger.info("Нет студентов с истекающими подписками")
                return

            for student in expiring_students:
                try:
                    user_id = student['user_id']
                    tier = student['subscription_tier']
                    end_date = datetime.fromisoformat(student['subscription_end'])
                    days_left = (end_date - datetime.now()).days

                    message_text = (
                        f"⏰ <b>Ваша подписка {tier.upper()} истекает!</b>\n\n"
                        f"Осталось дней: <b>{days_left}</b>\n\n"
                        f"Продлите подписку, чтобы не потерять доступ к ежедневным сериям упражнений!\n\n"
                        f"Нажмите «💳 Подписка» в меню бота."
                    )

                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode="HTML"
                    )

                except Exception as e:
                    logger.error(f"Ошибка при уведомлении студента {student['user_id']}: {e}")

            logger.info(f"Уведомлений об истечении: {len(expiring_students)}")

        except Exception as e:
            logger.error(f"Ошибка при проверке подписок: {e}")

    async def cleanup_old_data(self):
        """Очистить старые данные"""
        try:
            logger.info("Очистка старых данных завершена")
        except Exception as e:
            logger.error(f"Ошибка при очистке: {e}")

    # ==================== УТИЛИТЫ ====================

    def _format_exercise_message(self, exercise: dict, num: int, total: int) -> str:
        """Форматировать сообщение с упражнением в серии"""
        options = exercise.get('options', {})
        options_text = "\n".join([f"{k}) {v}" for k, v in options.items()])

        message = (
            f"<b>📝 Задание {num}/{total}</b>\n"
            f"─────────────────────\n"
            f"<b>Категория:</b> {exercise.get('category', '—')} · "
            f"<b>Уровень:</b> {exercise.get('difficulty', '—').upper()}\n\n"
            f"<b>{exercise.get('title', '')}</b>\n\n"
            f"{exercise.get('content', '')}\n\n"
            f"<b>Варианты ответов:</b>\n"
            f"{options_text}\n\n"
            f"<i>Правильный ответ: {exercise.get('correct_answer', '?')}</i>\n"
            f"<i>💡 {exercise.get('hint', '')}</i>"
        )
        return message.strip()

    def pause_scheduler(self):
        if self.is_running:
            self.scheduler.pause()
            logger.info("Планировщик приостановлен")

    def resume_scheduler(self):
        if self.is_running:
            self.scheduler.resume()
            logger.info("Планировщик возобновлён")

    def get_jobs_info(self) -> list:
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time
            })
        return jobs_info
