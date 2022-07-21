import os

from pyrogram.types import Message


def get_send_method_by_media_type(media_type: str) -> str:
    """
    Get send message method based on the given media type.

    Args:
        media_type (str): The media type.

    Returns:
        str: Send message method.
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
    Get message media file extension if it has any media.

    Args:
        message (Message): The message object.

    Returns:
        str: Media file extension. if the message doesn't have any media, empty string will consider.
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


def remove_attacker_session(session_name: str):
    """
    Remove attacker session by the given session name.

    Args:
        session_name (str): The name of the session file.
    """
    try:
        os.remove(f'attacker_controller/sessions/attackers/{session_name}.session')
    except FileNotFoundError:
        pass
