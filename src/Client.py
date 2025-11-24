from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contextlib import contextmanager
from logging import getLogger,DEBUG

from string import ascii_lowercase
from re import findall
from time import sleep


LOCATORS = {
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

UPDATE_INTERVALS = {
        'turn' : 0.1,
        'disconnect' : 30,
        'join' : 10
    }



class Client():
    def __init__(self, proxy : str =''):

        self.prevLW = 0 #internal for tracking life changes
        self.prevLL = 0 #internal for tracking life changes 

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

        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            'AppleWebKit/537.36 (KHTML, like Gecko)'
            'Chrome/142.0.0.0 Safari/537.36'
        )

        chrome_options.add_argument("--headless=new")
        
        chrome_options.page_load_strategy = 'eager'
        service = ChromeService()
        seleniumwire_options = {
            }

        if len(proxy) > 0:
            seleniumwire_options ['proxy'] = {
                'https': proxy,
                'http': proxy,
                'verify_ssl': False,
                'no_proxy': 'localhost,127.0.0.1'
                }
        else:
            proxy = 'localhost'
        self.driver = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=seleniumwire_options)

        self.console.info(f'initialized BombParty Client running @ {proxy}')


# ---- High-level UI interactions --------------------------------------

    def joinRoom(self, roomCode : str, username : str) -> bool: ## join the room and fill in the username + submit.

        try:
            self.console.info('joining room: '+roomCode)
            self.driver.get("https://jklm.fun/"+roomCode)
            self.driver.switch_to.default_content()

            if len(username) > 0:
                textbox = WebDriverWait(self.driver,MAX_WAIT).until(EC.visibility_of_element_located((By.XPATH, LOCATORS["nickname_input"])))

                textbox.clear()
                textbox.send_keys(username)
            
            submit = WebDriverWait(self.driver,MAX_WAIT).until(EC.element_to_be_clickable((By.XPATH, LOCATORS["submit_button"])))
            submit.click()
        
            if self.disconnect_check(): 
                self.console.warning('unable to connect to room')
                return False
            self.console.info('joined room')
            return True
        except:
            self.console.warning("some joinRoom elements not found or interactable")
            return False
        


# ---- Helper utilities -------------------------------------------------
    @contextmanager
    def in_frame(self, locator):
        ##Temporarily switch into an iframe, then switch back.
        try:
            self.driver.switch_to.frame(self.driver.find_element(By.XPATH, locator))
            yield
        finally:
            # Always go back to default content
            self.driver.switch_to.default_content()


        
    def safe_typer(self, input_value) -> bool:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                textbox = self.driver.find_element(By.XPATH, LOCATORS["textbox"])

                textbox.clear()

                if isinstance(input_value, str):
                    textbox.send_keys(input_value)
                else:
                    # assume an iterable of (char, delay)

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

# ---- Simple getters / parsers -----------------------------------------

    def get_int_val(self, elem) -> int:
        try:
            plaintext = elem.get_property("value")
            if plaintext and len(plaintext) > 0 and plaintext.isdecimal():
                return int(plaintext)
        except: pass
        return 0
    


    def get_str_val(self, elem) -> str:
        try:
            plaintext = elem.get_property("textContent")
            if plaintext and len(plaintext) > 0:
                return plaintext
        except: pass
        return ''

