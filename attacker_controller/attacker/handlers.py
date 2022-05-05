from pyrogram import filters
from pyrogram.handlers import MessageHandler

from attacker_controller import MAIN_ADMINS
from attacker_controller.attacker import commands
from attacker_controller.utils.custom_filters import admin

send_code_handler = MessageHandler(
    commands.send_code,
    filters.regex(r'^\/sendcode (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

login_attacker_handler = MessageHandler(
    commands.login_attacker,
    filters.regex(r'^\/login (\+\d+) (.+)$') &
    filters.group &
    ~filters.edited &
    admin
)

attacker_list_handler = MessageHandler(
    commands.attacker_list,
    filters.command('attackerlist') &
    filters.group &
    ~filters.edited &
    admin
)

remove_attacker_handler = MessageHandler(
    commands.remove_attacker,
    filters.regex(r'^\/removeattacker (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

clean_attacker_list_handler = MessageHandler(
    commands.clean_attacker_list,
    filters.command('cleanattackers') &
    filters.group &
    ~filters.edited &
    filters.user(MAIN_ADMINS)
)

set_first_name_all_handler = MessageHandler(
    commands.set_first_name_all,
    filters.command('setfirstnameall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)

set_last_name_all_handler = MessageHandler(
    commands.set_last_name_all,
    filters.command('setlastnameall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)

set_bio_all_handler = MessageHandler(
    commands.set_bio_all,
    filters.command('setbioall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)

set_profile_photo_all_handler = MessageHandler(
    commands.set_profile_photo_all,
    filters.command('setprofileall') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)

set_first_name_handler = MessageHandler(
    commands.set_first_name,
    filters.regex(r'^\/setfirstname (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

set_last_name_handler = MessageHandler(
    commands.set_last_name,
    filters.regex(r'^\/setlastname (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

set_bio_handler = MessageHandler(
    commands.set_bio,
    filters.regex(r'^\/setbio (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

set_profile_photo_handler = MessageHandler(
    commands.set_profile_photo,
    filters.regex(r'^\/setprofile (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

set_username_handler = MessageHandler(
    commands.set_username,
    filters.regex(r'^\/setusername (\+\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

get_group_members_handler = MessageHandler(
    commands.get_group_members,
    filters.regex(r'^\/members (\+\d+) @?(.*) (\d+)$') &
    filters.group &
    ~filters.edited &
    admin
)

set_banner_handler = MessageHandler(
    commands.set_banner,
    filters.command('setbanner') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)

get_current_banner_handler = MessageHandler(
    commands.get_current_banner,
    filters.command('banner') &
    filters.group &
    ~filters.edited &
    admin
)

set_attack_handler = MessageHandler(
    commands.attack,
    filters.regex(r'^\/attack (\+\d+)$') &
    filters.group &
    ~filters.edited &
    filters.reply &
    admin
)
