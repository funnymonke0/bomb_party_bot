from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.devtools.v149 import console
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from contextlib import contextmanager
from logging import getLogger, DEBUG
import os
import socket
import subprocess
from string import ascii_lowercase
from re import findall
from time import sleep


LOCATORS: dict[str, str] = {
    "nickname_input": '//input[@class = "styled nickname"]',
    "submit_button": "//button[@class = 'styled']",
    "bombparty_iframe": "//iframe[contains(@src, 'bombparty')]",
    "disconnect_page": '//div[@class = "disconnected page"]',
    "neterror_page": "//body[@class = 'neterror']",
    "bonus_alphabet": '//div[@class="bonusAlphabetField"]//div[@class="letterField"]//input',
    "min_turn_duration": '//div[@class = "setting rule minTurnDuration"]//div[@class = "field range"]//input[@type="number" and @min = "1" and @max = "10"]',
    "start_lives": "//input[@class = 'starting']",
    "max_lives": '//input[@class="max" and @type="number" and @min="1" and @max="10"]',
    "join_round_button": "//button[@class = 'styled joinRound']",
    "self_turn": '//div[@class = "selfTurn"]',
    "syllable": "//div[@class = 'syllable']",
    "textbox": '//form//input[@maxlength = "30"]',
    "stats_table_rows": "//table[@class='statsTable']//tr",
    "self_lives": "//table[@class='statsTable']//tr[contains(@class, 'self')]//td[@class='lives']",
    "reason": './/div[@class="reason"]'
}

MAX_WAIT = 5

UPDATE_INTERVALS: dict[str, float] = {
        'turn' : 0.1,
        'disconnect' : 30,
        'join' : 10
    }


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


def _free_port() -> int: #we host a local proxy to intercept traffic, so we need a free port to bind to
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)) #autopick
        return s.getsockname()[1] #port on local machine


def _start_mitm(upstream_proxy: str, local_port: int) -> subprocess.Popen: # type: ignore | we listen on the local proxy port and then send from the upstream actual proxy
    stripped = upstream_proxy.removeprefix('https://')
    userpswd, hostnameport = stripped.split('@')
    user, pswd = userpswd.split(':')
    hostname, port = hostnameport.split(':')
    cmd = [ #this is basically just a console command
        'mitmdump',
        '--mode', f'upstream:{hostname}',#this is our actual proxy
        '--upstream-auth', f'{user}:{pswd}',
        '--listen-port', str(local_port), #this is what the webdriver thinks is the proxy (so we can intercept)
        '--ssl-insecure',
        '--quiet',
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) #make the process with no verbose


def _wait_for_port(port: int, timeout: float = 0.5, retries: float = 10) -> bool: #attempts to connect to localhost
    for i in range(int(retries)):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=timeout):
                return True
        except OSError:
            sleep(0.2)
    return False




class Client:
    def __init__(self, proxy: str = ''):

        self.prev_lw = 0 #internal for tracking life changes
        self.prev_ll = 0 #internal for tracking life changes
        self._mitm_proc: subprocess.Popen | None = None # type: ignore

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

        if len(proxy) > 0:
            local_port = _free_port()
            self._mitm_proc = _start_mitm(proxy, local_port)
            if _wait_for_port(local_port):
                chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{local_port}')
                self.console.info(f'mitmdump ready on port {local_port}, upstream: {proxy}')
            else:
                self.console.warning('mitmdump did not become ready in time; proceeding without proxy')
                self._mitm_proc.kill()
                self._mitm_proc = None
                proxy = 'localhost'
        else:
            proxy = 'localhost'

        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.console.info(f'initialized BombParty Client running @ {proxy}')

    def join_room(self, room_code: str, username: str) -> bool:
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
                self.console.warning('unable to connect to room')
                return False
            self.console.info('joined room')
            return True
        except:
            self.console.warning("some join_room elements not found or interactable")
            return False


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
                self.driver.refresh()
                self.console.info(f'refreshing to see if disconnect is temporary')
                sleep(MAX_WAIT)
                self.disconnect_check()
        except: pass
        return False


    def neterr_check(self) -> bool:
        try:
            if self.driver.find_element(By.XPATH, LOCATORS["neterror_page"]).is_displayed():
                self.driver.refresh()
                sleep(MAX_WAIT)
                if self.driver.find_element(By.XPATH, LOCATORS["neterror_page"]).is_displayed():
                    return True
        except: pass
        return False

    def close(self):
        self.driver.quit()
        if self._mitm_proc is not None:
            self._mitm_proc.terminate()
            try:
                self._mitm_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._mitm_proc.kill()
            self._mitm_proc = None
