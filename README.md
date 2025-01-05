# Tasks application

Планировщик задач.  
Использует Quart.   
PostgresSQL в качестве базы данных 


## Перед тем как начать, убедитесь, что у вас установлены следующие компоненты:
- **Python** (версия 3.12)
- **PostgresSQL** (версия 16+)
- **pip** 
- **virtualenv** (опционально)

## Установка окружения

python -m venv venv
source venv/bin/activate  # Для macOS/Linux
venv\Scripts\activate     # Для Windows

## Установите зависимости:
pip install -r requirements.txt

Структура файла .env в корне:  
DB_HOST="адрес хоста"  
DB_USER="имя пользователя"  
DB_PASSWORD="пароль"  
DB_NAME="название создаваемой базы данных"  
DB_PORT=5432  

login="первичный пользователь"  
name="имя пользователя"  
position="должность"  
describe="краткое описание"  
password="пароль"  
(второй блок задействуется в установке, можно после удалить)  


## Установка:
Из корневой директории приложения  
*python3 -m create.install*

## Запуск приложения
Для запуска приложения, выполните следующую команду:  
*python3 app.py*



