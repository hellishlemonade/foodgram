# Foodgram – сайт для обмена рецептами

### catigram.ru (Домен)

Проект доступен по адресу https://catigram.ru/

## Описание

**Foodgram** представляет из себя сборник рецептов, которыми пользователи могут делиться, выкладывая их в ленту рецептов.

Вы можете подпиcываться на авторов, которые вам понравились. Добавлять рецепты в "Избранное". Добавлять в список покупок, который автоматически сформируется из добавленных рецептов.

## Стек технологий
![Python](https://img.shields.io/badge/python-3670A0?style=flat&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=flat&logo=django&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=flat&logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=flat&logo=react&logoColor=%2361DAFB)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=flat&logo=nginx&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=flat&logo=githubactions&logoColor=white)

## Клонирование
```
git clone https://github.com/hellishlemonade/foodgram.git
cd foodgram
```
## API
Проект включает API для взаимодействия с фронтендом и другими приложениями. Основные эндпоинты:

- `GET /api/recipes/` — получение списка рецептов.
- `POST /api/recipes/` — создание нового рецепта.
- `GET /api/ingredients/` — поиск ингредиентов по названию.
- `POST /api/users/` — регистрация нового пользователя.

Более подробные требования к полям моделей можно найти в спецификации к API. Находясь в папке infra, выполните в терминале команду: `docker compose up`

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.
## Развертывание
```
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
docker compose exec backend python manage.py import_csv
```

## Настройки окружения
Перед запуском приложения настройте переменные окружения (пример в файле .env_example):

- POSTGRES_DB — имя базы данных PostgreSQL.
- POSTGRES_USER — пользователь базы данных.
- POSTGRES_PASSWORD — пароль пользователя базы данных.
- DB_NAME – переменная для подключения к базе данных.
- DB_PORT — порт для подключения к базе данных.
- DB_HOST — хост базы данных.
- DEBUG — статус отладки Django.
- SECRET_KEY — секретный ключ Django.
- DB_HOST — хост базы данных.
- ALLOWED_HOSTS — список доступных хостов.
