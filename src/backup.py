from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException, ElementClickInterceptedException, WebDriverException, NoSuchFrameException, NoSuchElementException, InvalidElementStateException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contextlib import contextmanager
from math import log
import threading
from logging import Logger

import random
from string import ascii_lowercase
from re import findall as regex_findall
from time import sleep as blocking_sleep


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
    "self_lives": "//table[@class='statsTable']//tr[contains(@class, 'self')]//td[@class='lives']"
}

MAX_WAIT = 5

UPDATE_INTERVALS = {
        'turn' : 0.1,
        'disconnect' : 30,
        'join' : 10
    }

MISTAKE_MAP = {
    'q': ['w', 'a'],
    'w': ['q', 'e', 'a', 's'],
    'e': ['w', 'r', 's', 'd'],
    'r': ['e', 't', 'd', 'f'],
    't': ['r', 'y', 'f', 'g'],
    'y': ['t', 'u', 'g', 'h'],
    'u': ['y', 'i', 'h', 'j'],
    'i': ['u', 'o', 'j', 'k'],
    'o': ['i', 'p', 'k', 'l'],
    'p': ['o', 'l'],

    'a': ['q', 'w', 's', 'z'],
    's': ['a', 'w', 'e', 'd', 'z', 'x'],
    'd': ['s', 'e', 'r', 'f', 'x', 'c'],
    'f': ['d', 'r', 't', 'g', 'c', 'v'],
    'g': ['f', 't', 'y', 'h', 'v', 'b'],
    'h': ['g', 'y', 'u', 'j', 'b', 'n'],
    'j': ['h', 'u', 'i', 'k', 'n', 'm'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p'],

    'z': ['a', 's', 'x'],
    'x': ['z', 's', 'd', 'c'],
    'c': ['x', 'd', 'f', 'v'],
    'v': ['c', 'f', 'g', 'b'],
    'b': ['v', 'g', 'h', 'n'],
    'n': ['b', 'h', 'j', 'm'],
    'm': ['n', 'j', 'k']
}

class DisconnectException(Exception): pass


class Bot():
    def __init__(self, dicts: dict, logger : Logger, settings : dict, defunctFile:str, proxy : str =None):

        self.console = logger


        self.dicts = dicts 
        self.defunctFile = defunctFile 

        self.used = set()
        self.unusable = set()
        self.alphabet = []
        self.original = []

        self.ans = ""
        self.timeUsed = 0
        self.playerCt = 0 
        
        self.franticToggle = False
        self.spamToggle = False

        self.textbox = None 
        self.syllable = "" 

        self.promptTime = 5
        self.startLives = 2
        self.maxLives = 3
        self.currentLives = 2

        self.prevLW = 0
        self.prevLL = 0


        ## list unpacking. do this for convenient use cuz we dont want to have to get the variables from the settings list in each method
        [
            self.selectMode,
            self.cyberbullying,
            self.defaultWait,
            self.minWait, 
            self.rate,
            self.burstType,
            self.burstRate,
            self.burstChance,
            self.randomness,
            self.mistakes,
            self.mistakeChance, 
            self.mistakePause,
            self.franticType,
            self.franticRate,
            self.dynamicPauses,
            self.scaleFactor,
            self.spamType,
            self.spamRate,
            self.miniPause,
            self.useDefunct
        ] = settings


        chrome_options = ChromeOptions()
        chrome_options.page_load_strategy = 'eager'
        service = ChromeService()
        seleniumwire_options = {
            }

        if proxy:
            seleniumwire_options ['proxy'] = {
                'https': proxy,
                'http': proxy,
                'verify_ssl': False,
                'no_proxy': 'localhost,127.0.0.1'
                }
        else:
            proxy = 'localhost'
        self.driver = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=seleniumwire_options)

        self.console.info(f'initialized bot running @ {proxy}')
        self.wait = WebDriverWait(self.driver, MAX_WAIT)

        # threading control
        self._stop_event = threading.Event()
        self._threads = []



    def joinRoom(self, roomCode : str, username : str): ## join the room and fill in the username + submit.
        browser = self.driver
        console = self.console
        self.console.info('joining room')
        browser.get("https://jklm.fun/"+roomCode)
        browser.switch_to.default_content()
        
        try:
            if username is not None and len(username) > 0:
                textbox = WebDriverWait(browser,MAX_WAIT).until(EC.visibility_of_element_located((By.XPATH, LOCATORS["nickname_input"])))

                textbox.clear()
                textbox.send_keys(username)
            
            submit = WebDriverWait(browser,MAX_WAIT).until(EC.element_to_be_clickable((By.XPATH, LOCATORS["submit_button"])))
            submit.click()

            self.wait
            
        except TimeoutException:
            console.info('failed to join room')
            return False
        
        console.info('joined room')
        return True

    @contextmanager
    def in_frame(self, locator):
        """Temporarily switch into an iframe, then switch back."""
        try:
            self.wait.until(EC.frame_to_be_available_and_switch_to_it(locator))
            yield
        except NoSuchFrameException:
            self.console.debug("⚠ Frame not found, skipping")
            yield
        finally:
            # Always go back to default content
            self.driver.switch_to.default_content()


    def loadDefunct(self): ## loads the non-working words at the start of threadStart. Purely for saving unusables to file.
        console = self.console
        fn = self.defunctFile
        try:
            with open(fn, 'r') as file:
                self.unusable.update(file.readlines())
            console.info(f'loaded unusable word list from {fn}. Contains {len(self.unusable)} words')
        except (FileNotFoundError, FileExistsError):
            console.info(f"{fn} could not be loaded")
            self.useDefunct = False


    def safe_find(self, locator):
        """Find element safely (retries until found or timeout)."""
        return self.wait.until(EC.presence_of_element_located(locator))

    def safe_finds(self, locator):
        """Find element safely (retries until found or timeout)."""
        return self.wait.until(EC.presence_of_all_elements_located(locator))
    
    def safe_click(self, locator):
        """Click with re-locate and retry."""
        try:
            el = self.wait.until(EC.element_to_be_clickable(locator))
            el.click()
            return True
        except TimeoutException:
            return False
        
    def is_visible(self, locator):
        """Check visibility of element."""
        try:
            el = self.wait.until(EC.visibility_of_element_located(locator))
            return bool(el and el.is_displayed())
        except TimeoutException:
            return False
        
    def safe_typer(self, locator, input_value):
        textbox =  self.wait.until(EC.presence_of_element_located(locator))

        textbox.clear()

        if isinstance(input_value, str):
            textbox.send_keys(input_value)
        else:
            # assume an iterable of (char, delay)

            for letter, delay in input_value:
                textbox.send_keys(letter)
                self.timeUsed += delay
                blocking_sleep(delay)

        textbox.send_keys(Keys.ENTER)
        

    def join_round(self):
        """Click the join round button if available."""
        joined = self.safe_click((By.XPATH, LOCATORS["join_round_button"]))
        if joined:
            print("Joined a round")
        return joined
    

 


    def get_int_val(self, elem):
        plaintext = elem.get_property("value")
        if plaintext and len(plaintext) > 0 and plaintext.isdecimal():
            return int(plaintext)
        return None
    


    def get_str_val(self, elem):
        plaintext = elem.get_property("textContent")
        if plaintext and len(plaintext) > 0:
            return plaintext
        return None
    
    def bonus_alphabet(self):
            with self.in_frame(LOCATORS["bombparty_iframe"]):
                entries = self.safe_finds(LOCATORS["bonus_alphabet"]) or []
                alphabet_string = ''
                for index, letter in enumerate(entries):
                    numVal = self.get_int_val(letter)
                    if numVal:
                        alphabet_string += ascii_lowercase[index] * numVal

                if alphabet_string:
                    self.console.info(f'bonus alphabet updated. {alphabet_string}')
                    self.original = list(alphabet_string)
                    return

            self.console.info('bonus alphabet not updated. defaulting')
            self.original = list('abcdefghijklmnopqrstuvwy')


    def prompt_time(self):
        with self.in_frame(LOCATORS["bombparty_iframe"]):
            elem = self.safe_find(LOCATORS.get("min_turn_duration"))
            if elem:
                numVal = self.get_int_val(elem)
                if numVal:
                    self.promptTime = numVal
                    self.console.info(f'promptTime updated. {self.promptTime}')
                    return
        self.console.info('promptTime not updated')

    def start_lives(self):
        with self.in_frame(LOCATORS["bombparty_iframe"]):
            elem = self.safe_find(LOCATORS.get("start_lives"))
            if elem:
                numVal = self.get_int_val(elem)
                if numVal:
                    self.startLives = numVal
                    self.console.info(f'startLives updated. {self.startLives}')
                    return
        self.console.info('startLives not updated')

    def max_lives(self):
        with self.in_frame(LOCATORS["bombparty_iframe"]):
            elem = self.safe_find(By.XPATH, LOCATORS.get("max_lives"))
            if elem:
                numVal = self.get_int_val(elem)
                if numVal:
                    self.maxLives = numVal
                    self.console.info(f'maxLives updated. {self.maxLives}')
                    return
        self.console.info('maxLives not updated')


    def join_updates(self):
        self.bonus_alphabet()
        self.prompt_time()
        self.start_lives()
        self.max_lives()
        self.used = set()
        self.used.update(self.unusable)
        self.franticToggle = False
        self.spamToggle = False
        self.currentLives = self.startLives


    def turn_updates(self):
        self.timeUsed = 0
        self.prevLW = 0
        self.prevLL = 0
        self.update_players()
        self.update_current_lives()
        self.update_elements()

    def update_players(self):
            entries = self.safe_finds(LOCATORS["stats_table_rows"], fallback=[]) or []
            if entries and isinstance(entries, list) and len(entries) > 1:
                self.playerCt = len([player for player in entries if player.get_property('class') != 'isDead']) - 1  # -1 for header
                self.console.info(f'updated. {self.playerCt} players alive')


    def update_current_lives(self):
        elem = self.safe_find(LOCATORS["self_lives"])
        if elem:
            plaintext = self.get_str_val(elem)
            if plaintext:
                nums = [int(n) for n in regex_findall(r"[-+]?\d+", plaintext)]
                if nums is not None and len(nums) == 2:
                    self.currentLives += (nums[0] - self.prevLW) + (nums[1] - self.prevLL)
                    self.prevLW, self.prevLL = nums
                    self.console.info(f"current lives updated. {self.currentLives}")
                    return
        self.console.info("current lives not updated")

    def update_elements(self):  # find syllable and textbox
        with self.in_frame(LOCATORS["bombparty_iframe"]):
            syllable = self.safe_find(By.XPATH, LOCATORS["syllable"])
            textbox = self.safe_find(By.XPATH, LOCATORS["textbox"])
            if syllable and syllable.is_displayed() and textbox and textbox.is_enabled():
                plaintext = self.get_str_val(syllable)
                if plaintext and plaintext.isalpha():
                    self.syllable = plaintext.lower()
                    self.textbox = textbox
                    return True
        return False


    def disconnect_check(self): ##raises disconnect to delete bot if banned. loop logic.

        console = self.console
        try:
            dc = self.safe_find(LOCATORS["disconnect_page"])
            if dc and dc.is_displayed(): ##banned
                console.info('Bot disconnected due to ban')
                raise DisconnectException
                
            neterr = self.safe_find(LOCATORS["neterror_page"])
            if neterr and neterr.is_displayed(): ##neterr
                console.info('Bot disconnected due to neterr')
                raise DisconnectException
        except (TimeoutException, NoSuchElementException):
            pass
        
        


   



    def main_loop(self):
        console = self.console
        alphabet = self.alphabet
        while True:
            self.disconnect_check()
            if self.join_round():
                self.join_updates()
                while not self.is_visible(LOCATORS["join_round_button"]):
                    if self.is_visible(LOCATORS["self_turn"]):
                        self.turn_updates()
                        dicts = self.dicts
                        syll = self.syllable
                    
                        ansSet = dicts[syll] #set
                        
                        ansSet = ansSet - self.used
                        if ansSet and len(ansSet) > 0:
                            self.strategy(ansSet)
                            console.info(f"found answer {self.ans} to syllable {syll}")
                        else:
                            self.ans = '/suicide'
                            console.info("no valid ans found")

                        #answer
                        ans = self.ans
                        if self.cyberbullying and self.playerCt == 2:
                            self.safe_typer(ans)
                        else:
                            typeAns = self.formatSimType(ans)
                            syllFreq = 0

                            if not self.timeUsed > 0:  # initial wait
                                wait = self.minWait
                                if self.dynamicPauses:
                                    lenAns = len(ans)
                                    syllFreq = len(ansSet) / len(dicts)
                                    func = self.scaleFactor * lenAns * (1 - log(syllFreq))
                                    wait = max(wait, func)
                                else:
                                    wait = self.defaultWait

                                # block for the initial wait
                                blocking_sleep(wait)
                                self.timeUsed += wait

                            if self.spamType and len(ans) >= 20:
                                self.spamToggle = True

                            if self.spamToggle:
                                console.info('spam on')
                                spam = self.formatSpam()
                                self.safe_typer(spam)
                                blocking_sleep(self.miniPause)

                            self.safe_typer(typeAns)
                        
                        self.used.add(ans)

                        self.franticToggle = False
                        self.spamToggle = False

                        prevLives = self.currentLives
                        prevSyll = self.syllable
                        self.turn_updates()

                        currentLives = self.currentLives 
                        wrong = prevSyll != self.syllable

                        if (currentLives == 1 or wrong) and self.franticType: ##if you are on the verge of dying or answered wrong
                            self.franticToggle = True
                            console.info('frantic on')

                        if currentLives < prevLives and self.spamType:#if life lost this round, spam next round
                            self.spamToggle = True
                            console.info('spam on')

                        if wrong:
                            self.unusable.add(ans)

                        else:
                            self.timeUsed = 0
                            [alphabet.remove(letter) for letter in set(ans) if letter in alphabet]
                            console.info(f"remaining {alphabet} after pruning")
                            if len(alphabet) < 1:
                                alphabet = self.original.copy()
                                console.info(f"{alphabet} after regen reset")
                    else:
                        self.disconnect_check()
                    blocking_sleep(UPDATE_INTERVALS['turn'])

                


        


    


    def strategy(self, ansSet:set): #eval
        ans = self.ans
        rate = self.rate
        st = self.spamToggle
        alph = self.alphabet
        mode = self.selectMode
        cl = self.currentLives
        sr = self.spamRate
        pt = self.promptTime
        tu = self.timeUsed
        console = self.console

        if mode == 'long':
            ans = max(ansSet, key=len)

        elif mode == 'short' :
            ans = min(ansSet, key= len)

        elif mode == 'avg':
            if cl > 1:
                avgLen = round((len(min(ansSet, key= len))+len(max(ansSet, key=len)))/2)
                ans = min(ansSet, key = lambda word: abs(len(word)-avgLen)) #minimize difference from the averageLen
            else:
                console.info('life constraint; using shortest')
                ans = min(ansSet, key= len)

        elif mode == 'smart':
            if cl > 1:
                ans = max(ansSet, key=len)
                if not len(ans) >= 20:
                    if cl < self.maxLives:
                        ans = max(ansSet, key= lambda word: len(set(word) & set(alph)))
                    else:
                        avgLen = round((len(min(ansSet, key= len))+len(max(ansSet, key=len)))/2)
                        ans = min(ansSet, key = lambda word: abs(len(word)-avgLen))

                tr = rate
                if st:
                    tr += sr

                if len(ans)*(tr) > pt-tu:
                    console.info('time constraint; using shortest')
                    ans = min(ansSet, key= len)
            else:
                console.info('life constraint; using shortest')
                ans = min(ansSet, key= len)

        elif mode == 'regen':
            if cl > 1:
                if cl < self.maxLives:
                    ans = max(ansSet, key= lambda word: len(set(word) & set(alph)))
                else:
                    avgLen = round((len(min(ansSet, key= len))+len(max(ansSet, key=len)))/2)
                    ans = min(ansSet, key = lambda word: abs(len(word)-avgLen))

                tr = rate
                if st:
                    tr += sr
                    
                if len(ans)*(tr) >= pt-tu:
                    console.info('time constraint; using shortest')
                    ans = min(ansSet, key= len)
            else:
                console.info('life constraint; using shortest')
                ans = min(ansSet, key= len)

        self.ans = ans

        

    def formatSpam(self):

        length = random.randint(7,15)
        
        txt = [random.choice(ascii_lowercase) for i in range(0,length)] #needed so that it does the choice each time
        ratesList = [self.spamRate for i in range(0,length)]

        return zip(txt, ratesList)

    

    def formatSimType(self, txt : str): ##tool
        rand = lambda x: x*(1+random.choice((-1, 1))*random.uniform(0, self.randomness))
        ratesList = []
        txtList = []

        for letter in txt:
            #add mistake (char and delay)
            if self.mistakes and (random.random() <= self.mistakeChance) and letter in MISTAKE_MAP.keys(): #think about having mistakechance scale with typespeed
                mistakechars = MISTAKE_MAP[letter]

                txtList.append(random.choice(mistakechars))
                ratesList.append(self.mistakePause)

                txtList.append(Keys.BACKSPACE)
                ratesList.append(self.miniPause) 


            txtList.append(letter)
            #add delay
            if self.franticToggle: 
                ratesList.append(self.franticRate)
            elif self.burstType and (random.random() <= self.burstChance):
                ratesList.append(self.burstRate)
            else:
                ratesList.append(rand(self.rate))

        return zip(txtList, ratesList)



    def __del__(self):

        if self.useDefunct:
            with open(self.defunctFile, 'w') as file:
                file.writelines('\n'.join(self.unusable) + '\n')

            self.console.info('added unusable words to defunct list')

        self.console.info("POOF! Bot cleaned up.")