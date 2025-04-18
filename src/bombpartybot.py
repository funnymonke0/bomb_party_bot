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
        # self.selectMode = 'long'
        self.selectMode = 'short'
        # self.selectMode = 'avg'

        # self.cyberbullying = True

        self.cyberbullying = False
        self.offset = 0.6

        self.typeDelay = 0.12
        self.randomness = 0.07

        self.tickSpeed = 0

        self.ref = dicts
        self.dicts = dicts

        self.joinedRoom = self.joinRoom(roomCode)

    

    def procTerminated(self, message = '', verbose = True, pid = '', ret = False):
        if verbose:
            self.console.error(f'Error {message} occured in method {pid}.')
        return ret
    

    def procSuccess(self, message = '', verbose = False, pid = '', ret = True):
        if verbose:
            self.console.info(f'method {pid} completed {message} sucessfully.')
        return ret


    def findSuffix(self, suffix):
        lst = []
        try:
            for wrd in self.dicts:
                if suffix.lower() in wrd:
                    lst.append(wrd)
            lst.sort(key= lambda x: len(x))
            return self.procSuccess(ret=lst)
        except IndexError:
            pass
            return self.procTerminated(message='could not find suffix !', ret=None)
        
    
    
    def waitForLoad(self):
        browser = self.driver
        try:
            WebDriverWait(browser, 10)
            return self.procSuccess()   
        except TimeoutException:
            pass
            return self.procTerminated("page took too long to load.")
         
    

    def locate(self, locator, lmd, name = 'element', delay = 5, verbose = False):
        browser = self.driver

        wait = WebDriverWait(browser, delay, poll_frequency=self.tickSpeed)
        try:
            out = wait.until(lmd(locator))
            return self.procSuccess(pid= 'locate', message=f'find {name}', ret=out, verbose=verbose)
        except TimeoutException:
            pass
            return self.procTerminated(f"could not find element {name} !", pid= 'locate', verbose=verbose)


    def joinRoom(self, roomCode):
        browser = self.driver
        try:
            browser.get("https://jklm.fun/"+roomCode)
        except ConnectionError:
            pass
            return self.procTerminated(pid = 'joinRoom', message='unable to join room !')
            
        if roomCode == '':
            self.console.info('waiting for room selection')
            while True:
                try:
                    if WebDriverWait(browser, self.tickSpeed, ignored_exceptions=TimeoutException).until(EC.url_matches("^((https|http)\:\/\/jklm\.fun\/)[A-Z][A-Z][A-Z][A-Z]")):
                        break
                except:
                    pass

        if not self.waitForLoad():
            return self.procTerminated(pid = 'joinRoom')
        
        textbox = self.locate((By.XPATH, '//input[@class = "styled nickname"]'), name = 'nickname textbox', lmd = self.visibleCondition, verbose=True)
        if not textbox:
            return self.procTerminated(pid = 'joinRoom', message='unable to find nickname box !')

        submit = self.locate((By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button"), name = 'name submit button', lmd = self.clickableCondition, verbose=True)
        if not submit:
            return self.procTerminated(pid = 'joinRoom', message='unable to find ok button !')
        
        textbox.send_keys(Keys.CONTROL + Keys.BACKSPACE)
        sleep(0.1)
        textbox.send_keys(self.username)
        submit.click()

        if not self.waitForLoad():
            return self.procTerminated(pid = 'joinRoom')
        
        return self.procSuccess(pid='joinRoom')

    def updateIframe(self):
        browser = self.driver
        browser.switch_to.default_content()
        iFrame = self.locate((By.XPATH, "//iframe[contains(@src, 'bombparty')]"), name = 'game iframe',lmd= self.presenceCondition)
        if iFrame:

            browser.switch_to.frame(iFrame)
            return self.procSuccess(pid = 'updateIframe')
        return self.procTerminated(pid = 'updateIframe', message= 'unable to update game frame !')

    def join(self, sensitive = False):

        delay = self.tickSpeed
        if sensitive:
            delay = 5
        join = self.locate((By.XPATH, "//button[@class = 'styled joinRound']"), name='join button',delay= delay, lmd = self.clickableCondition, verbose=sensitive)
        if join:
            join.click()
            return self.procSuccess(pid='join')

        autojoin = self.locate((By.XPATH, "//button[@class = 'autojoinButton styled']"), name='autojoin button',delay=delay, lmd = self.clickableCondition, verbose=sensitive)
        if autojoin:
            autojoin.click()
            return self.procSuccess(pid='join')
        

        return self.procTerminated(pid='join', message='could not join round !', verbose=sensitive)

    
        
    def updateLoop(self):
        browser = self.driver
        browser.switch_to.default_content()
        disconnected = self.locate((By.XPATH, '//div[@class = "disconnected page"]'), name = 'disconnected page', delay= self.tickSpeed, lmd = self.visibleCondition)
        if disconnected:
            return self.procTerminated(pid = 'updateLoop', message = 'disconnected from room !')
        if not self.updateIframe():
            return self.procTerminated(pid='updateLoop')
        lastRound = self.locate((By.XPATH, '//div[@class = "lastRound"]'), name = 'last round', delay= self.tickSpeed, lmd = self.visibleCondition)
        if lastRound:
            self.join()
            self.console.info(f'used {len(self.ref)-len(self.dicts)} words out of {len(self.ref)}')
            self.console.info('reloading dictionary')
            self.dicts = self.ref
            
        return self.procSuccess(pid='updateLoop')
    
    def botLoop(self):

        if not self.joinedRoom:
            return self.procTerminated("must first join a room !", pid = 'botLoop')
        if not self.dicts:
            return self.procTerminated("must first load dicts !", pid = 'botLoop')
        
        if not self.updateIframe():
            return self.procTerminated(pid = 'botLoop')
        if not self.join(sensitive=True):
            return self.procTerminated(pid = 'botLoop')    

        while True:
            if not self.updateLoop():
                self.console.info("failed to complete update loop ! gracefully terminating...")
                return self.procSuccess(pid='botLoop')

            ans = None
            
            syllable = self.locate((By.XPATH, "//div[@class = 'syllable']"), name ='active syllable', delay=self.tickSpeed, lmd = self.visibleCondition)
            if syllable:  
                syllable = syllable.text
                
                lst = self.findSuffix(syllable)

                if lst:
                    if self.selectMode == 'long':
                        ans = lst[len(lst)-1]
                    elif self.selectMode == "avg":
                        ans = lst[round((len(lst)-1)/2)]
                    elif self.selectMode == 'short':
                        ans = lst[0]

            textbox = self.locate((By.XPATH, '//form//input[@maxlength = "30"]'), name = 'game input', delay=self.tickSpeed, lmd = self.visibleCondition)
            if textbox:
                if ans:
                    self.console.info(f'found syllable: {syllable}')
                    self.console.info(f'found answer: {ans}')
                    if self.cyberbullying:
                        try:
                            textbox.send_keys(ans) ##if you wanna get hackusated
                            textbox.send_keys(Keys.ENTER)
                        except:
                            pass
                    else:
                        sleep(self.offset)
                        self.simType(textbox, ans)
                        textbox.send_keys(Keys.ENTER)
                    
                    self.dicts.remove(ans)
                else:
                    self.console.error("syllable not in dictionary !")
                    textbox.send_keys('/suicide'+Keys.ENTER)
            else:
                self.console.info('waiting for turn...')

    def simType(self, obj, txt):
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

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        self.console.addHandler(ch)

        self.dicts = self.loadDicts(dictUrls)
        self.roomCode = roomCode
        self.username = username
        self.proxy = None
        self.proxyList = self.loadFromFile(proxyFile)

        self.genUsername = lambda x, y: x+str(random.randint(0,int('9'*y)))


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
            # username = self.genUsername('monkebotv4 #', 4)
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

        while proxyNo < len(proxyList):
            if not bot:
                self.proxy = proxyList[proxyNo]
                bot = self.botInit()
                if bot.botLoop():
                    self.console.info('internal bot error occurred; bot terminated gracefully')
                else:
                    self.console.error('Something went wrong.')
                proxyNo+=1
                bot = None

        self.console.info('goodbye!')

    def loadFromFile(self, filename):
        if filename:
            try:
                with open(filename, 'r') as file:
                    proxyList = file.readlines()
                f = "\n".join([x for x in proxyList])
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
        else:
            raise Exception().add_note('cannot use loadProxy in this context; possible format error in proxy list')
        
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
    # link = "nfue" hardcoded test room
    name = str(input("username: "))


    # manager = BotManager(dictUrls=dictionaries, roomCode=link, username=name)
    manager = BotManager(dictUrls=dictionaries, roomCode=link, proxyFile=filename, username=name)
    manager.persistLoop()