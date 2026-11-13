Метод	Эндпоинт	Назначение
GET	/next-lesson	Получить следующий урок
GET	/progress	Получить прогресс пользователя
PATCH	/settings	Изменить режим выбора уроков

Формат ответов, который ожидает бот
GET /next-lesson
{
  "lesson": {
    "name": "Название урока",
    "url": "https://platform.com/lesson/123"
  }
}


Если уроков нет:
{
  "lesson": null
}


GET /progress
{
  "user_id": 123456789,
  "progress": 65,
  "status": "in_progress",
  "last_activity_at": "2026-10-28T12:00:00Z",
  "has_pending_review": false
}


Здесь особенно важны last_activity_at и has_pending_review: без них логика напоминаний не сможет работать корректно.

PATCH /settings

Бот отправляет:
{
  "telegram_id": 123456789,
  "next_lesson_mode": "course_order"
}


Допустимые значения:
- course_order
- last_completed
API должен возвращать HTTP 200 с JSON или HTTP 204 без тела ответа.