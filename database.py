"""
Модели базы данных для бота репетитора русского языка
Database models for Russian language tutor bot
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH, SUBSCRIPTION_FEATURES, SUBSCRIPTION_PRICES
import json

class Database:
    """Класс для работы с SQLite базой данных"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Создать соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Инициализировать таблицы БД"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица студентов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_tier TEXT DEFAULT 'free',
                subscription_start TIMESTAMP,
                subscription_end TIMESTAMP,
                current_streak INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                total_exercises_completed INTEGER DEFAULT 0,
                total_tests_passed INTEGER DEFAULT 0,
                language TEXT DEFAULT 'ru'
            )
        """)

        # Таблица упражнений
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                difficulty TEXT DEFAULT 'intermediate',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                hint TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица истории упражнений студента
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                user_answer TEXT,
                is_correct INTEGER DEFAULT 0,
                completed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                attempt_number INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES students(user_id),
                FOREIGN KEY(exercise_id) REFERENCES exercises(exercise_id)
            )
        """)

        # Таблица тестов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tests (
                test_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                difficulty TEXT DEFAULT 'intermediate',
                total_questions INTEGER DEFAULT 0,
                passing_score INTEGER DEFAULT 70,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица вопросов в тестах
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_questions (
                question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL,
                explanation TEXT,
                FOREIGN KEY(test_id) REFERENCES tests(test_id)
            )
        """)

        # Таблица результатов тестов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                score INTEGER DEFAULT 0,
                max_score INTEGER DEFAULT 100,
                passed INTEGER DEFAULT 0,
                completed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answers TEXT,
                FOREIGN KEY(user_id) REFERENCES students(user_id),
                FOREIGN KEY(test_id) REFERENCES tests(test_id)
            )
        """)

        # Таблица домашних заданий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS homework (
                homework_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                task TEXT NOT NULL,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                submission_date TIMESTAMP,
                submission_text TEXT,
                status TEXT DEFAULT 'assigned',
                feedback TEXT,
                grade INTEGER,
                FOREIGN KEY(user_id) REFERENCES students(user_id)
            )
        """)

        # Таблица подписок и платежей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tier TEXT NOT NULL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                auto_renew INTEGER DEFAULT 0,
                payment_status TEXT DEFAULT 'pending',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES students(user_id)
            )
        """)

        # Таблица рефералов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                bonus_days INTEGER DEFAULT 7,
                bonus_applied INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(referrer_id) REFERENCES students(user_id),
                FOREIGN KEY(referred_id) REFERENCES students(user_id)
            )
        """)

        # Таблица последнего отправленного упражнения
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_exercise_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                sent_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY(user_id) REFERENCES students(user_id),
                FOREIGN KEY(exercise_id) REFERENCES exercises(exercise_id)
            )
        """)

        conn.commit()
        conn.close()

    # ==================== СТУДЕНТЫ ====================

    def add_or_update_student(self, user_id: int, username: str, first_name: str, last_name: str = "") -> bool:
        """Добавить или обновить студента"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO students
            (user_id, username, first_name, last_name, registration_date)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, username, first_name, last_name))

        conn.commit()
        conn.close()
        return True

    def get_student(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о студенте"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def get_all_students(self) -> List[Dict]:
        """Получить всех студентов"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students")
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def get_students_by_subscription(self, tier: str) -> List[Dict]:
        """Получить студентов с определённой подпиской"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM students
            WHERE subscription_tier = ? AND subscription_end > CURRENT_TIMESTAMP
        """, (tier,))
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def update_student_subscription(self, user_id: int, tier: str, days: int = 30):
        """Обновить подписку студента"""
        conn = self.get_connection()
        cursor = conn.cursor()

        start = datetime.now()
        end = start + timedelta(days=days)

        cursor.execute("""
            UPDATE students
            SET subscription_tier = ?, subscription_start = ?, subscription_end = ?
            WHERE user_id = ?
        """, (tier, start, end, user_id))

        conn.commit()
        conn.close()

    def update_streak(self, user_id: int, increment: bool = True):
        """Обновить streak студента"""
        conn = self.get_connection()
        cursor = conn.cursor()

        student = self.get_student(user_id)
        if not student:
            conn.close()
            return

        if increment:
            new_streak = student['current_streak'] + 1
        else:
            new_streak = 0

        max_streak = max(student['max_streak'], new_streak)

        cursor.execute("""
            UPDATE students
            SET current_streak = ?, max_streak = ?
            WHERE user_id = ?
        """, (new_streak, max_streak, user_id))

        conn.commit()
        conn.close()

    # ==================== УПРАЖНЕНИЯ ====================

    def add_exercise(self, category: str, title: str, content: str,
                    correct_answer: str, explanation: str,
                    difficulty: str = "intermediate", hint: str = "") -> int:
        """Добавить новое упражнение"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO exercises
            (category, title, content, correct_answer, explanation, difficulty, hint)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (category, title, content, correct_answer, explanation, difficulty, hint))

        conn.commit()
        exercise_id = cursor.lastrowid
        conn.close()

        return exercise_id

    def get_exercise(self, exercise_id: int) -> Optional[Dict]:
        """Получить упражнение по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM exercises WHERE exercise_id = ?", (exercise_id,))
        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def get_all_exercises(self) -> List[Dict]:
        """Получить все упражнения"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM exercises")
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def get_exercises_by_category(self, category: str) -> List[Dict]:
        """Получить упражнения по категории"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM exercises
            WHERE category = ?
            ORDER BY RANDOM()
        """, (category,))
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def get_random_exercise(self, max_count: int = 1) -> List[Dict]:
        """Получить случайные упражнения"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT * FROM exercises
            ORDER BY RANDOM()
            LIMIT ?
        """, (max_count,))
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def get_student_weak_areas(self, user_id: int) -> Dict[str, float]:
        """Получить слабые области студента (категории с низким процентом правильных ответов)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.category,
                COUNT(*) as total,
                SUM(CASE WHEN se.is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM student_exercises se
            JOIN exercises e ON se.exercise_id = e.exercise_id
            WHERE se.user_id = ?
            GROUP BY e.category
            ORDER BY (CAST(correct AS FLOAT) / total) ASC
        """, (user_id,))

        results = cursor.fetchall()
        conn.close()

        weak_areas = {}
        for row in results:
            success_rate = dict(row)['correct'] / dict(row)['total']
            weak_areas[dict(row)['category']] = success_rate

        return weak_areas

    def record_exercise_attempt(self, user_id: int, exercise_id: int,
                               user_answer: str, is_correct: bool) -> bool:
        """Записать попытку упражнения"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO student_exercises
            (user_id, exercise_id, user_answer, is_correct)
            VALUES (?, ?, ?, ?)
        """, (user_id, exercise_id, user_answer, 1 if is_correct else 0))

        # Обновить счётчик
        cursor.execute("""
            UPDATE students
            SET total_exercises_completed = total_exercises_completed + 1
            WHERE user_id = ?
        """, (user_id,))

        conn.commit()
        conn.close()

        return True

    def update_exercise(self, exercise_id: int, **kwargs):
        """Обновить упражнение"""
        conn = self.get_connection()
        cursor = conn.cursor()

        allowed_fields = ['category', 'title', 'content', 'correct_answer',
                         'explanation', 'difficulty', 'hint']

        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            conn.close()
            return False

        updates['updated_date'] = datetime.now()

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [exercise_id]

        cursor.execute(f"""
            UPDATE exercises
            SET {set_clause}
            WHERE exercise_id = ?
        """, values)

        conn.commit()
        conn.close()
        return True

    # ==================== ТЕСТЫ ====================

    def create_test(self, title: str, category: str, description: str = "",
                   difficulty: str = "intermediate", passing_score: int = 70) -> int:
        """Создать новый тест"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tests
            (title, description, category, difficulty, passing_score)
            VALUES (?, ?, ?, ?, ?)
        """, (title, description, category, difficulty, passing_score))

        conn.commit()
        test_id = cursor.lastrowid
        conn.close()

        return test_id

    def add_test_question(self, test_id: int, question_text: str,
                         option_a: str, option_b: str, option_c: str, option_d: str,
                         correct_option: str, explanation: str = "") -> int:
        """Добавить вопрос в тест"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO test_questions
            (test_id, question_text, option_a, option_b, option_c, option_d,
             correct_option, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_id, question_text, option_a, option_b, option_c, option_d,
              correct_option, explanation))

        # Обновить количество вопросов в тесте
        cursor.execute("UPDATE tests SET total_questions = total_questions + 1 WHERE test_id = ?",
                      (test_id,))

        conn.commit()
        question_id = cursor.lastrowid
        conn.close()

        return question_id

    def get_test(self, test_id: int) -> Optional[Dict]:
        """Получить информацию о тесте"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tests WHERE test_id = ?", (test_id,))
        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def get_test_questions(self, test_id: int) -> List[Dict]:
        """Получить вопросы теста"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM test_questions
            WHERE test_id = ?
            ORDER BY question_id
        """, (test_id,))
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def get_all_tests(self) -> List[Dict]:
        """Получить все тесты"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tests ORDER BY created_date DESC")
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def record_test_result(self, user_id: int, test_id: int, score: int,
                          max_score: int, answers: Dict[int, str]) -> bool:
        """Записать результат теста"""
        conn = self.get_connection()
        cursor = conn.cursor()

        test = self.get_test(test_id)
        passed = score >= test['passing_score']

        cursor.execute("""
            INSERT INTO student_tests
            (user_id, test_id, score, max_score, passed, answers)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, test_id, score, max_score, 1 if passed else 0, json.dumps(answers)))

        if passed:
            cursor.execute("""
                UPDATE students
                SET total_tests_passed = total_tests_passed + 1
                WHERE user_id = ?
            """, (user_id,))

        conn.commit()
        conn.close()

        return True

    # ==================== ДОМАШНИЕ ЗАДАНИЯ ====================

    def create_homework(self, user_id: int, teacher_id: int, title: str,
                       task: str, description: str = "", due_date: Optional[datetime] = None) -> int:
        """Создать домашнее задание"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO homework
            (user_id, teacher_id, title, description, task, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'assigned')
        """, (user_id, teacher_id, title, description, task, due_date))

        conn.commit()
        homework_id = cursor.lastrowid
        conn.close()

        return homework_id

    def submit_homework(self, homework_id: int, submission_text: str) -> bool:
        """Отправить домашнее задание"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE homework
            SET submission_text = ?, submission_date = CURRENT_TIMESTAMP, status = 'submitted'
            WHERE homework_id = ?
        """, (submission_text, homework_id))

        conn.commit()
        conn.close()

        return True

    def grade_homework(self, homework_id: int, feedback: str, grade: int) -> bool:
        """Оценить домашнее задание"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE homework
            SET feedback = ?, grade = ?, status = 'graded'
            WHERE homework_id = ?
        """, (feedback, grade, homework_id))

        conn.commit()
        conn.close()

        return True

    def get_homework(self, homework_id: int) -> Optional[Dict]:
        """Получить домашнее задание"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM homework WHERE homework_id = ?", (homework_id,))
        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def get_student_homework(self, user_id: int) -> List[Dict]:
        """Получить домашние задания студента"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM homework
            WHERE user_id = ?
            ORDER BY assigned_date DESC
        """, (user_id,))
        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def get_pending_homework(self, teacher_id: int = None) -> List[Dict]:
        """Получить неоценённые домашние задания"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if teacher_id:
            cursor.execute("""
                SELECT * FROM homework
                WHERE teacher_id = ? AND status = 'submitted'
                ORDER BY submission_date ASC
            """, (teacher_id,))
        else:
            cursor.execute("""
                SELECT * FROM homework
                WHERE status = 'submitted'
                ORDER BY submission_date ASC
            """)

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    # ==================== РЕФЕРАЛЫ ====================

    def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        """Добавить реферала"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO referrals
            (referrer_id, referred_id, bonus_days)
            VALUES (?, ?, 7)
        """, (referrer_id, referred_id))

        conn.commit()
        conn.close()

        return True

    def apply_referral_bonus(self, referrer_id: int) -> bool:
        """Применить бонус за реферала"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Получить неприменённые бонусы
        cursor.execute("""
            SELECT SUM(bonus_days) as total_bonus
            FROM referrals
            WHERE referrer_id = ? AND bonus_applied = 0
        """, (referrer_id,))

        result = cursor.fetchone()
        total_bonus = dict(result)['total_bonus'] if result and dict(result)['total_bonus'] else 0

        if total_bonus > 0:
            # Продлить подписку
            student = self.get_student(referrer_id)
            if student and student['subscription_tier'] != 'free':
                current_end = datetime.fromisoformat(student['subscription_end'])
                new_end = current_end + timedelta(days=total_bonus)
            else:
                new_end = datetime.now() + timedelta(days=total_bonus)

            cursor.execute("""
                UPDATE students
                SET subscription_end = ?
                WHERE user_id = ?
            """, (new_end, referrer_id))

            # Отметить бонусы как применённые
            cursor.execute("""
                UPDATE referrals
                SET bonus_applied = 1
                WHERE referrer_id = ? AND bonus_applied = 0
            """, (referrer_id,))

        conn.commit()
        conn.close()

        return True

    def get_referral_count(self, user_id: int) -> int:
        """Получить количество рефералов пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM referrals
            WHERE referrer_id = ?
        """, (user_id,))

        result = cursor.fetchone()
        conn.close()

        return dict(result)['count'] if result else 0

    # ==================== ПОДПИСКИ ====================

    def get_student_subscription(self, user_id: int) -> Optional[Dict]:
        """Получить активную подписку студента"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM subscriptions
            WHERE user_id = ?
            ORDER BY start_date DESC
            LIMIT 1
        """, (user_id,))

        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def get_expiring_subscriptions(self, days: int = 3) -> List[Dict]:
        """Получить подписки, которые истекают через N дней"""
        conn = self.get_connection()
        cursor = conn.cursor()

        future_date = datetime.now() + timedelta(days=days)

        cursor.execute("""
            SELECT * FROM students
            WHERE subscription_end IS NOT NULL
            AND subscription_end <= ?
            AND subscription_end > CURRENT_TIMESTAMP
        """, (future_date,))

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def get_students_for_daily_exercise(self) -> List[Dict]:
        """Получить студентов, которые должны получить упражнение"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Студенты с активной подпиской (любой уровень)
        cursor.execute("""
            SELECT * FROM students
            WHERE subscription_end IS NULL OR subscription_end > CURRENT_TIMESTAMP
        """)

        results = cursor.fetchall()
        conn.close()

        return [dict(row) for row in results]

    def check_daily_exercise_sent(self, user_id: int, exercise_id: int) -> bool:
        """Проверить, было ли упражнение уже отправлено сегодня"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM daily_exercise_log
            WHERE user_id = ? AND exercise_id = ? AND sent_date = CURRENT_DATE
        """, (user_id, exercise_id))

        result = cursor.fetchone()
        conn.close()

        return dict(result)['count'] > 0 if result else False

    def log_daily_exercise(self, user_id: int, exercise_id: int) -> bool:
        """Записать в лог отправку упражнения"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO daily_exercise_log
            (user_id, exercise_id, sent_date)
            VALUES (?, ?, CURRENT_DATE)
        """, (user_id, exercise_id))

        conn.commit()
        conn.close()

        return True

    # ==================== СТАТИСТИКА ====================

    def get_student_stats(self, user_id: int) -> Dict:
        """Получить статистику студента"""
        conn = self.get_connection()
        cursor = conn.cursor()

        student = self.get_student(user_id)

        if not student:
            return {}

        # Получить процент успеха в упражнениях
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM student_exercises
            WHERE user_id = ?
        """, (user_id,))

        exercise_stats = cursor.fetchone()
        if exercise_stats:
            exercise_stats = dict(exercise_stats)
            success_rate = exercise_stats['correct'] / exercise_stats['total'] * 100 if exercise_stats['total'] > 0 else 0
        else:
            exercise_stats = {'total': 0, 'correct': 0}
            success_rate = 0

        # Получить статистику по категориям
        weak_areas = self.get_student_weak_areas(user_id)

        conn.close()

        return {
            'user_id': user_id,
            'username': student['username'],
            'current_streak': student['current_streak'],
            'max_streak': student['max_streak'],
            'total_exercises': student['total_exercises_completed'],
            'total_tests_passed': student['total_tests_passed'],
            'exercise_success_rate': success_rate,
            'weak_areas': weak_areas,
            'subscription_tier': student['subscription_tier'],
            'subscription_end': student['subscription_end']
        }

    def get_admin_analytics(self) -> Dict:
        """Получить аналитику для администратора"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Общая статистика
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = dict(cursor.fetchone())['total']

        cursor.execute("SELECT COUNT(*) as total FROM students WHERE subscription_tier != 'free'")
        paying_students = dict(cursor.fetchone())['total']

        cursor.execute("""
            SELECT COUNT(*) as total
            FROM students
            WHERE subscription_end > CURRENT_TIMESTAMP OR subscription_end IS NULL
        """)
        active_students = dict(cursor.fetchone())['total']

        cursor.execute("SELECT COUNT(*) as total FROM exercises")
        total_exercises = dict(cursor.fetchone())['total']

        cursor.execute("SELECT COUNT(*) as total FROM tests")
        total_tests = dict(cursor.fetchone())['total']

        cursor.execute("""
            SELECT tier, COUNT(*) as count
            FROM students
            WHERE subscription_end > CURRENT_TIMESTAMP OR subscription_end IS NULL
            GROUP BY tier
        """)

        tier_distribution = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            tier_distribution[row_dict['tier']] = row_dict['count']

        conn.close()

        return {
            'total_students': total_students,
            'paying_students': paying_students,
            'active_students': active_students,
            'total_exercises': total_exercises,
            'total_tests': total_tests,
            'tier_distribution': tier_distribution
        }
