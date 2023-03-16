import re
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    add_prompt,
    query_prompt,
    query_prompts,
    remove_prompt,
)
from config import cfg
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
        html += f"<a href='https://t.me/{cfg.get('bot', 'name')}?start={s_id}'>{s_content}</a>\n"
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


async def new_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Please enter the title of the prompt.")
    return "NEW_PROMPT"


async def callback_new_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    title = update.message.text
    context.user_data["prompt_title"] = title
    await update.message.reply_text("Please enter the content of the prompt.")
    return "NEW_PROMPT_CONTENT"


async def callback_new_prompt_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    content = update.message.text
    user_id = update.effective_user.id
    title = context.user_data["prompt_title"]
    add_prompt(user_id, title, content)
    await update.message.reply_text(f"Prompt {title} created.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


async def new_session_with_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    prompts = query_prompts(user_id)

    if len(prompts) == 0:
        await update.message.reply_text("You have no prompt. Use /newp to start a new prompt.")
        return

    keyboard = [[InlineKeyboardButton(prompt["title"], callback_data=str(
        prompt["id"]))] for prompt in prompts]
    await update.message.reply_text("Select a prompt to start a new session:", reply_markup=InlineKeyboardMarkup(keyboard))
    return "SELECT_PROMPT"


async def callback_new_session_with_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    prompt_id = int(query.data)
    prompt = query_prompt(prompt_id)
    session_id = create_session(user_id)
    context.user_data["current_session_id"] = session_id
    add_message(session_id, "system", prompt['content'])
    await query.edit_message_text(text=f"New session created with prompt {prompt['title']}")
    return ConversationHandler.END


async def del_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    prompts = query_prompts(user_id)

    if len(prompts) == 0:
        await update.message.reply_text("You have no prompt. Use /newp to start a new prompt.")
        return

    keyboard = [[InlineKeyboardButton(prompt["title"], callback_data=str(
        prompt["id"]))] for prompt in prompts]
    await update.message.reply_text("Select a prompt to delete:", reply_markup=InlineKeyboardMarkup(keyboard))
    return "REMOVE_PROMPT"


async def callback_del_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    prompt_id = int(query.data)
    prompt = query_prompt(prompt_id)
    remove_prompt(prompt_id)
    await query.edit_message_text(text=f"Prompt {prompt['title']} deleted.")
    return ConversationHandler.END


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
    token = cfg.get("bot", "token")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_session))
    app.add_handler(CommandHandler("switch", switch_session))
    app.add_handler(CommandHandler("del", del_session))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("newp", new_prompt)],
        states={
            "NEW_PROMPT": [MessageHandler(filters.TEXT, callback_new_prompt)],
            "NEW_PROMPT_CONTENT": [MessageHandler(filters.TEXT, callback_new_prompt_content)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("nswp", new_session_with_prompt)],
        states={
            "SELECT_PROMPT": [CallbackQueryHandler(callback_new_session_with_prompt, pattern=r"\d+")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delp", del_prompt)],
        states={
            "REMOVE_PROMPT": [CallbackQueryHandler(callback_del_prompt, pattern=r"\d+")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), talk))
    return app


if __name__ == '__main__':
    # Check if tables exist
    with engine.connect() as conn:
        if not engine.dialect.has_table(conn, "prompt"):
            Base.metadata.create_all(engine)

    app = create_app()
    app.run_polling()
