import requests
from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import re
from time import sleep
import logging



class BPB():
    def __init__(self, dicts, username, roomCode, proxy = None):
        self.username = username
        self.console = logging.getLogger(f'{self.username} CONSOLE')
        self.console.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        self.console.addHandler(ch)
        
        
        ##const

        self.visibleCondition = lambda x: EC.visibility_of_element_located(x)
        self.clickableCondition = lambda x: EC.element_to_be_clickable(x)
        self.presenceCondition = lambda x: EC.presence_of_element_located(x)
        
        chrome_options = ChromeOptions()
        service = ChromeService()
        seleniumwire_options = {
            }

        ##extra options


        self.username = username
        self.roomCode = roomCode


        
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
        self.console.info(f'initialized bot {username} running @ {proxy}')

        

        ##settings
        self.maxWait = 5
        # self.selectMode = 'long'
        self.selectMode = 'short'
        # self.selectMode = 'avg'

        # self.cyberbullying = True

        self.cyberbullying = False
        self.offset = 0.6

        self.typeDelay = 0.12
        self.randomness = 0.07

        self.tickSpeed = 0.05

        self.dicts = dicts

        self.joinedRoom = self.joinRoom(roomCode)

    
    def findSuffix(self, suffix):
        lst = []
        try:
            for wrd in self.dicts:
                if suffix.lower() in wrd:
                    lst.append(wrd)
            lst.sort(key= lambda x: len(x))

            return lst
        except IndexError:
            pass
            return None        
    

    def locate(self, locator, lmd, delay = None):
        if not delay:
            delay = self.maxWait
        browser = self.driver

        wait = WebDriverWait(browser, delay, poll_frequency=self.tickSpeed)
        try:
            out = wait.until(lmd(locator))
            return out

        except TimeoutException:
            pass
        return None


    def joinRoom(self, roomCode=None):
        browser = self.driver
        browser.get("https://jklm.fun/"+roomCode)
        if roomCode == '':
            self.console.info('waiting for room selection')
            while True:
                try:
                    if WebDriverWait(browser, self.tickSpeed, ignored_exceptions=TimeoutException).until(EC.url_matches("^((https|http)\:\/\/jklm\.fun\/)[A-Z][A-Z][A-Z][A-Z]")):
                        
                        break
                except TimeoutException:
                    pass
        
        WebDriverWait(browser, self.maxWait)
        self.roomCode = browser.current_url.split('/',1)[1]

        textbox = self.locate((By.XPATH, '//input[@class = "styled nickname"]'), lmd = self.visibleCondition, delay=self.maxWait)

        submit = self.locate((By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button"), lmd = self.clickableCondition, delay=self.maxWait)
        
        textbox.send_keys(Keys.CONTROL + Keys.BACKSPACE)
        sleep(0.1)
        textbox.send_keys(self.username)
        submit.click()
        WebDriverWait(browser, self.maxWait)


    def updateIframe(self):
        browser = self.driver
        browser.switch_to.default_content()
        iFrame = self.locate((By.XPATH, "//iframe[contains(@src, 'bombparty')]"), lmd= self.presenceCondition,delay=self.tickSpeed)
        browser.switch_to.frame(iFrame)


    def join(self, delay):
        join = self.locate((By.XPATH, "//button[@class = 'styled joinRound']"), delay= delay, lmd = self.clickableCondition)
        if join:
            join.click()
        
    def updateLoop(self):
        browser = self.driver
        browser.switch_to.default_content()
        disconnected = self.locate((By.XPATH, '//div[@class = "disconnected page"]'), delay= self.tickSpeed, lmd = self.visibleCondition)
        if disconnected:
            browser.quit()
            return False
        self.updateIframe()
        
        lastRound = self.locate((By.XPATH, '//div[@class = "lastRound"]'), delay= self.tickSpeed, lmd = self.visibleCondition)
        if lastRound:
            self.join(self.maxWait)
            self.console.info('reloading dictionary')
            self.dicts = self.dicts+self.replace
            self.console.info(f'used {len(self.replace)} words out of {len(self.dicts)}')
            self.replace= []
        return True
            

    
    def botLoop(self):

        self.replace = []
        self.updateIframe()
        self.join(self.maxWait)
        while self.updateLoop():

            ans = None
            syllable = self.locate((By.XPATH, "//div[@class = 'syllable']"), delay=self.tickSpeed, lmd = self.visibleCondition)
            textbox = self.locate((By.XPATH, '//form//input[@maxlength = "30"]'), delay=self.tickSpeed, lmd = self.visibleCondition)
            if textbox and syllable:
                syllable = syllable.text
                self.console.info(f'found syllable: {syllable}')
                lst = self.findSuffix(syllable)

                if lst:
                    if self.selectMode == 'long':
                        ans = lst[len(lst)-1]
                    elif self.selectMode == "avg":
                        ans = lst[round((len(lst)-1)/2)]
                    elif self.selectMode == 'short':
                        ans = lst[0]
                if ans:
                    
                    self.console.info(f'found answer: {ans}')
                    if self.cyberbullying:
                        try:
                            textbox.send_keys(ans+Keys.ENTER) ##if you wanna get hackusated
                        except ElementNotInteractableException:
                            pass
                    else:
                        
                        self.simType(textbox, ans+Keys.ENTER)
                    
                    self.replace.append(ans)
                    self.dicts.remove(ans)
                else:
                    self.console.error("syllable not in dictionary !")
                    textbox.send_keys('/suicide'+Keys.ENTER)

    def simType(self, obj, txt):
        sleep(self.offset)
        txtArr = list(txt)
        for letter in txtArr:
            obj.send_keys(letter)
            sleep((random.randint(-10,10)*0.1)*self.randomness+self.typeDelay)
        




class BotManager():
    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dictUrls, roomCode = '', proxyFile = '', username = ''):
        
        self.console = logging.getLogger('MANAGER CONSOLE')
        self.console.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        fh = logging.FileHandler('BotManager.log')
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        self.console.addHandler(ch)

        self.dicts = self.loadDicts(dictUrls)
        self.roomCode = roomCode
        self.username = username
        self.proxy = None
        self.proxyList = self.loadFromFile(proxyFile)

        self.genUsername = lambda x, y: x+str(random.randint(1,9))+str(random.randint(0,9))*(y-1)


    def loadDicts(self, dictUrls):
        #use selenium for this?
        dicts = []
        for url in dictUrls:
            try:
                r = requests.get(url)
                soup = BeautifulSoup(r.content, 'html.parser')
                dicts += [*soup.get_text().lower().split()]
            except:
                pass
                return None
            
        dicts = list(set(dicts))

        return dicts

    def botInit(self):
        username = self.username

        if username == '':
            username = self.genUsername('Guest', 4)
            # username = self.genUsername('monkebotv5 #', 4)
        if self.proxy:
            addr, port, user, pswd = self.loadProxy(self.proxy)

            fProxy = f"https://{addr}:{port}"
            if user and pswd:
                fProxy = f"https://{user}:{pswd}@{addr}:{port}"

            bot = BPB(dicts=self.dicts, proxy=fProxy, username=username, roomCode=self.roomCode)
        else:
            bot = BPB(dicts=self.dicts, username=username, roomCode=self.roomCode)
        
        return bot
    
    
    def persistLoop(self):
        proxyNo = 0
        bot = None
        proxyList = self.proxyList
        retries = 0
        thresh = 2
        while proxyNo < len(proxyList):
            if not bot:
                if retries <= thresh:
                    self.proxy = proxyList[proxyNo]
                    bot = self.botInit()
                    try:
                        bot.botLoop()
                        bot = None
                        retries = 0
                        proxyNo+=1
                        
                    except Exception as s:
                        self.console.info(f'Exception {s} in Bot {bot.username}; retrying')
                        bot = None
                        retries += 1
                else:
                    retries = 0
                    proxyNo+=1    
        bot = None
        self.console.info('goodbye!')

    def loadFromFile(self, filename):
        if filename:
            try:
                with open(filename, 'r') as file:
                    proxyList = file.readlines()
                f = "\n".join([x for x in proxyList])
                ex = "(((25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|[1-9])\.){3}(25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|[1-9])|(\w*\.\w*\.\w*))\:(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d\d\d|[1-5]\d\d\d|[1-9]\d\d\d|[1-9]\d\d|[1-9]\d|[1-9])(\:.*\:.*)?"
                if re.match(ex,f):
                    self.console.info(f'proxies found {f}')
                    return proxyList
        
            except FileNotFoundError:
                self.console.error('cannot find proxy file; using localhost')
                return [None]
        self.console.info('no proxies provided; using localhost')
        return [None]
    
    def loadProxy(self, proxy):
        split = proxy.split(':')
        if len(split) == 4:
            return split[0], split[1], split[2], split[3]
        elif len(split) == 2:
            return split[0], split[1], None, None
        
if __name__ == "__main__" :

    # filename = None
    # filename = str(input("filename (of proxies): "))
    filename = 'proxies.txt'

    dictionaries = [
        "https://raw.githubusercontent.com/YoungsterGlenn/bpDictionaryStatistics/master/dictionary.txt",
        "https://norvig.com/ngrams/sowpods.txt", 
        "https://norvig.com/ngrams/enable1.txt",
        "https://pastebin.com/raw/UegdKLq8",
        "https://pastebin.com/raw/M6TZ8Uxy",
        ]
    link = str(input("paste code: ")).upper()
    name = str(input("username: "))


    # manager = BotManager(dictUrls=dictionaries, roomCode=link, username=name)
    manager = BotManager(dictUrls=dictionaries, roomCode=link, proxyFile=filename, username=name)
    manager.persistLoop()