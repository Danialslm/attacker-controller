# admin add, remove, get
ADMIN_ADDED = 'چت ایدی های داده شده به لیست ادمین‌ها اضافه شد.'
ADMIN_REMOVED = 'چت ایدی های داده شده از لیست ادمین‌ها حذف شد.'
ADMIN_LIST = 'لیست چت ایدی ادمین‌های فعلی ربات:\n\n'

# attacker add, remove, get
ATTACKER_LIST = 'لیست اتکرها : \n\n'
ATTACKER_REMOVED = 'شماره(های) داده شده از لیست اتکر‌ها حذف شد.'
ATTACKER_LIST_CLEANED = 'تمام اتکرها از ربات پاک شدند.'

# banner
BANNER_SAVED = 'بنر با موفقیت ذخیره شد.'
NO_BANNER_SET = 'بنری ست نشده است.'

# logging-in
SEND_CODE_FLOOD = (
    'ارسال درخواست با محدودیت مواجه شده است. لطفا {} ثانیه دیگر امتحان کنید.'
)
PHONE_NUMBER_INVALID = 'شماره وارد شده نادرست است.'
APP_CODE_SENT = 'پیام در پیوی تلگرام'
SMS_CODE_SENT = 'اس ام اس'
CALL_CODE_SENT = 'تماس تلفنی'
CODE_SENT = '.کد به صورت {} ارسال شد. یک دقیقه محلت ارسال دارید.'
SEND_CODE_REQUEST = 'مطمئن باشید قبل از لاگین به اکانت درخواست ارسال کد را کرده اید.'
WRONG_PASSWORD = 'پسورد اشتباه است!'
PASSWORD_REQUIRED = (
    'اکانت دارای پسورد می‌باشد. لطفا پسورد را بعد از کد با یک فاصله ارسال کنید.'
)
INVALID_CODE = 'کد منقضی یا اشتباه است.'
PHONE_NUMBER_UNOCCUPIED = 'شماره تلفن هنوز استفاده نمی‌شود.'
SIGNIN_FAILED = 'فرایند لاگین ناموفق بود.'

# update all attackers
TEXT_REPLY_REQUIRED = 'لطفا روی یک متن ریپلای بزنید و دستور را بفرستید.'
PHOTO_REPLY_REQUIRED = 'لطفا روی یک عکس ریپلای بزنید و دستور را بفرستید.'
ALL_FIRST_NAME_UPDATED = '{} اتکر نام کوچک‌شان به **{}** تغییر یافت.'
PROBLEM_WITH_UPDATING_ALL_FIRST_NAME = (
    '\nمشکلی در تغییر نام کوچک اتکرهای زیر به وجود آمد.\n'
)
ALL_LAST_NAME_UPDATED = '{} اتکر نام خانوادگی‌شان به **{}** تغییر یافت.'
PROBLEM_WITH_UPDATING_ALL_LAST_NAME = (
    '\nمشکلی در تغییر نام خانوادگی اتکرهای زیر به وجود آمد.\n'
)
ALL_BIOGRAPPHY_UPDATED = '{} اتکر بیو‌شان به **{}** تغییر یافت.'
PROBLEM_WITH_UPDATING_ALL_BIOGRAPHY = '\nمشکلی در تغییر بیو اتکرهای زیر به وجود آمد.\n'
ALL_PROFILE_PHOTO_UPDATED = '{} اتکر عکس پروفایل‌شان تغییر یافت.'
PROBLEM_WITH_UPDATING_ALL_PROFILE_PHOTO = (
    '\nمشکلی در تغییر پروفایل اتکرهای زیر به وجود آمد.\n'
)

# update single attacker
FIRST_NAME_UPDATED = 'اتکر {} نام کوچکش به **{}** تغییر یافت.'
PROBLEM_WITH_UPDATING_FIRST_NAME = 'مشکلی در تغییر نام کوچک اتکر {} به وجود آمد.'
LAST_NAME_UPDATED = 'اتکر {} نام خانوادگی اش به **{}** تغییر یافت.'
PROBLEM_WITH_UPDATING_LAST_NAME = 'مشکلی در تغییر نام خانوادگی اتکر {} به وجود آمد.'
BIOGRAPHY_UPDATED = 'اتکر {} بیو اش به **{}** تغییر یافت.'
PROBLEM_WITH_UPDATING_BIOGRAPHY = 'مشکلی در تغییر بیو اتکر {} به وجود آمد.'
PROFILE_PHOTO_UPDATED = 'اتکر {} عکس پروفایلش اش تغییر یافت.'
PROBLEM_WITH_UPDATING_PROFILE_PHOTO = 'مشکلی در تغییر عکس پروفایل اتکر {} به وجود آمد.'
USERNAME_UPDATED = 'اتکر {} نام کاربری اش به **{}** تغییر یافت.'
PROBLEM_WITH_UPDATING_USERNAME = (
    'مشکلی در تغییر نام کاربری اتکر {} به وجود آمد.\n'
    'ممکن است این نام کاربری از قبل رزرو شده باشد.\n'
    'همچنین توجه کنید که نام کاربری معتبر است.'
)

