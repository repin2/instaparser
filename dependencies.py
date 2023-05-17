import asyncio
import random
import tempfile
from typing import Coroutine

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebElement

chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-setuid-sandbox")


class WaitingException(Exception):
    pass


def waiter_elem(func: Coroutine):
    async def wrapper(*args, **kwargs):
        for _ in range(800):
            try:
                res = await func(*args, **kwargs)
                return res
            except NoSuchElementException:
                await asyncio.sleep(random.randint(1, 10) / 100)
        raise WaitingException

    return wrapper


@waiter_elem
async def get_max_posts_number(chrome: webdriver.Chrome) -> int:
    posts_elem = chrome.find_element(By.XPATH, "//li[contains(text(), 'posts')]")
    text = posts_elem.text
    return int(text.split(" ")[0].replace(",", ""))


@waiter_elem
async def login(chrome: webdriver.Chrome, username: str, password: str) -> None:
    username_el = chrome.find_element(By.NAME, "username")
    password_el = chrome.find_element(By.NAME, "password")
    username_el.send_keys(username)
    password_el.send_keys(password)
    password_el.send_keys(Keys.ENTER)


async def check_url(chrome: webdriver.Chrome, url: str) -> bool:
    for _ in range(300):
        if url in chrome.current_url:
            return True
        await asyncio.sleep(random.randint(1, 10) / 100)
    return False


async def prepare_chrome(login_username: str, login_password: str) -> webdriver.Chrome:
    chrome = webdriver.Chrome(options=chrome_options)
    chrome.get("https://www.instagram.com")
    await login(chrome, login_username, login_password)
    await asyncio.sleep(5)
    try:
        turn_off = chrome.find_element(By.XPATH, "//button[text()='Not Now']")
        turn_off.click()
        await asyncio.sleep(0.5)
    except NoSuchElementException:
        pass
    return chrome


@waiter_elem
async def get_create_button(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//*[name()='svg' and @aria-label='New post']")


@waiter_elem
def get_go_back(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//*[name()='svg' and @aria-label='Go Back']")


@waiter_elem
async def get_select_button(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//button[text()='Select from computer']")


@waiter_elem
async def get_input_form(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//input[@type='file']")


@waiter_elem
async def get_add_photo_button(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(
        By.XPATH, "//*[name()='svg' and @aria-label='Open media gallery']"
    )


@waiter_elem
async def get_plus_icon(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//div[@class='_aaef' and @role='button']")


@waiter_elem
async def get_next_div(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//div[text()='Next']")


@waiter_elem
async def get_caption_field(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//div[contains(text(),'Write a caption..')]")


@waiter_elem
async def get_share_div(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//div[text()='Share']")


@waiter_elem
async def get_profile_div(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.XPATH, "//*[contains(@alt, 'profile picture')]")


@waiter_elem
async def get_artice(chrome: webdriver.Chrome) -> WebElement:
    return chrome.find_element(By.TAG_NAME, "article")


async def get_last_post(chrome: webdriver.Chrome) -> str:
    profile_div = await get_profile_div(chrome)
    actions = ActionChains(chrome)
    await asyncio.sleep(2)
    actions.click(profile_div).perform()
    try:
        turn_off = chrome.find_element(By.XPATH, "//button[text()='Not Now']")
        turn_off.click()
        await asyncio.sleep(2)
    except NoSuchElementException:
        pass
    actions.click(profile_div).perform()
    article_elem = await get_artice(chrome)
    img_elem = article_elem.find_element(By.TAG_NAME, "img")
    actions.click(img_elem).perform()
    while True:
        try:
            go_back = await get_go_back(chrome)
            actions.click(go_back).perform()
        except WaitingException:
            return chrome.current_url


async def _add_with_plus_icon(
    chrome: webdriver.Chrome, image: str, actions: ActionChains
) -> None:
    plus_icon = await get_plus_icon(chrome)
    actions.click(plus_icon).perform()
    input_form = await get_input_form(chrome)
    input_form.send_keys(image)


@waiter_elem
async def check_shared(chrome: webdriver) -> None:
    chrome.find_element(By.XPATH, "//div[contains(text(),'Post shared')]")


@waiter_elem
async def add_photos(chrome: webdriver.Chrome, caption: str, images: list[str]) -> None:
    actions = ActionChains(chrome)

    create_button = await get_create_button(chrome)
    actions.click(create_button).perform()

    select_button = await get_select_button(chrome)
    actions.click(select_button).perform()

    for i, image in enumerate(images):
        if i == 0:
            input_form = await get_input_form(chrome)
            input_form.send_keys(image)
        elif i == 1:
            add_photo_button = await get_add_photo_button(chrome)
            actions.click(add_photo_button).perform()
            await _add_with_plus_icon(chrome, image, actions)
        else:
            await _add_with_plus_icon(chrome, image, actions)

    next_div = await get_next_div(chrome)
    actions.click(next_div).perform()
    await asyncio.sleep(1)
    next_div = await get_next_div(chrome)
    actions.click(next_div).perform()
    caption_field = await get_caption_field(chrome)
    actions.click(caption_field).perform()
    actions.send_keys(caption)
    share_div = await get_share_div(chrome)
    actions.click(share_div).perform()
    await check_shared(chrome)


@waiter_elem
async def _get_current_pics_links(chrome: webdriver.Chrome) -> list[str]:
    article_elem = chrome.find_element(By.TAG_NAME, "article")
    img_elems = article_elem.find_elements(By.TAG_NAME, "img")
    return [img.get_attribute("src") for img in img_elems]


async def get_links_by_scroll(chrome: webdriver.Chrome, return_number: int):
    actions = ActionChains(chrome)
    max_number = await get_max_posts_number(chrome)
    return_number = min(return_number, max_number)
    result_set = set()
    result = []
    while True:
        current_pics_links = await _get_current_pics_links(chrome)
        for pic in current_pics_links:
            if pic not in result_set:
                result_set.add(pic)
                result.append(pic)
                if len(result) == return_number:
                    return result
        actions.send_keys(Keys.SPACE).perform()
        await asyncio.sleep(random.randint(3, 10) / 20)


def write_temp_files(images: list[tempfile.TemporaryFile], files: list[bytes]):
    for image, file in zip(images, files):
        image.write(file)
        image.flush()


async def do_nothing_coro() -> None:
    return None
