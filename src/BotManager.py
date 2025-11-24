from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from string import ascii_lowercase
from re import sub, match
import logging
from os.path import join
from os import makedirs
from time import sleep
from datetime import datetime


from src.Bot import Bot


PLAINTEXT_REGEX = r"^\w+(\-\w+)?$"
URL_REGEX = r"^((https|http)\:\/\/)((\w+\.\w+\.\w+)|(\w+\.\w+))((\/.+)+)?"
SETTINGS_REGEX = r"^\w+(\s*)\:(\s*)(\w+)(\.\w+)?"
PROXY_REGEX = r"^((\d{1,3}\.){3}(\d{1,3})|\w+\.\w+(\.\w+)?):(\d{1,5})(:.+:.+)?"
ROTATE_RETRY_THRESH = 5





class DictionaryException(Exception):
    def __init__(self):
        super().__init__("Dictionary load failed. Please provide dictionary")
class SettingsException(Exception):
    def __init__(self):
        super().__init__("Settings load failed. Please provide settings")


class BotManager():
    
    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dictFile : str, settingsFile : str, proxyFile : str, invalidFile : str, roomCode : str, username : str = ''):
        
        
        self.roomCode = roomCode
        self.username = username
        self.invalid = set()
        self.invalidFile = invalidFile
        
        self.console = logging.getLogger('MANAGER-CONSOLE')
        self.console.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        logdir = "log"
        makedirs(logdir, exist_ok=True)
        logpath = join(logdir, f'BotManager {datetime.date(datetime.now())}.log')
        with open(logpath, 'w'):
            pass

        fh = logging.FileHandler(logpath,"w")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        self.console.addHandler(ch)
        self.console.addHandler(fh)#botconsole inherits all this

        self.loadSettings(settingsFile)
        self.loadProxies(proxyFile)
        self.loadDicts(dictFile)

        if invalidFile:
            self.loadInvalid(invalidFile)
        else:
            self.settings["saveInvalid"] = False

#____ Load functions _____________________________________________

    def loadSettings(self, settingsFile):#init proc


        settingsRaw = self.findInFile(settingsFile, SETTINGS_REGEX)

        if settingsRaw is None or len(settingsRaw) < 1:
            raise SettingsException
        
        self.settings = self.formatSettings(settingsRaw)
        
        self.console.info(f"loaded all {len(self.settings)} settings from {settingsFile}")



    def loadProxies(self, proxyFile):#init proc

        self.proxyList = self.findInFile(proxyFile, PROXY_REGEX)

        if not self.proxyList or len(self.proxyList) < 1:
            self.proxyList = ['']#use local IP
            self.console.info("No proxies provided. Using local machine IP")
        else:
            self.console.info(f"loaded {len(self.proxyList)} proxies from {proxyFile}")
        

    def loadInvalid(self, fn): ## loads the non-working words at the start
        self.console = self.console
        try:
            with open(fn, 'r') as file:
                self.invalid.update(file.readlines())
            self.console.info(f'loaded invalid word list from {fn}. Contains {len(self.invalid)} words')
        except FileNotFoundError:
            self.console.warning(f"{fn} could not be loaded because it does not exist. not saving invalid")
            self.settings["saveInvalid"] = False


    def loadDicts(self, dictFile):#init proc
        console = self.console

        dicts = set()

        dictUrls = self.findInFile(dictFile, URL_REGEX)
        console.info(f"loading {len(dictUrls)} dictionaries from urls in {dictFile}")
        dicts.update(self.parseFromUrls(dictUrls))
        dictPlainText = {x.lower() for x in self.findInFile(dictFile, PLAINTEXT_REGEX)}
        console.info(f"loading {len(dictPlainText)} entries from plaintext in {dictFile}")
        dicts.update(dictPlainText)

        if dicts is None or len(dicts) < 1:
            raise DictionaryException

        console.info(f"loaded {len(dicts)} words from {dictFile}")
        self.dictMap = self.formatDict(dicts)
        console.info(f"finished mapping all {len(self.dictMap)} (key,value) pairs")

        # for k, v in self.dictMap.items():
        #     if len(v) == 0:
        #         with open("unknowns.txt", "a") as file:
        #             file.write(k+"\n")
        # for mapping unknown syllables

