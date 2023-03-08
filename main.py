import re
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram import Update
from telegram.constants import ParseMode
from telegram import __version__ as TG_VER

from chatgpt import ask
from model import (
    engine,
    Base,
    create_session,
    query_sessions,
    add_message,
    query_messages,
    remove_session,
    update_previous_messages,
)
from config import Config
from logger import logger


try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # if no chat then create a new chat
    user_id = update.effective_user.id
    args = context.args
    if len(args) != 0:
        current_session_id = int(args[0])
        context.user_data["current_session_id"] = current_session_id
        logger.info("Session switched: {} by {}".format(
            current_session_id, user_id))
        await update.message.reply_text(f"Session {args[0]} loaded.")
    else:
        history = query_sessions(user_id)
        if len(history) == 0:
            session_id = create_session(user_id)
            context.user_data["current_session_id"] = session_id
            logger.info("Session created: {} by {}".format(
                session_id, user_id))
            await update.message.reply_text("New session created.")
        else:
            await switch_session(update, context)


async def new_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session_id = create_session(user_id)
    context.user_data["current_session_id"] = session_id
    logger.info("Session created: {} by {}".format(session_id, user_id))
    await update.message.reply_text("New session created.")


async def switch_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    sessions = query_sessions(user_id)

    if len(sessions) == 0:
        await update.message.reply_text("You have no chat history. Use /new to start a new chat.")
        return
    # reply a html message with a list of chats
    html = "Select a session to continue:\n"
    for s in sessions:
        s_id = s["session_id"]
        s_content = f"{s_id}. {s['message']}"
        html += f"<a href='https://t.me/{Config.bot.username}?start={s_id}'>{s_content}</a>\n"
    await update.message.reply_text(html, parse_mode=ParseMode.HTML)


async def del_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_session_id = context.user_data["current_session_id"]
    remove_session(current_session_id)
    context.user_data["current_session_id"] = None
    logger.info("Session deleted: {} by {}".format(
        current_session_id, update.effective_user.id))
    await update.message.reply_text(
        "Chat history deleted. Use /switch to switch to another chat or /new to start a new chat."
    )


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_session_id = context.user_data.get("current_session_id", None)
    if current_session_id is None:
        await update.message.reply_text(
            "Please use /new to create a new session or /switch to switch to an existing session."
        )
        return
    prompt = query_messages(current_session_id)
    msg = update.message.text
    role = "user"
    if len(prompt) == 0:
        role = "system"
        msgs = [{"role": role, "content": msg}]
    else:
        summary = ""
        all_text = "\n".join([m["content"] for m in prompt])
        if len(all_text) > 5000:
            request_text = "Please summarize the previous conversation. It will be used in the context of our subsequent conversations. Do not use like 'overall' to comment or draw conclusions about these contents."
            summary_request = prompt + \
                [{"role": role, "content": request_text}]
            summary = ask(summary_request)
            update_previous_messages(current_session_id, summary)
            prompt = [prompt[0], {"role": "assistant", "content": summary}]
        msgs = prompt + [{"role": role, "content": msg}]
    ans = ask(msgs)
    add_message(current_session_id, role, msg)
    add_message(current_session_id, "assistant", ans)
    escape = re.compile(r"([*_\[\]()~>#+-=|{}.!])")
    ans = escape.sub(r"\\\1", ans)
    await update.message.reply_text(ans, parse_mode=ParseMode.MARKDOWN_V2)


def create_app() -> ApplicationBuilder:
    app = ApplicationBuilder().token(Config.telegram.token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_session))
    app.add_handler(CommandHandler("switch", switch_session))
    app.add_handler(CommandHandler("del", del_session))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), talk))
    return app


if __name__ == '__main__':
    # Check if tables exist
    with engine.connect() as conn:
        if not engine.dialect.has_table(conn, "session"):
            Base.metadata.create_all(engine)

    app = create_app()
    app.run_polling()
