![Static Badge](https://img.shields.io/badge/Python-gray) ![Static Badge](https://img.shields.io/badge/Django_Rest_Framework-red?style=flat) ![Static Badge](https://img.shields.io/badge/JWT--Token-green) ![Static Badge](https://img.shields.io/badge/JavaScript-yellow) ![Static Badge](https://img.shields.io/badge/CSS-purple) ![Static Badge](https://img.shields.io/badge/Docker-blue) ![Static Badge](https://img.shields.io/badge/Gunicorn-pink) ![Static Badge](https://img.shields.io/badge/Nginx-green)

# Проект "Фудграм"
### Проект фудграм - это место, где вы можете делиться своими изысканными рецептами и их фотографиями, а также присоединиться к сообществу кулинаров и посмотреть рецепты других пользователей! Присоединяйтесь к нашему сообществу и подписывайтесь на любимых авторов, а также, составляйте свои списки покупок и скачивайте их себе, чтобы не забыть ;-) .

## Установка
1) Клонируйте репозиторий ```https://github.com/SiberianFalcon/foodgram-project-react.git```
2) перейдите в директорию ```backend_foodgram\backend_foodgram``` и выполните команду ```python -m venv venv```. После не продолжительного ожилания активируйте окуржение написав ```source venv/Scripts/acrivate``` .
3) создайте файл в корневой директории по названием ```.env``` и пропишите в указанные константы свои значения согласно их названия:
```
POSTGRES_USER   #имя пользователя базы данных
POSTGRES_PASSWORD   #пароль от базы данных
POSTGRES_DB   #название базы данных
DB_HOST   #название контейнера с базой данных
DB_PORT   #5432 по умолчанию
HOST_1   #localhost по умолчанию
HOST_2   #127.0.0.1 по умолчанию
HOST_3   #IP удалённого сервера
HOST_4   #домен удалённого сервера
SECRET_KEY   #секретный ключ (смотреть в настройках джанго проекта в файле settings.py)
```
4) запустите Docker на своём компьютере и из корневой директории выполните в терминале команду ```docker compose -f docker-compose.yml up```
5) применить миграции docker-compose exec web python manage.py migrate
6) создать суперпользователя командой docker-compose exec web python manage.py createsuperuser
7) собрать файлы статики для сервера nginx docker-compose exec web python manage.py collectstatic --no-input
8) откройте браузер и перейдите по адресу ```http://localhost:8888/```

## Для заполнения списка ингредиентов
Внутри проекта реализован механизм импорта .csv .xls .xlsx .json .yaml .tsv файлов в которых необходимо указать необходимые игредиенты. В проекте есть готовый файл с шаблоном и списком ингредиентов ingredient.json по адресу ```data\ingredients.json```. Можете использовать его, либо создать собственный список.
