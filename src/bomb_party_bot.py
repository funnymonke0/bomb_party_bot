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
    def __init__(self, dicts, username, roomCode, proxy=None, settings = [
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
        

        self.username = username
        
        if self.username:
            self.console = logging.getLogger(f'{self.username} CONSOLE')
        else:
            self.console = logging.getLogger(f'BOT CONSOLE')

        self.console.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        self.console.addHandler(ch)


        

        chrome_options = ChromeOptions()
        service = ChromeService()
        seleniumwire_options = {
            }


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

        if self.username:
            self.console.info(f'initialized bot {self.username} running @ {proxy}')
        else:
            self.console.info(f'initialized bot running @ {proxy}')

        ##settings
        self.maxWait = 5

        #burst typing - randomly type fast
        #random letter delete letter to simulate mistakes and also mistake rate
        #if its your turn in quick succession, increase typing speed
        #if there are fewer answers to a syllable or if the answer is long, type slower or pause before typing

        
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

        self.joinedRoom = self.joinRoom(roomCode)
    
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
                except:
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
    
        out = browser.find_elements(by, string)
        if out:
            out = out[0]
            if lmd(out):
                return out
        return None
    
    def locate(self, locator, lmd):
        browser = self.driver
        wait = WebDriverWait(browser, self.maxWait)
        try:
            return wait.until(lmd(locator))
    
        except TimeoutException:
            pass
        return None


    def joinRoom(self, roomCode):
        browser = self.driver
        browser.get("https://jklm.fun/"+roomCode)
        
        if self.username:
            textbox = self.locate((By.XPATH, '//input[@class = "styled nickname"]'), lmd = self.visibleCondition)
            textbox.send_keys(Keys.CONTROL + Keys.BACKSPACE)
            textbox.send_keys(self.username)

        submit = self.locate((By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button"), lmd = self.clickableCondition)
        submit.click()


    def updateIframe(self):
        browser = self.driver
        browser.switch_to.default_content()
        iFrame = self.instantLocate((By.XPATH, "//iframe[contains(@src, 'bombparty')]"), lmd= self.presenceCondition)
        if iFrame:
            try:
                browser.switch_to.frame(iFrame)
            except NoSuchFrameException:
                pass


    def checkDisconnect(self):
        browser = self.driver
        browser.switch_to.default_content()
        disconnected = self.instantLocate((By.XPATH, '//div[@class = "reason"]'), lmd = self.instantVisibleCondition)
        if disconnected:
            browser.quit()
            return True
        return False
    
    def tryJoin(self):
        join = self.instantLocate((By.XPATH, "//button[@class = 'styled joinRound']"), lmd = self.clickableCondition)
        if join:
            try:
                join.click()
                return True
            except (ElementNotInteractableException,ElementClickInterceptedException, StaleElementReferenceException):
                pass
        return False

    def recordPlayers(self):
        browser = self.driver
        browser.switch_to.default_content()
        self.playerList = []
        table =  self.instantLocate((By.XPATH, '//table[@class = "statsTable"]'), lmd= self.presenceCondition)
        if table:
            try:
                for player in table.find_elements(By.XPATH, './/tr'):
                    self.playerList.append(player)
                    try:
                        if player.get_attribute('class') == 'isDead':
                            self.playerList.remove(player)
                    except:
                        pass
            except:
                pass


    def updateLoop(self):
        if self.checkDisconnect():
            return False
        
        self.recordPlayers()

        self.updateIframe()


        if self.tryJoin():
            self.dicts = self.dicts+self.replace
            self.replace = []
        return True

    
    def botLoop(self):
        self.replace = []
        self.mult = 1
        self.frantic = False
        prevSyll = None
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
                        elif self.selectMode == 'smart':
                            ans = lst[0]
                            if len(lst[len(lst)-1])>20:
                                ans = lst[len(lst)-1]
                                self.frantic = True
                        
                        if self.dynamicPauses:
                            self.mult = len(lst)/len(self.dicts) #how frequent it is

                        if self.cyberbullying and len(self.playerList) == 3:##including table head
                            textbox.send_keys(ans+Keys.ENTER)##if you wanna get hackusated
                        else:
                            self.simType(textbox, ans+Keys.ENTER)
                            
                        self.replace.append(ans)
                        self.dicts.remove(ans)
                        self.frantic = False
                        prevSyll = syllable
                    else:
                        
                        if self.cyberbullying:
                            textbox.send_keys("/suicide"+Keys.ENTER)
                        else:
                            self.simType(textbox, "/suicide"+Keys.ENTER)

                except Exception as s:
                    pass


    def simType(self, obj, txt):
        txtArr = list(txt)
        
        defaultRate = self.rate
        mistake = False
        if self.frantic:
            defaultRate = self.burstRate
        else:
            w = self.maxOffset-self.maxOffset*self.mult
            if w > 0:
                sleep(w)
        
        for letter in txtArr:
            
            rate = defaultRate

            if self.burstType:
                burst = (random.random() <= self.burstChance)
                if burst:
                    rate = self.burstRate

            if self.mistakes:
                mistake = (random.random() <= self.mistakeChance)

            if mistake:
                obj.send_keys(random.choice(string.ascii_lowercase))
                w = self.mistakePause + random.uniform(-1, 1)*self.randomness*self.mistakePause
                sleep(w)
                obj.send_keys(Keys.BACKSPACE)

            obj.send_keys(letter)
            w = rate + random.uniform(-1, 1)*self.randomness*rate
            sleep(w)
                
            
class BotManager():

    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dictFile, roomCode, settingsFile, proxyFile, username = None):
        
        self.console = logging.getLogger('MANAGER CONSOLE')
        self.console.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        fh = logging.FileHandler('BotManager.log')
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        self.console.addHandler(ch)
        self.console.addHandler(fh)
        
        self.roomCode = roomCode
        self.username = username
        
        self.dicts = []
        
        settingsRegex = r"^\w+(\s*)\:(\s*)(\w+)(\.\w+)?"
        proxyRegex = r"(((25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|[1-9])\.){3}(25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|[1-9])|(\w+\.\w+\.\w+))\:(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d\d\d|[1-5]\d\d\d|[1-9]\d\d\d|[1-9]\d\d|[1-9]\d|[1-9])(\:.+\:.+)?"
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
            except:
                self.console.info(f'Cannot get url {url}')
                pass
            content = browser.find_elements(By.XPATH, '//pre')[0]
            if content:
                dicts += content.text.lower().split('\n')

        return dicts

    def botInit(self):
        fProxy = None 
        username = self.username

        if self.proxy:
            addr, port, user, pswd = self.parseProxy(self.proxy)

            fProxy = f"https://{addr}:{port}"
            if user and pswd:
                fProxy = f"https://{user}:{pswd}@{addr}:{port}"

        bot = BPB(dicts=self.dicts, proxy=fProxy, username=username, roomCode=self.roomCode, settings=self.settings)
        return bot
        
    
    
    def persistLoop(self):
        proxyNo = 0
        bot = None
        proxyList = self.proxyList
        if not proxyList:
            proxyList = [None]
        retries = 0
        thresh = 2
        while proxyNo < len(proxyList):
            if not bot:
                if retries <= thresh:
                    self.proxy = proxyList[proxyNo]
                    bot = self.botInit()
                    try:
                        bot.botLoop()
                        self.console.info(f'Bot disconnected successfully')
                        bot = None
                        retries = 0
                        proxyNo+=1
                        
                    except Exception as s:
                        self.console.info(f'Exception {s} in Bot; retrying with proxy {self.proxy}')
                        retries += 1
                else:
                    self.console.info(f'reached maximum retry limit for proxy {self.proxy}')
                    bot = None
                    retries = 0
                    proxyNo+=1    
        bot = None
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

    if link == '':
        print('ERROR: Must input room code !')
        quit()
    if name == '':
        name = None

    manager = BotManager(dictFile=dictionaries, roomCode=link, proxyFile=proxies, username=name, settingsFile=settings)
    manager.persistLoop()