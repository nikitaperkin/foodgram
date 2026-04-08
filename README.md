# Проект Foodgram

![Github Actions](https://github.com/nikitaperkin/foodgram/actions/workflows/main.yml/badge.svg)



## Описание

**Foodgram** — сервис для публикации кулинарных рецептов. Зарегистрированные пользователи могут размещать собственные рецепты, подписываться на других авторов, сохранять понравившиеся блюда в избранное, а также формировать и скачивать список покупок для выбранных рецептов. Гостям сайта доступны просмотр рецептов и страниц авторов без регистрации.

***

## Проект доступен по адресу

**Сайт:** https://forkfeed.hopto.org

**API документация:** https://forkfeed.hopto.org/api/docs/

**Панель администратора:** [https://forkfeed.hopto.org/admin/](https://forkfeed.hopto.org/admin/)

***

## Запуск проекта на сервере

На сервере должен быть установлен [Docker](https://docs.docker.com/engine/install/).

### 1. Скопировать конфигурационные файлы на сервер

```bash
git clone git@github.com:nikitaperkin/foodgram.git
cd foodgram
```

### 2. Добавить секреты в GitHub Actions

В настройках репозитория (`Settings → Secrets → Actions`) добавить следующие переменные:

```
DOCKER_USERNAME        # имя пользователя DockerHub
DOCKER_PASSWORD        # пароль DockerHub
HOST                   # IP-адрес удалённого сервера
USER                   # имя пользователя на сервере
SSH_KEY                # приватный SSH-ключ для подключения к серверу
ENV_FILE               # содержимое файла .env (все переменные окружения)
TELEGRAM_TO            # ID вашего Telegram-аккаунта
TELEGRAM_TOKEN         # токен Telegram-бота для уведомлений
```

Пример содержимого `ENV_FILE`:

```
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=your_domain.com,localhost,127.0.0.1
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
```

### 3. Запустить контейнеры на сервере

Создать файл `.env` на сервере и заполнить его по образцу выше:

```bash
touch ~/foodgram/.env
```

Перейти в папку проекта и запустить контейнеры:

```bash
cd ~/foodgram
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml up -d
```

Выполнить миграции, загрузить данные и собрать статику:

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_ingredients
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_tags
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

### 4. Создать суперпользователя

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

***

## Локальный запуск в контейнерах

Клонировать репозиторий:

```bash
git clone git@github.com:nikitaperkin/foodgram.git
cd foodgram
```

Создать файл `.env` в корне репозитория и заполнить его по образцу из раздела выше:

```bash
touch .env
```

Запустить контейнеры:

```bash
docker compose -f infra/docker-compose.yml up -d
```

Выполнить миграции и загрузить данные:

```bash
docker compose -f infra/docker-compose.yml exec backend python manage.py migrate
docker compose -f infra/docker-compose.yml exec backend python manage.py load_ingredients
docker compose -f infra/docker-compose.yml exec backend python manage.py load_tags
docker compose -f infra/docker-compose.yml exec backend python manage.py collectstatic --noinput
```

Создать суперпользователя:

```bash
docker compose -f infra/docker-compose.yml exec backend python manage.py createsuperuser
```

Проект доступен по адресу: [http://localhost/](http://localhost/)

***

## Локальный запуск без Docker

Клонировать репозиторий и перейти в папку backend:

```bash
git clone git@github.com:nikitaperkin/foodgram.git
cd foodgram/backend
```

Создать и активировать виртуальное окружение:

```bash
python3 -m venv venv

# Linux/macOS:
source venv/bin/activate

# Windows:
source venv/Scripts/activate
```

Установить зависимости:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Выполнить миграции и запустить сервер:

```bash
python manage.py migrate
python manage.py load_ingredients
python manage.py load_tags
python manage.py runserver
```

***

## Эндпоинты API

| Метод | Эндпоинт | Описание | Доступ |
|---|---|---|---|
| GET, POST | `/api/users/` | Список пользователей / регистрация | Без токена |
| GET | `/api/users/{id}/` | Профиль пользователя | Без токена |
| GET | `/api/users/me/` | Текущий пользователь | Авторизован |
| POST | `/api/users/set_password/` | Смена пароля | Авторизован |
| PUT | `/api/users/me/avatar/` | Загрузить аватар | Авторизован |
| DELETE | `/api/users/me/avatar/` | Удалить аватар | Авторизован |
| POST | `/api/auth/token/login/` | Получение токена | Без токена |
| POST | `/api/auth/token/logout/` | Удаление токена | Авторизован |
| GET | `/api/tags/` | Список тегов | Без токена |
| GET | `/api/tags/{id}/` | Тег по ID | Без токена |
| GET | `/api/ingredients/` | Список ингредиентов (поиск по началу названия) | Без токена |
| GET | `/api/ingredients/{id}/` | Ингредиент по ID | Без токена |
| GET, POST | `/api/recipes/` | Список рецептов / создание | Без токена / Авторизован |
| GET, PATCH, DELETE | `/api/recipes/{id}/` | Рецепт по ID | Без токена / Автор |
| GET | `/api/recipes/{id}/get-link/` | Короткая ссылка на рецепт | Без токена |
| POST, DELETE | `/api/recipes/{id}/favorite/` | Добавить/убрать из избранного | Авторизован |
| POST, DELETE | `/api/recipes/{id}/shopping_cart/` | Добавить/убрать из корзины | Авторизован |
| GET | `/api/recipes/download_shopping_cart/` | Скачать список покупок | Авторизован |
| POST, DELETE | `/api/users/{id}/subscribe/` | Подписаться/отписаться | Авторизован |
| GET | `/api/users/subscriptions/` | Мои подписки | Авторизован |

***

## Стек технологий

- **Backend:** Python 3.12, Django 5, Django REST Framework
- **База данных:** PostgreSQL 16
- **Фронтенд:** React, SPA (Single Page Application)
- **Инфраструктура:** Docker, Nginx, Gunicorn
- **CI/CD:** GitHub Actions

***

## Автор

**Никита Перкин** — [GitHub](https://github.com/nikitaperkin) | [Telegram](https://t.me/username_uu)
