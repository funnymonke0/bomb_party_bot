from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException, ElementClickInterceptedException, WebDriverException, NoSuchFrameException, NoSuchElementException, InvalidElementStateException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random, string
import re
import asyncio
from time import sleep
import logging
import numpy as np


class JoinRoomException(Exception):
    def __init__(self):
        super().__init__("Unable to join room")


class SettingsException(Exception):
    def __init__(self):
        super().__init__(f"Cannot find all settings; one or more missing")


class DisconnectException(Exception):
    def __init__(self):
        super().__init__()

class FormatException(Exception):
    def __init__(self):
        super().__init__("Proxies should be in the format addr:port or addr:port:username:password")

class EmptyDictionaryException(Exception):
    def __init__(self):
        super().__init__("Must provide dictionary")

    
class BPB():
    def __init__(self, dicts, logger, settings, proxy=None):

        self.console = logger
        self.dicts = dicts
        self.proxy = proxy
        self.settings = settings

        self.maxWait = 2


        self.settings = self.parseSettings()

        chrome_options = ChromeOptions()
        chrome_options.page_load_strategy = 'eager'
        service = ChromeService()
        seleniumwire_options = {
            }

        if self.proxy:
            seleniumwire_options ['proxy'] = {
                'https': self.proxy,
                'http': self.proxy,
                'verify_ssl': False,
                'no_proxy': 'localhost,127.0.0.1'
                }
        else:
            self.proxy = 'localhost'
        self.driver = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=seleniumwire_options)

        self.console.info(f'initialized bot running @ {self.proxy}')

    def parseSettings(self):
        s={}

        for line in self.settings:
            key, value = line.split(':', 1)
            if value.lower() == 'true':
                s[key] = True
            elif value.lower() == 'false':
                s[key] = False
            else:
                try:
                    s[key] = float(value)
                except ValueError:
                    s[key] = value
                    pass
        try:
            self.selectMode = s['selectMode']
            self.cyberbullying = s['cyberbullying']
            self.maxOffset = s['maxOffset']
            self.rate = s['rate']
            self.burstType = s['burstType']
            self.burstRate = s['burstRate']
            self.burstChance = s['burstChance']
            self.randomness = s['randomness']
            self.mistakes = s['mistakes']
            self.mistakeChance = s['mistakeChance']
            self.mistakePause = s['mistakePause']
            self.franticType = s['franticType']
            self.dynamicPauses = s['dynamicPauses']
            self.spam = s['spam']
            self.spamRate = s['spamRate']
            self.miniPause = s['miniPause']
        except KeyError:
            pass
            raise SettingsException

    def joinRoom(self, roomCode, username = None):
        browser = self.driver
        browser.get("https://jklm.fun/"+roomCode)
        try:
            if username:
                textbox = WebDriverWait(browser,self.maxWait).until(EC.visibility_of_element_located((By.XPATH, '//input[@class = "styled nickname"]')))

                textbox.clear()
                textbox.send_keys(username)

            submit = WebDriverWait(browser,self.maxWait).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button")))
            submit.click()
            WebDriverWait(browser,self.maxWait)
        except TimeoutException:
            pass
            raise JoinRoomException

    async def tryJoin(self):
        browser = self.driver
        self.updateFrame()
        try:
            join = browser.find_element(By.XPATH, "//button[@class = 'styled joinRound']")
            join.click()
            self.console.debug(f"join success")
            return True
        except (NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException):
            pass
        return False

    async def updatePlayers(self):
        
        browser = self.driver
        browser.switch_to.default_content()
        self.playerCt = 0
        try:
            entries = browser.find_element(By.XPATH, '//table[@class = "statsTable"]').find_elements(By.XPATH, './/tr')
            self.playerCt = len([player for player in entries if player.get_attribute('class') != 'isDead'])
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        

    def getWordStat(self):
        browser = self.driver
        browser.switch_to.default_content()
        try:
            string = browser.find_element(By.XPATH, '//table[@class = "statsTable"]//tr[@class = "self"]//td[@class = "words"]').text
            if string != '':
                return int(string)
            self.console.debug(f'grabbed {string} used words from statsTable')
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        return self.expectedWords

    def updateFrame(self):
        browser = self.driver
        browser.switch_to.default_content()
        try:
            frame = browser.find_element(By.XPATH, "//iframe[contains(@src, 'bombparty')]")
            browser.switch_to.frame(frame)
        except (NoSuchElementException, ElementNotInteractableException, NoSuchFrameException, WebDriverException, InvalidElementStateException, StaleElementReferenceException):
            pass
    async def checkDC(self):
        browser = self.driver
        browser.switch_to.default_content()
        try:
            if browser.find_element(By.XPATH, '//div[@class = "disconnected page"]').is_displayed():
                raise DisconnectException
            if browser.find_element(By.XPATH, "//div[@class = 'loading page']").is_displayed():
                raise DisconnectException
            elif browser.find_element(By.XPATH, "//body[@class ='neterror']").is_displayed():
                raise DisconnectException
        except (NoSuchElementException, StaleElementReferenceException):
            pass
    async def selfTurn(self): ##not solving double answer issue
        browser = self.driver
        self.updateFrame()
        try:
            if browser.find_element(By.XPATH, '//div[@class = "selfTurn"]').is_displayed():
                return True
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        return False

    def updateBonusAlphabet(self):
        
        browser = self.driver
        self.updateFrame()

        try:
            stg = ''
            entries = browser.find_element(By.XPATH, '//div[@class = "bonusAlphabetField"]').find_elements(By.XPATH, './/div[@class = "letterField"]//input')
            for index, letter in enumerate(entries):
                times = int(letter.get_attribute("value"))
                stg += string.ascii_lowercase[index]*times
            self.alphabet = list(stg)
            self.console.debug(f'reset alphabet: {self.alphabet}')
        except (NoSuchElementException, StaleElementReferenceException, ValueError, TypeError):
            self.alphabet = string.ascii_lowercase
            self.console.debug(f'Unable to grab bonus words. Reset alphabet: {self.alphabet}')
            pass
        
        

    async def botLoop(self):
        toggle = False ##needed because selfTurn is visible at start
        while True:
            await asyncio.create_task(self.checkDC())#make thread? add threading to all eventually
            await asyncio.create_task(self.updatePlayers())
            join = await asyncio.create_task(self.tryJoin())
            turn = await asyncio.create_task(self.selfTurn())

            if join:
                toggle = True
                self.used = []
                self.mult = 0
                self.expectedWords = 0
                self.franticToggle = False
                self.spamToggle = False
                self.updateBonusAlphabet()
                self.console.info("Round ended. Resetting all variables.")

            if toggle and turn:
                if len(self.alphabet) < 1:
                    self.updateBonusAlphabet()
                self.processes()
                
