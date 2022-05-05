def get_send_method_by_media_type(media_type: str):
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
