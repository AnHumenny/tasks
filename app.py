import hashlib
import markdown
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature, BadData
import os
from quart import Quart, request, render_template, send_from_directory, jsonify, redirect, url_for, session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from shemas.repository import Repo
from shemas.database import engine
from datetime import datetime
import pytz

app = Quart(__name__)
app.secret_key = os.urandom(24)  # ключ для шифрования токенов
serializer = URLSafeTimedSerializer(app.secret_key)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER                 # папка загрузки файлов (фото, аватарки пользователей (на перспективу))
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024         # max 4mb
ALLOWED_EXTENSIONS = {'fb2', 'epub', 'pdf'}                 # разрешённые типы файлов
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text)


@app.route('/files/<path:filename>')                        # директория загрузки файлов
async def serve_file(filename):
    return await send_from_directory('files', filename)


def generate_token(username):                               # создание токена
    return serializer.dumps(username)


def verify_token(token):                                    # проверка токена
    try:
        username = serializer.loads(token, max_age=3600)  # Токен действителен 1 час
        return username
    except SignatureExpired:
        print("Токен истек.")
        return None
    except BadSignature:
        print("Недействительная подпись токена.")
        return None
    except BadData:
        print("Некорректные данные токена.")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/login')
async def log():
    return await render_template("login.html")


