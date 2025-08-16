from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException, ElementClickInterceptedException, WebDriverException, NoSuchFrameException, NoSuchElementException, InvalidElementStateException
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC
from math import log
import asyncio
from logging import Logger

import random
from string import ascii_lowercase
from re import findall as regex_findall
# from traceback import format_exc as format_traceback
from time import sleep as blocking_sleep




MAX_WAIT = 5

UPDATE_INTERVALS = {
        'element' : 0.06,
        'turn' : 0.12,
        'disconnect' : 30,
        'join' : 10
    }

MISTAKE_MAP = {
    'q': ['w', 'a', 's'],
    'w': ['q', 'e', 'a', 's', 'd'],
    'e': ['w', 'r', 's', 'd', 'f'],
    'r': ['e', 't', 'd', 'f', 'g'],
    't': ['r', 'y', 'f', 'g', 'h'],
    'y': ['t', 'u', 'g', 'h', 'j'],
    'u': ['y', 'i', 'h', 'j', 'k'],
    'i': ['u', 'o', 'j', 'k', 'l'],
    'o': ['i', 'p', 'k', 'l'],
    'p': ['o', 'l'],

    'a': ['q', 'w', 's', 'z', 'x'],
    's': ['q', 'w', 'e', 'a', 'd', 'z', 'x', 'c'],
    'd': ['w', 'e', 'r', 's', 'f', 'x', 'c', 'v'],
    'f': ['e', 'r', 't', 'd', 'g', 'c', 'v', 'b'],
    'g': ['r', 't', 'y', 'f', 'h', 'v', 'b', 'n'],
    'h': ['t', 'y', 'u', 'g', 'j', 'b', 'n', 'm'],
    'j': ['y', 'u', 'i', 'h', 'k', 'n', 'm'],
    'k': ['u', 'i', 'o', 'j', 'l', 'm'],
    'l': ['i', 'o', 'p', 'k'],

    'z': ['a', 's', 'x'],
    'x': ['a', 's', 'd', 'z', 'c'],
    'c': ['s', 'd', 'f', 'x', 'v'],
    'v': ['d', 'f', 'g', 'c', 'b'],
    'b': ['f', 'g', 'h', 'v', 'n'],
    'n': ['g', 'h', 'j', 'b', 'm'],
    'm': ['h', 'j', 'k', 'n']
}


class DisconnectException(Exception):
    def __init__(self):
        super().__init__()


def safeExec(func):#decorater

    def wrapper(*args, **kwargs):
        try:    
            obj = func(*args, **kwargs)
            if obj is not None:
                return obj
            return True
        
        except (WebDriverException, NoSuchElementException, StaleElementReferenceException, InvalidElementStateException, ElementNotInteractableException, ElementClickInterceptedException) as e:
            # self.console.warning(f"safeWrapper caught {type(e).__name__}: {e}")
            return False
    return wrapper


