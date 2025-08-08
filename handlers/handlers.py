
from decorators import *


@error_logging
@chunks4096
async def assistant_handler(update, context):
    chat_id = update.effective_chat.id

    thread = await get_user_thread(context)
    iprint("running")
    stream = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
        stream=True,
    )
    iprint("streaming")
    buffer = ""
    async for event in stream:
        if event.event == "thread.message.delta":
            for part in event.data.delta.content:
                buffer += format_openai_response(part)
    return buffer


@error_logging
@delete_update_message
async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('last_bot_message_id'):
        try:
            await context.bot.delete_message(update.effective_chat.id, context.user_data['last_bot_message_id'])
        except Exception as e:
            print(e)
    for key in USER_DATA_TO_CLEAR:
        if context.user_data.get(key):
            context.user_data.pop(key)
    await delete_user_thread(context)
    delete_current_session(context)
    current_session(context)


@error_logging
@delete_update_message
async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ok.")


@error_logging
@delete_update_message
async def wait_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['locked'] = True


@error_logging
@delete_update_message
async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['locked'] = False
    chunks = await assistant_handler(update, context)
    for chunk in chunks:
        time.sleep(0.5)
        try:
            await send_or_edit_message(context, text=chunk, chat_id=update.effective_chat.id, parse_mode="Markdown")
        except Exception as e:
            await send_or_edit_message(context, text=chunk, chat_id=update.effective_chat.id)


#  /start command handler
@error_logging
@delete_update_message
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_queue(context)
    push_last(context, "start")
    return await sample_handler(update, context)


@error_logging
@delete_update_message
async def sample_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, cond=EDIT):
    print_queue(context)
    if check_cur(context):
        obj = get_cur(context)
        last_obj = get_last(context)
    else:
        return ConversationHandler.END
    if not obj.get("id"):
        return ConversationHandler.END

    if last_obj.get('validate'):
        if await invalid_answer(last_obj, update.message):
            obj = last_obj
            push_last(context, obj.get('id'))

    nxt = obj.get('next')
    text = obj.get('text', "")

    if obj.get('type') == "queue":
        for content in context.user_data.setdefault("selected_options", {}).setdefault(obj.get('from'), set()):
            push_last(context, f"{obj.get('id')}_{content}")

        push_last(context, nxt)
        iprint(f"popped {move_obj(context).get('id')}")

        return await sample_handler(update, context)

    markup = None

    if obj.get('options'):
        markup = make_buttons(obj, context)
    iprint(cond)
    await send_or_edit_message(context, update.effective_chat.id, text=text, reply_markup=markup, condition=cond)

    push_last(context, nxt)
    move_obj(context)

    if obj.get('type') == "collect":
        return COLLECT

    if obj.get('type') == 'estimate':
        await ask_gpt_for_estimate(context)
        await text_handler(update, context)

    if obj.get('id') == 'pages':
        print_queue(context)
        iprint("^^^^^^ from pages")
    return CONTINUE if check_cur(context) else ConversationHandler.END


@error_logging
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()
    reply = get_reply(context, query.data)

    print(reply.get('session'))
    print(updated_session(context))

    if not reply.get('session') or reply.get('session') != updated_session(context):
        return CONTINUE
    _from = Globals.sample_objects.get(reply.get('node_id', ''), {})

    if reply.setdefault("type", "") == "multiselect":
        option = get_option(reply)
        selected = context.user_data.setdefault("selected_options", {}).setdefault(_from.get('id'), set())
        text = (option.get("text", "") if isinstance(option, dict) else option)
        if text in selected:
            selected.remove(text)
        else:
            selected.add(text)
        _text = _from.get('text')
        await send_or_edit_message(context, update.effective_chat.id, _text, make_buttons(_from, context))

        return ConversationHandler.END

    elif reply.get("type", "") == "done":

        return await sample_handler(update, context)
    else:
        nxt = reply.get('next_node')

        push_last(context, nxt)

        return await sample_handler(update, context)


@error_logging
@update_thread()
@locker
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not await can_start(chat_id):
        await update.message.reply_text("Please wait… I'm still working on your last message.")
        return

    lock(chat_id)
    await show_typing(update, context)
    chunks = await assistant_handler(update, context)
    for chunk in chunks:
        await show_typing(update, context)
        time.sleep(0.5)
        try:
            await send_or_edit_message(
                context, text=chunk, chat_id=update.effective_chat.id, parse_mode="Markdown", condition=SEND
            )
        except Exception as e:
            await send_or_edit_message(
                context, text=chunk, chat_id=update.effective_chat.id, condition=SEND
            )

    await finish(chat_id)


@error_logging
@locker
async def process_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("processing media group")
    await show_typing(update, context)
    # group_id = update.message.media_group_id
    # pending = context.user_data.get("pending_albums", {})
    # album = pending.pop(group_id, [])
    #
    # await add_message_to_thread(context, content=album, role="user")
    # await update_answers(update, context)
    chunks = await assistant_handler(update, context)
    for chunk in chunks:
        await show_typing(update, context)
        await asyncio.sleep(0.5)
        try:
            await send_or_edit_message(context, text=chunk, chat_id=update.effective_chat.id, parse_mode="Markdown")
        except Exception as e:
            await send_or_edit_message(context, text=chunk, chat_id=update.effective_chat.id)


@error_logging
@update_thread()
async def media_group_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message
    if not msg or not msg.photo:
        return

    if not msg.media_group_id:
        await process_media_group(update, context)
        return

    group_id = msg.media_group_id

    if group_id in group_timers:
        group_timers[group_id].cancel()
    print("something in media_group_handler")
    group_timers[group_id] = asyncio.get_event_loop().call_later(
        1.0, lambda: asyncio.create_task(process_media_group(update, context))
    )


@error_logging
async def estimate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('has_design') or context.user_data.get('figma_link'):
        await prepare_design(context)
        await add_message_to_thread(context, "Use this instructions for estimating time and cost "
                                    "required to create site on Shopify platform: " + str(estimates) +
                                    "take all necessary information about site layout from the uploaded file "
                                    " 'figma_data.json' ", "user",
                                    context.user_data.get('figma_json_file_id'))
        await text_handler(update, context)

    else:
        await add_message_to_thread(context, "Use this instructions for estimating time and cost: " + str(estimates), "user")
        await text_handler(update, context)


@error_logging
async def ready_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    iprint("ready handler aoaoaoaoo")
    return await sample_handler(update, context, cond=(SEND | EDIT))


@error_logging
@collect_all_messages()
async def collect_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    collected = context.user_data.get("collected_messages", {}).setdefault(get_last(context).get('id'), [])
    print(f"Collected so far: {len(collected)} messages")
    return COLLECT


@error_logging
async def uid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = f"uid - {user.id}"
    await update.message.reply_text(data)


@error_logging
async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread = await get_user_thread(context)
    messages = await client.beta.threads.messages.list(thread_id=thread.id)
    for msg in messages:
        print(msg.id, msg.role, msg.content, msg.attachments)

