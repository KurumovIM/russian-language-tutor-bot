"""
Основной файл бота для репетитора русского языка
Main bot file for Russian language tutor
"""

import logging
import asyncio
from datetime import datetime, timedelta
import json

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN, ADMIN_IDS, SUBSCRIPTION_FEATURES, SUBSCRIPTION_PRICES
from database import Database
from keyboards import *
from exercises import get_all_exercises, get_exercise_categories, get_random_exercise, get_exercise_by_category
from scheduler import BotScheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== FSM СОСТОЯНИЯ ====================

class StudentStates(StatesGroup):
    """Состояния для студентов"""
    solving_exercise = State()
    exercise_category = State()
    taking_test = State()
    test_question = State()
    submitting_homework = State()
    homework_text = State()
    choosing_subscription = State()


class AdminStates(StatesGroup):
    """Состояния для администраторов"""
    adding_exercise = State()
    exercise_category = State()
    exercise_title = State()
    exercise_content = State()
    exercise_answer = State()
    exercise_explanation = State()
    exercise_difficulty = State()
    creating_test = State()
    test_title = State()
    test_description = State()
    test_category = State()
    assigning_homework = State()
    homework_title = State()
    homework_task = State()
    homework_student = State()
    sending_broadcast = State()
    broadcast_message = State()


# ==================== ИНИЦИАЛИЗАЦИЯ ====================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()
scheduler = BotScheduler(bot)

user_current_exercise = {}
user_test_session = {}
user_test_answers = {}

# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "User"
    first_name = message.from_user.first_name or ""
    db.add_or_update_student(user_id, username, first_name)
    student = db.get_student(user_id)

    welcome_text = f"""
👋 <b>Добро пожаловать в бота репетитора русского языка!</b>

Я помогу вам:
📚 Решать ежедневные упражнения по грамматике, пунктуации и орфографии
📝 Проходить интерактивные тесты
📊 Отслеживать ваш прогресс
💳 Выбрать нужную подписку

<b>Ваш текущий статус:</b>
Подписка: {student['subscription_tier'].upper()}
Решено упражнений: {student['total_exercises_completed']}
Текущий streak: {student['current_streak']} дней 🔥

Нажмите кнопку ниже, чтобы начать!
    """

    if user_id in ADMIN_IDS:
        keyboard = admin_menu_kb()
        welcome_text += "\n\n👑 <b>Вы администратор!</b>"
    else:
        keyboard = student_menu_kb()

    await state.clear()
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
<b>📚 Справка по боту</b>

<b>Основные функции:</b>
/start - Начало работы
/help - Справка
/menu - Главное меню
/stats - Мою статистику
/subscription - Управление подпиской
/referral - Реферальная система

<b>Для студентов:</b>
📚 Упражнение - решить упражнение дня
📝 Тест - пройти интерактивный тест
📊 Прогресс - посмотреть статистику
💳 Подписка - выбрать план

<b>Для администраторов:</b>
/admin_menu - Меню администратора
/analytics - Аналитика бота
/broadcast - Отправить рассылку
    """
    await message.answer(help_text, parse_mode="HTML")


@dp.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    if user_id in ADMIN_IDS:
        keyboard = admin_menu_kb()
    else:
        keyboard = student_menu_kb()
    await message.answer("🏠 Главное меню", reply_markup=keyboard)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    stats = db.get_student_stats(user_id)
    if not stats:
        await message.answer("❌ Статистика не найдена. Начните с /start")
        return

    stats_text = f"""
<b>📊 Ваша статистика</b>

👤 <b>Имя:</b> {stats['username']}
🎯 <b>Подписка:</b> {stats['subscription_tier'].upper()}
📚 <b>Решено упражнений:</b> {stats['total_exercises']}
🔥 <b>Текущий streak:</b> {stats['current_streak']} дней
🏆 <b>Максимальный streak:</b> {stats['max_streak']} дней
✅ <b>Тестов пройдено:</b> {stats['total_tests_passed']}
📈 <b>Успешность:</b> {stats['exercise_success_rate']:.1f}%

