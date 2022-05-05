from pyrogram.types import Message


def get_send_method_by_media_type(media_type: str) -> str:
    """
    Get send method based on given media type.
    """
    if media_type == 'photo':
        method = 'send_photo'
    elif media_type == 'video':
        method = 'send_video'
    elif media_type == 'animation':
        method = 'send_animation'
    elif media_type == 'voice':
        method = 'send_voice'
    elif media_type == 'sticker':
        method = 'send_sticker'
    else:
        method = 'send_message'

    return method


def get_message_file_extension(message: Message) -> str:
    """
    Return the message file extension.
    If no file is in the given message, empty string will return.
    """
    if message.media == 'photo':
        file_ext = 'jpg'
    elif message.media == 'video' or message.media == 'animation':
        file_ext = 'mp4'
    elif message.media == 'voice':
        file_ext = 'ogg'
    elif message.media == 'sticker':
        file_ext = 'webm'
        if message.sticker.is_animated:
            file_ext = 'tgs'
    else:
        file_ext = ''

    return file_ext
