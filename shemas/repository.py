from sqlalchemy import select, delete, and_, update
from sqlalchemy.exc import NoResultFound, IntegrityError, SQLAlchemyError
import logging
from shemas.database import DTask, DUser, DTutor, new_session, DPost


class Repo:

    @classmethod
    async def search_executor_tasks(cls, search):
        if not search:
            return "Ошибка при поиске"
        async with new_session() as session:
            try:
                q = select(DTask).where(DTask.implementer.like(f"%{search}%"))
                result = await session.execute(q)
                answer = result.scalars().all()
                await session.commit()
                if not answer:
                    return None
                return answer
            except ValueError:
                return False
            except NoResultFound:
                return False
            except IntegrityError:
                await session.rollback()
                return False
            except SQLAlchemyError:
                await session.rollback()
                return False


    @classmethod
    async def select_user(cls, login, password):
        async with new_session() as session:
            q = select(DUser).where(and_(DUser.login == login, DUser.password == password))
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return True


    @classmethod
    async def select_info_user(cls, login):
        async with new_session() as session:
            q = select(DUser.name, DUser.login, DUser.status).where(DUser.login == login)
            result = await session.execute(q)
            answer = result.fetchall()
            if answer:
                return {'name': answer[0][0],  'login': answer[0][1], 'status': answer[0][2]}
            return None


    @classmethod
    async def select_all_users(cls) -> list[DUser ]:
        try:
            async with new_session() as session:
                q = select(DUser).order_by(DUser.id.desc())
                result = await session.execute(q)
                answer = result.scalars().all()
                return answer
        except SQLAlchemyError as e:
            logging.error(f"Error occurred while selecting users: {e}")
            return []


    @classmethod
    async def select_all_tasks(cls):
        async with new_session() as session:
            try:
                q = select(DTask).order_by(DTask.id.desc())
                result = await session.execute(q)
                tasks = result.scalars().all()
                return tasks
            except Exception as e:
                print(f"Произошла ошибка при выборке задач: {e}")
                return None

    @classmethod
    async def select_user_tasks(cls, name):
        async with new_session() as session:
            try:
                q = select(DTask).where(DTask.implementer == name).order_by(DTask.id.desc())
                result = await session.execute(q)
                tasks = result.scalars().all()
                return tasks
            except Exception as e:
                print(f"Произошла ошибка при выборке задач: {e}")
                return None


    @classmethod
    async def select_tasks_user(cls, login):
        async with new_session() as session:
            try:
                q = select(DTask).where(DTask.implementer == login)
                result = await session.execute(q)
                tasks_user = result.scalars().all()
                return tasks_user
            except Exception as e:
                print(f"Произошла ошибка при выборке задач: {e}")
                return None


    @classmethod
    async def select_info(cls, login):
        async with new_session() as session:
            q = select(DTask).where(DTask.implementer == login)
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return answer


    @classmethod
    async def create_task(cls, date_created, date_control, facilitator, implementer, describe, priority, stat_task):
        async with new_session() as session:
            new_task = DTask(
                date_created=date_created,
                date_control=date_control,
                facilitator=facilitator,
                implementer=implementer,
                describe=describe,
                priority=priority,
                stat_task=stat_task
            )
            session.add(new_task)
            await session.commit()


    @classmethod
    async def create_user(cls, date_created_naive, logins, status, name, position, describe, hashed_password):
        async with new_session() as session:
            new_user = DUser(
                date_created=date_created_naive,
                login=logins,
                status=status,
                name=name,
                post=position,
                describe=describe,
                password=hashed_password
            )
            session.add(new_user)

            try:
                await session.commit()
                print("Пользователь успешно добавлен!")
                return new_user  # Возврат нового пользователя или его ID
            except IntegrityError as e:
                await session.rollback()  # Откат транзакции в случае ошибки
                print("Ошибка: Дублирование данных или нарушение уникальности.")
                # Здесь можно обработать исключение, например, логировать его или вернуть сообщение об ошибке
                return None  # Или вернуть сообщение об ошибке
            except SQLAlchemyError as e:
                await session.rollback()  # Откат транзакции в случае ошибки
                print(f"Ошибка базы данных: {str(e)}")
                return None  # Или вернуть сообщение об ошибке
            except Exception as e:
                await session.rollback()  # Откат транзакции в случае ошибки
                print(f"Произошла ошибка: {str(e)}")
                return None  # Или вернуть сообщение об ошибке


    @classmethod
    async def search_all(cls, search, search_type):
        if not search:
            return "Ошибка при поиске "
        async with new_session() as session:
            try:
                if search_type == "name":
                    q = select(DTask).where(DTask.implementer == search)
                if search_type == "open" or  search_type == "close" or  search_type == "check":
                    q = select(DTask).where(and_(DTask.implementer == search, DTask.stat_task == search_type))
                result = await session.execute(q)
                answer = result.scalars().all()
                await session.commit()
                if not answer:
                    return None
                return answer
            except ValueError:
                return False
            except NoResultFound:
                return False
            except IntegrityError:
                await session.rollback()
                return False
            except SQLAlchemyError:
                await session.rollback()
                return False


    @classmethod
    async def select_task_id(cls, ssid):
        async with new_session() as session:
            q = select(DTask).where(DTask.id == int(ssid))
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return answer


    @classmethod
    async def delete_task(cls, ssid):
        async with new_session() as session:
            q = delete(DTask).where(DTask.id == int(ssid))
            await session.execute(q)
            await session.commit()
        return


    @classmethod
    async def select_task_id_personal(cls, ssid, name):
        async with new_session() as session:
            q = select(DTask).where(and_(DTask.id == int(ssid), DTask.implementer == name))
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return answer

    @classmethod
    async def update_task(cls, ssid, implementer, facilitator, priority, describe, stat_task):
        async with new_session() as session:
            q = (
                update(DTask)
                .where(DTask.id == int(ssid))
                .values(
                    implementer=implementer,
                    facilitator=facilitator,
                    priority=priority,
                    describe=describe,
                    stat_task=stat_task
                )
            )
            await session.execute(q)
            await session.commit()
        return


    @classmethod
    async def delete_user(cls, ssid):
        async with new_session() as session:
            q = delete(DUser).where(DUser.id == int(ssid))
            await session.execute(q)
            await session.commit()
        return


    @classmethod
    async def update_user(cls, ssid, name, position, status, describe):
        async with new_session() as session:
            q = (
                update(DUser)
                .where(DUser.id == int(ssid))
                .values(
                    name=name,
                    post=position,
                    status=status,
                    describe=describe
                )
            )
            await session.execute(q)
            await session.commit()
        return


    @classmethod
    async def select_user_id(cls, ssid):
        async with new_session() as session:
            q = select(DUser).where(DUser.id == int(ssid))
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return answer


    @classmethod
    async def select_user_post(cls, ssid):
        async with new_session() as session:
            q = select(DUser.post).where(DUser.id == int(ssid))
            result = await session.execute(q)
            answer = result.scalar()
            if answer is None:
                return None
            return answer


    @classmethod
    async def select_tutor_all(cls):
        async with new_session() as session:
            try:
                q = select(DTutor.tutor, DTutor.name).order_by(DTutor.id.desc())
                result = await session.execute(q)
                rows = result.fetchall()
                tasks_user = [(row.tutor, row.name) for row in rows]     #в кортежи
                return tasks_user
            except Exception as e:
                print(f"Ничего не найдено: {e}")
                return None


    @classmethod
    async def select_posts_all(cls):
        async with new_session() as session:
            try:
                q = select(DPost.position).order_by(DPost.id.desc())
                result = await session.execute(q)
                answer = result.scalars().all()
                return answer
            except Exception as e:
                print(f"Ничего не найдено: {e}")
                return []


    @classmethod
    async def select_user_all(cls):
        async with new_session() as session:
            try:
                q = select(DUser.id, DUser.name).order_by(DUser.id.desc())
                result = await session.execute(q)
                rows = result.fetchall()
                name_user = [(row[0], row[1]) for row in rows]
                return name_user
            except Exception as e:
                print(f"Ничего не найдено: {e}")
                return None


    @classmethod
    async def select_posts(cls):
        async with new_session() as session:
            try:
                q = select(DPost.position)
                result = await session.execute(q)
                posts = result.scalars().all()
                return posts
            except Exception as e:
                print(f"Произошла ошибка при выборке задач: {e}")
                return None


    @classmethod
    async def add_position(cls, position):
        async with new_session() as session:
            try:
                new_post = DPost(position=position)
                session.add(new_post)
                await session.commit()
                return "OK"
            except IntegrityError:
                await session.rollback()
                return 'Должность должна быть уникальной!'
            except Exception as e:
                await session.rollback()
                return f'Произошла ошибка: {str(e)}'