<b>🔍 Слабые области:</b>
    """

    weak_areas = stats.get('weak_areas', {})
    if weak_areas:
        for category, success_rate in sorted(weak_areas.items(), key=lambda x: x[1])[:3]:
            stats_text += f"\n• {category}: {success_rate*100:.1f}%"
    else:
        stats_text += "\n• Нет данных"

    if stats['subscription_end']:
        end_date = datetime.fromisoformat(stats['subscription_end'])
        days_left = (end_date - datetime.now()).days
        if days_left > 0:
            stats_text += f"\n\n💳 <b>Подписка активна ещё {days_left} дней</b>"

    await message.answer(stats_text, parse_mode="HTML")


# ==================== ГЛАВНОЕ МЕНЮ ====================

@dp.message(F.text == "🏠 Главное меню")
async def handle_main_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    if user_id in ADMIN_IDS:
        keyboard = admin_menu_kb()
    else:
        keyboard = student_menu_kb()
    await message.answer("🏠 Главное меню", reply_markup=keyboard)


# ==================== УПРАЖНЕНИЯ ====================

@dp.message(F.text == "📚 Упражнение")
async def start_exercise(message: Message, state: FSMContext):
    user_id = message.from_user.id
    student = db.get_student(user_id)
    if not student:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    if student['subscription_tier'] == 'free':
        await message.answer(
            "📌 Вы используете Free план. Упражнения доступны для Premium и Pro подписок.",
            reply_markup=subscription_kb()
        )
        return
    categories = get_exercise_categories()
    keyboard = categories_kb(categories)
    await state.set_state(StudentStates.exercise_category)
    await message.answer("📚 Выберите категорию упражнения:", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("cat_"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    category = callback.data.replace("cat_", "")
    exercises = get_exercise_by_category(category)
    if not exercises:
        await callback.answer("❌ В этой категории нет упражнений")
        return
    import random
    exercise = random.choice(exercises)
    user_current_exercise[user_id] = exercise
    exercise_text = f"""
<b>{exercise['title']}</b>

📌 <b>Категория:</b> {exercise['category']}
📊 <b>Уровень:</b> {exercise['difficulty'].upper()}

{exercise['content']}

<b>Варианты ответов:</b>
A) {exercise['options']['A']}
B) {exercise['options']['B']}
C) {exercise['options']['C']}
D) {exercise['options']['D']}
    """
    keyboard = exercise_answer_kb(exercise.get('id', 0))
    await state.set_state(StudentStates.solving_exercise)
    await callback.message.answer(exercise_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.startswith("answer_"))
async def answer_exercise(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id not in user_current_exercise:
        await callback.answer("❌ Упражнение не найдено")
        return
    exercise = user_current_exercise[user_id]
    user_answer = callback.data.replace("answer_", "").split("_")[0].upper()
    correct_answer = exercise['correct_answer']
    is_correct = user_answer == correct_answer
    db.record_exercise_attempt(user_id, exercise.get('id', 0), user_answer, is_correct)
    if is_correct:
        db.update_streak(user_id, increment=True)
    if is_correct:
        result_text = f"""
<b>✅ Правильно!</b>

<b>Ваш ответ:</b> {user_answer}
<b>Объяснение:</b>
{exercise['explanation']}

🎉 Отлично! Вы набрали 1 очко!
        """
    else:
        result_text = f"""
<b>❌ Неверно!</b>

<b>Ваш ответ:</b> {user_answer}
<b>Правильный ответ:</b> {correct_answer}

<b>Объяснение:</b>
{exercise['explanation']}

<b>Подсказка:</b>
{exercise.get('hint', 'Подсказки нет')}

