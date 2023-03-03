import time
from sqlalchemy import Column, String, Integer, TEXT, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config

engine = create_engine(
    f"mysql+pymysql://{Config.mysql.user}:{Config.mysql.password}@{Config.mysql.host}/{Config.mysql.db}?charset=utf8mb4",
)
Sess = sessionmaker(bind=engine)

Base = declarative_base()


class Session(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    created_at = Column(String(20))
    updated_at = Column(String(20))


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer)
    text = Column(TEXT)
    role = Column(String(64))
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


def fetch_sessions(user_id):
    sess = Sess()
    sessions = sess.query(Session).filter_by(user_id=user_id).all()
    # query all first message of each session
    first_messages = [
        sess.query(Message).filter_by(session_id=s.id).first()
        for s in sessions
    ]
    ret = []
    for s, m in zip(sessions, first_messages):
        if m:
            word_list = m.text.split(" ")
            if len(word_list) > 5:
                message = " ".join(word_list[:5]) + "..."
            else:
                message = m.text[:10] + "..." if len(m.text) > 10 else m.text
        else:
            message = "(No message)"
        ret.append({
            "session_id": s.id,
            "message": message,
        })
    sess.close()
    return ret


def del_session(session_id):
    sess = Sess()
    sess.query(Session).filter_by(id=session_id).delete()
    sess.query(Message).filter_by(session_id=session_id).delete()
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


def fetch_messages(session_id):
    sess = Sess()
    messages = sess.query(Message).filter_by(session_id=session_id).all()
    ret = [
        {"role": msg.role, "content": msg.text}
        for msg in messages
    ]
    sess.close()
    return ret


if __name__ == "__main__":
    # update table
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
