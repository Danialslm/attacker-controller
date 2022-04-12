import os
import random
import re
from time import sleep
import logging
import redis
import requests
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.raw import functions
from pyrogram.raw.functions.account import GetAuthorizations
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
logging.basicConfig(level='INFO')
# Pishniyaz
app = Client('attack', 1735810, '92c95a8087736c3d61e115bc2fb54171', bot_token='5145180460:AAFySTiZfvxXdTOCc_0MKljB8Xjx5z8PaqE')
redis = redis.StrictRedis(host='localhost', port=6379, db=8, charset='UTF-8', decode_responses=True)
user = [763410818, 2130894243, 1758226276, 631740306, 1819858111]
apps = {}
delay_each_atk = 8
attacker = {}
delay_time = 3
aname = ['MatrixAttack', 'Matrix', 'AttackBot', 'Mahdi', 'Soltan', 'Special', 'Power']
lname = ['Zavare', 'Majnon', 'Matrixs', 'Javad', 'Darioush', 'Mendy', 'Irani']
tname = ['Matrix_Manager', 'Eshgh_Maani', 'Jnane_Mn', 'World_On_Fire_Game']


# Create AppHash,MoreFunction
def list_splitter(my_list, n):
    final = [my_list[i * n:(i + 1) * n] for i in range((len(my_list) + n - 1))]
    return final


def get_stats(user_id):
    wuff_url = "http://www.tgwerewolf.com/Stats/PlayerStats/?pid={}&json=true"
    stats = requests.get(wuff_url.format(user_id)).json()
    return stats


def writefile(filename, input):
    f = open(filename, "w")
    f.write(input)
    f.close()
    return True


def chunk(List, Chunk):
    return [List[x:x + Chunk] for x in range(0, len(List), Chunk)]


def chunkplus(a, b):
    return [a[x:x + b] for x in range(0, len(a), b)]


def scarp_tg_existing_app(stel_token):
    """scraps the web page using the provided cookie,
    returns True or False appropriately"""
    request_url = "https://my.telegram.org/apps"
    custom_header = {
        "Cookie": stel_token
    }
    response_c = requests.get(request_url, headers=custom_header)
    response_text = response_c.text
    soup = BeautifulSoup(response_text, features="html.parser")
    title_of_page = soup.title.string
    re_dict_vals = {}
    re_status_id = None
    if "configuration" in title_of_page:
        g_inputs = soup.find_all("span", {"class": "input-xlarge"})
        app_id = g_inputs[0].string
        api_hash = g_inputs[1].string
        test_configuration = g_inputs[4].string
        production_configuration = g_inputs[5].string
        re_dict_vals = {
            "App Configuration": {
                "app_id": app_id,
                "api_hash": api_hash
            },
            "Available MTProto Servers": {
                "test_configuration": test_configuration,
                "production_configuration": production_configuration
            },
            "Disclaimer": "It is forbidden to pass this value to third parties."
        }
        re_status_id = True
    else:
        tg_app_hash = soup.find("input", {"name": "hash"}).get("value")
        re_dict_vals = {
            "tg_app_hash": tg_app_hash
        }
        re_status_id = False
    return re_status_id, re_dict_vals


def tg_code_get_random_hash(input_phone_number):
    request_url = "https://my.telegram.org/auth/send_password"
    request_data = {
        "phone": input_phone_number
    }
    response_c = requests.post(request_url, data=request_data)
    json_response = response_c.json()
    return json_response["random_hash"]


def login_step_get_stel_cookie(
    input_phone_number,
    tg_random_hash,
    tg_cloud_password
):
    """Logins to my.telegram.org and returns the cookie,
    or False in case of failure"""
    request_url = "https://my.telegram.org/auth/login"
    request_data = {
        "phone": input_phone_number,
        "random_hash": tg_random_hash,
        "password": tg_cloud_password
    }
    response_c = requests.post(request_url, data=request_data)
    re_val = None
    re_status_id = None
    if response_c.text == "true":
        re_val = response_c.headers.get("Set-Cookie")
        re_status_id = True
    else:
        re_val = response_c.text
        re_status_id = False
    return re_status_id, re_val


def create_new_tg_app(
    stel_token,
    tg_app_hash,
    app_title,
    app_shortname,
    app_url,
    app_platform,
    app_desc
):
    """ creates a new my.telegram.org/apps
    using the provided parameters """
    request_url = "https://my.telegram.org/apps/create"
    custom_header = {
        "Cookie": stel_token
    }
    request_data = {
        "hash": tg_app_hash,
        "app_title": app_title,
        "app_shortname": app_shortname,
        "app_url": app_url,
        "app_platform": app_platform,
        "app_desc": app_desc
    }
    response_c = requests.post(
        request_url,
        data=request_data,
        headers=custom_header
    )
    return response_c


# End Function
# Start CapcherOne

@app.on_message(filters.command(["cleanall"]))
def clenall(client, message):
    user = message.from_user.id
    lists = redis.smembers(f'accounts{user}')
    for i in lists:
        n = f'{i}{user}'
        try:
            apps[n].get_me().id
        except Exception as e:
            if "KeyError" or f"'{n}'" in str(e):
                Id = redis.get(f"appids{i}{user}") or 993381
                Hash = redis.get(f"apphashs{i}{user}") or "10df0e3b765cf30c0b8bd147b3b10c92"
                apps[n] = Client(n, int(Id), Hash)
                apps[n].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
    for x in lists:
        name = f'{x}{user}'
        try:
            apps[name].log_out()
        except:
            pass
        try:
            os.remove(f"{name}.session")
        except:
            pass
        try:
            os.remove(f"{name}.session-journal")
        except:
            pass
    apps.clear()
    message.reply_text("• اکانت های شما از داخل ربات پاکسازی شد !")
    for i in lists:
        n = f'{i}{user}'
        Id = redis.get(f"appids{i}{user}")
        Hash = redis.get(f"apphashs{i}{user}")
        try:
            apps[n].disconnect()
        except:
            pass
    redis.delete(f'accounts{user}')
    print("Down")


@app.on_message(filters.command(["del"]))
def delacc(client, message):
    user = message.from_user.id
    ph = int(message.command[1])
    name = f'{ph}{user}'
    redis.srem(f'accounts{user}', ph)
    try:
        apps[name].log_out()
    except:
        pass
    try:
        os.remove(f"{name}.session")
    except:
        pass
    try:
        apps.pop(name)
    except:
        pass
    message.reply_text(f"• اکانت {ph} با موفقیت حذف شد !")


@app.on_message(filters.command(["check"]))
def setlink(client, message):
    if message.text:
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        message.reply_text("صبررر")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        for i in lists:
            n = f'{i}{user}'
            try:
                id = apps[n].get_me().id
            except Exception as e:
                try:
                    if "[400 CHANNEL_INVALID]" in str(e):
                        print('nist to gp')
                    elif "[401 AUTH_KEY_UNREGISTERED]" in str(e):
                        message.reply_text(f"اکانت {i} دیلیت شده !")
                        redis.srem(f'accounts{user}', i)
                    elif "[401 SESSION_REVOKED]" in str(e):
                        message.reply_text(f"اکانت {i} دیلیت شده !")
                        redis.srem(f'accounts{user}', i)
                    elif "[401 SESSION_REVOKED]" in str(e):
                        message.reply_text(f"اکانت {i} دیلیت شده !")
                        redis.srem(f'accounts{user}', i)
                    elif "[401 USER_DEACTIVATED_BAN]" in str(e):
                        message.reply_text(f"اکانت {i} دیلیت شده !")
                        redis.srem(f'accounts{user}', i)
                    elif "[401 USER_DEACTIVATED]" in str(e):
                        message.reply_text(f"اکانت {i} دیلیت شده !")
                        redis.srem(f'accounts{user}', i)
                    else:
                        message.reply_text(e)
                except:
                    pass
        message.reply_text("چک کردن به پایان رسید !")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")