Попробуйте ещё раз или переходите к следующему!
        """
    keyboard = exercise_result_kb(exercise.get('id', 0), is_correct)
    await callback.message.answer(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.startswith("hint_"))
async def hint_exercise(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_current_exercise:
        await callback.answer("❌ Упражнение не найдено")
        return
    exercise = user_current_exercise[user_id]
    hint = exercise.get('hint', 'Подсказки нет для этого упражнения')
    await callback.answer(f"💡 Подсказка: {hint}", show_alert=True)


@dp.callback_query(F.data.startswith("next_exercise"))
async def next_exercise(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if user_id in user_current_exercise:
        del user_current_exercise[user_id]
    categories = get_exercise_categories()
    keyboard = categories_kb(categories)
    await state.set_state(StudentStates.exercise_category)
    await callback.message.answer("📚 Выберите следующее упражнение:", reply_markup=keyboard)
    await callback.answer()


# ==================== ТЕСТЫ ====================

@dp.message(F.text == "📝 Тест")
async def start_test(message: Message, state: FSMContext):
    user_id = message.from_user.id
    student = db.get_student(user_id)
    if not student:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
    if student['subscription_tier'] == 'free':
        await message.answer(
            "📌 Базовые тесты доступны. Полный доступ на Premium и Pro подписках.",
            reply_markup=subscription_kb()
        )
    tests = db.get_all_tests()
    if not tests:
        await message.answer("❌ Тестов пока нет. Вернитесь позже!")
        return
    keyboard = test_selection_kb(tests)
    await state.set_state(StudentStates.test_question)
    await message.answer("📝 Выберите тест:", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("test_"))
async def select_test(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    test_id = int(callback.data.replace("test_", ""))
    test = db.get_test(test_id)
    if not test:
        await callback.answer("❌ Тест не найден")
        return
    questions = db.get_test_questions(test_id)
    if not questions:
        await callback.answer("❌ В этом тесте нет вопросов")
        return
    user_test_session[user_id] = {'test_id': test_id, 'current_question': 0, 'score': 0}
    user_test_answers[user_id] = {}
    question = questions[0]
    question_text = f"""
<b>{test['title']}</b>

<b>Вопрос 1 из {len(questions)}</b>

{question['question_text']}

A) {question['option_a']}
B) {question['option_b']}
C) {question['option_c']}
D) {question['option_d']}
    """
    keyboard = test_question_kb(question['question_id'])
    await callback.message.answer(question_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data.startswith("test_ans_"))
async def answer_test_question(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_test_session:
        await callback.answer("❌ Сессия теста не найдена")
        return
    answer = callback.data.split("_")[2].upper()
    question_id = int(callback.data.split("_")[3])
    if user_id not in user_test_answers:
        user_test_answers[user_id] = {}
    user_test_answers[user_id][question_id] = answer
    session = user_test_session[user_id]
    test_id = session['test_id']
    questions = db.get_test_questions(test_id)
    question = next((q for q in questions if q['question_id'] == question_id), None)
    if question and answer == question['correct_option']:
        session['score'] += 1
        await callback.answer("✅ Правильно!")
    else:
        await callback.answer(f"❌ Неверно. Правильный ответ: {question['correct_option']}")
    session['current_question'] += 1
    if session['current_question'] < len(questions):
        next_question = questions[session['current_question']]
        question_text = f"""
<b>{db.get_test(test_id)['title']}</b>

<b>Вопрос {session['current_question'] + 1} из {len(questions)}</b>

{next_question['question_text']}

A) {next_question['option_a']}
B) {next_question['option_b']}
C) {next_question['option_c']}
D) {next_question['option_d']}
        """
        keyboard = test_question_kb(next_question['question_id'])
        await callback.message.answer(question_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        test = db.get_test(test_id)
        score = session['score']
        max_score = len(questions)
        percent = (score / max_score * 100) if max_score > 0 else 0
        db.record_test_result(user_id, test_id, score, max_score, user_test_answers[user_id])
        result_text = f"""
<b>🎉 Тест завершен!</b>

<b>{test['title']}</b>

📊 <b>Результат:</b> {score}/{max_score} ({percent:.1f}%)

{'✅ <b>Вы прошли тест!</b>' if percent >= test['passing_score'] else '❌ <b>Вы не прошли тест.</b>'}
        """
        await callback.message.answer(result_text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
        if user_id in user_test_session:
            del user_test_session[user_id]
        if user_id in user_test_answers:
            del user_test_answers[user_id]


# ==================== ПРОГРЕСС ====================

@dp.message(F.text == "📊 Мой прогресс")
async def show_progress(message: Message):
    user_id = message.from_user.id
    stats = db.get_student_stats(user_id)
    if not stats:
        await message.answer("❌ Данные не найдены")
        return
    progress_text = f"""
<b>📊 Ваш прогресс</b>

