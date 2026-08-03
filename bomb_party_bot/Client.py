import os
import time
from contextlib import contextmanager
from logging import getLogger, DEBUG
from re import findall
from string import ascii_lowercase
from time import sleep

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .constants import LOCATORS, MAX_WAIT
from .ProxyServer import ProxyServer


def _get_int_val(elem:WebElement) -> int:
    try:
        plaintext = str(elem.get_property("value"))# type: ignore
        if plaintext and len(plaintext) > 0 and plaintext.isdecimal():
            return int(plaintext)
    except: pass
    return 0


def _get_str_val(elem:WebElement) -> str:
    try:
        plaintext = str(elem.get_property("textContent"))# type: ignore
        if plaintext and len(plaintext) > 0:
            return plaintext
    except: pass
    return ''



class Client:
    def __init__(self, proxy: str = ''):

        self.prev_lw = 0 #internal for tracking life changes
        self.prev_ll = 0 #internal for tracking life changes

        self.console = getLogger('MANAGER-CONSOLE.BOT-CONSOLE.CLIENT-CONSOLE')
        self.console.setLevel(DEBUG)

        chrome_options = ChromeOptions()

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--metrics-recording-only')

        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-cloud-import')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-default-apps')

        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--guest')
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")

        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            'AppleWebKit/537.36 (KHTML, like Gecko)'
            'Chrome/142.0.0.0 Safari/537.36'
        )

        chrome_options.add_argument("--headless=new")
        chrome_options.page_load_strategy = 'eager'

        # Clear proxy env so Selenium Manager downloads Chrome without proxy interference
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            os.environ.pop(key, None)
        os.environ["NO_PROXY"] = "*"
        os.environ["no_proxy"] = "*"

        service = ChromeService()

        self.server = None
        if len(proxy) > 0:
            self.server = ProxyServer(proxy)
            self.server.start()
            start_time = time.time()
            success = False
            timeout = 10
            while time.time() - start_time < timeout:
                local_port = self.server.info()[1]
                if local_port > 0:
                    chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{local_port}')
                    self.console.info(f'mitmdump ready on port {local_port}, upstream: {proxy}')
                    success = True
                    break
                time.sleep(0.02)
            if not success:
                self.console.info(f'mitmdump initialization failed. defaulting to localhost')
                proxy = 'localhost'

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.console.info(f'initialized BombParty Client running @ {proxy}')

    def join_room(self, room_code: str, username: str) -> tuple[bool,bool]: #this has 3 possible modes: bot is banned and cannot join (expected, don't continue), bot is not banned and cannot join (unexpected, don't continue), bot is not banned and can join (expected, continue)
        try:
            self.console.info('joining room: ' + room_code)
            self.driver.get("https://jklm.fun/" + room_code)
            self.driver.switch_to.default_content()

            if len(username) > 0:
                textbox = WebDriverWait(self.driver,MAX_WAIT).until(EC.visibility_of_element_located((By.XPATH, LOCATORS["nickname_input"])))
                textbox.clear()
                textbox.send_keys(username)

            submit = WebDriverWait(self.driver,MAX_WAIT).until(EC.element_to_be_clickable((By.XPATH, LOCATORS["submit_button"])))
            submit.click()

            if self.disconnect_check() or self.neterr_check():
                self.console.warning('banned')
                return (True, False)
            self.console.info('joined room')
            return (True, True)
        except Exception as e:
            self.console.warning(f"some join_room elements not found or interactable: {e}")
            return (False, False)


# Helper func
    @contextmanager
    def in_frame(self, locator: str):
        ##Temporarily switch into an iframe, then switch back.
        try:
            self.driver.switch_to.frame(self.driver.find_element(By.XPATH, locator))
            yield
        finally:
            self.driver.switch_to.default_content()


    def safe_typer(self, input_value: str | list[tuple[str, float]]) -> bool:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                textbox = self.driver.find_element(By.XPATH, LOCATORS["textbox"])
                textbox.clear()

                if isinstance(input_value, str):
                    textbox.send_keys(input_value)
                else:
                    for letter, delay in input_value:
                        textbox.send_keys(letter)
                        sleep(delay)

                textbox.send_keys(Keys.ENTER)
                return True
        except: pass
        return False


    def try_join_round(self) -> bool:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                button = self.driver.find_element(By.XPATH, LOCATORS["join_round_button"])
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    self.console.info('joined round')
                    return True
        except: pass
        return False