#____ Main functions _____________________________________________      
 
    def persistLoop(self): 
        try:
            for proxy in self.proxyList:
                if len (proxy) > 0:
                    proxy = self.formatProxy(proxy)

                if 'rotate' in proxy.lower():
                    rotateRetries = 0
                    while rotateRetries < ROTATE_RETRY_THRESH:
                        bot = Bot(dicts=self.dictMap, proxy=proxy, settings=self.settings, invalid=self.invalid)
                        if bot.joinRoom(roomCode=self.roomCode, username=self.username):
                            rotateRetries = 0

                            bot.main_loop()
                            self.console.info(f'Bot session with proxy {proxy} ended gracefully')
                            
                            if self.settings["saveInvalid"]:
                                self.invalid.update(bot.invalid)
                                self.saveInvalid()
                        else:
                            rotateRetries +=1
                        sleep(2)
                        self.console.info(f"reloading bot using rotating proxy {proxy}")

                else:
                    bot = Bot(dicts=self.dictMap, proxy=proxy, settings=self.settings, invalid=self.invalid)
                    if bot.joinRoom(roomCode=self.roomCode, username=self.username):

                        bot.main_loop()
                        self.console.info(f'Bot session with proxy {proxy} ended gracefully')

                        if self.settings["saveInvalid"]:
                            self.invalid.update(bot.invalid)
                            self.saveInvalid()
                sleep(2)
                self.console.info(f"using next proxy in the list")
        except KeyboardInterrupt:
            self.console.info("User aborted BotManager")

        self.console.info('Session ended. Goodbye!')
        
#____ Tool functions _____________________________________________

    def findInFile(self, filename:str, ex:str) -> list: # returns a list of strings matching ex from filename ##tool
        lst = []
        try:
            with open(filename, 'r') as file:
                out = file.readlines()
            lst = [sub(r'\s+', '', x) for x in out if match(ex,x)]
        except:
            self.console.warning("failed to find regex in file")
        return lst



    def formatSettings(self, raw) -> dict: ##tool
        s=dict()

        for line in raw:
            if len(line) > 0:
                key, value = line.split(':', 1)
                if value.lower() == 'true':
                    s[key] = True
                elif value.lower() == 'false':
                    s[key] = False
                elif match(r"^\d+\.\d*$", value):
                    s[key] = float(value)
                elif match(r"^\d+$|^\d+\.0+$",value):
                    s[key] = int(value)
                else:
                    s[key] = value #string
        
        return s
    


    def formatDict(self, dicts) -> dict: ##tool
        hsmp = dict()
        dicts = {wrd for wrd in dicts if 0<len(wrd)<21}
        for letter1 in ascii_lowercase:
            k1 = letter1
            value = {wrd for wrd in dicts if k1 in wrd}
            hsmp[k1] = value
            for letter2 in ascii_lowercase:
                k2 = k1 + letter2
                value = {wrd for wrd in hsmp[k1] if k2 in wrd}
                hsmp[k2] = value
                for letter3 in ascii_lowercase:
                    k3 = k2+letter3
                    value = {wrd for wrd in hsmp[k2] if k3 in wrd}
                    hsmp[k3] = value
        return hsmp



    def formatProxy(self, proxy:str) -> str: ##Tool
        split = proxy.split(':')
        fProxy = ''

        if len(split) == 4:
            addr, port, user, pswd = split[0], split[1], split[2], split[3]
            fProxy = f"https://{user}:{pswd}@{addr}:{port}"

        elif len(split) == 2:
            addr, port = split[0], split[1]
            fProxy = f"https://{addr}:{port}"

        return fProxy
    


    def parseFromUrls(self, dictUrls:list) -> set: 
        dicts = set()
        if len(dictUrls) > 0:
            service = ChromeService()
            options = ChromeOptions()
            options.add_argument('--headless=new')
            options.page_load_strategy = 'eager'
            browser = webdriver.Chrome(service=service, options=options)

            for url in dictUrls:
                try:
                    browser.get(url)
                    WebDriverWait(browser, 5)
                except Exception as e:
                    self.console.warning(f'Cannot get url {url} because of Exception {e}')
                content = browser.find_element(By.XPATH, '//pre').text.lower().strip().split('\n')
                dicts.update(content)
            browser.quit()

        return dicts
    


    def saveInvalid(self):
        if self.invalidFile and len(self.invalidFile) > 0:
            try:
                with open(self.invalidFile, 'w') as file:
                    file.writelines('\n'.join(self.invalid) + '\n')
                self.console.info('added invalid words to invalid list')
            except FileNotFoundError:
                self.console.warning(f"could not save to file {self.invalidFile}")