👤 <b>Имя:</b> {stats['username']}
🎯 <b>Подписка:</b> {stats['subscription_tier'].upper()}

<b>📈 Статистика упражнений:</b>
• Решено: {stats['total_exercises']}
• Успешность: {stats['exercise_success_rate']:.1f}%

<b>🔥 Streaks:</b>
• Текущий: {stats['current_streak']} дней
• Максимальный: {stats['max_streak']} дней

<b>📋 Тесты:</b>
• Пройдено: {stats['total_tests_passed']}
    """
    weak_areas = stats.get('weak_areas', {})
    if weak_areas:
        progress_text += "\n\n<b>🎯 Слабые области:</b>"
        for i, (category, success_rate) in enumerate(sorted(weak_areas.items(), key=lambda x: x[1])[:5], 1):
            progress_text += f"\n{i}. {category}: {success_rate*100:.1f}%"
    await message.answer(progress_text, reply_markup=back_to_menu_kb(), parse_mode="HTML")


# ==================== ПОДПИСКА ====================

@dp.message(F.text == "💳 Подписка")
async def manage_subscription(message: Message, state: FSMContext):
    user_id = message.from_user.id
    student = db.get_student(user_id)
    info_text = f"""
<b>💳 Подписка и планы</b>

<b>Ваш текущий план:</b> {student['subscription_tier'].upper()}

<b>🎁 Free (Бесплатно)</b>
✓ 1 упражнение в день
✓ Базовые тесты
✗ Нет объяснений

<b>⭐ Premium ($5/месяц)</b>
✓ Неограниченные упражнения
✓ Все тесты
✓ Детальные объяснения
✓ Домашние задания

<b>👑 Pro ($10/месяц)</b>
✓ Всё из Premium
✓ Приоритетная поддержка
✓ Персональные рекомендации

Выберите план:
    """
    await state.set_state(StudentStates.choosing_subscription)
    await message.answer(info_text, reply_markup=subscription_kb(), parse_mode="HTML")


@dp.callback_query(F.data.startswith("sub_"))
async def choose_subscription(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    tier = callback.data.replace("sub_", "")
    if tier == "free":
        await callback.message.answer("✅ Вы уже используете бесплатный план!", reply_markup=back_to_menu_kb())
    else:
        price = SUBSCRIPTION_PRICES[tier]
        db.update_student_subscription(user_id, tier, 30)
        confirm_text = f"""
<b>💳 Подписка активирована!</b>

<b>План:</b> {tier.upper()}
<b>Цена:</b> ${price}/месяц
<b>Период:</b> 30 дней
        """
        await callback.message.answer(confirm_text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
        await callback.answer("✅ Подписка активирована!", show_alert=True)
    await state.clear()


# ==================== РЕФЕРАЛЫ ====================

@dp.message(F.text == "👥 Реферралы")
async def show_referral(message: Message):
    user_id = message.from_user.id
    referral_count = db.get_referral_count(user_id)
    referral_text = f"""
<b>👥 Реферральная система</b>

Пригласите друга и получайте бонусы!

<b>Как это работает:</b>
1️⃣ Поделитесь своей реферальной ссылкой
2️⃣ Ваш друг зарегистрируется по ссылке
3️⃣ Вы получите 7 дней бесплатной подписки!

<b>Ваша статистика:</b>
✅ Успешных рефералов: {referral_count}
🎁 Бонусов получено: {referral_count * 7} дней

