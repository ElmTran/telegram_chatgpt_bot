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

import logging
from chatgpt import ask
from model import (
    create_session,
    fetch_sessions,
    add_message,
    fetch_messages,
    del_session,
)
from config import Config


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


# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


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
        history = fetch_sessions(user_id)
        if len(history) == 0:
            session_id = create_session(user_id)
            context.user_data["current_session_id"] = session_id
            logger.info("Session created: {} by {}".format(
                session_id, user_id))
            await update.message.reply_text("New session created.")
        else:
            await switch_chat(update, context)


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    session_id = create_session(user_id)
    context.user_data["current_session_id"] = session_id
    logger.info("Session created: {} by {}".format(session_id, user_id))
    await update.message.reply_text("New session created.")


async def switch_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    sessions = fetch_sessions(user_id)

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


async def del_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_session_id = context.user_data["current_session_id"]
    del_session(current_session_id)
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
    prompt = fetch_messages(current_session_id)
    msg = update.message.text
    role = "user"
    if len(prompt) == 0:
        role = "system"
        msgs = [{"role": role, "content": msg}]
        # todo: summary
    else:
        msgs = prompt + [{"role": role, "content": msg}]
    ans = ask(msgs)
    add_message(current_session_id, role, msg)
    add_message(current_session_id, "assistant", ans)
    await update.message.reply_text(ans)

if __name__ == '__main__':
    application = ApplicationBuilder().token(Config.telegram.token).build()

    start_handler = CommandHandler('start', start)
    new_chat_handler = CommandHandler('new', new_chat)
    switch_chat_handler = CommandHandler('switch', switch_chat)
    del_chat_handler = CommandHandler('del', del_chat)
    talk_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), talk)

    application.add_handler(start_handler)
    application.add_handler(new_chat_handler)
    application.add_handler(switch_chat_handler)
    application.add_handler(del_chat_handler)
    application.add_handler(talk_handler)

    application.run_polling()
