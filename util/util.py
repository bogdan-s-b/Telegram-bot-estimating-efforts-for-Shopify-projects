import datetime
import random

from Globals import *


async def can_start(chat_id):
    return chat_states.get(chat_id, True)


async def finish(chat_id):
    chat_states[chat_id] = True


def lock(chat_id):
    chat_states[chat_id] = False


async def show_typing(update, context):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")


# THREAD UTILS

async def delete_user_thread(context):
    try:
        all_threads.remove((await get_user_thread(context)).id)
    except Exception as e:
        print(f'failed to delete all files {e}')
    context.user_data['thread'] = None


async def get_user_thread(context):
    if context.user_data.get('thread') is None:
        context.user_data['thread'] = await client.beta.threads.create()
        all_threads.add(context.user_data['thread'].id)
    return context.user_data['thread']


async def add_message_to_thread(context, content, role='user', file_id=None):
    thread = await get_user_thread(context)

    message_kwargs = {
        "thread_id": thread.id,
        "content": content,
        "role": role
    }

    if file_id:

        message_kwargs["attachments"] = [
            {
                "file_id": file_id,
                "tools": [{"type": "code_interpreter"}, {"type": "file_search"}]
            }
        ]

    message = await client.beta.threads.messages.create(**message_kwargs)


async def get_all_thread_messages(thread_id):
    all_messages = []
    cursor = None

    while True:
        response = await client.beta.threads.messages.list(thread_id=thread_id, after=cursor)
        all_messages.extend(response.data)

        if response.has_more:
            cursor = response.data[-1].id
        else:
            break

    return all_messages

# TODO: ########### XZ ###########


def serialize_content_block(block):
    try:
        if block.type == "text":
            return {"type": "text", "value": block.text.value}
        elif block.type == "code":
            return {"type": "code", "value": block.text.value}
        else:
            return {"type": block.type, "value": "[Unsupported content type]"}
    except Exception as e:
        return {"type": "error", "value": str(e)}


async def invalid_answer(obj, message):
    validate_type = obj.get("validate", {}).get("type", "")
    text = message.text.strip()

    types = validate_type.split("|")

    for v_type in types:
        if REGEX_MAP.get(v_type) and re.match(wrap(REGEX_MAP.get(v_type)), text):
            return False
    funcs = obj.get("validate", {}).get("func", "").split("|")
    for func in funcs:
        data = parse_function(func)
        if (REGEX_FUNCS.get(data.get('name')) and
                re.match(wrap(REGEX_FUNCS.get(data.get('name'))(data.get('args'))), text)):
            return False

    return True  # No validator matched


# TODO: ######## GOOGLE DOCS UTIL ########

async def refresh_docs(context):
    try:
        async with Globals.refresh_lock:
            iprint(f"refreshing docs at {datetime.datetime.now()}")
            Globals.doc = docs_client.get_document(SAMPLE_ID)
            Globals.layers_tab = GoogleDocsService.get_tab(Globals.doc, 'layers')
            Globals.brief_tab = GoogleDocsService.get_tab(Globals.doc, 'brief')
            Globals.screen_tab = GoogleDocsService.get_tab(Globals.doc, 'screen')
            Globals.request_tab = GoogleDocsService.get_tab(Globals.doc, 'request')
            Globals.estimate_tab = GoogleDocsService.get_tab(Globals.doc, 'estimate')
            Globals.estimates_tab = GoogleDocsService.get_tab(Globals.doc, 'estimates')
            Globals.sample = []
            Globals.estimates = []

            try:
                Globals.sample.extend(json.loads(GoogleDocsService.tab_text(Globals.layers_tab)))
                Globals.sample.extend(json.loads(GoogleDocsService.tab_text(Globals.brief_tab)))
                Globals.sample.extend(json.loads(GoogleDocsService.tab_text(Globals.screen_tab)))
                Globals.sample.extend(json.loads(GoogleDocsService.tab_text(Globals.request_tab)))
                Globals.sample.extend(json.loads(GoogleDocsService.tab_text(Globals.estimate_tab)))
                Globals.estimates = GoogleDocsService.tab_text(Globals.estimates_tab)
            except Exception as json_exc:
                print(f'Failed to load tabs to json : {json_exc}')

            Globals.sample_objects = {}
            for obj in Globals.sample:
                Globals.sample_objects[obj.get('id')] = obj
    except Exception as e:
        await context.bot.send_message(chat_id=OWNER_ID, text=f"❌ Google Docs refresh failed: {e}")
    iprint(f"docs refreshed at {datetime.datetime.now()}")


# TODO: ######## CLEANUP ########

async def cleanup_orphaned_files():
    try:
        async for f in client.files.list():
            if getattr(f, "purpose", None) == "vision":
                try:
                    await client.files.delete(f.id)
                    print(f"✅ Deleted assistant file: {f.id} ({getattr(f, 'filename', 'unknown')})")
                except Exception as e:
                    print(f"❌ Failed to delete file {f.id}: {e}")
    except Exception as e:
        print(f"❌ Failed to list assistant files: {e}")


