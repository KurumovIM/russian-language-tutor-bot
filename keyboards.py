"""
Клавиатуры и кнопки для бота
Keyboards and buttons for the bot
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# ==================== ОСНОВНЫЕ КЛАВИАТУРЫ ====================

def main_menu_kb() -> ReplyKeyboardMarkup:
    """Главное меню"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="📚 Упражнение")
    kb.button(text="📝 Тест")
    kb.button(text="📊 Мой прогресс")
    kb.button(text="📥 Домашнее задание")
    kb.button(text="👥 Реферальная система")
    kb.button(text="💳 Подписка")
    kb.button(text="ℹ️ Помощь")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def student_menu_kb() -> ReplyKeyboardMarkup:
    """Меню студента"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="📚 Упражнение дня")
    kb.button(text="📝 Все тесты")
    kb.button(text="📊 Мой прогресс")
    kb.button(text="💳 Подписка")
    kb.button(text="👥 Реферралы")
    kb.button(text="🎯 Слабые области")
    kb.button(text="🏠 Главное меню")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def admin_menu_kb() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Добавить упражнение")
    kb.button(text="📋 Управление тестами")
    kb.button(text="📊 Аналитика")
    kb.button(text="📝 Проверить ДЗ")
    kb.button(text="📧 Рассылка")
    kb.button(text="📌 Объявление")
    kb.button(text="🏠 Главное меню")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

# ==================== ИНЛАЙН КЛАВИАТУРЫ ====================

def subscription_kb() -> InlineKeyboardMarkup:
    """Выбор подписки"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🎁 Free (бесплатно)", callback_data="sub_free")
    kb.button(text="⭐ Premium ($5/мес)", callback_data="sub_premium")
    kb.button(text="👑 Pro ($10/мес)", callback_data="sub_pro")
    kb.button(text="ℹ️ Подробнее", callback_data="sub_info")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def exercise_answer_kb(exercise_id: int) -> InlineKeyboardMarkup:
    """Кнопки для ответа на упражнение (если множественный выбор)"""
    kb = InlineKeyboardBuilder()
    kb.button(text="A", callback_data=f"answer_a_{exercise_id}")
    kb.button(text="B", callback_data=f"answer_b_{exercise_id}")
    kb.button(text="C", callback_data=f"answer_c_{exercise_id}")
    kb.button(text="D", callback_data=f"answer_d_{exercise_id}")
    kb.button(text="💡 Подсказка", callback_data=f"hint_{exercise_id}")
    kb.button(text="⏭️ Пропустить", callback_data=f"skip_{exercise_id}")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()

def exercise_result_kb(exercise_id: int, is_correct: bool) -> InlineKeyboardMarkup:
    """Результат упражнения"""
    kb = InlineKeyboardBuilder()
    if is_correct:
        kb.button(text="✅ Верно! Отлично!", callback_data=f"next_exercise")
    else:
        kb.button(text="❌ Неверно. Попробать ещё?", callback_data=f"retry_{exercise_id}")
        kb.button(text="📖 Читать объяснение", callback_data=f"explain_{exercise_id}")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1, 1)
    return kb.as_markup()

def test_selection_kb(tests: list) -> InlineKeyboardMarkup:
    """Выбор теста"""
    kb = InlineKeyboardBuilder()
    for test in tests:
        kb.button(text=f"📝 {test['title']}", callback_data=f"test_{test['test_id']}")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1)
    return kb.as_markup()

def test_question_kb(question_id: int) -> InlineKeyboardMarkup:
    """Кнопки для вопроса теста"""
    kb = InlineKeyboardBuilder()
    kb.button(text="A", callback_data=f"test_ans_a_{question_id}")
    kb.button(text="B", callback_data=f"test_ans_b_{question_id}")
    kb.button(text="C", callback_data=f"test_ans_c_{question_id}")
    kb.button(text="D", callback_data=f"test_ans_d_{question_id}")
    kb.adjust(2, 2)
    return kb.as_markup()

def homework_kb() -> InlineKeyboardMarkup:
    """Меню домашних заданий"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📥 Мои задания", callback_data="hw_my")
    kb.button(text="✍️ Написать ответ", callback_data="hw_submit")
    kb.button(text="📊 Мои результаты", callback_data="hw_results")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def referral_kb(user_id: int) -> InlineKeyboardMarkup:
    """Реферальная система"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔗 Получить реферальную ссылку", callback_data="get_referral_link")
    kb.button(text="📊 Мои рефералы", callback_data="my_referrals")
    kb.button(text="📋 Как это работает", callback_data="referral_info")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение действия"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, подтверждаю", callback_data="confirm_yes")
    kb.button(text="❌ Отменить", callback_data="confirm_no")
    kb.adjust(1, 1)
    return kb.as_markup()

def categories_kb(categories: list) -> InlineKeyboardMarkup:
    """Выбор категории упражнений"""
    kb = InlineKeyboardBuilder()
    for category in categories:
        kb.button(text=f"📌 {category}", callback_data=f"cat_{category}")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1)
    return kb.as_markup()

def admin_exercise_kb() -> InlineKeyboardMarkup:
    """Управление упражнениями"""
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить новое", callback_data="admin_add_exercise")
    kb.button(text="✏️ Редактировать", callback_data="admin_edit_exercise")
    kb.button(text="📊 Статистика", callback_data="admin_exercise_stats")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def admin_test_kb() -> InlineKeyboardMarkup:
    """Управление тестами"""
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Создать новый тест", callback_data="admin_create_test")
    kb.button(text="✏️ Редактировать тест", callback_data="admin_edit_test")
    kb.button(text="➕ Добавить вопрос", callback_data="admin_add_question")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

def admin_homework_kb() -> InlineKeyboardMarkup:
    """Управление домашними заданиями"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Задать новое ДЗ", callback_data="admin_assign_hw")
    kb.button(text="📋 Проверить ДЗ", callback_data="admin_check_hw")
    kb.button(text="📊 Статистика ДЗ", callback_data="admin_hw_stats")
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()

# ==================== УТИЛИТЫ ====================

def back_to_menu_kb() -> InlineKeyboardMarkup:
    """Кнопка вернуться в меню"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Главное меню", callback_data="to_main_menu")
    return kb.as_markup()

def yes_no_kb() -> InlineKeyboardMarkup:
    """Да/Нет"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="yes")
    kb.button(text="❌ Нет", callback_data="no")
    kb.adjust(1, 1)
    return kb.as_markup()

def pagination_kb(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Навигация между страницами"""
    kb = InlineKeyboardBuilder()

    if page > 1:
        kb.button(text="◀️ Назад", callback_data=f"{prefix}_page_{page-1}")

    kb.button(text=f"{page}/{total_pages}", callback_data="page_info")

    if page < total_pages:
        kb.button(text="Вперед ▶️", callback_data=f"{prefix}_page_{page+1}")

    kb.button(text="🏠 Меню", callback_data="to_main_menu")
    kb.adjust(2, 1)
    return kb.as_markup()

def difficulty_kb() -> InlineKeyboardMarkup:
    """Выбор уровня сложности"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📌 Легко", callback_data="diff_easy")
    kb.button(text="📊 Среднее", callback_data="diff_medium")
    kb.button(text="🔴 Сложно", callback_data="diff_hard")
    kb.button(text="🎲 Случайно", callback_data="diff_random")
    kb.adjust(2, 2)
    return kb.as_markup()
