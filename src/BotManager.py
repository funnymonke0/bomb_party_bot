from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import string
import re
import logging
import os


from Bot import Bot


class SettingsException(Exception):
    def __init__(self):
        super().__init__(f"Settings load failed. One or more missing")

class ProxyException(Exception):
    def __init__(self):
        super().__init__("Proxy load failed. Proxies should be in the format addr:port or addr:port:username:password")

class DictionaryException(Exception):
    def __init__(self):
        super().__init__("Dictionary load failed. Please provide dictionary")

class BotManager():

    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dictFile : str, roomCode : str, settingsFile : str, proxyFile : str, defunctFile : str, username : str = None, ):
        
        
        
        self.roomCode = roomCode
        self.username = username

        self.defunctFile = defunctFile
        self.genConsoles()
        self.loadSettings(settingsFile)
        self.loadProxies(proxyFile)
        self.loadDicts(dictFile)

        if not self.username:
            self.username = None
        


    def genConsoles(self): #init proc
        self.console = logging.getLogger('MANAGER-CONSOLE')
        self.botconsole = logging.getLogger('MANAGER-CONSOLE.BOT')
        
        self.console.setLevel(logging.DEBUG)
        self.botconsole.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        os.makedirs("log",exist_ok=True)
        fh = logging.FileHandler(os.path.join('log','BotManager.log'),"w")
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        self.console.addHandler(ch)
        self.console.addHandler(fh)#botconsole inherits all this



    def loadSettings(self, settingsFile):#init proc
        console = self.console
        try:
            settingsRegex = r"^\w+(\s*)\:(\s*)(\w+)(\.\w+)?"
            settingsRaw = self.parseFromFile(settingsFile, settingsRegex)

            if settingsRaw is None or len(settingsRaw) < 1:
                raise SettingsException
            
            self.settings = self.parseSettings(settingsRaw)
            
            console.info(f"loaded all {len(self.settings)} settings from {settingsFile}")
        except:
            raise SettingsException


    def loadProxies(self, proxyFile):#init proc
        console = self.console
        try:
            proxyRegex = r"^((\d{1,3}\.){3}(\d{1,3})|\w+\.\w+(\.\w+)?):(\d{1,5})(:.+:.+)?"

            self.proxyList = self.parseFromFile(proxyFile, proxyRegex)

            if not self.proxyList or len(self.proxyList) < 1:
                self.proxyList = [None]
                console.info("No proxies found. Using local machine IP.")
            else:
                console.info(f"loaded {len(self.proxyList)} proxies from {proxyFile}")
            
        except:
            raise ProxyException
        

    def loadDicts(self, dictFile ):#init proc
        console = self.console
        try:
            plaintextRegex = r"^\w+(\-\w+)?$"
            urlRegex = r"^((https|http)\:\/\/)((\w+\.\w+\.\w+)|(\w+\.\w+))((\/.+)+)?"
            
            dicts = set()

            dictUrls = self.parseFromFile(dictFile, urlRegex)

            if dictUrls is not None:
                console.info(f"loading {len(dictUrls)} dictionaries from urls in {dictFile}")
                dicts.update(self.parseUrls(dictUrls))

            dictPlainText = {x.lower() for x in self.parseFromFile(dictFile, plaintextRegex)}

            if dictPlainText is not None:
                console.info(f"loading {len(dictPlainText)} entries from plaintext in {dictFile}")
                dicts.update(dictPlainText)

            
            if dicts is None or len(dicts) < 1:
                raise DictionaryException

            
            console.info(f"loaded {len(dicts)} words from {dictFile}")

            self.dictMap = self.parseDict(dicts)
            
            console.info(f"finished mapping all {len(self.dictMap)} (key,value) pairs")

        except:
            raise DictionaryException
        # for k, v in self.dictMap.items():
        #     if len(v) == 0:
        #         with open("unknowns.txt", "a") as file:
        #             file.write(k+"\n")


    
        
    
    async def persistLoop(self): #main proc
        console = self.console
        thresh = 1
        for proxy in self.proxyList:
            if proxy:
                proxy = self.formatProxy(proxy)
            retries = 0
            while not retries > thresh:
                retries += 1
                try:
                    bot = Bot(dicts=self.dictMap, proxy=proxy, settings=self.settings, logger=self.botconsole, defunctFile = self.defunctFile)
                    if bot.joinRoom(roomCode=self.roomCode, username=self.username):
                        await bot.start()
                
                except KeyboardInterrupt:
                    console('Session interrupted by user')
                    break
                except Exception as e: 
                    console.debug(f"Exception {e} in Bot @ {proxy}", exc_info=True)

        console.info('Session ended. Goodbye!')
        


        

    def parseFromFile(self, filename:str, ex:str): # must return list because settings are ordered. Tool

        lst = []
        
        with open(filename, 'r') as file:
            out = file.readlines()
        
        lst = [re.sub(r'\s+', '', x) for x in out if re.match(ex,x)]

        return lst



    def parseSettings(self, raw): ##tool
        s=dict()

        for line in raw:
            
            key, value = line.split(':', 1)
            if value.lower() == 'true':
                s[key] = True
            elif value.lower() == 'false':
                s[key] = False
            else:
                if re.match(r"^\d+\.\d*$", value):
                    s[key] = float(value)
                elif re.match(r"^\d+$|^\d+\.0+$",value):
                    s[key] = int(value)
                else:
                    s[key] = value #string
    
        settingsParsed = [
            s['selectMode'],
            s['cyberbullying'],
            s['maxOffset'],
            s['rate'],
            s['burstType'],
            s['burstRate'],
            s['burstChance'],
            s['randomness'],
            s['mistakes'], 
            s['mistakeChance'], 
            s['mistakePause'], 
            s['franticType'], 
            s['franticRate'],
            s['dynamicPauses'], 
            s['scaleFactor'],
            s['spamType'], 
            s['spamRate'], 
            s['miniPause'],
            s['useDefunct']
            ]

        return settingsParsed
    


    def parseDict(self, dicts): ##tool

        hsmp = dict()
        for letter1 in string.ascii_lowercase:
            k1 = letter1
            value = {wrd for wrd in dicts if k1 in wrd}
            hsmp[k1] = value
            for letter2 in string.ascii_lowercase:
                k2 = k1 + letter2
                value = {wrd for wrd in hsmp[k1] if k2 in wrd}
                hsmp[k2] = value
                for letter3 in string.ascii_lowercase:
                    k3 = k2+letter3
                    value = {wrd for wrd in hsmp[k2] if k3 in wrd}
                    hsmp[k3] = value

        return hsmp


    
    def formatProxy(self, proxy:str): ##Tool

        split = proxy.split(':')
        fProxy = None
        if len(split) == 4:
            
            addr, port, user, pswd = split[0], split[1], split[2], split[3]
            fProxy = f"https://{user}:{pswd}@{addr}:{port}"

        elif len(split) == 2:
            addr, port = split[0], split[1]
            fProxy = f"https://{addr}:{port}"

        return fProxy
    
    def parseUrls(self, dictUrls:list): #could use multiple loaders asynchronously. create proclist by zipping together loaderlist and urls, then asyncio.wait. Tool
        console = self.console
        service = ChromeService()
        options = ChromeOptions()
        options.add_argument('--headless=new')
        options.page_load_strategy = 'eager'

        browser = webdriver.Chrome(service=service, options=options)
        dicts = set()


        for url in dictUrls:
            try:
                browser.get(url)
                WebDriverWait(browser, 5)
            except (ConnectionResetError,ConnectionAbortedError,ConnectionError,ConnectionRefusedError) as e:
                console.error(f'Cannot get url {url} because of Exception {e}')

            content = browser.find_element(By.XPATH, '//pre').text.lower().strip().split('\n')
            dicts.update(content)

        return dicts