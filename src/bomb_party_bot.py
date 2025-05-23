from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException,ElementNotInteractableException, StaleElementReferenceException, ElementClickInterceptedException, NoSuchFrameException, NoSuchElementException, InvalidElementStateException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random, string
import re
from time import sleep
import logging



class BPB():
    def __init__(self, dicts, logger, settings, proxy=None):

        self.console = logger
        self.dicts = dicts
        self.proxy = proxy

        self.initDriver()

        self.visibleCondition = lambda x: x.is_displayed()
        self.clickableCondition = lambda x: x.is_displayed() and x.is_enabled()
        self.presenceCondition = lambda x: EC.presence_of_element_located(x)
        self.maxWait = 15

        


        self.ignoredExceptions = (AttributeError,TimeoutError, NoSuchFrameException, InvalidElementStateException, ElementNotInteractableException,ElementClickInterceptedException, StaleElementReferenceException,NoSuchElementException, NoSuchFrameException)

        
        
        self.settings = self.parseSettings(settings)

        self.selectMode = self.settings['selectMode']
        self.cyberbullying = self.settings['cyberbullying']
        self.maxOffset = self.settings['maxOffset']
        self.rate = self.settings['rate']
        self.burstType = self.settings['burstType']
        self.burstRate = self.settings['burstRate']
        self.burstChance = self.settings['burstChance']
        self.randomness = self.settings['randomness']
        self.mistakes = self.settings['mistakes']
        self.mistakeChance = self.settings['mistakeChance']
        self.mistakePause = self.settings['mistakePause']
        self.franticType = self.settings['franticType']
        self.dynamicPauses = self.settings['dynamicPauses']
        self.spam = self.settings['spam']
        self.spamRate = self.settings['spamRate']
        self.miniPause = self.settings['miniPause']
    
    def initDriver(self):
        chrome_options = ChromeOptions()
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

    def parseSettings(self, settings):
        settingsDict={}
        for line in settings:
            key, value = line.split(':', 1)
            if value.lower() == 'true':
                settingsDict[key] = True
            elif value.lower() == 'false':
                settingsDict[key] = False
            else:
                try:
                    settingsDict[key] = float(value)
                except ValueError:
                    settingsDict[key] = value
                    pass
        return settingsDict
            
    
    def findSuffix(self, suffix):
        lst = []
        try:
            for wrd in self.dicts:
                if suffix.lower() in wrd.lower():
                    lst.append(wrd)
            if lst:
                lst.sort(key= lambda x: len(x))
                return lst
        except IndexError:
            pass
        return None        
        

    def locate(self, locator, lmd, switch = True, obj = None, all = False): #delayless is better
        browser = self.driver
        if obj:
            browser = obj
        by, string = locator
        if switch:
            self.updateFrame()

        try:
            out = browser.find_elements(by, string)
            if out:
                if not all:
                    out = out[0]
                    if lmd(out):
                        return out
                else:
                    return out
        except self.ignoredExceptions:
            pass
        return None
    

    def joinRoom(self, roomCode, username = None):
        browser = self.driver
        browser.get("https://jklm.fun/"+roomCode)
        try:
            if username:
                textbox = WebDriverWait(browser,self.maxWait).until(EC.visibility_of_element_located((By.XPATH, '//input[@class = "styled nickname"]')))

                textbox.send_keys(Keys.CONTROL + Keys.BACKSPACE)
                sleep(0.1)
                textbox.send_keys(username)

            submit = WebDriverWait(browser,self.maxWait).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button")))
            submit.click()
            WebDriverWait(browser,self.maxWait)
        except self.ignoredExceptions:
            pass


    def checkDisconnect(self):
        browser = self.driver
        browser.switch_to.default_content()
        if self.locate((By.XPATH, '//div[@class = "disconnected page"]'), lmd = self.visibleCondition, switch=False):
            return True
        return False
    
    def tryJoin(self):
        join = self.locate((By.XPATH, "//button[@class = 'styled joinRound']"), lmd = self.clickableCondition)
        if join:
            try:
                join.click()
                return True
            except self.ignoredExceptions:
                pass
        return False

    def recordPlayers(self):
        
        browser = self.driver
        browser.switch_to.default_content()
        self.playerList = []
        table = self.locate((By.XPATH, '//table[@class = "statsTable"]'),lmd=self.presenceCondition,switch=False)
        if table:
            entries = self.locate((By.XPATH, './/tr'), self.presenceCondition, switch=False, obj=table, all=True) 
            if entries:
                for player in entries:
                    try:
                        self.playerList.append(player)
                        if player.get_attribute('class') == 'isDead':
                            self.playerList.remove(player)
                    except self.ignoredExceptions:
                        self.console.debug("did not find attribute 'isDead' in player")
                        continue


    def updateFrame(self):
        browser = self.driver
        browser.switch_to.default_content()
        frame = self.locate((By.XPATH, "//iframe[contains(@src, 'bombparty')]"), lmd= self.presenceCondition, switch=False)
        if frame:
            try:
                browser.switch_to.frame(frame)
            except self.ignoredExceptions:
                self.console.debug("unable to switch to iframe")
                pass

    def updateLoop(self):
        if self.checkDisconnect():
            return False
        
        self.recordPlayers()

        if self.tryJoin():
            self.dicts = self.dicts+self.replace
            self.replace = []
        return True

    
    def botLoop(self):
        self.replace = []
        self.mult = 1
        self.frantic = False
        self.spamToggle = False
        prevSyll = None
        lmb = None
        while self.updateLoop():
            textbox = self.locate((By.XPATH, '//form//input[@maxlength = "30"]'), lmd = self.clickableCondition)
            syllable = self.locate((By.XPATH, "//div[@class = 'syllable']"), lmd = self.visibleCondition)

            if textbox and syllable:
                try:
                    textbox.clear()
                    syllable = syllable.text

                    if prevSyll == syllable:
                        self.frantic = True

                    lst = self.findSuffix(syllable)
                    
                    
                    ans = "/suicide"
                    if lst:
                        if self.selectMode == 'long' or (self.selectMode == 'smart' and len(lst[len(lst)-1])>20):
                            ans = lst[len(lst)-1]
                            self.frantic = True
                            self.spamToggle = True
                        elif self.selectMode == 'short' or self.selectMode == 'smart':
                            ans = lst[0]
                        elif self.selectMode == 'avg':
                            ans = lst[int((len(lst)-1)/2)]
    

                        if self.dynamicPauses:
                            self.mult = len(lst)/len(self.dicts) #how frequent it is
                        self.replace.append(ans)
                        self.dicts.remove(ans)
                        self.console.info(f"found answer {ans} to syllable {syllable}")

                    lmb = lambda x: self.simType(textbox, x)

                    if self.cyberbullying and len(self.playerList) == 3:##including table head
                        lmb = lambda x: textbox.send_keys(x)##if you wanna get hackusated

                    lmb(ans+Keys.ENTER)
                    sleep(0.1)
                    
                    self.frantic = False
                    self.spamToggle = False
                    prevSyll = syllable
                except self.ignoredExceptions as e:
                    pass

    def simType(self, obj, txt):
        
        ratesList = []
        rand = lambda x: x*(1+random.uniform(-1, 1)*self.randomness)
        
        

        for letter in txt:
            if self.mistakes and (random.uniform(0, 1) <= self.mistakeChance):
                txt += random.choice(string.ascii_lowercase)
                ratesList.append(rand(self.mistakePause))
                txt += Keys.BACKSPACE
                ratesList.append(0)

            if self.franticType and self.frantic:
                ratesList.append(rand(self.burstRate))

            elif self.burstType and(random.random() <= self.burstChance):
                ratesList.append(rand(self.burstRate))
            else:
                ratesList.append(rand(self.rate))
                

        if self.spam and self.spamToggle:
            length = random.randint(10,21)
            spam = ''.join([random.choice(string.ascii_lowercase) for i in range(0,length)])
            rates = [rand(self.spamRate) for i in range(0,length)]
            txt = ''+spam+Keys.ENTER+''+txt
            ratesList = [self.miniPause]+rates+[0]+[self.miniPause]+ratesList
        else:
            wait = self.maxOffset-(self.maxOffset*self.mult)
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
        self.loadAll()
        

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

    def loadAll(self):
        self.dicts = []
        
        settingsRegex = r"^\w+(\s*)\:(\s*)(\w+)(\.\w+)?"
        proxyRegex = r"^((\d{1,3}\.){3}(\d{1,3})|\w+\.\w+(\.\w+)?):(\d{1,5})(:.+:.+)?"
        plaintextRegex = r"^\w+(\-\w+)?$"
        urlRegex = r"^((https|http)\:\/\/)((\w+\.\w+\.\w+)|(\w+\.\w+))((\/.+)+)?"

        self.settings = self.parseFromFile(self.settingsFile, settingsRegex) 

        self.proxyList = self.parseFromFile(self.proxyFile, proxyRegex)

        self.console.info(f"loaded {len(self.proxyList)} proxies from {self.proxyFile}")
        
        dictUrls = self.parseFromFile(self.dictFile, urlRegex)

        if dictUrls:
            self.console.info(f"loading {len(dictUrls)} dictionaries from urls")
            self.dicts += self.loadUrls(dictUrls)

        
        dictPlainText = [x.lower() for x in self.parseFromFile(self.dictFile, plaintextRegex)]

        if dictPlainText:
            self.console.info(f"loading {len(dictPlainText)} entries from plaintext")
            self.dicts += dictPlainText

        self.dicts = list(set(self.dicts))

        self.console.info(f"loaded {len(self.dicts)} words from {self.dictFile}")

        if not self.proxyList:
            self.proxyList = [None]
        if not self.username:
            self.username = None


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
                self.console.info(f'Cannot get url {url} because of Exception {e}')
                pass
            content = browser.find_element(By.XPATH, '//pre')
            if content:
                dicts += content.text.lower().split('\n')

        return dicts

    def botInit(self, proxy = None):

        if proxy:
            proxy = self.formatProxy(proxy)

        bot = BPB(dicts=self.dicts, proxy=proxy, settings=self.settings, logger=self.botconsole)
        return bot
        
    
    
    def persistLoop(self):
        proxyNo = 0


        thresh = 2
        retries = 0
        while proxyNo < len(self.proxyList):

            retries = 0
            while not retries > thresh:
                try:
                    bot = self.botInit(self.proxyList[proxyNo])
                    bot.joinRoom(roomCode=self.roomCode, username=self.username)
                    bot.botLoop()
                    self.console.info(f'Bot #{proxyNo} @ {self.proxyList[proxyNo]} disconnected successfully')
                    retries = 0
                except Exception as e:
                    self.console.debug(f"Exception {e} in bot #{proxyNo} @ {self.proxyList[proxyNo]}")
                retries += 1
            
            
            proxyNo+=1
            
        self.console.info('goodbye!')
        
    def parseFromFile(self, filename, ex):

        lst = []
        try:
            with open(filename, 'r') as file:
                out = file.readlines()
            
            for x in out:
                if re.match(ex,x):
                    lst.append(re.sub(r"\s+", "", x))
            return lst
    
        except FileNotFoundError:
            pass
            self.console.error(f'cannot find file {filename} !')
        return None

    
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
            self.console.error("proxy format not recognized!")
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
    manager.persistLoop()