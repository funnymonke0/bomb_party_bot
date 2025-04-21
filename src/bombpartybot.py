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
    def __init__(self, dicts, username, roomCode=None, proxy=None):

        self.visibleCondition = lambda x: EC.visibility_of_element_located(x)
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
        # self.selectMode = 'long'
        self.selectMode = 'short'
        # self.selectMode = 'smart'

        #burst typing - randomly type fast
        #random letter delete letter to simulate mistakes and also mistake rate
        #if its your turn in quick succession, increase typing speed
        #if there are fewer answers to a syllable or if the answer is long, type slower or pause before typing

        
        self.settings = { #eventually have this in a config file as well and be passed by manager to the bot
            'selectMode' :'smart',
            'cyberbullying' : False,
            'offset' : 0.6,
            'rate': 0.12,
            'randomness' : 0.07,
            'mistakes' : True,
            'frantic' : True,
            'dynamicPauses' : True}
        
        self.cyberbullying = False
        # self.cyberbullying = True
        self.offset = 0.6

        self.rate = 0.15
        self.randomness = 0.1

        self.tickSpeed = 0.005 #const for the most part; determines polling speed

        self.dicts = dicts

        self.joinedRoom = self.joinRoom(roomCode)
    
    
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
        

    def locate(self, locator, lmd, delay = 0):
        browser = self.driver

        wait = WebDriverWait(browser, delay+self.tickSpeed, poll_frequency=self.tickSpeed) #always at least 1 check
        try:
            out = wait.until(lmd(locator))
            return out

        except TimeoutException:
            pass
        return None


    def joinRoom(self, roomCode):
        browser = self.driver
        browser.get("https://jklm.fun/"+roomCode)

        if not roomCode:
            self.console.info('waiting for room selection')
            while True:
                try:
                    if WebDriverWait(browser, self.tickSpeed).until(EC.url_matches("^((https|http)\:\/\/jklm\.fun\/)[A-Z][A-Z][A-Z][A-Z]")):
                        break
                except TimeoutException:
                    pass
        
        WebDriverWait(browser, self.maxWait)
        
        if self.username:
            textbox = self.locate((By.XPATH, '//input[@class = "styled nickname"]'), lmd = self.visibleCondition, delay=self.maxWait)
            textbox.send_keys(Keys.CONTROL + Keys.BACKSPACE)
            textbox.send_keys(self.username)

        submit = self.locate((By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button"), lmd = self.clickableCondition, delay=self.maxWait)
        submit.click()
        WebDriverWait(browser, self.maxWait)


    def updateIframe(self):
        browser = self.driver
        browser.switch_to.default_content()
        iFrame = self.locate((By.XPATH, "//iframe[contains(@src, 'bombparty')]"), lmd= self.presenceCondition)
        try:
            browser.switch_to.frame(iFrame)
        except:
            pass


    def checkDisconnect(self):
        browser = self.driver
        disconnected = self.locate((By.XPATH, '//div[@class = "disconnected page"]'), lmd = self.visibleCondition)
        if disconnected:
            browser.quit()
            return True
        return False
    
    def checkJoin(self):
        join = self.locate((By.XPATH, "//button[@class = 'styled joinRound']"), lmd = self.clickableCondition)
        try:
            join.click()
            self.dicts = self.dicts+self.replace
            self.replace= []
        except:
            pass

        
    def updateLoop(self):
        browser = self.driver
        browser.switch_to.default_content()
        if self.checkDisconnect():
            return False
        self.updateIframe()
        self.checkJoin()
        return True

    
    def botLoop(self):

        self.replace = []

        while self.updateLoop():

            

                try:
                    textbox = self.locate((By.XPATH, '//form//input[@maxlength = "30"]'), lmd = self.visibleCondition)
                    syllable = self.locate((By.XPATH, "//div[@class = 'syllable']"), lmd = self.visibleCondition)
                    syllable = syllable.text## unfortunately can end up choosing the previous person's syllable because the webpage does not update as fast :/
                    
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

                        if self.cyberbullying:
                            textbox.send_keys(ans)
                            textbox.send_keys(Keys.ENTER) ##if you wanna get hackusated
                        else:
                            self.simType(textbox, ans)
                            textbox.send_keys(Keys.ENTER)
                        
                        self.replace.append(ans)
                        self.dicts.remove(ans)
                    else:
                        self.console.error(f"syllable {syllable} not in dictionary !")
                        textbox.send_keys('/suicide')
                        textbox.send_keys(Keys.ENTER)
                except:
                    pass



    def simType(self, obj, txt):
        sleep(self.offset)
        txtArr = list(txt)
        for letter in txtArr:
            obj.send_keys(letter)
            sleep((random.randint(-10,10)*0.1)*self.randomness+self.rate)
        




class BotManager():

    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dictFile, roomCode = None, proxyFile = None, username = None):
        
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
        self.proxy = None
        self.proxyList = [None]
        self.dicts = []
        
        
        proxyRegex = "(((25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|[1-9])\.){3}(25[0-5]|2[0-4]\d|1\d\d|[1-9]\d|[1-9])|(\w*\.\w*\.\w*))\:(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d\d\d|[1-5]\d\d\d|[1-9]\d\d\d|[1-9]\d\d|[1-9]\d|[1-9])(\:.*\:.*)?"
        if proxyFile:
            self.proxyList = self.loadFromFile(proxyFile, proxyRegex)
            self.console.info(f"loaded {len(self.proxyList)} proxies from {proxyFile}")

        dictUrls = self.loadFromFile(dictFile, "^((https|http)\:\/\/)((\w*\.\w*\.\w*)|(\w*\.\w*))((\/\w*(\.\w*)?)*)?")

        if dictUrls:
            self.console.info(f"loading {len(dictUrls)} dictionaries from urls")
            self.dicts += self.loadUrls(dictUrls)

        dictPlainText = self.loadFromFile(dictFile, "^\w*$")
        if dictPlainText:
            self.console.info("loading dicts from plaintext")
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
                content = browser.find_element(By.XPATH, '//pre').text.lower()
                dicts += content.split('\n')
            except:
                self.console.info(f'Cannot get url {url}')
                pass

        return dicts

    def botInit(self):
        fProxy = None 
        username = self.username

        if self.proxy:
            addr, port, user, pswd = self.loadProxy(self.proxy)

            fProxy = f"https://{addr}:{port}"
            if user and pswd:
                fProxy = f"https://{user}:{pswd}@{addr}:{port}"

        bot = BPB(dicts=self.dicts, proxy=fProxy, username=username, roomCode=self.roomCode)
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
                        self.console.info(f'Bot disconnected successfully')
                        bot = None
                        retries = 0
                        proxyNo+=1
                        
                    except Exception as s:
                        self.console.info(f'Exception {s} in Bot; retrying with proxy {self.proxy}')
                        bot = None
                        retries += 1
                else:
                    self.console.info(f'reached maximum retry limit for proxy {self.proxy}')
                    bot = None
                    retries = 0
                    proxyNo+=1    
        bot = None
        self.console.info('goodbye!')

    def loadFromFile(self, filename, ex):

        lst = []
        try:
            with open(filename, 'r') as file:
                out = file.readlines()
            for x in out:
                if re.match(ex,x):
                    lst.append(x)
            return lst
    
        except FileNotFoundError:
            pass
            self.console.error(f'cannot find file {filename}!')
            return None

    
    def loadProxy(self, proxy):
        split = proxy.split(':')
        if len(split) == 4:
            return split[0], split[1], split[2], split[3]
        elif len(split) == 2:
            return split[0], split[1], None, None

##TO-DO: change these setting to be stored in a config file    
if __name__ == "__main__" :

    # filename = None
    # filename = str(input("filename (of proxies): "))
    # proxies = None
    proxies = 'proxies.config'
    # dictionaries = str(input("filename (of dictionaries): "))
    dictionaries = 'dictionaries.txt'
    link = str(input("paste code: ")).upper()
    name = str(input("username: "))

    if proxies == '':
        proxies = None
    if dictionaries == '':
        dictionaries = None
    if link == '':
        link = None
    if name == '':
        name = None

    manager = BotManager(dictFile=dictionaries, roomCode=link, proxyFile=proxies, username=name)
    manager.persistLoop()