## fix double answering
    
    def processes(self): #split into smaller processes
        browser = self.driver
        try:
            self.updateFrame()
            textbox = browser.find_element(By.XPATH, '//form//input[@maxlength = "30"]')
            syllable = browser.find_element(By.XPATH, "//div[@class = 'syllable']").text
            textbox.send_keys(Keys.ENTER)
            
            lst = self.dicts[syllable.lower()]
            # if not len(lst) >= 1:
            #     with open("unknowns.txt","a") as file:
            #         file.write(syllable.lower()+"\n")

            lst = list(set(lst) - set(self.used))
            
            

            if lst and len(lst) > 0:
                if self.selectMode == 'long':
                    ans = lst[len(lst)-1]

                elif self.selectMode == 'short' :
                    ans = lst[0]
                elif self.selectMode == 'avg':
                    ans = lst[int((len(lst)-1)/2)]

                elif self.selectMode == 'smart':
                    ans = lst[int((len(lst)-1)/2)]
                    if len(lst[len(lst)-1])>20:
                        ans = lst[len(lst)-1]
                        self.console.info(f"long {ans} found")

                elif self.selectMode == 'regen':
                    ans = max(lst, key= lambda word: len(list(set(word) & set(self.alphabet))))
                    self.console.info(f"highword {ans} found")
            else:
                ans = "/suicide"
            
            if len(ans) > 20:
                self.franticToggle = True
                self.spamToggle = True

            if self.dynamicPauses:
                self.mult = len(lst)/len(self.dicts) #how frequent it is

            self.used.append(ans)
            self.console.info(f"found answer {ans} to syllable {syllable}")
            

            if self.cyberbullying and self.playerCt == 3:##including table head
                lmb = lambda x: textbox.send_keys(x)##if you wanna get hackusated
            else:
                lmb = lambda x: self.simType(textbox, x)
            lmb(ans)
            textbox.send_keys(Keys.ENTER)

            
            
            actual = self.getWordStat()

            self.expectedWords += 1

            if self.expectedWords != actual:
                self.franticToggle = True
                self.spamToggle = False
                self.expectedWords = actual

            else:
                self.franticToggle = False
                self.spamToggle = False

                self.alphabet = (np.array(self.alphabet) - np.array(list(ans))).tolist()
                self.console.debug('remaining:' + str(self.alphabet))

        except (NoSuchElementException, ElementNotInteractableException, InvalidElementStateException, AttributeError, StaleElementReferenceException):
            pass

    def simType(self, obj, txt):
        
        ratesList = []
        rand = lambda x: x*(1+random.uniform(-1, 1)*self.randomness)
        
        txt = list(txt)

        for index, letter in enumerate(txt):
            if self.mistakes and (random.uniform(0, 1) <= self.mistakeChance):
                txt.insert(index+1, random.choice(string.ascii_lowercase))
                ratesList.append(self.mistakePause)
                txt.insert(index+2, Keys.BACKSPACE)
                ratesList.append(0)

            if self.franticType and self.franticToggle:
                ratesList.append(self.burstRate)

            elif self.burstType and(random.random() <= self.burstChance):
                ratesList.append(self.burstRate)
            else:
                ratesList.append(rand(self.rate))
                

        if self.spam and self.spamToggle:
            length = random.randint(10,21)
            spam = [random.choice(string.ascii_lowercase) for i in range(0,length)]
            rates = [rand(self.spamRate) for i in range(0,length)]
            txt = spam + [Keys.ENTER,''] + txt
            ratesList = rates+ [0,self.miniPause]+ratesList
        else:
            wait = self.maxOffset-(self.maxOffset*self.mult)
            if wait > 0:
                sleep(wait)
            

        for letter, delay in list(zip(txt, ratesList)):
            sleep(delay)
            if letter != '':
                obj.send_keys(letter)
            

        
    def __del__(self):
        self.driver.quit()
        
        self.console.info("POOF!")

    
            
