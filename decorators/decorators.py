
import functools

from util import *


def error_logging(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            await app.bot.send_message(chat_id=OWNER_ID, text=f"🚨 Exception in {func.__name__}: {str(e)}")
            raise e
    return wrapper


def chunks4096(func):
    async def wrapper(update, context, *args, **kwargs):
        text = await func(update, context, *args, **kwargs)
        if isinstance(text, str):
            chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
            return chunks
        else:
            return []
    return wrapper


def update_thread(prefix_text="", suffix_text=""):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            msg = update.message
            if not msg:
                return await func(update, context)
            thread_payload = []
            print(f"decorating {msg}")
            if msg.text and not any([msg.photo, msg.document, msg.audio, msg.voice, msg.video]):
                thread_payload.append({
                    "type": "text",
                    "text": f"{prefix_text}{msg.text}{suffix_text}"
                })

            elif msg.photo:
                group = msg.media_group_id or "__single__"
                pending = context.user_data.setdefault("pending_albums", {})
                album = pending.setdefault(group, [])

                photo_file = await context.bot.get_file(msg.photo[-1].file_id)
                data = await photo_file.download_as_bytearray()
                buf = BytesIO(data)
                buf.name = "photo.jpg"
                buf.seek(0)

                uploaded = await client.files.create(file=buf, purpose='assistants')
                album.append({
                    "type": "image_file",
                    "image_file": {"file_id": uploaded.id}
                })

                if msg.caption:
                    album.append({
                        "type": "text",
                        "text": f"{prefix_text}{msg.caption}{suffix_text}"
                    })

                if not msg.media_group_id:
                    thread_payload = album
                    pending.pop(group, None)

            elif msg.document:
                doc_file = await context.bot.get_file(msg.document.file_id)
                data = await doc_file.download_as_bytearray()
                buf = BytesIO(data)
                buf.name = msg.document.file_name or "file"
                buf.seek(0)

                uploaded = await client.files.create(file=buf, purpose='assistants')
                thread_payload.append({
                    "type": "file",
                    "file": {"file_id": uploaded.id}
                })

                if msg.caption:
                    thread_payload.append({
                        "type": "text",
                        "text": f"{prefix_text}{msg.caption}{suffix_text}"
                    })

            elif msg.voice:
                voice_file = await context.bot.get_file(msg.voice.file_id)
                data = await voice_file.download_as_bytearray()
                buf = BytesIO(data)
                buf.name = "voice.ogg"
                buf.seek(0)

                uploaded = await client.files.create(file=buf, purpose='assistants')
                thread_payload.append({
                    "type": "audio_file",
                    "audio_file": {"file_id": uploaded.id}
                })

            elif msg.audio:
                audio_file = await context.bot.get_file(msg.audio.file_id)
                data = await audio_file.download_as_bytearray()
                buf = BytesIO(data)
                buf.name = msg.audio.file_name or "audio.mp3"
                buf.seek(0)

                uploaded = await client.files.create(file=buf, purpose='assistants')
                thread_payload.append({
                    "type": "audio_file",
                    "audio_file": {"file_id": uploaded.id}
                })

            elif msg.video:
                video_file = await context.bot.get_file(msg.video.file_id)
                data = await video_file.download_as_bytearray()
                buf = BytesIO(data)
                buf.name = "video.mp4"
                buf.seek(0)

                uploaded = await client.files.create(file=buf, purpose='assistants')
                thread_payload.append({
                    "type": "video_file",
                    "video_file": {"file_id": uploaded.id}
                })

                if msg.caption:
                    thread_payload.append({
                        "type": "text",
                        "text": f"{prefix_text}{msg.caption}{suffix_text}"
                    })

            elif msg.sticker:
                sticker_file = await context.bot.get_file(msg.sticker.file_id)
                data = await sticker_file.download_as_bytearray()
                buf = BytesIO(data)
                buf.name = "sticker.webp"
                buf.seek(0)

                uploaded = await client.files.create(file=buf, purpose='assistants')
                thread_payload.append({
                    "type": "image_file",  # Often interpreted as image
                    "image_file": {"file_id": uploaded.id}
                })

            if thread_payload:
                await add_message_to_thread(context, content=thread_payload, role="user")

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def locker(func):
    @functools.wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        if context.user_data.get('locked', False):
            print(f"locked {func.__name__}")
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper


def delete_update_message(func):
    @functools.wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        msg = update.message
        result = await func(update, context, *args, **kwargs)
        if msg:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.id)
            except Exception as e:
                print(e)

        return result
    return wrapper


def collect_all_messages():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            msg = update.message
            if not msg:
                return await func(update, context)

            user_data = context.user_data.setdefault("collected_messages", {}).setdefault(get_last(context).get("id"), [])

            # Text message
            if msg.text and not any([msg.photo, msg.document, msg.audio, msg.voice, msg.video]):
                user_data.append({
                    "type": "text",
                    "text": msg.text,
                    "filename": "text.txt"
                })

            # Photo
            elif msg.photo:
                photo_file = await context.bot.get_file(msg.photo[-1].file_id)
                data = await photo_file.download_as_bytearray()
                user_data.append({
                    "type": "photo",
                    "data": data,
                    "caption": msg.caption or "",
                    "filename": "image.png"
                })

            # Document
            elif msg.document:
                doc_file = await context.bot.get_file(msg.document.file_id)
                data = await doc_file.download_as_bytearray()
                user_data.append({
                    "type": "document",
                    "data": data,
                    "filename": msg.document.file_name or "file",
                    "caption": msg.caption or ""
                })

            # Voice
            elif msg.voice:
                voice_file = await context.bot.get_file(msg.voice.file_id)
                data = await voice_file.download_as_bytearray()
                user_data.append({
                    "type": "voice",
                    "data": data,
                    "filename": "voice.mp3"
                })

            # Audio
            elif msg.audio:
                audio_file = await context.bot.get_file(msg.audio.file_id)
                data = await audio_file.download_as_bytearray()
                user_data.append({
                    "type": "audio",
                    "data": data,
                    "filename": msg.audio.file_name or "audio.mp3"
                })

            # Video
            elif msg.video:
                video_file = await context.bot.get_file(msg.video.file_id)
                data = await video_file.download_as_bytearray()
                user_data.append({
                    "type": "video",
                    "data": data,
                    "caption": msg.caption or "",
                    "filename": "video.mp4"
                })

            # Sticker
            elif msg.sticker:
                sticker_file = await context.bot.get_file(msg.sticker.file_id)
                data = await sticker_file.download_as_bytearray()
                user_data.append({
                    "type": "sticker",
                    "data": data
                })

            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

