import time
from sqlalchemy import Column, String, Integer, TEXT, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from config import cfg
from logger import logger
try:
    engine = create_engine(
        f"mysql+pymysql://{cfg.get('mysql', 'user')}:{cfg.get('mysql', 'password')}@{cfg.get('mysql', 'host')}:{cfg.getint('mysql', 'port')}/{cfg.get('mysql', 'db')}?charset=utf8mb4",
    )
except OperationalError as e:
    logger.error(e)
    exit(1)

Sess = sessionmaker(bind=engine)

Base = declarative_base()


class Session(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    is_del = Column(Integer, default=0)
    created_at = Column(String(20))
    updated_at = Column(String(20))


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer)
    text = Column(TEXT)
    role = Column(String(64))
    is_del = Column(Integer, default=0)
    created_at = Column(String(20))  # format: 2021-01-01 00:00:00
    updated_at = Column(String(20))  # format: 2021-01-01 00:00:00


class Prompt(Base):
    __tablename__ = 'prompt'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    title = Column(String(1024))
    text = Column(TEXT)
    is_del = Column(Integer, default=0)
    created_at = Column(String(20))
    updated_at = Column(String(20))


def create_session(user_id):
    sess = Sess()
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    session = Session(user_id=user_id, created_at=now, updated_at=now)
    sess.add(session)
    sess.commit()
    session_id = session.id
    sess.close()
    return session_id


def query_sessions(user_id):
    sess = Sess()
    sessions = sess.query(Session).filter_by(
        user_id=user_id).filter_by(is_del=0).all()
    # query all first message of each session
    session_ids = [session.id for session in sessions]
    first_messages = (
        sess.query(Message)
        .filter(Message.session_id.in_(session_ids))
        .filter_by(is_del=0)
        .group_by(Message.session_id)
        .all()
    )
    ret = []
    for sid in session_ids:
        msg_text = ""
        for msg in first_messages:
            if sid == msg.session_id:
                words = msg.text.split()
                msg_text = " ".join(words[:7]) + \
                    "..." if len(words) > 7 else msg.text
                msg_text = msg_text[:30] + \
                    "..." if len(msg_text) > 30 else msg_text
                break
        if not msg_text:
            msg_text = "(No message)"
        ret.append({"session_id": sid, "message": msg_text})
    sess.close()
    return ret


def remove_session(session_id):
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sess = Sess()
    sess.query(Session).filter_by(id=session_id).update(
        {"is_del": 1, "updated_at": now})
    sess.query(Message).filter_by(session_id=session_id).update(
        {"is_del": 1, "updated_at": now})
    sess.commit()
    sess.close()


def add_message(session_id, role, message):
    sess = Sess()
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    msg = Message(
        session_id=session_id,
        text=message,
        role=role,
        created_at=now,
        updated_at=now
    )
    sess.add(msg)
    sess.commit()
    msg_id = msg.id
    sess.close()
    return msg_id


def query_messages(session_id):
    sess = Sess()
    messages = sess.query(Message) \
        .filter_by(session_id=session_id) \
        .filter_by(is_del=0) \
        .all()
    ret = [
        {"role": msg.role, "content": msg.text}
        for msg in messages
    ]
    sess.close()
    return ret


def update_previous_messages(session_id, message):
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sess = Sess()
    # del previous messages except the first one
    min_id = sess.query(func.min(Message.id)).filter_by(
        session_id=session_id).scalar()

    sess.query(Message).filter_by(session_id=session_id) \
        .filter(Message.id != min_id) \
        .filter_by(is_del=0) \
        .update({"is_del": 1, "updated_at": now})

    new_message = Message(
        session_id=session_id,
        text=message,
        role="assistant",
        created_at=now,
        updated_at=now
    )
    sess.add(new_message)
    sess.commit()


def add_prompt(user_id, title, text):
    sess = Sess()
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    prompt = Prompt(
        user_id=user_id,
        title=title,
        text=text,
        created_at=now,
        updated_at=now
    )
    sess.add(prompt)
    sess.commit()
    sess.close()


def query_prompts(user_id):
    sess = Sess()
    prompts = sess.query(Prompt) \
        .filter_by(user_id=user_id) \
        .filter_by(is_del=0) \
        .all()
    ret = [
        {
            "id": prompt.id,
            "title": prompt.title,
            "text": prompt.text,
        } for prompt in prompts
    ]
    sess.close()
    return ret


def query_prompt(prompt_id):
    sess = Sess()
    prompt = sess.query(Prompt) \
        .filter_by(id=prompt_id) \
        .filter_by(is_del=0) \
        .first()
    ret = {
        "title": prompt.title,
        "content": prompt.text,
    }
    sess.close()
    return ret


def remove_prompt(prompt_id):
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    sess = Sess()
    sess.query(Prompt).filter_by(id=prompt_id).update(
        {"is_del": 1, "updated_at": now})
    sess.commit()
    sess.close()