async def cleanup():
    try:
        if ASSISTANT_ID != AI_ASSISTANT_FOR_TELEGRAM_BOT_ID:
            await client.beta.assistants.delete(ASSISTANT_ID)
            print(f"✅ Deleted assistant: {ASSISTANT_ID}")
    except Exception as e:
        if 'No assistant found' in str(e):
            print("ℹ️ Assistant already deleted.")
        else:
            print(f"❌ Failed to delete assistant: {e}")

    try:
        for thread_id in all_threads:
            try:
                messages = []
                async for msg in client.beta.threads.messages.list(thread_id=thread_id):
                    messages.append(msg)

                file_ids = []
                for msg in messages:
                    attachments = getattr(msg, "attachments", [])
                    for item in attachments:
                        if item.get("file_id"):
                            file_ids.append(item["file_id"])

                for fid in file_ids:
                    try:
                        await client.files.delete(fid)
                        print(f"✅ Deleted file from thread: {fid}")
                    except Exception as e:
                        print(f"❌ Failed to delete file {fid}: {e}")
            except Exception as e:
                print(f"❌ Failed to list messages for thread {thread_id}: {e}")

            try:
                await client.beta.threads.delete(thread_id)
                print(f"✅ Deleted thread: {thread_id}")
            except Exception as e:
                print(f"❌ Failed to delete thread {thread_id}: {e}")

        all_threads.clear()
        print("✅ All threads cleared.")
    except Exception as e:
        all_threads.clear()
        print(f"❌ Failed to delete all threads: {e}")

    await cleanup_orphaned_files()


def signal_handler(sig, frame):
    print("Interrupted! Cleaning up...")

    loop = asyncio.get_event_loop()
    task = loop.create_task(cleanup())

    def on_cleanup_done(future):
        sys.exit(0)

    task.add_done_callback(on_cleanup_done)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# TODO: ### FIGMA UTILS ###


async def prepare_design(context):
    async with refresh_lock:
        url = context.user_data.get('figma_link')
        figma_file_key = url.removeprefix('https://www.figma.com/files/').split('/')[0]
        print(f"figma file key: {figma_file_key}")

        extractor = FigmaDataExtractor(file_key=figma_file_key, headers=headers)
        data = extractor.extract()

        with open('something.json', 'w') as f:
            json.dump(data, f, indent=2)

        file_like_object = io.BytesIO(json.dumps(data).encode("utf-8"))
        file_like_object.name = 'figma_data.json'  # Required for OpenAI to infer file type

        uploaded_file = openai.files.create(
            file=file_like_object,
            purpose="assistants"
        )

        print(f"file id: {uploaded_file.id}")
        if not uploaded_file.id:
            raise ValueError("File upload failed. No ID returned.")

        context.user_data['figma_json_file_id'] = uploaded_file.id


# TODO: ####### SEND OR EDIT MESSAGE #######


async def send_or_edit_message(context, chat_id, text, reply_markup=None, parse_mode=None, condition=EDIT):
    last_msg_id = context.user_data.get("last_bot_message_id")
    # iprint(f"sending or editing message: {last_msg_id}, with markup: {reply_markup}")
    if condition & SEND:
        sent = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        context.user_data["last_bot_message_id"] = sent.message_id if condition & EDIT else None
        return
    try:
        if last_msg_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=last_msg_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            raise Exception("No previous message")
    except Exception:
        sent = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        context.user_data["last_bot_message_id"] = sent.message_id


# TODO: ######## SESSION ########


def current_session(context):
    return context.user_data.setdefault('session', datetime.datetime.utcnow())


def session_expired(context):
    return datetime.datetime.utcnow() - current_session(context) > SESSION_DURATION


def updated_session(context):
    if session_expired(context):
        context.user_data['session'] = datetime.datetime.utcnow()
    return current_session(context)


def delete_current_session(context):
    if context.user_data.get('session'):
        context.user_data.pop('session')

# TODO: ######## BUTTON DATA WITH CODE MAP ########


def get_next_code(context):
    code = context.user_data.setdefault("next_code", random.randint(1, PRIME_B - 1))
    code = code * PRIME_A % PRIME_B
    context.user_data["next_code"] = code
    return str(code)


def register_code(context, node_id, option_index, next_node=None, type="question"):
    code = get_next_code(context)
    context.user_data.setdefault("code_map", {})[code] = {
        "type": type,
        "node_id": node_id,
        "option_index": option_index,
        "next_node": next_node,
        "session": updated_session(context),
    }
    return code


def get_reply(context, code):
    code = str(code)
    return context.user_data.setdefault("code_map", {}).get(code, {})


def get_option(reply):
    try:
        return Globals.sample_objects.get(reply.get("node_id", ""), {}).get('options')[int(reply.get("option_index", "0"))]
    except Exception as e:
        print(e)