# getters

    # page parsers
    def get_bonus_alphabet(self) -> list[str]:
            alphabet_string = ''
            try:
                with self.in_frame(LOCATORS["bombparty_iframe"]):
                    entries = self.driver.find_elements(By.XPATH, LOCATORS["bonus_alphabet"])
                    for index, letter in enumerate(entries):
                        num_val = _get_int_val(letter)
                        if num_val > 0:
                            alphabet_string += ascii_lowercase[index] * num_val

                if len(alphabet_string) > 0:
                    self.console.info(f'bonus alphabet updated. {alphabet_string}')
                    return list(alphabet_string)
                else:
                    self.console.info("defaulting")
            except: self.console.warning('bonus alphabet not found. defaulting')
            return list('abcdefghijklmnopqrstuvwy')


    def get_self_turn(self) -> bool:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                elem = self.driver.find_element(By.XPATH, LOCATORS["self_turn"])
                if elem.is_displayed():
                    return True
        except: pass
        return False


    def get_prompt_time(self) -> int:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                elem = self.driver.find_element(By.XPATH, LOCATORS["min_turn_duration"])
                num_val = _get_int_val(elem)
                if num_val > 0:
                    self.console.info(f'prompt_time updated. {num_val}')
                    return num_val
        except: self.console.warning('prompt_time not found; defaulting')
        return 5


    def get_start_lives(self) -> int:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                elem = self.driver.find_element(By.XPATH, LOCATORS["start_lives"])
                num_val = _get_int_val(elem)
                if num_val > 0:
                    self.console.info(f'start_lives updated. {num_val}')
                    return num_val
        except: self.console.warning('start_lives not found; defaulting')
        return 2


    def get_max_lives(self) -> int:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                elem = self.driver.find_element(By.XPATH, LOCATORS["max_lives"])
                num_val = _get_int_val(elem)
                if num_val > 0:
                    self.console.info(f'max_lives updated. {num_val}')
                    return num_val
        except: self.console.warning('max_lives not found; defaulting')
        return 3


    def clear_life_trackers(self) -> None:
        self.prev_lw = 0
        self.prev_ll = 0


    def get_players(self) -> int:
            try:
                self.driver.switch_to.default_content()
                entries = self.driver.find_elements(By.XPATH, LOCATORS["stats_table_rows"])
                if entries and len(entries) > 1:
                    player_ct = len([player for player in entries if str(player.get_property('class')) != 'isDead']) - 1  # type: ignore | -1 for header
                    self.console.info(f'updated. {player_ct} players alive')
                    return player_ct
            except: self.console.warning('player count not found; defaulting')
            return 3


    def get_life_change(self) -> int:
        try:
            self.driver.switch_to.default_content()
            elem = self.driver.find_element(By.XPATH, LOCATORS["self_lives"])
            plaintext = _get_str_val(elem)
            if plaintext != '':
                nums = [int(n) for n in findall(r"[-+]?\d+", plaintext)]
                if len(nums) == 2:
                    life_change = (nums[0] - self.prev_lw) + (nums[1] - self.prev_ll)
                    self.prev_lw, self.prev_ll = nums
                    self.console.info(f"Life change updated. {life_change}")
                    return life_change
        except: self.console.warning("Life changes not found; defaulting")
        return 0


    def get_syllable(self) -> str:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                syllable = self.driver.find_element(By.XPATH, LOCATORS["syllable"])
                plaintext = _get_str_val(syllable)
                return plaintext.lower()
        except: self.console.warning('syllable not found; defaulting')
        return ''

# page checks

    def disconnect_check(self) -> bool:
        try:
            if self.driver.find_element(By.XPATH, LOCATORS["disconnect_page"]).is_displayed():
                try:
                    reason = self.driver.find_element(By.XPATH, LOCATORS["reason"])
                    message = _get_str_val(reason).lower()
                    if "banned" in message:
                        self.console.info(f'Bot disconnected due to ban or error. Reason: {message}')
                        return True
                except:
                    pass
                #follow up to check since no reason detected
                counter = 0
                failed = True
                while counter < 3 and failed:
                    self.driver.refresh()
                    try:
                        WebDriverWait(self.driver, MAX_WAIT).until(EC.visibility_of_element_located((By.XPATH, LOCATORS["disconnect_page"])))
                    except TimeoutException:
                        failed = False
                        break
                    time.sleep(0.2)
                    counter += 1

                if failed:
                    self.console.info(f'Bot disconnected due to ban or error. Reason: unknown')
                    return True
        except: pass
        return False


    def neterr_check(self) -> bool:
        try:
            if self.driver.find_element(By.XPATH, LOCATORS["neterror_page"]).is_displayed():
                self.driver.refresh()
                try:
                    WebDriverWait(self.driver, MAX_WAIT).until(EC.visibility_of_element_located((By.XPATH, LOCATORS["neterror_page"])))
                    return True
                except TimeoutException:
                    pass
        except: pass
        return False

    def close(self):
        self.console.info('closing client')
        try:
            self.driver.quit()
            if self.server:
                self.server.close()
        except Exception as e:
            self.console.warning(f"Error during client close: {e}")


    def __del__(self):
        self.console.info("Client is deleted")
        self.console.handlers = []
