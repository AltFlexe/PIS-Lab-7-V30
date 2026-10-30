# Лабораторная работа 7 — JavaScript в Django

Учебный проект об аренде помещений продолжает предыдущую работу. JavaScript выводит список студентов в консоль и на страницу, отбирает студентов по группе и среднему баллу и позволяет сворачивать отдельные статьи.

## Запуск

При установленном Python 3.11 из корня проекта в PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/manage.py migrate
.\.venv\Scripts\python.exe src/manage.py loaddata demo
.\.venv\Scripts\python.exe src/manage.py createsuperuser
.\.venv\Scripts\python.exe src/manage.py test articles
.\.venv\Scripts\python.exe src/manage.py runserver
```

Откройте `http://127.0.0.1:8000/`. Для появления статей создайте их через административную панель `/admin/`. Список студентов учебный. Фильтры расположены под архивом статей; полный список также выводится в консоль браузера.

Сценарии находятся в `src/articles/static/js/`: `helloworld.js` отвечает за список и фильтры, `fold-post.js` — за сворачивание. Ключ Django берётся из переменной `DJANGO_SECRET_KEY` или создаётся при локальном запуске. Учебная база пользователей в проект не входит.