def make_buttons(node, context):
    buttons = []
    node_id = node["id"]
    node_type = node.get("type", "question")
    options = node.get("options", [])

    selected = context.user_data.setdefault("selected_options", {}).setdefault(node_id, set())

    for idx, opt in enumerate(options):
        text = opt["text"].strip() if isinstance(opt, dict) else opt
        next_node = opt.get("next") if isinstance(opt, dict) else None

        if node_type == "multiselect":
            is_selected = True if text in selected else False
            prefix = "✅ " if is_selected else "☐ "
            code = register_code(context, node_id, idx, next_node, type="multiselect")
            buttons.append([InlineKeyboardButton(prefix + text, callback_data=code)])
        else:
            code = register_code(context, node_id, idx, next_node, type="question")
            buttons.append([InlineKeyboardButton(text, callback_data=code)])

    if node_type == "multiselect":
        done_code = register_code(context, node_id, None, next_node=node.get("next"), type="done")
        buttons.append([InlineKeyboardButton("Done", callback_data=done_code)])

    return InlineKeyboardMarkup(buttons)


# TODO: ######## QUEUE ########


def print_queue(context):
    iprint("queue :")
    for content in context.user_data.setdefault('queue', []):
        iprint(content.get('id'))
    iprint("queue ended")


def get_cur(context):
    if len(context.user_data.setdefault('queue', [])) == 0:
        raise Exception('Convesation Queue Is Empty')
    return context.user_data['queue'][0]


def push_last(context, nxt_id: str):
    if nxt_id and Globals.sample_objects.get(nxt_id):
        context.user_data.setdefault('queue', []).append(Globals.sample_objects[nxt_id])


def get_last(context):
    return context.user_data.setdefault('last_obj', {})


def clear_queue(context):
    context.user_data['queue'] = []


def check_cur(context):
    return len(context.user_data.setdefault('queue', [])) > 0


def move_obj(context):
    if len(context.user_data.setdefault('queue', [])) == 0:
        raise Exception('Convesation Queue Is Empty')
    context.user_data['last_obj'] = context.user_data['queue'].pop(0)
    return context.user_data['last_obj']


# TODO: ######## ASK GPT FOR ESTIMATE ########


# async def extract_text_from_image(image_bytes: bytes) -> str:
#     image = Image.open(io.BytesIO(image_bytes))
#     text = pytesseract.image_to_string(image, lang='eng')
#     return text.strip()


async def upload_file_to_openai(data: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1] or ".bin"

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        file = await client.files.create(file=f, purpose="vision")

    os.remove(tmp_path)
    return file.id


async def send_brief_to_openai(context):
    collected = context.user_data.get("collected_messages", {})
    selected_options = context.user_data.get("selected_options", {})
    formatted = []
    file_ids = []

    for section_id, messages in collected.items():
        formatted.append(f"### {section_id.upper()} ###")

        for msg in messages:
            msg_type = msg["type"]
            if msg_type == "text":
                formatted.append(f"- Text: {msg['text']}")
            elif msg_type in ["photo", "document", "video", "sticker"]:
                ext = SUPPORTED_EXTENSIONS.get(msg_type, ".bin")
                filename = msg.get("filename") or f"{msg_type}{ext}"
                file_id = await upload_file_to_openai(msg["data"], filename)
                file_ids.append(file_id)

                formatted.append(f"- Photo uploaded: {filename}")

                # extracted_text = await extract_text_from_image(msg["data"])
                # if extracted_text:
                #     formatted.append(f"  Извлечённый текст: {extracted_text}")
                # if "caption" in msg:
                #     formatted.append(f"  Описание: {msg['caption']}")

    formatted.append("")

    if selected_options:
        formatted.append("### CHOSEN OPTIONS ОПЦИИ ###")
        for node_id, selections in selected_options.items():
            node_text = sample_objects.get(node_id, {}).get("text", "")
            formatted.append(f"- Block: {node_text}")
            for option in selections:
                formatted.append(f"  • {option}")
        formatted.append("")

    thread = await get_user_thread(context)

    prompt = (
        f"""
    You are an experienced Shopify developer. 
    The client has sent a technical specification and design screenshots. 
    Based on the images, please assess:
    Estimated implementation time ( in hours and weeks)

    Approximate    cost( in USD)

    What details need to be clarified before starting work

    If the images don’t provide enough
    information, specify what exactly needs to be supplemented.

    Here’s the
    textual description: {'\n'.join(formatted)}

    Here are the uploaded images(unnecessary): {', '.join(file_ids) if len(file_ids) > 0 else "No images"}
        """
    )

    await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt,
        attachments=[
            {"file_id": fid, "tools": [{"type": "code_interpreter"}]}
            for fid in file_ids
        ]
    )


async def ask_gpt_for_estimate(context):
    await send_brief_to_openai(context)