@app.route('/')
async def index():
    status = session.get('status')
    page = int(request.args.get('page', 1))
    per_page = 8
    async with async_session() as sessions:
        async with sessions.begin():
            answer = await Repo.select_all_tasks()
            total_answer = len(answer)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_tasks = answer[start:end]
        pagination_links = []
        total_pages = (total_answer // per_page) + (1 if total_answer % per_page > 0 else 0)
        return await render_template('index.html', tasks=paginated_tasks, status=status,
                                     total_answer=total_answer, total_pages=total_pages, page=page, per_page=per_page,
                                     pagination_links=pagination_links)


@app.route('/login', methods=['POST'])
async def login():
    form_data = await request.form
    username = form_data.get('username')
    password = form_data.get('password')
    hashed_password = hash_password(password)
    answer = await Repo.select_user(username, hashed_password)
    if answer is True:
        token = generate_token(username)
        session['token'] = token
        session['username'] = username  # сессия в username
        info = await Repo.select_info_user(username)
        session['name'] = info.get("name")
        session['status'] = info.get("status")
        session['login'] = info.get("login")
        return redirect(url_for('personal'))  # переадресация в личный кабинет
    return jsonify({"message": "Ошибка доступа"}), 401


@app.route('/personal')
async def personal():
    username = session.get('username')
    name = session.get('name')
    status = session.get('status')
    if not username:
        return redirect(url_for('login'))
    async with async_session() as sessions:
        async with sessions.begin():
            user = await Repo.select_info(username)
    page = int(request.args.get('page', 1))
    per_page = 8
    async with async_session() as sess:
        async with sess.begin():
            tasks = await Repo.select_user_tasks(name)
            total_answer = len(tasks)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_tasks = tasks[start:end]
        pagination_links = []
        total_pages = (total_answer // per_page) + (1 if total_answer % per_page > 0 else 0)
    return await render_template('personal.html', user=user, tasks=paginated_tasks, status=status,
                                 total_answer=total_answer, total_pages=total_pages, page=page, per_page=per_page,
                                 pagination_links=pagination_links, name=name
                                 )

#task
@app.route('/add_task')
async def upload_form():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("index.html")
    tutor = await Repo.select_tutor_all()
    user = await Repo.select_user_all()
    for row in user:
        print(row)
    return await render_template("add_task.html", tutor=tutor, user=user)


@app.route('/upload_task', methods=['POST'])
async def add_user_task():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("index.html")
    form_data = await request.form
    date_created_str = form_data.get('date_created')
    date_control_str = form_data.get('date_control')
    timezone_str = form_data.get('timezone')

    if timezone_str is None:
        timezone_str = 'UTC'

    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone('UTC')
    if date_created_str:
        naive_datetime_created = datetime.strptime(date_created_str,
                                                   '%Y-%m-%dT%H:%M')
        date_created = local_tz.localize(naive_datetime_created)
        date_created_naive = date_created.replace(tzinfo=None)
    if date_control_str:
        naive_datetime_control = datetime.strptime(date_control_str,
                                                   '%Y-%m-%dT%H:%M')
        date_control = local_tz.localize(naive_datetime_control)
        date_control_naive = date_control.replace(tzinfo=None)
    facilitator = form_data.get('facilitator')
    implementer = form_data.get('implementer')
    describe = form_data.get('describe')
    formatted_describe = describe.replace('\n', '<br>')
    priority = form_data.get('priority')
    stat_task = form_data.get('stat_task')
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.create_task(date_created_naive, date_control_naive,
                                   facilitator, implementer, formatted_describe, priority, stat_task)
    return redirect(url_for('index'))


@app.route('/task_detail/<int:task_id>', methods=['GET'])
async def task_detail(task_id):
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    name = session.get('name')
    if not access:
        return redirect(url_for('login'))
    if status == "admin":
        answer = await Repo.select_task_id(task_id)
        print('answer', answer)
        return await render_template("view_detail.html", task=answer)
    if status == "user":
        print("userlogin", name)
        answer = await Repo.select_task_id_personal(task_id, name)
        print('answer', answer)
        return await render_template("view_detail.html", task=answer)


@app.route('/update_task_id', methods=['POST'])
async def update_task_id():
    token = session.get('token')
    access = verify_token(token)
    form_data = await request.form
    ssid = form_data.get('update_task_id')
    status = session.get("status")
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return redirect(url_for('index'))
    if not ssid:
        return redirect(url_for('index'))
    answer = await Repo.select_task_id(ssid)
    tutor = await Repo.select_tutor_all()
    return await render_template("update_task.html", answer=answer, tutor=tutor)


@app.route('/update_task', methods=['POST'])
async def update_task():
    token = session.get('token')
    access = verify_token(token)
    stat = session.get('status')
    form_data = await request.form
    ssid = form_data.get('id')
    implementer = form_data.get('implementer')
    facilitator = form_data.get('facilitator')
    priority = form_data.get('priority')
    describe = form_data.get('describe')
    stat_task = form_data.get('stat_task')
    print("в теле ", ssid,  implementer, facilitator, priority, describe)
    if not access:
        return await render_template("login.html")
    if stat != "admin":
        return await render_template("index.html")
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.update_task(ssid, implementer, facilitator, priority, describe, stat_task)
    return redirect(url_for('personal'))


@app.route('/delete_task', methods=['POST'])
async def delete_task():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return redirect(url_for('personal'))
    form_data = await request.form
    ssid = form_data.get('delete_task')
    if ssid is None:
        return "ID задачи не предоставлено", 400
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.delete_task(ssid)
    return redirect(url_for('personal'))
#end task

#user
@app.route('/user')
async def all_users():
    token = session.get('token')
    access = verify_token(token)
    if not access:
        return await render_template("login.html")
    status = session.get('status')               # можно добавить сортировку по группам и т.д.
    page = int(request.args.get('page', 1))
    per_page = 32
    if access:
        async with async_session() as sessions:
            async with sessions.begin():
                answer = await Repo.select_all_users()
                total_answer = len(answer)
                start = (page - 1) * per_page
                end = start + per_page
                paginated_tasks = answer[start:end]
            pagination_links = []
            total_pages = (total_answer // per_page) + (1 if total_answer % per_page > 0 else 0)

        return await render_template('users.html', answer=paginated_tasks, status=status,
                                 total_answer=total_answer, total_pages=total_pages, page=page, per_page=per_page,
                                 pagination_links=pagination_links )
    return await render_template("login.html")


@app.route('/add_user')
async def user_form():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("index.html")
    answer = await Repo.select_posts()
    return await render_template("add_user.html", position=answer)


@app.route('/insert_user', methods=['POST'])
async def add_new_user():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return redirect(url_for('index'))
    form_data = await request.form
    date_created_str = form_data.get('date_created')
    timezone_str = form_data.get('timezone')
    logins = form_data.get('login')
    name = form_data.get('name')
    position = form_data.get('position')
    print("это позиция - ", position)
    status = form_data.get('status')
    describe = form_data.get('describe')
    password = form_data.get('password')
    hashed_password = str(hash_password(password))
    if timezone_str is None:
        timezone_str = 'UTC+3'
    try:
        local_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.timezone('UTC')
    if date_created_str:
        naive_datetime_created = datetime.strptime(date_created_str,
                                                  '%Y-%m-%dT%H:%M')
        date_created = local_tz.localize(naive_datetime_created)
        date_created_naive = date_created.replace(tzinfo=None)
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.create_user(date_created_naive, logins, status, name, position, describe, hashed_password)
    return redirect(url_for('all_users'))


@app.route('/update_id', methods=['POST'])
async def update_id():
    token = session.get('token')
    access = verify_token(token)
    form_data = await request.form
    ssid = form_data.get('update_user')
    status = session.get("status")
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return redirect(url_for('index'))
    if not ssid:
        return redirect(url_for('index'))
    answer = await Repo.select_user_id(ssid)
    position = await Repo.select_posts_all()
    return await render_template("update_user.html", answer=answer, position=position)


@app.route('/update_user', methods=['POST'])
async def update_user():
    token = session.get('token')
    access = verify_token(token)
    stat = session.get('status')
    form_data = await request.form
    ssid = form_data.get('id')
    logins = form_data.get('login')
    name = form_data.get('name')
    position = form_data.get('position')
    status = form_data.get('status')
    describe = form_data.get('describe')
    if not access:
        return await render_template("login.html")
    if stat != "admin":
        return await render_template("index.html")
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.update_user(ssid, name, position, status, describe)
    return redirect(url_for('all_users'))


@app.route('/delete_user', methods=['POST'])
async def delete_user():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("delete_user.html")
    form_data = await request.form
    ssid = form_data.get('delete_user')
    if ssid == "1":
        return redirect(url_for('all_users'))
    if ssid is None:
        return "ID пользователя не предоставлен", 400
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.delete_user(ssid)
    return redirect(url_for('all_users'))
#end user


#search
@app.route('/search', methods=['POST'])
async def search_all():
    token = session.get('token')
    access = verify_token(token)
    if not access:
        return await render_template("login.html")
    form_data = await request.form
    name = form_data.get('search')
    search_type = form_data.get('search_type')
    session['search_data'] = {'name': name, 'search_type': search_type}
    return redirect(url_for('search_results', page=1))


@app.route('/search/results', methods=['GET'])
async def search_results():
    token = session.get('token')
    access = verify_token(token)
    if not access:
        return await render_template("login.html")
    search_data = session.get('search_data', {})
    name = search_data.get('name')
    search_type = search_data.get('search_type')
    page = int(request.args.get('page', 1))
    per_page = 8
    async with async_session() as sessions:
        async with sessions.begin():
            tasks = await Repo.search_all(name, search_type)
            if not tasks:
                paginated_tasks = "По данному запросу нет результатов"
                total_answer = 0
                return await render_template('search.html', error=paginated_tasks,
                                             page=page, per_page=per_page, total_answer=total_answer
                                             )
            else:
                total_answer = len(tasks)
                start = (page - 1) * per_page
                end = start + per_page
                paginated_tasks = tasks[start:end]
        total_pages = (total_answer // per_page) + (1 if total_answer % per_page > 0 else 0)
    return await render_template('search.html', tasks=paginated_tasks,
                                 total_answer=total_answer, total_pages=total_pages, page=page,
                                 per_page=per_page)
#end search


#functional
@app.route('/add_post')
async def add_post():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("index.html")
    answer = await Repo.select_posts()
    return await render_template("add_post.html", answer=answer)


@app.route('/insert_post', methods=['POST'])
async def add_new_post():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return redirect(url_for('index'))
    form_data = await request.form
    position = form_data.get('position')
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.add_position(position)
    return redirect(url_for('add_post'))


@app.route('/add_facilitator')
async def add_facilitator():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("index.html")
    answer = await Repo.select_facilitator()
    users = await Repo.select_all_users()
    return await render_template("add_facilitator.html", answer=answer, users=users)


@app.route('/insert_facilitator', methods=['POST'])
async def add_new_facilitator():
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return redirect(url_for('index'))
    form_data = await request.form
    tutor = form_data.get('group')
    name = form_data.get('name')
    print("tutor, name", tutor, name)
    async with async_session() as sessions:
        async with sessions.begin():
            await Repo.add_facilitator(tutor, name)
    return redirect(url_for('index'))


@app.route('/delete_facilitator/<int:id>', methods=['POST'])
async def delete_facilitator(id):
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("users.html")
    if id is None:
        return "ID пользователя не предоставлен", 400
    async with async_session() as sess:
        async with sess.begin():
            await Repo.delete_facilitator(id)
    return redirect(url_for('add_facilitator'))


@app.route('/delete_post/<int:id>', methods=['POST'])
async def delete_post(id):
    token = session.get('token')
    access = verify_token(token)
    status = session.get('status')
    if not access:
        return await render_template("login.html")
    if status != "admin":
        return await render_template("users.html")
    if id is None:
        return "ID пользователя не предоставлен", 400
    async with async_session() as sess:
        async with sess.begin():
            await Repo.delete_post(id)
    return redirect(url_for('add_post'))


@app.route('/logout')
async def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