# attack
INVALIED_ID = 'ایدی نامعتبر است.'
INVALIED_TARGET = 'هدف گروه یا سوپرگروه نیست.'
GETTING_MEMBERS_FINISHED = 'فرایند گرفتن ممبرهای گروه {} تمام شد.'
ATTACKING_FLOOD = (
    'اکانت به مدت {} ثانیه فلود خورد. '
    'بعد از اتمام فلود اتک دوباره شروع خواهد شد.\n'
    'تعداد اتک های زده شده تا به الان: {}.'
)
ATTACKER_IS_BUSY = 'درحال حاضر این اتکر درحال اتک است.'
FLOODED_DURING_ATTACK = 'اتکر در حین اتک به محدودیت خورد. تعداد اتک های موفق: {}.'
ATTACKER_IS_FLOODED = 'اتکر به محدودیت خورده است.'
ATTACK_FINISHED = 'اتک تمام شد. تعداد اتک های موفق: {}.'
ATTACKER_DEACTIVATED = 'حساب کاربری اتکر غیرفعال یا حذف شده است.'
ATTACKING_ATTACKERS_UPDATE_ERROR = 'لطفا بعد از اینکه اتک اتکر ها تمام شد امتحان کنید.\n اتکرهای درحال اتک:\n\n{}'
ATTACKING_ATTACKER_UPDATE_ERROR = 'این اتکر درحال اتک است. لطفا بعد از اینکه اتک تمام شد امتحان کنید.'

# other stuff
UNEXPECTED_ERROR = 'خطای غیر منتظره‌ای رخ داده است. {} - {}'
PLEASE_WAIT = 'لطفا صبر کنید...'
SESSION_EXPIRED = 'سشن اتکر {} در ربات منسوخ شده است. لطفا اتکر را یک بار از ربات پاک و سپس اضافه کنید.'


HELP = '''
`/adminlist` - لیست ادمین های معمولی
`/addadmin` - اضافه کردن ادمین جدید (جلوش یک چت ایدی یا چند چت ایدی باید باشه)
`/removeadmin` - حذف کردن ادمین جدید (جلوش یک چت ایدی یا چند چت ایدی باید باشه)

`/sendcode` - ارسال کد لاگین (جلوش شماره باید باشه)
`/login` - لاگین به اکانت (جلوش شماره و کد و پسورد اگه داشت باید باشه)

`/attackerlist` - لیست اتکر‌ها
`/removeattacker` - حذف کردن اتکر (جلوش یک یا چند شماره باید باشه)
`/cleanattackers` - حذف کردن تمام اتکرها

`/setfirstnameall` - ست کردن نام کوچک برای همه اتکرها
`/setlastnameall` - ست کردن نام خانوادگی برای همه اتکرها
`/setbioall` - ست کردن بیو برای همه اتکرها
`/setprofileall` - ست کردن عکس پروفایل برای همه اتکرها

`/setfirstname` - ست کردن نام کوچک برای یک اتکر (جلوش شماره باید باشه)
`/setlastname` - ست کردن نام خانوادگی برای یک اتکر (جلوش شماره باید باشه)
`/setbio` - ست کردن بیو برای یک اتکر (جلوش شماره باید باشه)
`/setprofile` - ست کردن عکس پروفایل برای یک اتکر (جلوش شماره باید باشه)
`/setusername` - ست کردن نام کاربری برای یک اتکر (جلوش شماره باید باشه)

`/members` - گرفتن ممبرا (جلوش شماره و ایدی گپ و تعداد ممبرای دریافتی باید باشه)
`/attack` - اتک (جلوش شماره باید باشه)

`/setbanner` - ست کردن بنر جدید
`/banner` - بنر فعلی
'''