@app.on_message(filters.group & filters.text & ~filters.edited & filters.user(user))
def group(client, message):
    user = message.from_user.id
    chat = message.chat.id
    men = message.from_user.mention
    name = message.from_user.first_name
    if redis.get("timename" + str(user)):
        ph = int(redis.get("timeph" + str(user)))
        keyboards = [[InlineKeyboardButton("• لاگ اوت", callback_data=f"matrix log {user} {ph}"),
                      InlineKeyboardButton("• تغییر اسم اکانت", callback_data=f"matrix name {user} {ph}")],
                     [InlineKeyboardButton("• تغییر بیو اکانت", callback_data=f"matrix bio {user} {ph}"),
                      InlineKeyboardButton("• تغییر یوزنیم اکانت", callback_data=f"matrix usernmae {user} {ph}")],
                     [InlineKeyboardButton(f"• برگشت", callback_data=f"matrix d {user} {ph}")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        try:
            apps[f"{ph}{user}"].get_me().id
        except Exception as e:
            if "KeyError" or f"{ph}{user}" in str(e):
                Id = redis.get(f"appids{ph}{user}")
                Hash = redis.get(f"apphashs{ph}{user}")
                apps[f"{ph}{user}"] = Client(f"{ph}{user}", int(Id), Hash)
                apps[f"{ph}{user}"].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        apps[f"{ph}{user}"].update_profile(first_name=f"{message.text}")
        app.send_message(message.chat.id, "با موفقیت ست شد !", parse_mode='HTML', reply_markup=reply_markups)
        redis.delete("timename" + str(user))
        try:
            apps[f"{ph}{user}"].disconnect()
        except:
            pass
    if redis.get("timebio" + str(user)):
        ph = int(redis.get("timeph" + str(user)))
        keyboards = [[InlineKeyboardButton("• لاگ اوت", callback_data=f"matrix log {user} {ph}"),
                      InlineKeyboardButton("• تغییر اسم اکانت", callback_data=f"matrix name {user} {ph}")],
                     [InlineKeyboardButton("• تغییر بیو اکانت", callback_data=f"matrix bio {user} {ph}"),
                      InlineKeyboardButton("• تغییر یوزنیم اکانت", callback_data=f"matrix usernmae {user} {ph}")],
                     [InlineKeyboardButton(f"• برگشت", callback_data=f"matrix d {user} {ph}")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        try:
            apps[f"{ph}{user}"].get_me().id
        except Exception as e:
            if "KeyError" or f"{ph}{user}" in str(e):
                Id = redis.get(f"appids{ph}{user}")
                Hash = redis.get(f"apphashs{ph}{user}")
                apps[f"{ph}{user}"] = Client(f"{ph}{user}", int(Id), Hash)
                apps[f"{ph}{user}"].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        apps[f"{ph}{user}"].update_profile(bio=f"{message.text}")
        app.send_message(message.chat.id, "با موفقیت ست شد !", parse_mode='HTML', reply_markup=reply_markups)
        redis.delete("timebio" + str(user))
        try:
            apps[f"{ph}{user}"].disconnect()
        except:
            pass
    if redis.get("timeusername" + str(user)):
        ph = int(redis.get("timeph" + str(user)))
        keyboards = [[InlineKeyboardButton("• لاگ اوت", callback_data=f"matrix log {user} {ph}"),
                      InlineKeyboardButton("• تغییر اسم اکانت", callback_data=f"matrix name {user} {ph}")],
                     [InlineKeyboardButton("• تغییر بیو اکانت", callback_data=f"matrix bio {user} {ph}"),
                      InlineKeyboardButton("• تغییر یوزنیم اکانت", callback_data=f"matrix usernmae {user} {ph}")],
                     [InlineKeyboardButton(f"• برگشت", callback_data=f"matrix d {user} {ph}")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        try:
            apps[f"{ph}{user}"].get_me().id
        except Exception as e:
            if "KeyError" or f"{ph}{user}" in str(e):
                Id = redis.get(f"appids{ph}{user}")
                Hash = redis.get(f"apphashs{ph}{user}")
                apps[f"{ph}{user}"] = Client(f"{ph}{user}", int(Id), Hash)
                apps[f"{ph}{user}"].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        try:
            apps[f"{ph}{user}"].update_username(message.text)
        except Exception as e:
            print(e)
            app.send_message(message.chat.id, "یوزرنیم وجود دارد !", parse_mode='HTML')
            return
        app.send_message(message.chat.id, "با موفقیت ست شد !", parse_mode='HTML', reply_markup=reply_markups)
        redis.delete("timeusername" + str(user))
        try:
            apps[f"{ph}{user}"].disconnect()
        except:
            pass
    if redis.get("timecode" + str(user)):
        user = message.from_user.id
        aa = random.choice(aname)
        ab = random.choice(lname)
        phnum = redis.get(f"phone{user}")
        name = f'{phnum}{user}'
        phhash = redis.get(f"phhash{phnum}{user}")
        Id = redis.get(f"appid{user}")
        Hash = redis.get(f"apphash{user}")
        ph1 = message.text.split()[0]
        try:
            try:
                apps[name].sign_in(phnum, phhash, ph1)
            except Exception as e:
                print(e)
                if "[400 PHONE_CODE_EXPIRED]" in str(e):
                    message.reply_text(f"• کد وارد شده منقضی شده است !")
                    redis.delete("timecode" + str(user))
                    return
                elif "[401 AUTH_KEY_UNREGISTERED]" in str(e):
                    message.reply_text(f"• رمز دوم اکانت نادرست وارد  شده است !")
                    return
                elif "[401 SESSION_PASSWORD_NEEDED]" in str(e):
                    try:
                        codes = message.text.split()[1]
                    except:
                        message.reply_text(f"• اکانت دارای دومرحله ایی میباشد !\n◂ لطفا با یک فاصله گذر را وارد کنید:")
                        return
                    apps[name].check_password(codes)
            aes_mesg_i = app.send_message(message.chat.id, '• لطفا صبر کنید !')
        except Exception as e:
            if "[400 PASSWORD_HASH_INVALID]" in str(e):
                message.reply_text(f"• گذر اکانت را اشتباه وارد کردید !")
                return
            else:
                app.send_message(message.chat.id, '• کد اشتباه وارد شد !')
                return
        request_url = "https://my.telegram.org/auth/send_password"
        request_data = {
            "phone": redis.get(f"phone{user}")
        }
        response_c = requests.post(request_url, data=request_data)
        try:
            json_response = response_c.json()
        except:
            redis.sadd(f'accounts{user}', phnum)
            s = message.reply_text(f"• سرور با موفقیت لوگین شد !")
            redis.delete("timecode" + str(user))
            if redis.get(f'setname{user}'):
                name1 = redis.get(f'nemeauto{user}')
                apps[name].update_profile(first_name=f"{name1}")
                s2 = app.edit_message_text(message.chat.id, s.message_id, "• سرور با موفقیت لوگین شد !",
                                           parse_mode='HTML')
                redis.delete("timecode" + str(user))
            if redis.get(f'setbio{user}'):
                name1 = redis.get(f'bioauto{user}')
                apps[name].update_profile(bio=f"{name1}")
                s3 = app.edit_message_text(message.chat.id, s2.message_id, "• سرور با موفقیت لوگین شد !",
                                           parse_mode='HTML')
                redis.delete("timecode" + str(user))
            if redis.get(f'setphoto{user}'):
                name1 = redis.get(f'photoauto{user}')
                apps[name].set_profile_photo(photo=f"./downloads/{name1}.jpg")
                s4 = app.edit_message_text(message.chat.id, s3.message_id, "• سرور با موفقیت لوگین شد !",
                                           parse_mode='HTML')
                redis.delete("timecode" + str(user))
            if redis.get(f'setpass{user}'):
                name1 = redis.get(f'passauto{user}')
                try:
                    apps[name].enable_cloud_password(f"{name1}", hint="Matrix Attack")
                except:
                    apps[name].change_cloud_password(f"{message.text.split()[1]}", f"{name1}", new_hint="Matrix Attack")
                app.edit_message_text(message.chat.id, s4.message_id, "• سرور با موفقیت لوگین شد !", parse_mode='HTML')
                redis.delete("timecode" + str(user))
                try:
                    apps[name].disconnect()
                except:
                    pass
            aes_mesg_i.delete()
        input_text = redis.get(f"phone{user}")
        if input_text is None:
            message.reply_text(text="• متاسفم کد وارد شده  شما اشتباه است !", parse_mode='HTML')
        random_hash = tg_code_get_random_hash(input_text)
        redis.set(f"input{user}", input_text)
        redis.set(f"random{user}", random_hash)
        result = apps[name].get_history(777000, limit=1)
        incoming_message_text = result[0].text
        incoming_message_text_in_lower_case = incoming_message_text.lower()
        if "web login code" in incoming_message_text_in_lower_case:
            parted_message_pts = incoming_message_text.split("\n")
            if len(parted_message_pts) >= 2:
                telegram__web_login_code = parted_message_pts[1]
        elif "\n" in incoming_message_text_in_lower_case:
            print("did it come inside this 'elif' ?")
        else:
            telegram__web_login_code = incoming_message_text
        provided_code = telegram__web_login_code
        if provided_code is None:
            app.edit_message_text(message.chat.id, aes_mesg_i.message_id, "• متاسفم کد وارد شده  شما اشتباه است !")
            return INPUT_PHONE_NUMBER
        status_r, cookie_v = login_step_get_stel_cookie(
            redis.get(f"input{user}"),
            redis.get(f"random{user}"),
            provided_code
        )
        if status_r:
            status_t, response_dv = scarp_tg_existing_app(cookie_v)
            if not status_t:
                create_new_tg_app(
                    cookie_v,
                    response_dv.get("tg_app_hash"),
                    os.environ.get("APP_TITLE", f"{aa}"),
                    os.environ.get("APP_SHORT_NAME", f"{ab}"),
                    os.environ.get("APP_URL", f"https://telegram.dog/matrix_manager"),
                    "other",
                    os.environ.get("APP_DESCRIPTION", "Use Help Members")
                )
            status_t, response_dv = scarp_tg_existing_app(cookie_v)
            if status_t:
                apphash = response_dv["App Configuration"]["api_hash"]
                appid = response_dv["App Configuration"]["app_id"]
                number = redis.get(f"input{user}")
                redis.set(f'appid{user}', int(appid))
                redis.set(f'apphash{user}', apphash)
                aes_mesg_i.delete()
                names = message.reply_text("• سرور با موفقیت لوگین شد !", parse_mode='HTML')
                redis.delete("timecode" + str(user))
                redis.sadd(f'accounts{user}', number)
                try:
                    apps[name].disconnect()
                except:
                    pass
            else:
                neon = app.edit_message_text(message.chat.id, aes_mesg_i.message_id, "• سرور با موفقیت لوگین شد !")
                redis.delete("timecode" + str(user))
                try:
                    apps[name].disconnect()
                except:
                    pass
                redis.sadd(f'accounts{user}', phnum)
                if redis.get(f'setname{user}'):
                    name1 = redis.get(f'nemeauto{user}')
                    apps[name].update_profile(first_name=f"{name1}")
                if redis.get(f'setbio{user}'):
                    name1 = redis.get(f'bioauto{user}')
                    apps[name].update_profile(bio=f"{name1}")
                if redis.get(f'setphoto{user}'):
                    name1 = redis.get(f'photoauto{user}')
                    apps[name].set_profile_photo(photo=f"./downloads/{name1}.jpg")
                if redis.get(f'setpass{user}'):
                    name1 = redis.get(f'passauto{user}')
                    try:
                        apps[name].enable_cloud_password(f"{name1}", hint="Matrix Attack")
                    except:
                        apps[name].change_cloud_password(f"{message.text.split()[1]}", f"{name1}",
                                                         new_hint="Matrix Attack")
        else:
            app.edit_message_text(message.chat.id, aes_mesg_i.message_id, cookie_v, disable_web_page_preview=True)
            if redis.get(f'setname{user}'):
                name1 = redis.get(f'nemeauto{user}')
                apps[name].update_profile(first_name=f"{name1}")
            if redis.get(f'setbio{user}'):
                name1 = redis.get(f'bioauto{user}')
                apps[name].update_profile(bio=f"{name1}")
            if redis.get(f'setphoto{user}'):
                name1 = redis.get(f'photoauto{user}')
                apps[name].set_profile_photo(photo=f"./downloads/{name1}.jpg")
            if redis.get(f'setpass{user}'):
                name1 = redis.get(f'passauto{user}')
                try:
                    apps[name].enable_cloud_password(f"{name1}", hint="Matrix Attack")
                except:
                    apps[name].change_cloud_password(f"{message.text.split()[1]}", f"{name1}", new_hint="Matrix Attack")
    if redis.get('timebio' + str(user)):
        name = message.text
        redis.set(f'bioauto{user}', name)
        redis.set('setbios' + str(user), "Ture")
        message.reply_text("• بیو هوشمند با موفقیت ثبت شد !")
        redis.delete("timebio" + str(user))
    if redis.get('timename' + str(user)):
        name = message.text
        redis.set(f'nemeauto{user}', name)
        redis.set('setnames' + str(user), "Ture")
        message.reply_text("• اسم هوشمند با موفقیت ثبت شد !")
        redis.delete("timename" + str(user))
    if redis.get('timeapp' + str(user)):
        try:
            ids = message.text.split()[0]
        except:
            message.reply_text("• لطفا پیشفرض های درست وارد کنید\nابتدا Api Id سپس با یک فاصله ApiHash را وارد کنید !")
            return
        try:
            hash = message.text.split()[1]
        except:
            message.reply_text("• پیشفرض درست وارد نشده!\nلدفن بین ApiId و ApiHash فاصله بگذارید !")
            return
        try:
            redis.set(f'appid{user}', int(ids))
        except:
            message.reply_text("پیشفرض API ID عدد میباشد !")
            return
        try:
            redis.set(f'apphash{user}', hash)
            app.send_message(message.chat.id, f'• کانفینگ شما با موفقیت ثبت شد !\n• اپ ایدی: {ids}\n• اپ هش: {hash}',
                             reply_to_message_id=message.message_id)
        except:
            print('rid')
        redis.delete("timeapp" + str(user))
    if re.search("^[!/]?attack", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        if message.reply_to_message:
            result2 = message.reply_text("• ارسال شروع شد :")
            attacker[user] = True
            delayer = 0;
            success = 0;
            inuser = [];
            nashod = 0;
            rep = 0;
            unsuccess = 0;
            rounds = 0;
            num = 0
            for i in lists:
                n = f'{i}{user}'
                try:
                    apps[n].get_me().id
                except Exception as e:
                    if "KeyError" or f"'{n}'" in str(e):
                        Id = redis.get(f"appids{i}{user}")
                        Hash = redis.get(f"apphashs{i}{user}")
                        apps[n] = Client(n, int(Id), Hash)
                        apps[n].connect()
                    else:
                        app.send_message(message.chat.id, f"{e}")
            f = re.findall("(@[^_][\d\w]{4,32})", message.reply_to_message.text)
            lists = redis.smembers(f'accounts{user}')
            for ass in lists:
                n = f"{int(ass)}{user}"
                ids = apps[n].get_me().id
                result = apps[n].get_history(ids, limit=1)
                if attacker[user] == True:
                    for mem in f:
                        try:
                            apps[n].forward_messages(mem, ids, result[0].message_id)
                            success += 1
                            delayer += 1
                        except Exception as e:
                            try:
                                if "[420 FLOOD_WAIT_X]" in str(e):
                                    app.edit_message_text(message.chat.id, result2.message_id,
                                                          f"• اکانت فلود خورد به مدت {str(e)[30:33]} ثانیه !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                                    sleep(int(str(e).split()[5]))
                                elif "[403 CHAT_WRITE_FORBIDDEN]" in str(e):
                                    redis.sadd(f'inuser{user}', mem)
                                    unsuccess += 1
                                    nashod += 1
                                    sleep(1.5)
                                    app.edit_message_text(message.chat.id, result2.message_id,
                                                          f"• ایدی  {mem} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                                elif "[400 USERNAME_NOT_OCCUPIED]" in str(e):
                                    redis.sadd(f'inuser{user}', mem)
                                    unsuccess += 1
                                    nashod += 1
                                    app.edit_message_text(message.chat.id, result2.message_id,
                                                          f"• ایدی  {mem} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                                    sleep(1.5)
                                elif "[400 USERNAME_INVALID]" in str(e):
                                    redis.sadd(f'inuser{user}', mem)
                                    unsuccess += 1
                                    nashod += 1
                                    app.edit_message_text(message.chat.id, result2.message_id,
                                                          f"• ایدی  {mem} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                                elif "The method can't be used because your account is limited" in str(e):
                                    rep += 1
                                    nashod += 1
                                    app.edit_message_text(message.chat.id, result2.message_id,
                                                          f"• اکانت ربات ریپورت شده است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                                else:
                                    unsuccess += 1
                                    nashod += 1
                            except:
                                pass
                        if delayer == delay_each_atk:
                            sleep(delay_time)
                            delayer = 0
                else:
                    return
            try:
                app.edit_message_text(message.chat.id, result2.message_id,
                                      f"• وضعیت ارسال به کاربران ! : \n• اکانت {ass} در حال ارسال است !\n• تعداد اکانت هایی کار ان تمام شده: {rounds}\n\n• وضعیت بنر :\n• موفق : {success}\n• ناموفق : {unsuccess}")
            except:
                pass
            rounds += 1
        tedad = redis.smembers(f'inuser{message.from_user.id}')
        a = ''
        if redis.scard(f'inuser{message.from_user.id}') == 0:
            a = 'وجود ندارد'
        else:
            for li in tedad:
                num += 1
                a += f'{num}- {li}\n'
        result2.delete()
        keyboards = [[InlineKeyboardButton("• ارسال موفق", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(success), callback_data="matrix")],
                     [InlineKeyboardButton("• یوزرنیم اشتباه:", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(unsuccess), callback_data="matrix")],
                     [InlineKeyboardButton("• ریپورت بودن:", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(rep), callback_data="matrix")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        message.reply_text(f"• اتک به پایان رسید !\n▸ یوزرنیم های اشتباه:\n{a}", parse_mode='HTML',
                           reply_markup=reply_markups)
        attacker[user] = False
        redis.delete(f'inuser{user}')
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?atk", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        result2 = app.send_message(message.chat.id, "• ارسال شروع شد :")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        attacker[user] = True
        delayer = 0;
        success = 0;
        nashod = 0;
        rep = 0;
        unsuccess = 0;
        rounds = 0;
        num = 0
        f = re.findall("(@[^_][\d\w]{4,32})", message.reply_to_message.text)
        lists = redis.smembers(f'accounts{user}')
        for member in f:
            for ass in lists:
                n = f'{ass}{user}'
                try:
                    ids = apps[n].get_me().id
                    result = apps[n].get_history(ids, limit=1)
                except:
                    pass
                if attacker[user] == True:
                    try:
                        apps[n].forward_messages(member, ids, result[0].message_id)
                        success += 1
                        delayer += 1
                    except Exception as e:
                        try:
                            if "[420 FLOOD_WAIT_X]" in str(e):
                                app.edit_message_text(message.chat.id, result2.message_id,
                                                      f"• اکانت {ass} فلود خورد به مدت {str(e)[30:33]} ثانیه !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                                sleep(int(str(e).split()[5]))
                            elif "[403 CHAT_WRITE_FORBIDDEN]" in str(e):
                                redis.sadd(f'inuser{user}', member)
                                unsuccess += 1
                                nashod += 1
                                app.edit_message_text(message.chat.id, result2.message_id,
                                                      f"• ایدی  {member} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                            elif "[400 USERNAME_NOT_OCCUPIED]" in str(e):
                                redis.sadd(f'inuser{user}', member)
                                unsuccess += 1
                                nashod += 1
                                app.edit_message_text(message.chat.id, result2.message_id,
                                                      f"• ایدی  {member} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                            elif "[400 USERNAME_INVALID]" in str(e):
                                redis.sadd(f'inuser{user}', member)
                                unsuccess += 1
                                nashod += 1
                                app.edit_message_text(message.chat.id, result2.message_id,
                                                      f"• ایدی  {member} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                            elif "The method can't be used because your account is limited" in str(e):
                                rep += 1
                                nashod += 1
                                app.edit_message_text(message.chat.id, result2.message_id,
                                                      f"• اکانت ربات ریپورت شده است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                            else:
                                nashod += 1
                                rep += 1
                        except:
                            pass
                    if delayer == delay_each_atk:
                        sleep(delay_time)
                        delayer = 0
                else:
                    return
            try:
                app.edit_message_text(message.chat.id, result2.message_id,
                                      f"• وضعیت ارسال به کاربران: \n\n• وضعیت بنر :\n• موفق : {success}\n• ناموفق : {unsuccess}")
            except:
                pass
        tedad = redis.smembers(f'inuser{user}')
        a = ''
        if redis.scard(f'inuser{user}') == 0:
            a = 'وجود ندارد'
        else:
            for li in tedad:
                num += 1
                a += f'{num}- {li}\n'
        result2.delete()
        keyboards = [[InlineKeyboardButton("• ارسال موفق", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(success), callback_data="matrix")],
                     [InlineKeyboardButton("• یوزرنیم اشتباه:", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(unsuccess), callback_data="matrix")],
                     [InlineKeyboardButton("• ریپورت بودن:", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(rep), callback_data="matrix")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        message.reply_text(f"• ارسال به پایان رسید !\n▸ یوزرنیم های اشتباه:\n{a}", parse_mode='HTML',
                           reply_markup=reply_markups)
        attacker[user] = False
        redis.delete(f'inuser{user}')
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?send", message.text, re.I):
        user = message.from_user.id
        try:
            phone = int(message.text.split()[1])
        except:
            message.reply_text(
                "لطفا پیشفرض درست را وارد کنید !\nsend phone listname\n» جای عبارت phone شماره اکانت !\n» جای عبارت listname اسم لیستی که ثبت کردید را وارد کنید\n»برای ثبت لیست رویه لیست ریپلی کنید سپس دستور setlist name را وارد کنید !")
            return
        try:
            slist = message.text.split()[2]
        except:
            message.reply_text("لطفا اسم لیست ثبت شده را بعد شماره اکانت با یک فاصله وارد کنید !")
            return
        name = f"{int(phone)}{user}"
        try:
            apps[name].get_me().id
        except Exception as e:
            if "KeyError" or f"'{name}'" in str(e):
                Id = redis.get(f"appids{phone}{user}")
                Hash = redis.get(f"apphashs{phone}{user}")
                apps[name] = Client(name, int(Id), Hash)
                apps[name].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        attacker[user] = True
        delayer = 0
        success = 0
        rep = 0
        nashod = 0
        unsuccess = 0
        rounds = 0
        users = redis.smembers(f'list{user}{slist}')
        ids = apps[name].get_me().id
        result = apps[name].get_history(ids, limit=1)
        result2 = message.reply_text("• ارسال شروع شد :")
        for member in users:
            if attacker[user] == True:
                try:
                    apps[name].forward_messages(member, ids, result[0].message_id)
                    success += 1
                    delayer += 1
                except Exception as e:
                    try:
                        if "[420 FLOOD_WAIT_X]" in str(e):
                            app.edit_message_text(message.chat.id, result2.message_id,
                                                  f"• اکانت فلود خورد به مدت {str(e)[30:33]} ثانیه !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                            sleep(int(str(e).split()[5]))
                        elif "[403 CHAT_WRITE_FORBIDDEN]" in str(e):
                            unsuccess += 1
                            nashod += 1
                            app.edit_message_text(message.chat.id, result2.message_id,
                                                  f"• ایدی  {member} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                        elif "[400 USERNAME_NOT_OCCUPIED]" in str(e):
                            unsuccess += 1
                            nashod += 1
                            app.edit_message_text(message.chat.id, result2.message_id,
                                                  f"• ایدی  {member} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                        elif "[400 USERNAME_INVALID]" in str(e):
                            unsuccess += 1
                            nashod += 1
                            app.edit_message_text(message.chat.id, result2.message_id,
                                                  f"• ایدی  {member} اشتباه است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                        elif "The method can't be used because your account is limited" in str(e):
                            rep += 1
                            nashod += 1
                            app.edit_message_text(message.chat.id, result2.message_id,
                                                  f"• اکانت ربات ریپورت شده است !\n\n• وضعیت بنر :\n• موفق {success}\n• ناموفق {unsuccess}")
                        else:
                            rep += 1
                            nashod += 1
                    except:
                        pass
                if delayer == delay_each_atk:
                    sleep(delay_time)
                    delayer = 0
        result2.delete()
        keyboards = [[InlineKeyboardButton("• موفق", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(success), callback_data="matrix")],
                     [InlineKeyboardButton("• یوزرنیم", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(unsuccess), callback_data="matrix")],
                     [InlineKeyboardButton("• ریپورتی", callback_data="matrix"),
                      InlineKeyboardButton("{}".format(rep), callback_data="matrix")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        message.reply_text("• ارسال به پایان رسید!\n▿ ریز اطلاعات:", parse_mode='HTML', reply_markup=reply_markups)
        attacker[user] = False
        try:
            apps[name].disconnect()
        except:
            pass
    if re.search("^[!/]?getcode", message.text, re.I):
        user = message.from_user.id
        ph = int(message.text.split()[1])
        name = f"{int(ph)}{user}"
        try:
            apps[name].get_me().id
        except Exception as e:
            if "KeyError" or f"'{name}'" in str(e):
                Id = redis.get(f"appids{ph}{user}")
                Hash = redis.get(f"apphashs{ph}{user}")
                apps[name] = Client(name, int(Id), Hash)
                apps[name].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        ids = apps[name].get_me().id
        result = apps[name].get_history(777000, limit=1)
        incoming_message_text = result[0].text
        code = re.search("Login code: (\d+)", incoming_message_text)
        if code:
            app.send_message(message.chat.id, f"code: <code>{code[1]}</code>", parse_mode='HTML')
        else:
            app.send_message(message.chat.id, f"Not Code!", parse_mode='HTML')
        try:
            apps[name].disconnect()
        except:
            pass
    if re.search("^[!/]?setbanner", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        message.reply_text("• لطفا منتظر بمونید !")
        for i in lists:
            print(i)
            n = f'{i}{user}'
            print(n)
            try:
                apps[f'{i}{user}'].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(f'{i}{user}', int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        if message.reply_to_message:
            lists = redis.smembers(f'accounts{user}')
            if message.reply_to_message:
                if message.reply_to_message.text:
                    lists = redis.smembers(f'accounts{user}')
                    for ass in lists:
                        try:
                            n = f'{ass}{user}'
                            ids = apps[n].get_me().id
                            Banner = message.reply_to_message.text
                            apps[n].send_message(ids, f'{Banner}')
                        except:
                            pass
                    message.reply_text("• نوع بنر : متن\nبنر با موفقیت ثبت شد !")
                elif message.reply_to_message.photo:
                    lists = redis.smembers(f'accounts{user}')
                    for ass in lists:
                        try:
                            n = f'{ass}{user}'
                            ids = apps[n].get_me().id
                            Banner = message.reply_to_message.caption
                            apps[n].send_photo(ids, message.reply_to_message.photo.file_id, caption=Banner)
                        except Exception as e:
                            print(e)
                            pass
                    app.send_photo(message.chat.id, message.reply_to_message.photo.file_id, caption=Banner)
                    message.reply_text("• نوع بنر: عکس\nبنر با موفقیت ثبت شد !")
                elif message.reply_to_message.animation:
                    lists = redis.smembers(f'accounts{user}')
                    for ass in lists:
                        try:
                            n = f'{ass}{user}'
                            ids = apps[n].get_me().id
                            gif = message.reply_to_message.download(file_name='gif.mp4')
                            Banner = message.reply_to_message.caption
                            apps[n].send_animation(ids, gif, caption=Banner)
                        except:
                            pass
                    message.reply_text("• نوع بنر: گیف\nبنر با موفقیت ثبت شد !")
                elif message.reply_to_message.sticker:
                    lists = redis.smembers(f'accounts{user}')
                    for ass in lists:
                        try:
                            n = f'{ass}{user}'
                            ids = apps[n].get_me().id
                            stick = message.reply_to_message.download(file_name='sticker.webp')
                            apps[n].send_sticker(ids, stick)
                        except:
                            pass
                    message.reply_text("• نوع بنر: استیکر\nبنر با موفقیت ثبت شد !")
                elif message.reply_to_message.voice:
                    lists = redis.smembers(f'accounts{user}')
                    for ass in lists:
                        try:
                            n = f'{ass}{user}'
                            ids = apps[n].get_me().id
                            gif = message.reply_to_message.download(file_name='voice.ogg')
                            Banner = message.reply_to_message.caption
                            apps[n].send_voice(ids, gif, caption=Banner)
                        except:
                            pass
                    message.reply_text("• نوع بنر: ویس\nبنر با موفقیت ثبت شد !")

    if re.search("^[!/]?panel", message.text, re.I):
        keyboards = [[InlineKeyboardButton("▴ مشاهده آمار فعلی", callback_data=f"matrix stats {user}")],
                     [InlineKeyboardButton("▴ تکمیل کانفینگ", callback_data=f"matrix config {user}")],
                     [InlineKeyboardButton("▴ ارسال کد هوشمند", callback_data=f"matrix codesmart {user}")],
                     [InlineKeyboardButton("▴ نام هوشمند", callback_data=f"matrix namesmart {user}"),
                      InlineKeyboardButton("▴ بیو هوشمند", callback_data=f"matrix biosmart {user}")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        message.reply_text(f"• کاربر {men} به پنل ربات خوشومدید !", parse_mode='HTML', reply_markup=reply_markups)
    if re.search("^[!/]?ph", message.text, re.I):
        if redis.get(f"appid{user}") and redis.get(f"apphash{user}"):
            try:
                phone = message.text.split()[1]
                ph = int(phone)
                redis.set(f'phone{user}', int(phone))
                print(ph)
            except:
                print("ok")
                return
            api = redis.get(f"appid{user}")
            hash = redis.get(f"apphash{user}")
            name = f"{int(phone)}{user}"
            redis.set(f'appids{ph}{user}', api)
            redis.set(f'apphashs{ph}{user}', hash)
            try:
                apps[name] = Client(name, int(api), hash)
                apps[name].connect()
            except:
                os.remove(f"{name}.session")
                apps[name] = Client(name, int(api), hash)
                apps[name].connect()
            try:
                phhash = apps[name].send_code(phone)
                redis.set(f'phhash{ph}{user}', str(phhash.phone_code_hash))
                print(phhash)
            except Exception as e:
                try:
                    if "[420 FLOOD_WAIT_X]" in str(e):
                        app.send_message(message.chat.id,
                                         f'◂ شماره {t} به مدت {str(e)[30:33]} دقیقه محدود از دریافت کد میباشد !')
                    elif "[400 PHONE_NUMBER_BANNED]" in str(e):
                        app.send_message(message.chat.id, f'◂ شماره {t} مسدود از تلگرام میباشد !')
                    elif "[400 PHONE_NUMBER_FLOOD]" in str(e):
                        app.send_message(message.chat.id, f'◂ شماره {t} از سمت تلگرام فلود خورده است !')
                    elif "[406 PHONE_NUMBER_INVALID]" in str(e):
                        app.send_message(message.chat.id, f'◂ شماره {t} اشتباه میباشد !')
                    else:
                        app.send_message(message.chat.id, e)
                except:
                    pass
            redis.set(f'phhash{phone}{user}', str(phhash.phone_code_hash))
            message.reply_text(
                "• کد با موفقیت ارسال شد !\n◂ برای وارد کردن کد 60 ثانیه مهلت دارید:\n↑ درصورت وجود گذر دوم با یک فاصله کنار کد وارد کنید !")
            redis.setex("timecode" + str(user), 60, "Ture")
        else:
            message.reply_text(
                f"• کاربر {men} لطفا کانفیگ خود را تکمیل کنید سپس شروع به وارد کردن اکانت کنید !\n◂ برای تکمیل کانفیگ دستور panel را وارد کنید !")
    if re.search("^[!/]?acc", message.text, re.I):
        keyboards = [[InlineKeyboardButton("▴ بازکردن به صورت اینلاین !", callback_data=f"matrix accounts {user}")]]
        reply_markups = InlineKeyboardMarkup(keyboards)
        lists = redis.smembers(f'accounts{user}')
        list1 = redis.scard(f'accounts{user}')
        accounts = '-'
        acc_num = []
        num = 0
        for x in lists:
            num += 1
            acc_num.append(f'{num}- <code>{x}</code>')
            accounts = "\n".join(acc_num)
            if len(acc_num) == 80:
                message.reply_text(f'• کاربر: {men}\n• اکانت های شما:\n {accounts}', parse_mode="html",
                                   reply_markup=reply_markups)
                acc_num.clear()
        if len(acc_num) > 0:
            message.reply_text(f'• کاربر: {men}\n• اکانت های شما:\n {accounts}', parse_mode="html",
                               reply_markup=reply_markups)
        elif len(acc_num) == 0:
            message.reply_text(f'• کاربر: {men}\n• شما اکانتی در ربات ندارید !', parse_mode="html")
    if re.search("^[!/]?sort", message.text, re.I):
        text = message.reply_to_message.text
        try:
            sort = message.text.split()[1]
        except:
            sort = 45
        f = re.findall("(@[^_][\d\w]{4,32})", text)
        f = chunk(f, int(sort))
        for username in f:
            app.send_message(message.chat.id, "\n".join(username))
    if re.search("^[!/]?stop", message.text, re.I):
        user = message.from_user.id
        if attacker[user] == True:
            message.reply_text("اتک کنسل شد !")
            attacker[user] = False
        else:
            message.reply_text("ربات درحال اتک نبود !")

    if re.search("^[!/]?joinall", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        suc = 0
        t = redis.scard(f'accounts{user}')
        command = message.text.split(" ", maxsplit=2)
        link = command[1].replace('+', "joinchat/")
        lists = redis.smembers(f'accounts{user}')
        for ass in lists:
            n = f'{ass}{user}'
            Id = redis.get(f"appids{ass}{user}")
            Hash = redis.get(f"apphashs{ass}{user}")
            try:
                g = apps[n].join_chat(f"{link}")
                suc += 1
                apps[n].send_message(g.id, command[2])
                apps[n].send_message(message.chat.id, '• انجام شد !')
            except Exception as e:
                print(e)
                pass
        message.reply_text(
            f"▴ پروسه عضو شدن در گروه با موفقیت به اتمام رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد اکانت های عضو شده: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?setlist", message.text, re.I):
        okey = 0
        user = message.from_user.id
        if message.reply_to_message:
            redis.delete(f'list{user}{message.text.split()[1]}')
            f = re.findall("(@[^_][\d\w]{4,32})", message.reply_to_message.text)
            for member in f:
                try:
                    redis.sadd(f'list{user}{message.text.split()[1]}', member)
                    redis.sadd(f'lists{user}', message.text.split()[1])
                    okey += 1
                    print(f'ok aded list {member}')
                except Exception as e:
                    print(e)
                    pass
            message.reply_text(f'▴ لیست ثبت شد✅\n▾ تعداد یوزرنیم ها: {okey}')
    if re.search("^[!/]?showlist", message.text, re.I):
        user = message.from_user.id
        users = redis.smembers(f'list{user}{message.text.split()[1]}')
        a = ""
        if redis.scard(f'list{user}{message.text.split()[1]}') == 0:
            a = '▵ لیست خالی میباشد !'
        else:
            for member in users:
                a += f'{member}\n'
        message.reply_text(f'▵ یوزرنیم های ثبت شده:\n{a}')
    if re.search("^[!/]?lists", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'lists{user}')
        a = ''
        if redis.scard(f'lists{user}') == 0:
            a = 'Nil'
        else:
            for li in lists:
                a += f'{li}\n'
        message.reply_text(f'▵ لیست های ثبت شده :\n{a}')
    if re.search("^[!/]?remlist", message.text, re.I):
        user = message.from_user.id
        redis.delete(f'list{user}{message.text.split()[1]}')
        redis.srem(f'lists{user}', message.text.split()[1])
        message.reply_text(f'▾ لیست {message.text.split()[1]} با موفقیت حذف شد !')
    if re.search("^[!/]?joingame", message.text, re.I) and message.reply_to_message:
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        bot = "@werewolfbot"
        suc = 0
        try:
            l = message.text.split()[1]
        except:
            message.reply_text("▴ لطفا لینک گروه را بعد دستور بنویسید !")
            return
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        link = l.replace('+', "joinchat/")
        text = message.reply_to_message.reply_markup.inline_keyboard[0][0].url
        text1 = text.replace('https://t.me/werewolfbot?', '')
        text2 = text1.replace('start=', '/start ')
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        for ass in lists:
            n = f'{ass}{user}'
            from_user = app.get_users(bot)
            try:
                g = apps[n].join_chat(link)
                apps[n].send_message(from_user.id, text2)
                sleep(1)
                apps[n].send_message(from_user.id, text2)
                apps[n].send_message(from_user.id, text2)
                sleep(1)
                apps[n].send_message(from_user.id, text2)
                apps[n].send_message(from_user.id, text2)
                suc += 1
            except Exception as e:
                try:
                    if "[400 USER_ALREADY_PARTICIPANT]" in str(e):
                        g = apps[n].get_chat(link)
                        apps[n].send_message(from_user.id, text2)
                        sleep(1)
                        apps[n].send_message(from_user.id, text2)
                        apps[n].send_message(from_user.id, text2)
                        sleep(1)
                        apps[n].send_message(from_user.id, text2)
                        apps[n].send_message(from_user.id, text2)
                        suc += 1
                except:
                    print("be kir matrix ke nashod")
            except:
                pass
        message.reply_text(f"▴ پروسه تخریبی به پایان رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد جوین موفق: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?spam", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        try:
            l = message.text.split()[1]
        except:
            message.reply_text("▴ لطفا لینک گروه را بعد دستور بنویسید !")
            return
        try:
            l = message.text.split()[2]
        except:
            message.reply_text("▴ لطفا تعداد دفعات اسپم را بعد لینک بنویسید !")
            return
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        command = message.text.split(" ", maxsplit=3)
        link = command[1].replace('+', "joinchat/")
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        message.reply_text(f"Wait :D")
        for ass in lists:
            n = f'{ass}{user}'
            try:
                g = apps[n].join_chat(link)
                for i in range(int(command[2])):
                    apps[n].send_message(g.id, command[3])
            except Exception as e:
                print(e)
                try:
                    if "[400 USER_ALREADY_PARTICIPANT]" in str(e):
                        g = apps[n].get_chat(link)
                        for i in range(int(command[2])):
                            apps[n].send_message(g.id, command[3])
                except:
                    print('bash')
            except:
                pass
        message.reply_text(f"Ez :D")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?okname", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        suc = 0
        nums = {1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹", 10: "¹⁰",
                11: "¹¹", 12: "¹²", 13: "¹³", 14: "¹⁴", 15: "¹⁵", 16: "¹⁶", 17: "¹⁷", 18: "¹⁸", 19: "¹⁹", 20: "²⁰",
                21: "²¹", 22: "²²", 23: "²³", 24: "²⁴", 25: "²⁵", 26: "²⁶", 27: "²⁷", 28: "²⁸", 29: "²⁹", 30: "³⁰"
            , 31: "³¹", 40: "⁴⁰", 41: "⁴¹", 42: "⁴²", 43: "⁴³", 44: "⁴⁴", 45: "⁴⁵", 46: "⁴⁶", 47: "⁴⁷", 48: "⁴⁸",
                49: "⁴⁹", 50: "⁰", 60: "⁶⁰", 32: "³²", 33: "³³", 34: "³⁴", 35: "³⁵", 36: "³⁶", 37: "³⁷", 38: "³⁸",
                39: "³⁹",
                51: "⁵¹", 52: "⁵²", 53: "⁵³", 54: "⁵⁴", 55: "⁵⁵", 56: "⁵⁶", 57: "⁵⁷", 58: "⁵⁸", 59: "⁵⁹", 0: "⁰",
                60: "⁶⁰", 61: "⁶¹", 62: "⁶²", 63: "⁶³", 64: "⁶⁴", 65: "⁶⁵", 66: "⁶⁶", 67: "⁶⁷", 68: "⁶⁸", 69: "⁶⁹",
                70: "⁷⁰", 71: "⁷¹", 72: "⁷²", 73: "⁷³", 74: "⁷⁴", 75: "⁷⁵", 76: "⁷⁶", 77: "⁷⁷", 78: "⁷⁸", 79: "⁷⁹",
                80: "⁸⁰", 81: "⁸¹", 82: "⁸²", 83: "⁸³", 84: "⁸⁴", 85: "⁸⁵", 86: "⁸⁶", 87: "⁸⁷", 88: "⁸⁸", 89: "⁸⁹",
                90: "⁵⁹⁰", 91: "⁹¹", 92: "⁹²", 93: "⁹³", 94: "⁹⁴", 95: "⁹⁵", 96: "⁹⁶", 97: "⁹⁷", 98: "⁹⁸", 99: "⁹⁹",
                100: "¹⁰⁰"}
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        for ass in lists:
            n = f'{ass}{user}'
            suc += 1
            add = nums[suc]
            try:
                apps[n].update_profile(last_name=f"{add}")
            except:
                message.reply_text(f"به کیر ماتریکس که شماره {ass} نتونست")
        message.reply_text(f"▴ پروسه به پایان رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد موفق: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?leaveall", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        suc = 0
        try:
            l = message.text.split()[1]
        except:
            message.reply_text("▴ لطفا لینک گروه را بعد دستور بنویسید !")
            return
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        link = l.replace('+', "joinchat/")
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        for ass in lists:
            n = f'{ass}{user}'
            try:
                g = apps[n].get_chat(link)
            except:
                pass
            try:
                apps[n].leave_chat(g.id)
            except:
                pass
            suc += 1
        message.reply_text(
            f"▴ پروسه خروج اکانت ها از گروه با موفقیت به اتمام رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد اکانت های خارج شده: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?dpro", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        suc = 0
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        for ass in lists:
            n = f'{ass}{user}'
            Id = redis.get(f"appids{ass}{user}")
            Hash = redis.get(f"apphashs{ass}{user}")
            ids = apps[n].get_me().id
            photos = apps[n].get_profile_photos(ids)
            apps[n].delete_profile_photos(photos[0].file_id)
            suc += 1
        message.reply_text(
            f"▴ پروسه حذف پروفایل با موفقیت به اتمام رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد موفق: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?setbio", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        suc = 0
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        command = message.text.split(" ", maxsplit=1)
        name = command[1]
        for ass in lists:
            n = f'{ass}{user}'
            Id = redis.get(f"appids{ass}{user}")
            Hash = redis.get(f"apphashs{ass}{user}")
            try:
                apps[n].update_profile(bio=f"{name}")
                suc += 1
                apps[n].send_message(message.chat.id, '• انجام شد !')
            except:
                pass
        message.reply_text(
            f"▴ پروسه تنظیم بایوگرافی با موفقیت به اتمام رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد اکانت های با موفقیت ست شده: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?setname", message.text, re.I):
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        suc = 0
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        command = message.text.split(" ", maxsplit=1)
        name = command[1]
        for ass in lists:
            n = f'{ass}{user}'
            Id = redis.get(f"appids{ass}{user}")
            Hash = redis.get(f"apphashs{ass}{user}")
            try:
                apps[n].update_profile(first_name=f"{name}")
                suc += 1
                apps[n].send_message(message.chat.id, '• انجام شد !')
            except:
                pass
        message.reply_text(
            f"▴ پروسه تنظیم نام با موفقیت به اتمام رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد اکانت های با موفقیت ست شده: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?setpro", message.text, re.I) and message.reply_to_message.photo:
        user = message.from_user.id
        lists = redis.smembers(f'accounts{user}')
        app.send_message(message.chat.id, "• لطفا صبر کنید !")
        for i in lists:
            n = f'{i}{user}'
            try:
                apps[n].get_me().id
            except Exception as e:
                if "KeyError" or f"'{n}'" in str(e):
                    Id = redis.get(f"appids{i}{user}")
                    Hash = redis.get(f"apphashs{i}{user}")
                    apps[n] = Client(n, int(Id), Hash)
                    apps[n].connect()
                else:
                    app.send_message(message.chat.id, f"{e}")
        suc = 0
        t = redis.scard(f'accounts{user}')
        lists = redis.smembers(f'accounts{user}')
        photos = message.reply_to_message.download(file_name='photo.jpg')
        message.reply_text("▴ لطفا منتظر بمونید !")
        for ass in lists:
            n = f'{ass}{user}'
            Id = redis.get(f"appids{ass}{user}")
            Hash = redis.get(f"apphashs{ass}{user}")
            try:
                apps[n].set_profile_photo(photo=photos)
                suc += 1
                apps[n].send_message(message.chat.id, '• انجام شد !')
            except:
                pass
            message.reply_text(
                f"▴ پروسه تنظیم پروفایل با موفقیت به اتمام رسید✅\n◂ تعداد همه اکانت ها: {t}\n◂ تعداد اکانت های با موفقیت ست شده: {suc}")
        for i in lists:
            n = f'{i}{user}'
            Id = redis.get(f"appids{i}{user}")
            Hash = redis.get(f"apphashs{i}{user}")
            try:
                apps[n].disconnect()
            except:
                pass
        print("Down")
    if re.search("^[!/]?getlist", message.text, re.I):
        user = message.from_user.id
        try:
            m = message.text.split()[3]
        except:
            m = 0
        try:
            ph = int(message.text.split()[1])
        except:
            message.reply_text("▴ لطفا شماره اکانت را بعد دستور بزارید!")
        try:
            l = message.text.split()[2]
        except:
            message.reply_text("▴ لطفا لینک گروه را بعد شماره بنویسید !")
        link = l.replace('+', "joinchat/")
        name = f"{int(ph)}{user}"
        try:
            apps[name].get_me().id
        except Exception as e:
            if "KeyError" or f"'{name}'" in str(e):
                Id = redis.get(f"appids{ph}{user}")
                Hash = redis.get(f"apphashs{ph}{user}")
                apps[name] = Client(name, int(Id), Hash)
                apps[name].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        Id = redis.get(f"appids{ph}{user}")
        Hash = redis.get(f"apphashs{ph}{user}")
        try:
            g = apps[name].join_chat(link)
        except:
            g = apps[name].get_chat(link)
        result = app.send_message(message.chat.id, 'وایسا')
        text = "لیست اعضای گروه :\nیوزرنیم | تعداد بازی\n\n"
        gcm = apps[name].get_chat_members(g.id)
        Lists_num = 1
        List = f"{g.title} - {Lists_num}\n"
        user_num = 0
        for usr in gcm:
            if usr['user']['username']:
                stats = get_stats(usr['user']['id'])
                if stats:
                    user_num += 1
                    text += "{}- @{} | {:<5}\n".format(user_num, usr['user']['username'], stats['gamesPlayed'])
                else:
                    text += "{}- @{} | 0\n".format(user_num, usr['user']['username'])
                    if user_num == 45:
                        app.send_message(message.chat.id, text)
                        Lists_num += 1
        app.edit_message_text(message.chat.id, result.message_id, "{}".format(text))
        try:
            apps[name].disconnect()
        except:
            pass
    if re.search("^[!/]?onlinelist", message.text, re.I):
        user = message.from_user.id
        try:
            m = message.text.split()[3]
        except:
            m = 0
        try:
            ph = int(message.text.split()[1])
        except:
            message.reply_text("▴ لطفا شماره اکانت را بعد دستور بزارید!")
        try:
            l = message.text.split()[2]
        except:
            message.reply_text("▴ لطفا لینک گروه را بعد شماره بنویسید !")
        link = l.replace('+', "joinchat/")
        name = f"{int(ph)}{user}"
        try:
            apps[name].get_me().id
        except Exception as e:
            if "KeyError" or f"'{name}'" in str(e):
                Id = redis.get(f"appids{ph}{user}")
                Hash = redis.get(f"apphashs{ph}{user}")
                apps[name] = Client(name, int(Id), Hash)
                apps[name].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        Id = redis.get(f"appids{ph}{user}")
        Hash = redis.get(f"apphashs{ph}{user}")
        try:
            g = apps[name].join_chat(link)
        except:
            g = apps[name].get_chat(link)
        result = app.send_message(message.chat.id, 'وایسا')
        text = "لیست اعضای گروه :\nیوزرنیم\n\n"
        gcm = apps[name].iter_chat_members(g.id)
        for usr in gcm:
            if usr['user']['username']:
                user = usr.user
                if user.status == 'online':
                    text += "@{}\n".format(usr['user']['username'])
        app.edit_message_text(message.chat.id, result.message_id, "{}".format(text))
        try:
            apps[name].disconnect()
        except:
            pass

    if re.search("^[!/]?allmembers", message.text, re.I):
        user = message.from_user.id
        tagtext = []
        try:
            m = message.text.split()[3]
        except:
            m = 0
        try:
            ph = int(message.text.split()[1])
        except:
            message.reply_text("▴ لطفا شماره اکانت را بعد دستور بزارید!")
            return
        try:
            l = message.text.split()[2]
        except:
            message.reply_text("▴ لطفا لینک گروه را بعد شماره بنویسید !")
            return
        link = l.replace('+', "joinchat/")
        name = f"{int(ph)}{user}"
        try:
            apps[name].get_me().id
        except Exception as e:
            if "KeyError" or f"'{name}'" in str(e):
                Id = redis.get(f"appids{ph}{user}")
                Hash = redis.get(f"apphashs{ph}{user}")
                apps[name] = Client(name, int(Id), Hash)
                apps[name].connect()
            else:
                app.send_message(message.chat.id, f"{e}")
        try:
            g = apps[name].join_chat(link)
        except:
            g = apps[name].get_chat(link)
        result = app.send_message(message.chat.id, 'وایسا')
        for usr in apps[name].iter_chat_members(g.id, filter="administrators"):
            if usr['user']['username']:
                tagtext.append("@{}".format(usr.user.username))
        txt = "\n".join(tagtext)
        app.send_message(message.chat.id, f"administrators\n{txt}")
        tagtext.clear()
        for member in apps[name].iter_chat_members(g.id):
            if member['user']['username']:
                tagtext.append("@{}".format(member.user.username))
        txt = "\n".join(tagtext)
        writefile("AllMembers.txt", txt)
        app.send_document(message.chat.id, "AllMembers.txt", caption=f"All Members {g.title}")
        tagtext.clear()
        try:
            apps[name].disconnect()
        except:
            pass

    if re.search("^[+]?(\d+)", message.text, re.I):
        if redis.get("codesmart" + str(user)) and re.search("([^_][\d\w]{6,32})", message.text):
            if redis.get(f"appid{user}") and redis.get(f"apphash{user}"):
                try:
                    phone = message.text
                    ph = int(phone)
                    redis.set(f'phone{user}', int(phone))
                    print(ph)
                except:
                    print("ok")
                    return
                api = redis.get(f"appid{user}")
                hash = redis.get(f"apphash{user}")
                name = f"{int(phone)}{user}"
                redis.set(f'appids{ph}{user}', api)
                redis.set(f'apphashs{ph}{user}', hash)
                try:
                    apps[name] = Client(name, int(api), hash)
                    apps[name].connect()
                except:
                    os.remove(f"{name}.session")
                    apps[name] = Client(name, int(api), hash)
                    apps[name].connect()
                try:
                    phhash = apps[name].send_code(phone)
                    redis.set(f'phhash{ph}{user}', str(phhash.phone_code_hash))
                    print(phhash)
                except Exception as e:
                    try:
                        if "[420 FLOOD_WAIT_X]" in str(e):
                            app.send_message(message.chat.id,
                                             f'◂ شماره {t} به مدت {str(e)[30:33]} دقیقه محدود از دریافت کد میباشد !')
                        elif "[400 PHONE_NUMBER_BANNED]" in str(e):
                            app.send_message(message.chat.id, f'◂ شماره {t} مسدود از تلگرام میباشد !')
                        elif "[400 PHONE_NUMBER_FLOOD]" in str(e):
                            app.send_message(message.chat.id, f'◂ شماره {t} از سمت تلگرام فلود خورده است !')
                        elif "[406 PHONE_NUMBER_INVALID]" in str(e):
                            app.send_message(message.chat.id, f'◂ شماره {t} اشتباه میباشد !')
                        else:
                            app.send_message(message.chat.id, e)
                    except:
                        pass
                message.reply_text(
                    "• کد با موفقیت ارسال شد !\n◂ برای وارد کردن کد 60 ثانیه مهلت دارید:\n↑ درصورت وجود گذر دوم با یک فاصله کنار کد وارد کنید !")
                redis.setex("timecode" + str(user), 60, "Ture")
            else:
                message.reply_text(
                    f"• کاربر {men} لطفا کانفیگ خود را تکمیل کنید سپس شروع به وارد کردن اکانت کنید !\n◂ برای تکمیل کانفیگ دستور panel را وارد کنید !")


@app.on_callback_query()
def button(client, callback_query):
    cb_data = callback_query.data
    cb = callback_query
    user = cb.from_user.id
    chat = cb.message.chat.id
    data = cb.data.replace('matrix ', '', 1).split(' ')
    if data[0] == 'accounts':
        if int(user) == int(data[1]):
            users = data[1]
            lists = redis.smembers(f'accounts{users}')
            list1 = redis.scard(f'accounts{users}')
            accounts = '-'
            acc_num = []
            num = 0
            k = []
            for x in lists:
                num += 1
                l = [[InlineKeyboardButton(f"{x}", callback_data=f"matrix d {users} {x}")]]
                k.extend(l)
            try:
                app.edit_message_text(chat, cb.message.message_id,
                                      f"• کاربر: {cb.from_user.mention}\n• لیست اکانت های شما:",
                                      reply_markup=InlineKeyboardMarkup(k))
                k.clear()
            except:
                for i in list_splitter(k, 50):
                    app.send_message(chat, f"• کاربر: {cb.from_user.mention}\n• لیست اکانت های شما:",
                                     reply_markup=InlineKeyboardMarkup(i))
    if data[0] == 'd':
        if int(user) == int(data[1]):
            users = data[1]
            ph = data[2]
            name = f"{int(ph)}{users}"
            num = 0
            try:
                apps[name].get_me().id
            except Exception as e:
                if "KeyError" or f"'{name}'" in str(e):
                    Id = redis.get(f"appids{ph}{users}")
                    Hash = redis.get(f"apphashs{ph}{users}")
                    apps[name] = Client(name, int(Id), Hash)
                    apps[name].connect()
                else:
                    app.send_message(chat, f"{e}")
            ids = apps[name].get_me()
            result = apps[name].send(GetAuthorizations()).authorizations
            for auth in result:
                num += 1
            keyboards = [[InlineKeyboardButton("• لاگ اوت", callback_data=f"matrix log {users} {ph}"),
                          InlineKeyboardButton("• تغییر اسم اکانت", callback_data=f"matrix name {users} {ph}")],
                         [InlineKeyboardButton("• تغییر بیو اکانت", callback_data=f"matrix bio {users} {ph}"),
                          InlineKeyboardButton("• تغییر یوزنیم اکانت", callback_data=f"matrix usernmae {users} {ph}")],
                         [InlineKeyboardButton("• برگشت", callback_data=f"matrix accounts {users}")]]
            reply_markups = InlineKeyboardMarkup(keyboards)
            app.edit_message_text(chat, cb.message.message_id,
                                  f"• اسم اکانت: {ids.first_name}\n• ایدی عددی: {ids.id}\n• یوزرنیم: @{ids.username}\n•شماره اکانت: <code>{ids.phone_number}</code>\n• تعداد سشن ها: {num}",
                                  reply_markup=reply_markups)
            try:
                apps[name].disconnect()
            except:
                pass
    if data[0] == 'log':
        if int(user) == int(data[1]):
            users = data[1]
            ph = data[2]
            name = f"{int(ph)}{users}"
            num = 0
            try:
                apps[name].get_me().id
            except Exception as e:
                if "KeyError" or f"'{name}'" in str(e):
                    Id = redis.get(f"appids{ph}{users}")
                    Hash = redis.get(f"apphashs{ph}{users}")
                    apps[name] = Client(name, int(Id), Hash)
                    apps[name].connect()
                else:
                    app.send_message(chat, f"{e}")
            ids = apps[name].get_me().id
            result = apps[name].send(GetAuthorizations()).authorizations
            k = []
            txt = ""
            for auth in result:
                num += 1
                txt += f"{num}- device_model: <code>{auth.device_model}</code>\nhash: <code>{auth.hash}</code>\napp_name: <code>{auth.app_name}</code> \napp_version: <code>{auth.app_version}</code>\n\n"
                if not auth.hash == 0:
                    l = [[InlineKeyboardButton(f"device_model:{auth.device_model}",
                                               callback_data=f"matrix login {users} {ph} {auth.hash}")]]
                    k.extend(l)
            k.extend([[InlineKeyboardButton(f"کیل کردن همه سشن ها", callback_data=f"matrix kills {users} {ph}")]])
            k.extend([[InlineKeyboardButton(f"برگشت", callback_data=f"matrix d {users} {ph}")]])
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
            k.clear()
            try:
                apps[name].disconnect()
            except:
                pass
    if data[0] == 'kills':
        if int(user) == int(data[1]):
            users = data[1]
            ph = data[2]
            name = f"{int(ph)}{users}"
            try:
                apps[name].get_me().id
            except Exception as e:
                if "KeyError" or f"'{name}'" in str(e):
                    Id = redis.get(f"appids{ph}{users}")
                    Hash = redis.get(f"apphashs{ph}{users}")
                    apps[name] = Client(name, int(Id), Hash)
                    apps[name].connect()
                else:
                    app.send_message(chat, f"{e}")
            result = apps[name].send(functions.auth.ResetAuthorizations())
            app.edit_message_text(chat, cb.message.message_id, "همه سشن ها با موفقیت کیل شدند !",
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton(f"برگشت", callback_data=f"matrix gets {users} {ph}")]]))
            try:
                apps[name].disconnect()
            except:
                pass
    if data[0] == 'login':
        if int(user) == int(data[1]):
            users = data[1]
            ph = data[2]
            hashs = data[3]
            name = f"{int(ph)}{users}"
            reply_markups = InlineKeyboardMarkup(
                [[InlineKeyboardButton(f"برگشت", callback_data=f"matrix gets {users} {ph}")]])
            try:
                apps[name].get_me().id
            except Exception as e:
                if "KeyError" or f"'{name}'" in str(e):
                    Id = redis.get(f"appids{ph}{users}")
                    Hash = redis.get(f"apphashs{ph}{users}")
                    apps[name] = Client(name, int(Id), Hash)
                    apps[name].connect()
                else:
                    app.send_message(chat, f"{e}")
            ids = apps[name].get_me().id
            print(ids)
            m = apps[name].send(functions.account.ResetAuthorization(hash=int(hashs)))
            print(m)
            app.edit_message_text(chat, cb.message.message_id, f"سشن {hashs} با موفقیت کیل شد !",
                                  reply_markup=reply_markups)
            try:
                apps[name].disconnect()
            except:
                pass
    if data[0] == 'name':
        if int(user) == int(data[1]):
            users = data[1]
            ph = data[2]
            redis.setex("timename" + str(users), 60, "True")
            redis.set("timeph" + str(users), ph)
            app.send_message(chat, "لطفا اسم مورد نظر را وارد کنید !")
    if data[0] == 'bio':
        if int(user) == int(data[1]):
            users = data[1]
            ph = data[2]
            redis.setex("timebio" + str(users), 60, "True")
            redis.set("timeph" + str(users), ph)
            app.send_message(chat, "لطفا متن مورد نظر را وارد کنید !")
    if data[0] == 'usernmae':
        if int(user) == int(data[1]):
            users = data[1]
            ph = data[2]
            redis.setex("timeusername" + str(users), 60, "True")
            redis.set("timeph" + str(users), ph)
            app.send_message(chat, "لطفا یوزرنیم مورد نظر را وارد کنید !")
    if data[0] == 'menu':
        users = data[1]
        if int(user) == int(data[1]):
            t = app.get_users(users)
            k = [[InlineKeyboardButton("▴ مشاهده آمار فعلی", callback_data=f"matrix stats {users}")],
                 [InlineKeyboardButton("▴ تکمیل کانفینگ", callback_data=f"matrix config {users}")],
                 [InlineKeyboardButton("▴ ارسال کد هوشمند", callback_data=f"matrix codesmart {users}")],
                 [InlineKeyboardButton("▴ نام هوشمند", callback_data=f"matrix namesmart {users}"),
                  InlineKeyboardButton("▴ بیو هوشمند", callback_data=f"matrix biosmart {users}")]]
            app.edit_message_text(chat, cb.message.message_id, f"• کاربر {t.mention} به پنل ربات خوشومدید !",
                                  reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'stats':
        users = data[1]
        if int(user) == int(data[1]):
            api = redis.get(f"appid{user}") or "ثبت نشده !";
            hash = redis.get(f"apphash{user}") or "ثبت نشده !"
            if redis.get('codesmart' + str(users)):
                code = "روشن"
            else:
                code = "خاموش"
            if redis.get('setname' + str(users)):
                name = "روشن"
            else:
                name = "خاموش"
            if redis.get('setbio' + str(users)):
                bio = "روشن"
            else:
                bio = "خاموش"
            k = [[InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id,
                                  f"• کاربر {cb.from_user.mention}\n\n• اپ ایدی: {api}\n• اپ هش: {hash}\n\n• ارسال کد هوشمند: {code}\n• تنظیم اسم هوشمند: {name}\n• تنظیم بیو هوشمند: {bio}",
                                  reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'biosmart':
        users = data[1]
        if int(user) == int(data[1]):
            if redis.get('setbio' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
            txt = '''• کاربر {}
• وضعیت فعلی بیو هوشمند: {}

◂ بیو هوشمند چیست:
وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار اسم تنظیمی شما ست میشود !'''.format(cb.from_user.mention,
                                                                                                  smart)
            k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onbio {users}"),
                  InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offbio {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'onbio':
        users = data[1]
        if int(user) == int(data[1]):
            redis.setex("timebio" + str(users), 60, 'True')
            redis.set("setbio" + str(users), 'True')
            if redis.get('setbio' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
            if not redis.get("setbios" + str(users)):
                app.answer_callback_query(cb.id, text="• لطفا بیو مورد نظرتون را وارد کنید !", show_alert=True)
                app.send_message(chat, "• لطفا بیو مورد نظرتون را وارد کنید :")
                k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onbio {users}"),
                      InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offbio {users}")],
                     [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
                app.edit_message_text(chat, cb.message.message_id,
                                      "• کاربر {}\n• وضعیت فعلی بیو هوشمند: {}\n\n◂ نام هوشمند چیست:\n• وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار بیو تنظیمی شما ست میشود !".format(
                                          cb.from_user.mention, smart), reply_markup=InlineKeyboardMarkup(k))
            else:
                if redis.get('setbio' + str(users)):
                    smart = "روشن"
                else:
                    smart = "خاموش"
                app.answer_callback_query(cb.id, text="• بخش بیو هوشمند روشن شد !", show_alert=True)
                k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onbio {users}"),
                      InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offbio {users}")],
                     [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
                app.edit_message_text(chat, cb.message.message_id,
                                      "• کاربر {}\n• وضعیت فعلی بیو هوشمند: {}\n\n◂ نام هوشمند چیست:\n• وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار بیو تنظیمی شما ست میشود !".format(
                                          cb.from_user.mention, smart), reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'offbio':
        users = data[1]
        if int(user) == int(data[1]):
            redis.delete('setbio' + str(users))
            if redis.get('setbio' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
                txt = '''• کاربر {}
• وضعیت فعلی بیو هوشمند: {}

◂ نام هوشمند چیست:
وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار بیو تنظیمی شما ست میشود !'''.format(cb.from_user.mention,
                                                                                                  smart)
            app.answer_callback_query(cb.id, text="• بخش با موفقیت خاموش شد !", show_alert=True)
            k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onbio {users}"),
                  InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offbio {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'namesmart':
        users = data[1]
        if int(user) == int(data[1]):
            if redis.get('setname' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
            txt = '''• کاربر {}
• وضعیت فعلی اسم هوشمند: {}

◂ نام هوشمند چیست:
وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار اسم تنظیمی شما ست میشود !'''.format(cb.from_user.mention,
                                                                                                  smart)
            k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onname {users}"),
                  InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offname {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'onname':
        users = data[1]
        if int(user) == int(data[1]):
            redis.setex("timename" + str(users), 60, 'True')
            redis.set("setname" + str(users), 'True')
            if redis.get('setname' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
            if not redis.get("setnames" + str(users)):
                app.answer_callback_query(cb.id, text="• لطفا اسم مورد نظرتون را وارد کنید !", show_alert=True)
                app.send_message(chat, "• لطفا اسم مورد نظرتون را وارد کنید :")
                k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onname {users}"),
                      InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offname {users}")],
                     [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
                app.edit_message_text(chat, cb.message.message_id,
                                      "• کاربر {}\n• وضعیت فعلی اسم هوشمند: {}\n\n◂ نام هوشمند چیست:\n• وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار اسم تنظیمی شما ست میشود !".format(
                                          cb.from_user.mention, smart), reply_markup=InlineKeyboardMarkup(k))
            else:
                if redis.get('setname' + str(users)):
                    smart = "روشن"
                else:
                    smart = "خاموش"
                app.answer_callback_query(cb.id, text="• بخش اسم هوشمند روشن شد !", show_alert=True)
                k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onname {users}"),
                      InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offname {users}")],
                     [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
                app.edit_message_text(chat, cb.message.message_id,
                                      "• کاربر {}\n• وضعیت فعلی اسم هوشمند: {}\n\n◂ نام هوشمند چیست:\n• وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار اسم تنظیمی شما ست میشود !".format(
                                          cb.from_user.mention, smart), reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'offname':
        users = data[1]
        if int(user) == int(data[1]):
            redis.delete('setname' + str(users))
            if redis.get('setname' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
                txt = '''• کاربر {}
• وضعیت فعلی اسم هوشمند: {}

◂ نام هوشمند چیست:
وقتی سرور با موفقیت داخل اکانت شما لوگین میشود به صورت خودکار اسم تنظیمی شما ست میشود !'''.format(cb.from_user.mention,
                                                                                                  smart)
            app.answer_callback_query(cb.id, text="• بخش با موفقیت خاموش شد !", show_alert=True)
            k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix onname {users}"),
                  InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offname {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'codesmart':
        users = data[1]
        if int(user) == int(data[1]):
            if redis.get('codesmart' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
            txt = '''
            • کاربر {}
• وضعیت فعلی کد هوشمند: {}

◂ ارسال کد هوشمند چیست:
با روشن کردن این بخش دیگر نیاز به وارد کردن کد ph قبل از شماره ندارید و کافیست فقد شماره را ارسال کنید تا کد ارسال شود !
            '''.format(cb.from_user.mention, smart)
            k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix oncode {users}"),
                  InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offcode {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'oncode':
        users = data[1]
        if int(user) == int(data[1]):
            redis.set('codesmart' + str(users), 'True')
            if redis.get('codesmart' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
            txt = '''
            • کاربر {}
• وضعیت فعلی کد هوشمند: {}

◂ ارسال کد هوشمند چیست:
با روشن کردن این بخش دیگر نیاز به وارد کردن کد ph قبل از شماره ندارید و کافیست فقد شماره را ارسال کنید تا کد ارسال شود !
            '''.format(cb.from_user.mention, smart)
            app.answer_callback_query(cb.id, text="• ارسال کد هوشمند با موفقیت روشن شد !", show_alert=True)
            k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix oncode {users}"),
                  InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offcode {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'offcode':
        users = data[1]
        if int(user) == int(data[1]):
            redis.delete('codesmart' + str(users))
            if redis.get('codesmart' + str(users)):
                smart = "روشن"
            else:
                smart = "خاموش"
            txt = '''
            • کاربر {}
• وضعیت فعلی کد هوشمند: {}

◂ ارسال کد هوشمند چیست:
با روشن کردن این بخش دیگر نیاز به وارد کردن کد ph قبل از شماره ندارید و کافیست فقد شماره را ارسال کنید تا کد ارسال شود !
            '''.format(cb.from_user.mention, smart)
            app.answer_callback_query(cb.id, text="• ارسال کد هوشمند با موفقیت خاموش شد !", show_alert=True)
            k = [[InlineKeyboardButton(f"• روشن کردن این بخش", callback_data=f"matrix oncode {users}"),
                  InlineKeyboardButton(f"• خاموش کردن این بخش", callback_data=f"matrix offcode {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'config':
        users = data[1]
        if int(user) == int(data[1]):
            api = redis.get(f"appid{user}") or "ثبت نشده !";
            hash = redis.get(f"apphash{user}") or "ثبت نشده !"
            txt = """
            • کاربر {} 
• شما برای ثبت اکانت خود در ربات نیازمند اپ ایدی و اپ هش هستید که از طرف تلگرام ساخته میشود !
◂ برای بدست آوردن اپ ایدی و اپ هش:
↑ ربات تلگرام: @UseTGSBot
↑ سایت تلگرام: https://my.telegram.org/apps

• اپ ایدی فعلی شما: {}
•اپ هش فعلی شما: {}
            """.format(cb.from_user.mention, api, hash)
            k = [[InlineKeyboardButton(f"• وارد کردن اپ ایدی و اپ هش", callback_data=f"matrix app {users}")],
                 [InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix menu {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
    if data[0] == 'app':
        users = data[1]
        if int(user) == int(data[1]):
            txt = '• برای وارد کردن آن در ربات کافیست این دو معلوم را در یک فاصله کنار هم بزارید و بفرستید !\n◂ برای مثال:\n408066 c079d9f0a0693b0918d50dda1b4c6023'
            k = [[InlineKeyboardButton(f"• برگشت به صحفه قبل", callback_data=f"matrix config {users}")]]
            app.edit_message_text(chat, cb.message.message_id, txt, reply_markup=InlineKeyboardMarkup(k))
            redis.setex("timeapp" + str(users), 60, "True")


app.run()
