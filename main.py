from handlers import *

# ---


async def error_handler(update, context):
    try:
        raise context.error
    except Exception as e:
        await context.application.bot.send_message(chat_id=OWNER_ID, text=f"🚨 Oops - {str(e)} happened")


def main():

    app.add_handler(CommandHandler("reset", reset_handler))
    # app.add_handler(CommandHandler("estimate", estimate_handler))
    app.add_handler(CommandHandler("uid", uid_handler))
    app.add_handler(CommandHandler("debug", debug_handler))
    # app.add_handler(CommandHandler("wait", wait_handler))
    # app.add_handler(CommandHandler("reply", reply_handler))

    states_dict = {
        CONTINUE: [
            CallbackQueryHandler(button_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, partial(sample_handler, cond=EDIT))
        ],
        COLLECT: [
            MessageHandler(filters.ALL & ~filters.COMMAND, collect_handler),
            CommandHandler("ready", ready_handler),
        ],
    }

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler), CallbackQueryHandler(button_handler)],
        states=states_dict,
        fallbacks=[
            CommandHandler('cancel', callback=cancel_handler),
            CommandHandler("start", start_handler),
            CommandHandler("reset", reset_handler),
        ],
    )
    app.add_handler(conv_handler)

    app.add_handler(MessageHandler(
        (filters.TEXT & ~filters.COMMAND),
        text_handler
    ))
    app.add_handler(MessageHandler(filters.PHOTO, media_group_handler))

    app.job_queue.run_repeating(refresh_docs, interval=60, first=0)

    # app.add_error_handler(error_handler)

    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    finally:
        asyncio.run(cleanup())