class BotManager():

    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dictFile, roomCode, settingsFile, proxyFile, username = None):
        
        
        
        self.roomCode = roomCode
        self.username = username
        self.dictFile = dictFile
        self.settingsFile = settingsFile
        self.proxyFile = proxyFile
        self.genConsoles()
        self.loadProxies()
        self.loadDicts()
        

    def genConsoles(self):
        self.console = logging.getLogger('MANAGER-CONSOLE')
        self.botconsole = logging.getLogger('MANAGER-CONSOLE.BOT')
        logger_root = logging.getLogger()

        self.console.setLevel(logging.DEBUG)
        self.botconsole.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        fh = logging.FileHandler('BotManager.log')
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        self.console.addHandler(ch)
        logger_root.addHandler(fh)

    def loadProxies(self):
        
        settingsRegex = r"^\w+(\s*)\:(\s*)(\w+)(\.\w+)?"
        proxyRegex = r"^((\d{1,3}\.){3}(\d{1,3})|\w+\.\w+(\.\w+)?):(\d{1,5})(:.+:.+)?"
        

        self.settings = self.parseFromFile(self.settingsFile, settingsRegex)
        self.console.info(f"loaded all settings")

        self.proxyList = self.parseFromFile(self.proxyFile, proxyRegex)

        self.console.info(f"loaded {len(self.proxyList)} proxies from {self.proxyFile}")

        if not self.proxyList:
            self.proxyList = [None]
        if not self.username:
            self.username = None
        
    def loadDicts(self):
        plaintextRegex = r"^\w+(\-\w+)?$"
        urlRegex = r"^((https|http)\:\/\/)((\w+\.\w+\.\w+)|(\w+\.\w+))((\/.+)+)?"
        dictUrls = self.parseFromFile(self.dictFile, urlRegex)
        dicts = []
        if dictUrls:
            self.console.info(f"loading {len(dictUrls)} dictionaries from urls")
            dicts += self.loadUrls(dictUrls)

        
        dictPlainText = [x.lower() for x in self.parseFromFile(self.dictFile, plaintextRegex)]

        if dictPlainText:
            self.console.info(f"loading {len(dictPlainText)} entries from plaintext")
            dicts += dictPlainText

        
        if not dicts or len(dicts) == 0:
            raise EmptyDictionaryException
        
        dicts = list(set(dicts))

        self.console.info(f"loaded {len(dicts)} words from {self.dictFile}")

        self.hsmp = {}

        for letter1 in string.ascii_lowercase:
            k1 = letter1
            value = [wrd for wrd in dicts if k1 in wrd.lower()]
            self.hsmp[k1] = value
            for letter2 in string.ascii_lowercase:
                k2 = k1 + letter2
                value = [wrd for wrd in self.hsmp[k1] if k2 in wrd.lower()]
                self.hsmp[k2] = value
                for letter3 in string.ascii_lowercase:
                    k3 = k2+letter3
                    value = [wrd for wrd in self.hsmp[k2] if k3 in wrd.lower()]
                    self.hsmp[k3] = value
        self.console.info(f"finished mapping all {len(self.hsmp)} (key,value) pairs")

        # for k, v in self.hsmp.items():
        #     if len(v) == 0:
        #         with open("unknowns.txt", "a") as file:
        #             file.write(k+"\n")

    def loadUrls(self, dictUrls):
        service = ChromeService()
        options = ChromeOptions()
        options.add_argument('--headless=new')
        browser = webdriver.Chrome(service=service, options=options)
        
        dicts = []
        for url in dictUrls:
            try:
                browser.get(url)
                WebDriverWait(browser, 5)
            except (ConnectionResetError,ConnectionAbortedError,ConnectionError,ConnectionRefusedError) as e:
                self.console.error(f'Cannot get url {url} because of Exception {e}')
                pass
            content = browser.find_element(By.XPATH, '//pre')
            dicts += content.text.lower().split('\n')

        return dicts

        

    async def persistLoop(self):
        proxyNo = 0


        thresh = 2
        retries = 0
        for proxy in self.proxyList:
            
            proxy = self.formatProxy(proxy)
            retries = 0
            while not retries > thresh:
                try:
                    bot = BPB(dicts=self.hsmp, proxy=proxy, settings=self.settings, logger=self.botconsole)
                    bot.joinRoom(roomCode=self.roomCode, username=self.username)
                    await asyncio.create_task(bot.botLoop())
                    
                except DisconnectException:
                    self.console.info(f'Bot #{proxyNo} @ {self.proxyList[proxyNo]} disconnected successfully')
                    retries = 0
                except Exception as e:
                    self.console.debug(f"Exception {e} in bot #{proxyNo} @ {self.proxyList[proxyNo]}", exc_info=True)
                retries += 1
            
            
            proxyNo+=1
            
        self.console.info('goodbye!')
        
    def parseFromFile(self, filename, ex):

        lst = []
        
        with open(filename, 'r') as file:
            out = file.readlines()
        
        for x in out:
            if re.match(ex,x):
                lst.append(re.sub(r"\s+", "", x))
        return lst


    
    def formatProxy(self, proxy):
        split = proxy.split(':')
        fProxy = None
        if len(split) == 4:
            
            addr, port, user, pswd = split[0], split[1], split[2], split[3]
            fProxy = f"https://{user}:{pswd}@{addr}:{port}"

        elif len(split) == 2:
            addr, port = split[0], split[1]
            fProxy = f"https://{addr}:{port}"
        else:
            raise FormatException
        return fProxy
        
if __name__ == "__main__" :
    proxies = 'proxies.config' ##adjust to autorecognize
    settings = 'settings.config'
    dictionaries = 'dictionaries.txt'
    link = str(input("paste code: ")).upper()
    name = str(input("username: "))

    if len(link) == '':
        print('ERROR: Must input valid room code !')
        quit()
    if name == '':
        name = None

    manager = BotManager(dictFile=dictionaries, roomCode=link, proxyFile=proxies, username=name, settingsFile=settings)

    asyncio.run(manager.persistLoop())