class Bot():
    def __init__(self, dicts: dict, logger : Logger, settings : dict, defunctFile:str, proxy : str =None):

        self.console = logger


        self.dicts = dicts ## is a self var since cycle is inside a bunch of processes
        self.defunctFile = defunctFile # is a self var since two methods use it and is inside a bunch of processes

        self.used = set()#✅
        self.unusable = set()#✅
        self.alphabet = []#✅
        self.original = []

        self.ans = ""
        self.timeUsed = 0
        self.playerCt = 0 #✅
        self.wordCt = 0

        self.expectedWords = 0#✅
        
        self.franticToggle = False#✅
        self.spamToggle = False

        self.iFrame = None #✅
        
        self.textbox = None #✅
        self.syllable = "" #✅


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
            self.maxOffset,
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
        #the settings and webdriver init can stay together cuz fuck you thats why
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



    def joinRoom(self, roomCode : str, username : str): ## join the room and fill in the username + submit. Needs default frame. Tool. External use
        browser = self.driver
        console = self.console
        self.console.info('joining room')
        browser.get("https://jklm.fun/"+roomCode)
        browser.switch_to.default_content()
        
        try:
            if username is not None and len(username) > 0:
                textbox = WebDriverWait(browser,MAX_WAIT).until(EC.visibility_of_element_located((By.XPATH, '//input[@class = "styled nickname"]')))

                textbox.clear()
                textbox.send_keys(username)
            
            submit = WebDriverWait(browser,MAX_WAIT).until(EC.element_to_be_clickable((By.XPATH, "//button[@class = 'styled']")))
            submit.click()

            WebDriverWait(browser,MAX_WAIT)
            
        except TimeoutException:
            console.info('failed to join room')
            return False
        
        console.info('joined room')
        return True



    def loadDefunct(self): ## loads the non-working words at the start of threadStart. Purely for saving unusables to file
        console = self.console
        fn = self.defunctFile
        try:
            with open(fn, 'r') as file:
                self.unusable.update(file.readlines())
            console.info(f'loaded unusable word list from {fn}. Contains {len(self.unusable)} words')
        except (FileNotFoundError, FileExistsError):
            console.info(f"{fn} could not be loaded")
            self.useDefunct = False



    async def backgroundLoop(self, logic, wait): 
        while True:

            logic()

            await asyncio.sleep(wait)
            

    
    def disconnectProc(self): ##raises disconnect to delete bot if banned. loop logic

        browser = self.driver
        console = self.console

        @safeExec
        def ban():
            browser.switch_to.default_content()
            dc = browser.find_element(By.XPATH, '//div[@class = "disconnected page"]')
            if dc.is_displayed(): ##banned
                console.info('Bot disconnected due to ban')
                raise DisconnectException
        @safeExec
        def neterr():
            browser.switch_to.default_content()
            neterr = browser.find_element(By.XPATH, "//body[@class = 'neterror']")
            if neterr.is_displayed(): ##neterr
                console.info('Bot disconnected due to neterr')
                raise DisconnectException
            
        console.info('scanning for disconnection')
        ban()
        neterr()



    def joinProc(self):
        browser = self.driver
        console = self.console


        @safeExec
        def bonusAlphabet(): ##tool. find and update bonus alphabet letters.
            self.original = list('abcdefghijklmnopqrstuvwy')
            self.switchIFrame()
            entries = browser.find_elements(By.XPATH, '//div[@class="bonusAlphabetField"]//div[@class="letterField"]//input')
            strAlph = ''
            for index, letter in enumerate(entries):
                times = letter.get_property("value")
                if times.isdecimal():
                    times = int(times)
                    strAlph += ascii_lowercase[index]*times
            if len(strAlph) > 0:
                console.info(f'bonus alphabet updated. {strAlph}')
                self.original = list(strAlph)
            else:
                console.info('bonus alphabet not updated. defaulting')


        @safeExec
        def promptTime():
            self.switchIFrame()
            rawElemVal = browser.find_element(By.XPATH, '//div[@class = "setting rule minTurnDuration"]//div[@class = "field range"]//input[@type="number" and @min = "1" and @max = "10"]').get_property('value')
            console.info(rawElemVal)
            if rawElemVal.isdecimal():
                self.promptTime = int(rawElemVal)
                console.info(f'promptTime updated. {self.promptTime}')
            else:
                console.info('promptTime not updated')


        @safeExec
        def startLives():
            self.switchIFrame()
            rawElemVal = browser.find_element(By.XPATH, "//input[@class = 'starting']").get_property("value")
            console.info(rawElemVal)
            if rawElemVal.isdecimal():
                self.startLives = int(rawElemVal)
                console.info(f"starting lives updated. {self.startLives}")
            else:
                console.info("starting lives not updated")


        @safeExec
        def maxLives():
            self.switchIFrame()
            rawElemVal = browser.find_element(By.XPATH, '//input[@class="max" and @type="number" and @min="1" and @max="10"]').get_property("value")
            console.info(rawElemVal)
            if rawElemVal.isdecimal():
                self.maxLives = int(rawElemVal)
                console.info(f"max lives updated. {self.maxLives}")
            else:
                console.info("max lives not updated")


        @safeExec
        def joinLogic():
            console.info('scanning for round join')
            self.switchIFrame()
            join = browser.find_element(By.XPATH, "//button[@class = 'styled joinRound']")

            if join.is_displayed(): #simpler than using player count
                console.info('joining round')
                join.click()
                bonusAlphabet()
                promptTime()
                startLives()
                maxLives()

                self.used = set()
                self.used.update(self.unusable)
                

                self.expectedWords = 0
                self.wordCt = 0
                self.franticToggle = False
                self.spamToggle = False
                self.currentLives = self.startLives

        joinLogic()



    async def mainLoop(self):
        console = self.console
        browser = self.driver
        alphabet = self.alphabet


        @safeExec
        def turnLogic():
            self.switchIFrame()
            turn = browser.find_element(By.XPATH, '//div[@class = "selfTurn"]')
            if turn.is_displayed():
                return True
            return False
        

        @safeExec
        def updateElements(): ## find syllable and textbox. essential loop logic
            self.switchIFrame()
            syllable = browser.find_element(By.XPATH, "//div[@class = 'syllable']")
            textbox = browser.find_element(By.XPATH, '//form//input[@maxlength = "30"]')
            if syllable.is_displayed() and textbox.is_enabled():
                textbox.clear()
                syllable = syllable.get_property("textContent").lower()
                if syllable.isalpha() and len(syllable) > 0:
                    self.syllable = syllable
                    self.textbox = textbox
                    console.info(f'updated syllable {syllable} and textbox')
                    return True
                console.info('failed to update syllable and textbox')
            return False
        

        @safeExec
        def safeTyper(input):
            textbox = self.textbox
            self.switchIFrame()
            if type(input) is str:
                textbox.send_keys(input)


            elif type(input) is zip:
                for letter, delay in input:
                    if letter != '':
                        
                        textbox.send_keys(letter)
                    self.timeUsed += delay
                    blocking_sleep(delay)
        #same end
            textbox.send_keys(Keys.ENTER)


        @safeExec
        def statsTableUpdate():
           

            @safeExec
            def updatePlayers():
                browser.switch_to.default_content()
                entries = browser.find_elements(By.XPATH, "//table[@class='statsTable']//tr")
                if len(entries) > 1: ##1 for the header
                    self.playerCt = len([player for player in entries if player.get_property('class') != 'isDead'])-1 ## -1 for the header
                    console.info(f'updated. {self.playerCt} players alive')
            
            @safeExec
            def updateWordStat():
                browser.switch_to.default_content()
                rawElemVal = browser.find_element(By.XPATH, "//table[@class='statsTable']//tr[contains(@class, 'self')]//td[@class='words']").get_property("textContent")
                if rawElemVal.isdigit():
                    self.wordCt = int(rawElemVal)
                    console.info(f"used words updated. {self.wordCt} words used")

                    
                else:
                    console.info("used words not updated")
                    self.wordCt = self.expectedWords

            @safeExec
            def updateCurrentLives():
                browser.switch_to.default_content()
                rawElemVal = browser.find_element(By.XPATH, "//table[@class='statsTable']//tr[contains(@class, 'self')]//td[@class='lives']").get_property("textContent")
                self.console.info(rawElemVal)
                nums = [int(n) for n in regex_findall(r"[-+]?\d+", rawElemVal)]
                
                if nums is not None and len(nums) == 2:
                    self.currentLives = self.currentLives + (nums[0]-self.prevLW) + (nums[1]-self.prevLL) #abs change from last turn
                    self.prevLW, self.prevLL = nums 
                    console.info(f"current lives updated. {self.currentLives}")
                else:
                    console.info("current lives not updated")

            updatePlayers()
            updateWordStat()
            updateCurrentLives()


        wrong = False
        while True:
            if turnLogic():
                console.info('turn started')

                if updateElements():
                    ##find
                    dicts = self.dicts
                    syll = self.syllable
                
                    ansSet = dicts[syll] #set
                    
                    ansSet = ansSet - self.used
                    if ansSet and len(ansSet) > 0:
                        self.strategy(ansSet)
                        console.info(f"found answer {self.ans} to syllable {syll}")
                    else:
                        # with open("unknowns.txt","a") as file:
                        #     file.write(syllable.lower()+"\n")
                        self.ans = '/suicide'
                        console.info("no valid ans found")


                    #answer
                    ans = self.ans

                    if self.cyberbullying and self.playerCt == 2:
                        safeTyper(ans)
                    else:

                        syllFreq = 0
                        if self.dynamicPauses:
                            
                            lenAns = len(ans)
                            syllFreq = len(ansSet)/len(dicts) #scale based on how rare it is (rare syllables take longer to type). the smaller the value the closer to maxOffset the pause
                        
                            wait = self.scaleFactor*lenAns*(1-log(syllFreq)) #scary big function for time scaling
                        else:
                            wait = self.maxOffset
                        
                        if wait <= 0:
                            wait = UPDATE_INTERVALS.get("element")
                            
                        await asyncio.sleep(wait)
                        self.timeUsed += wait

                        if self.spamType and len(ans) >= 20: #if word long
                            self.spamToggle = True

                        if self.spamToggle:
                            console.info('spam on')
                            safeTyper(self.formatSpam()) 
                            await asyncio.sleep(self.miniPause)
                        safeTyper(self.formatSimType(ans))

                    #post
                    self.used.add(ans)
                    self.expectedWords += 1
                    self.franticToggle = False
                    self.spamToggle = False

                    prevLives = self.currentLives
                    statsTableUpdate()
                    currentLives = self.currentLives 
                    wrong = self.wordCt != self.expectedWords
                    if wrong:
                        self.expectedWords = self.wordCt
                        self.unusable.add(ans)
                    else:
                        [alphabet.remove(letter) for letter in set(ans) if letter in alphabet]
                        console.info(f"remaining {alphabet} after pruning")
                        if len(alphabet) < 1:
                            alphabet = self.original.copy()
                            console.info(f"{alphabet} after regen reset")

                    if (currentLives == 1 or wrong) and self.franticType: ##if you are on the verge of dying or answered wrong
                        self.franticToggle = True
                        console.info('frantic on')

                    if currentLives < prevLives and self.spamType:#if life lost this round, spam next round
                        self.spamToggle = True
                        console.info('spam on')

            if not wrong:
                self.timeUsed = 0

            await asyncio.sleep(UPDATE_INTERVALS.get("turn"))

    

    def switchIFrame(self): ## tool. switch to the bombparty iframe. must be called before any other interaction with the page.
        browser = self.driver
        console = self.console
        browser.switch_to.default_content()
        while True:
            try:

                if self.iFrame is not None:
                    browser.switch_to.frame(self.iFrame)
                    return
            except (WebDriverException, NoSuchElementException, StaleElementReferenceException, InvalidElementStateException, ElementNotInteractableException):
                console.info(f"Failed to switch to iframe. refinding")

            self.iFrame = browser.find_element(By.XPATH, "//iframe[contains(@src, 'bombparty')]")
    
            

    async def start(self): ##external use
    
        self.console.info('Bot started')

        if self.useDefunct:
            self.loadDefunct()


        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.backgroundLoop(self.disconnectProc, UPDATE_INTERVALS.get('disconnect')))
                tg.create_task(self.backgroundLoop(self.joinProc, UPDATE_INTERVALS.get('join')))
                tg.create_task(self.mainLoop())
            
        except* KeyboardInterrupt:
            self.console.info('Session interrupted by user')

        except* DisconnectException:
            self.console.info('Bot disconnected gracefully due to ban or neterr')

        except* Exception as e:
            self.console.error(f'Exception caught with traceback: {e}.', exc_info=True)


    def strategy(self, ansSet:set): ##tool
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

        txt = list(txt)


        for index, letter in enumerate(txt):

            #add mistake (char and delay)
            if self.mistakes and (random.random() <= self.mistakeChance):
                    
                txt.insert(index+1, random.choice(MISTAKE_MAP.get(letter)))
                ratesList.append(self.mistakePause)

                txt.insert(index+2, Keys.BACKSPACE)
                ratesList.append(self.miniPause) #short thinking pause

            #add delay
            if self.franticToggle: #think about having mistakechance scale with typespeed
                ratesList.append(self.franticRate)
            elif self.burstType and (random.random() <= self.burstChance):
                ratesList.append(self.burstRate)
            else:
                ratesList.append(rand(self.rate))

        return zip(txt, ratesList)



    def __del__(self):

        if self.useDefunct:
            with open(self.defunctFile, 'w') as file:
                file.writelines('\n'.join(self.unusable) + '\n')

            self.console.info('added unusable words to defunct list')

        self.console.info("POOF! Bot cleaned up.")


    