<b>Ваша реферальная ссылка:</b>
https://t.me/russian_practice_ege_bot?start=ref_{user_id}
    """
    await message.answer(referral_text, reply_markup=referral_kb(user_id), parse_mode="HTML")


# ==================== ДОМАШНИЕ ЗАДАНИЯ ====================

@dp.message(F.text == "📥 Домашнее задание")
async def manage_homework(message: Message):
    user_id = message.from_user.id
    homework_list = db.get_student_homework(user_id)
    active = [hw for hw in homework_list if hw['status'] != 'graded']
    homework_text = f"<b>📥 Домашние задания</b>\n\n<b>Активных заданий:</b> {len(active)}\n"
    if homework_list:
        for hw in homework_list[:5]:
            status_emoji = {'assigned': '📌', 'submitted': '✍️', 'graded': '✅'}.get(hw['status'], '❓')
            homework_text += f"\n{status_emoji} {hw['title']}"
            if hw['status'] == 'graded' and hw['grade']:
                homework_text += f" - Оценка: {hw['grade']}/100"
    else:
        homework_text += "\nПока нет заданий 😊"
    await message.answer(homework_text, reply_markup=homework_kb(), parse_mode="HTML")


# ==================== CALLBACK: ГЛАВНОЕ МЕНЮ ====================

@dp.callback_query(F.data == "to_main_menu")
async def to_main_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.clear()
    if user_id in ADMIN_IDS:
        keyboard = admin_menu_kb()
    else:
        keyboard = student_menu_kb()
    await callback.message.answer("🏠 Главное меню", reply_markup=keyboard)
    await callback.answer()


# ==================== АДМИНИСТРАТОР ====================

@dp.message(F.text == "➕ Добавить упражнение")
async def admin_add_exercise(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора")
        return
    await state.set_state(AdminStates.exercise_category)
    await message.answer("📝 Введите категорию упражнения:", reply_markup=back_to_menu_kb())


@dp.message(AdminStates.exercise_category)
async def admin_exercise_category(message: Message, state: FSMContext):
    if message.text == "🏠 Главное меню":
        await state.clear()
        await message.answer("Отмена", reply_markup=admin_menu_kb())
        return
    await state.update_data(category=message.text)
    await state.set_state(AdminStates.exercise_title)
    await message.answer("📝 Введите название упражнения:")


@dp.message(AdminStates.exercise_title)
async def admin_exercise_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AdminStates.exercise_content)
    await message.answer("📝 Введите содержание упражнения и варианты A/B/C/D:")


@dp.message(AdminStates.exercise_content)
async def admin_exercise_content(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    await state.set_state(AdminStates.exercise_answer)
    await message.answer("📝 Какой правильный ответ? (A, B, C или D):")


@dp.message(AdminStates.exercise_answer)
async def admin_exercise_answer(message: Message, state: FSMContext):
    answer = message.text.upper()
    if answer not in ['A', 'B', 'C', 'D']:
        await message.answer("❌ Пожалуйста, выберите A, B, C или D")
        return
    await state.update_data(correct_answer=answer)
    await state.set_state(AdminStates.exercise_explanation)
    await message.answer("📝 Введите объяснение ответа:")


@dp.message(AdminStates.exercise_explanation)
async def admin_exercise_explanation(message: Message, state: FSMContext):
    await state.update_data(explanation=message.text)
    await state.set_state(AdminStates.exercise_difficulty)
    await message.answer("📝 Уровень сложности (easy, intermediate, hard):")


@dp.message(AdminStates.exercise_difficulty)
async def admin_exercise_difficulty(message: Message, state: FSMContext):
    difficulty = message.text.lower()
    if difficulty not in ['easy', 'intermediate', 'hard']:
        difficulty = 'intermediate'
    data = await state.get_data()
    db.add_exercise(
        category=data['category'],
        title=data['title'],
        content=data['content'],
        correct_answer=data['correct_answer'],
        explanation=data['explanation'],
        difficulty=difficulty
    )
    await state.clear()
    await message.answer("✅ Упражнение добавлено успешно!", reply_markup=admin_menu_kb())


@dp.message(F.text == "📊 Аналитика")
async def admin_analytics(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора")
        return
    analytics = db.get_admin_analytics()
    analytics_text = f"""
<b>📊 Аналитика бота</b>

<b>👥 Студенты:</b>
• Всего: {analytics['total_students']}
• Активных: {analytics['active_students']}
• Платящих: {analytics['paying_students']}

<b>📚 Контент:</b>
• Упражнений: {analytics['total_exercises']}
• Тестов: {analytics['total_tests']}

<b>💳 Распределение по подпискам:</b>
    """
    for tier, count in analytics['tier_distribution'].items():
        analytics_text += f"\n• {tier.upper()}: {count}"
    await message.answer(analytics_text, reply_markup=back_to_menu_kb(), parse_mode="HTML")


# ==================== ЗАПУСК ====================

async def main():
    """Запуск бота"""
    logger.info("Запуск бота...")
    scheduler.start()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
