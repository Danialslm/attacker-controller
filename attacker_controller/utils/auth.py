from asyncio.exceptions import TimeoutError
from typing import Tuple

from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from attacker_controller.utils import storage
from attacker_controller import logger

timeout = ClientTimeout(total=10)


def create_web_application_res_error(res):
    logger.error(
        'Error in creating web application. '
        f'request response status code: {res.status}. '
        f'response reason: {res.reason}.'
    )


async def _create_application(
    session: ClientSession,
    stel_token: str,
    app_hash: str,
    app_title: str = 'attacker',
    app_shortname: str = 'attacker',
    app_url: str = '',
    app_platform: str = 'other',
    app_desc: str = '',
):
    """
    Create a new application by provided credentials.

    URL: 'https://my.telegram.org/apps/create'
    """
    url = 'https://my.telegram.org/apps/create'
    headers = {'Cookie': 'stel_token=' + stel_token}
    data = {
        'hash': app_hash,
        'app_title': app_title,
        'app_shortname': app_shortname,
        'app_url': app_url,
        'app_platform': app_platform,
        'app_desc': app_desc,
    }

    async with session.post(url, data=data, headers=headers) as res:
        res_text = (await res.read()).decode()
        if not res.ok or res_text == 'ERROR':
            create_web_application_res_error(res)
            return False
        return True


async def _get_api_id_and_api_hash(
    session: ClientSession, stel_token: str
) -> Tuple[str, str]:
    """
    Get `api_id` and `api_hash` by scraping on https://my.telegram.org/apps.

    If account doesn't have an application, create one.
    """
    url = 'https://my.telegram.org/apps'
    headers = {
        'Cookie': 'stel_token=' + stel_token,
    }

    async with session.get(url, headers=headers) as res:
        if not res.ok:
            create_web_application_res_error(res)
            return

        html_content = await res.read()
        soup = BeautifulSoup(html_content.decode(), 'html.parser')
        # check with the title page whether the app was already created or not
        page_title = soup.title.string
        if page_title == 'Create new application':
            # if there is no application, create and try again
            app_hash = soup.find("input", {"name": "hash"}).get("value")
            if await _create_application(session, stel_token, app_hash):
                api_id, api_hash = await _get_api_id_and_api_hash(session, stel_token)
            else:
                return

        elif page_title == 'App configuration':
            inputs = soup.find_all("span", {"class": "input-xlarge"})
            api_id = inputs[0].string
            api_hash = inputs[1].string

        return api_id, api_hash


async def send_password(phone: str) -> Tuple[bool, str]:
    """
    Send password to given phone number telegram account by requesting to https://my.telegram.org/auth/send_password.

    Return a tuple which contains boolean that shows the request sent successfully and a string
    that may be `random_hash` if request was successful or response error text.
    """
    url = 'https://my.telegram.org/auth/send_password'
    data = {'phone': phone}
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, data=data) as res:
                if res.status == 200:
                    if res.content_type == 'text/html':
                        message = await res.read()
                        return False, message.decode()

                    elif res.content_type == 'application/json':
                        res_data = await res.json()
                        random_hash = res_data.get('random_hash')

                        # store random_hash for web login step
                        await storage.set_random_hash(phone, random_hash, 60)
                        return True, random_hash

                res_text = await res.read()
                message = f'{res_text.decode()}خروجی غیرمنتظره! ریسپانس تلگرام : '
                return False, message
        except TimeoutError:
            return (
                False,
                f'جوابی از سوی تلگرام بعد از {timeout.total} ثانیه دریافت نشد.',
            )


async def login(phone: str, password: str) -> Tuple[bool, str]:
    """
    Login account with provided credentials by requesting to https://my.telegram.org/auth/login

    Return a tuple which contains a boolean that shows the proccess was successful and response error text.
    """
    # get `random_hash` by phone number
    random_hash = await storage.get_random_hash(phone)
    if not random_hash:
        return False, 'هش کد منقضی یا نامعتبر است.'

    url = 'https://my.telegram.org/auth/login'
    data = {
        'phone': phone,
        'password': password,
        'random_hash': random_hash,
    }

    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, data=data) as res:
                if res.status == 200:
                    if res.content_type == 'text/html':
                        message = await res.read()
                        return False, message.decode()

                    elif res.content_type == 'application/json':
                        # get telegram cookie after login
                        stel_token = res.cookies.get('stel_token').value

                        result = await _get_api_id_and_api_hash(session, stel_token)
                        if result:
                            api_id, api_hash = result
                        else:
                            return False, 'مشکلی در گرفتن api id و api hash وجود دارد.'
                        await storage.add_new_attacker(phone, api_id, api_hash)
                        return True, None

                res_text = await res.read()
                return False, f'{res_text.decode()}خروجی غیرمنتظره! ریسپانس تلگرام :\n '
        except TimeoutError:
            return (
                False,
                f'جوابی از سوی تلگرام بعد از {timeout.total} ثانیه دریافت نشد.',
            )
