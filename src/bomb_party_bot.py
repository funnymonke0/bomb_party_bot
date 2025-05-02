from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException,ElementNotInteractableException, StaleElementReferenceException, ElementClickInterceptedException, NoSuchFrameException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random, string
import re
from time import sleep
import logging



class BPB():
    def __init__(self, dicts, logger, proxy=None, settings = [
                        'selectMode:smart',
                        'cyberbullying:False',
                        'offset:0.6',
                        'rate:0.15',
                        'randomness:0.1',
                        'mistakes:True',
                        'frantic:True',
                        'dynamicPauses:True']):

        self.visibleCondition = lambda x: EC.visibility_of_element_located(x)
        self.instantVisibleCondition = lambda x: x.is_displayed()
        self.clickableCondition = lambda x: EC.element_to_be_clickable(x)
        self.presenceCondition = lambda x: EC.presence_of_element_located(x)
        
        self.proxy = proxy
        

        self.console = logger


        

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

        self.maxWait = 5
        
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

        self.dicts = dicts

    
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
            lst.sort(key= lambda x: len(x))

            return lst
        except IndexError:
            pass
            return None        
        

    def instantLocate(self, locator, lmd): #delayless is better for proxies
        browser = self.driver
        by, string = locator

        try:
            out = browser.find_elements(by, string)
            if out:
                out = out[0]
                if lmd(out):
                    return out
        except (ElementNotInteractableException,ElementClickInterceptedException, StaleElementReferenceException) as e:
            pass
        return None
    
    def locate(self, locator, lmd):
        browser = self.driver
        wait = WebDriverWait(browser, self.maxWait)
        try:
            return wait.until(lmd(locator))
    
        except TimeoutException:
            pass
        return None


    def joinRoom(self, roomCode, username = None):
        browser = self.driver
        browser.get("https://jklm.fun/"+roomCode)
        
        if username:
            textbox = self.locate((By.XPATH, '//input[@class = "styled nickname"]'), lmd = self.visibleCondition)
            textbox.send_keys(Keys.CONTROL + Keys.BACKSPACE)
            textbox.send_keys(username)

        submit = self.locate((By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button"), lmd = self.clickableCondition)
        submit.click()


    def switchIframe(self):
        browser = self.driver
        browser.switch_to.default_content()
        iFrame = self.instantLocate((By.XPATH, "//iframe[contains(@src, 'bombparty')]"), lmd= self.presenceCondition)
        if iFrame:
            try:
                browser.switch_to.frame(iFrame)
            except (NoSuchFrameException, ElementNotInteractableException,ElementClickInterceptedException, StaleElementReferenceException) as e:
                pass


    def checkDisconnect(self):
        if self.instantLocate((By.XPATH, '//div[@class = "reason"]'), lmd = self.instantVisibleCondition):
            return True
        return False
    
    def tryJoin(self):
        join = self.instantLocate((By.XPATH, "//button[@class = 'styled joinRound']"), lmd = self.clickableCondition)
        if join:
            try:
                join.click()
                return True
            except (ElementNotInteractableException,ElementClickInterceptedException, StaleElementReferenceException) as e:
                pass
        return False

    def recordPlayers(self):
        
        
        self.playerList = []
        table =  self.instantLocate((By.XPATH, '//table[@class = "statsTable"]'), lmd= self.presenceCondition)
        try:
            if table:
                entries = table.find_elements(By.XPATH, './/tr')
                if entries:
                    for player in entries:
                        self.playerList.append(player)
                        if player.get_attribute('class') == 'isDead':
                            self.playerList.remove(player)
        except (ElementNotInteractableException,ElementClickInterceptedException, StaleElementReferenceException) as e:
                pass


    def updateLoop(self):
        browser = self.driver
        browser.switch_to.default_content()
        if self.checkDisconnect():
            return False
        
        self.recordPlayers()

        self.switchIframe()

        if self.tryJoin():
            self.dicts = self.dicts+self.replace
            self.replace = []
        return True

    
    def botLoop(self):
        self.replace = []
        self.mult = 1
        self.frantic = False
        prevSyll = None
        lmb = None
        while self.updateLoop():
            textbox = self.instantLocate((By.XPATH, '//form//input[@maxlength = "30"]'), lmd = self.instantVisibleCondition)
            syllable = self.instantLocate((By.XPATH, "//div[@class = 'syllable']"), lmd = self.instantVisibleCondition)
            if textbox and syllable:
                try:
                    textbox.clear()
                    syllable = syllable.text
                    if prevSyll == syllable:
                        self.frantic = True

                    lst = self.findSuffix(syllable)
                    
                    if lst:
                        if self.selectMode == 'long':
                            ans = lst[len(lst)-1]
                        elif self.selectMode == 'short':
                            ans = lst[0]
                        elif self.selectMode == 'avg':
                            ans = lst[int((len(lst)-1)/2)]
                        elif self.selectMode == 'smart':
                            ans = lst[0]
                            if len(lst[len(lst)-1])>20:
                                ans = lst[len(lst)-1]
                                self.frantic = True

                        self.console.info(f"found answer {ans} to syllable {syllable}")
                        if self.dynamicPauses:
                            self.mult = len(lst)/len(self.dicts) #how frequent it is

                        if self.cyberbullying and len(self.playerList) == 3:##including table head
                            ans = lst[len(lst)-1]
                            lmb = lambda x: textbox.send_keys(x)##if you wanna get hackusated
                        else:
                            lmb = lambda x: self.simType(textbox, x)

                        lmb(ans+Keys.ENTER)

                        self.replace.append(ans)
                        self.dicts.remove(ans)
                        self.frantic = False
                        prevSyll = syllable
                    else:

                        self.console.info(f"Cannot find answer to syllable {syllable} !")
                        lmb("/suicide"+Keys.ENTER)

                except (ElementNotInteractableException,ElementClickInterceptedException, StaleElementReferenceException) as e:
                    pass


    def simType(self, obj, txt):
        
        if not self.frantic:
            w = self.maxOffset-(self.maxOffset*self.mult)
            if w > 0:
                sleep(w)
        
        ratesList = []
        rand = lambda x: x*(1+random.uniform(-1, 1)*self.randomness)
        for letter in txt:

            if self.frantic:
                ratesList.append(rand(self.burstRate))

            elif self.burstType and(random.random() <= self.burstChance):
                ratesList.append(rand(self.burstRate))

            else:
                ratesList.append(rand(self.rate))
            
            

        for letter, delay in list(zip(txt, ratesList)):
            if self.mistakes and (random.random() <= self.mistakeChance):
                obj.send_keys(random.choice(string.ascii_lowercase))
                sleep(rand(self.mistakePause))
                obj.send_keys(Keys.BACKSPACE)

            obj.send_keys(letter)
            sleep(delay)
        sleep(0.05)##hardcoded delay to prevent detection of the same syllable twice
    
    def __del__(self):
        self.driver.quit()
        
        self.console.info("POOF!")

    
            
class BotManager():

    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dictFile, roomCode, settingsFile, proxyFile, username = None):
        
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
        
        self.roomCode = roomCode
        self.username = username
        
        
        self.dicts = []
        
        settingsRegex = r"^\w+(\s*)\:(\s*)(\w+)(\.\w+)?"
        proxyRegex = r"^((\d{1,3}\.){3}(\d{1,3})|\w+\.\w+(\.\w+)?):(\d{1,5})(:.+:.+)?"
        plaintextRegex = r"^\w+(\-\w+)?$"
        urlRegex = r"^((https|http)\:\/\/)((\w+\.\w+\.\w+)|(\w+\.\w+))((\/.+)+)?"

        self.settings = self.parseFromFile(settingsFile, settingsRegex) 


        self.proxyList = self.parseFromFile(proxyFile, proxyRegex)

        self.console.info(f"loaded {len(self.proxyList)} proxies from {proxyFile}")
        
        dictUrls = self.parseFromFile(dictFile, urlRegex)

        if dictUrls:
            self.console.info(f"loading {len(dictUrls)} dictionaries from urls")
            self.dicts += self.loadUrls(dictUrls)

        
        dictPlainText = self.parseFromFile(dictFile, plaintextRegex)

        if dictPlainText:
            self.console.info(f"loading {len(dictPlainText)} entries from plaintext")
            self.dicts += dictPlainText

        self.dicts = list(set(self.dicts))

        self.console.info(f"loaded {len(self.dicts)} words from {dictFile}")

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
            content = browser.find_elements(By.XPATH, '//pre')[0]
            if content:
                dicts += content.text.lower().split('\n')

        return dicts

    def botInit(self, proxy = None):
        fProxy = None 

        if proxy:
            addr, port, user, pswd = self.parseProxy(proxy)

            fProxy = f"https://{addr}:{port}"
            if user and pswd:
                fProxy = f"https://{user}:{pswd}@{addr}:{port}"

        bot = BPB(dicts=self.dicts, proxy=fProxy, settings=self.settings, logger=self.botconsole)
        return bot
        
    
    
    def persistLoop(self):
        proxyNo = -1
        while proxyNo < len(self.proxyList):
            

            try:
                proxy = self.proxyList[proxyNo]
                bot = self.botInit(proxy)
                bot.joinRoom(roomCode=self.roomCode, username=self.username)
                bot.botLoop()
                self.console.info(f'Bot #{proxyNo} @ {proxy} disconnected successfully')
            except Exception as e:
                self.console.debug(f"Exception {e} in bot #{proxyNo} @ {proxy}")
            
            
            try:
                del bot
            except UnboundLocalError:
                pass
            sleep(5) #wait for garbage collector
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

    
    def parseProxy(self, proxy):
        split = proxy.split(':')
        if len(split) == 4:
            return split[0], split[1], split[2], split[3]
        elif len(split) == 2:
            return split[0], split[1], None, None
        
if __name__ == "__main__" :

    proxies = 'proxies.config'
    settings = 'settings.config'
    dictionaries = 'dictionaries.txt'
    link = str(input("paste code: ")).upper()
    name = str(input("username: "))

    if len(link) == '':
        print('ERROR: Must input valid oom code !')
        quit()
    if name == '':
        name = None

    manager = BotManager(dictFile=dictionaries, roomCode=link, proxyFile=proxies, username=name, settingsFile=settings)
    manager.persistLoop()