# ---- Game-specific reads ---------------------------------------------
    def get_bonus_alphabet(self) -> list:
            alphabet_string = ''
            try:
                with self.in_frame(LOCATORS["bombparty_iframe"]):
                    entries = self.driver.find_elements(By.XPATH, LOCATORS["bonus_alphabet"])
                    for index, letter in enumerate(entries):
                        numVal = self.get_int_val(letter)
                        if numVal > 0:
                            alphabet_string += ascii_lowercase[index] * numVal

                if len(alphabet_string) > 0:
                    self.console.info(f'bonus alphabet updated. {alphabet_string}')
                    return list(alphabet_string)
                else:
                    self.console.info("defaulting")
            except: self.console.warning('bonus alphabet not found. defaulting')
            return list('abcdefghijklmnopqrstuvwy')##defaults can be changed later.



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

                
                numVal = self.get_int_val(elem)
                if numVal > 0:
                    self.console.info(f'promptTime updated. {numVal}')
                    return numVal
        except: self.console.warning('promptTime not found; defaulting')
        return 5 ##defaults can be changed later.
    


    def get_start_lives(self) -> int:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                elem = self.driver.find_element(By.XPATH, LOCATORS["start_lives"])

                numVal = self.get_int_val(elem)
                if numVal > 0:
                    self.console.info(f'startLives updated. {numVal}')
                    return numVal
                    
        except: self.console.warning('startLives not found; defaulting')
        return 2##defaults can be changed later.



    def get_max_lives(self) -> int:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                elem = self.driver.find_element(By.XPATH, LOCATORS["max_lives"])
                numVal = self.get_int_val(elem)
                if numVal > 0:
                    self.console.info(f'maxLives updated. {numVal}')
                    return numVal
        except: self.console.warning('maxLives not found; defaulting')
        return 3##defaults can be changed later.
    


    def clear_life_trackers(self):
        self.prevLW = 0
        self.prevLL = 0



    def get_players(self) -> int:
            try:
                self.driver.switch_to.default_content()
                entries = self.driver.find_elements(By.XPATH, LOCATORS["stats_table_rows"])
                if entries and isinstance(entries, list) and len(entries) > 1:
                    playerCt = len([player for player in entries if player.get_property('class') != 'isDead']) - 1  # -1 for header
                    self.console.info(f'updated. {playerCt} players alive')
                    return playerCt
            except:self.console.warning('player count not found; defaulting')
            return 3##defaults can be changed later.



    def get_life_change(self) -> int: #tracks differences in lives won/lost since last check 
        try:
            self.driver.switch_to.default_content()
            elem = self.driver.find_element(By.XPATH, LOCATORS["self_lives"])
            plaintext = self.get_str_val(elem)
            if plaintext != '':
                nums = [int(n) for n in findall(r"[-+]?\d+", plaintext)] #extract numbers from text
                if len(nums) == 2:
                    lifeChange = (nums[0] - self.prevLW) + (nums[1] - self.prevLL)
                    self.prevLW, self.prevLL = nums
                    self.console.info(f"Life change updated. {lifeChange}")
                    return lifeChange
        except: self.console.warning("Life changes not found; defaulting")
        return 0  ##defaults can be changed later.
        


    def get_syllable(self) -> str:
        try:
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                
                syllable = self.driver.find_element(By.XPATH, LOCATORS["syllable"])
                
                plaintext = self.get_str_val(syllable)
                return plaintext.lower()
        except: self.console.warning('syllable not found; defaulting')
        return ''
    
# ---- Utility page operations -----------------------------------------

    def disconnect_check(self): ##raises disconnect to delete bot if banned.
        retries = 2
        try:
            if self.driver.find_element(By.XPATH, LOCATORS["disconnect_page"]).is_displayed(): #is disconnected
                try:
                    reason = self.driver.find_element(By.XPATH, LOCATORS["reason"])
                    message = self.get_str_val(reason).lower()
                    if "banned" in message or "error" in message or "403" in message:
                        self.console.info(f'Bot disconnected due to ban or error. Reason: {message}') ##banned
                        return True
            
                except: ###could not find reason, retrying refresh to see if it was temporary\
                    self.driver.refresh()
                    retries -=1
                    if retries > 0:
                        sleep(MAX_WAIT)
                        self.disconnect_check()
        except: pass
        return False
    


    def neterr_check(self):
        try:
            if self.driver.find_element(By.XPATH, LOCATORS["neterror_page"]).is_displayed(): ##neterr, retry refresh
                self.driver.refresh()
                sleep(MAX_WAIT)
                if self.driver.find_element(By.XPATH, LOCATORS["neterror_page"]).is_displayed():
                    return True
        except: pass
        return False