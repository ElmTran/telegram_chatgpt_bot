import time
from sqlalchemy import Column, String, Integer, TEXT, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from config import Config
from logger import logger
try:
    engine = create_engine(
        f"mysql+pymysql://{Config.mysql.user}:{Config.mysql.password}@{Config.mysql.host}:{Config.mysql.port}/{Config.mysql.db}?charset=utf8mb4",
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
                msg_text = " ".join(words[:5]) + \
                    "..." if len(words) > 5 else msg.text
                msg_text = msg_text[:10] + \
                    "..." if len(msg_text) > 10 else msg_text
                break
        if not msg_text:
            msg_text = "(No message)"
        ret.append({"session_id": sid, "message": msg_text})
    sess.close()
    return ret


def remove_session(session_id):
    sess = Sess()
    sess.query(Session).filter_by(id=session_id).update({"is_del": 1})
    sess.query(Message).filter_by(session_id=session_id).update({"is_del": 1})
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
    sess.query(Message).filter_by(session_id=session_id) \
        .order_by(Message.created_at.desc()) \
        .offset(1) \
        .update({"is_del": 1})
    new_message = Message(
        session_id=session_id,
        text=message,
        role="assistant",
        created_at=now,
        updated_at=now
    )
    sess.add(new_message)
    sess.commit()
