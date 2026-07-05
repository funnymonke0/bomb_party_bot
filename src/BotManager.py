import requests
from bs4 import BeautifulSoup

from string import ascii_lowercase
from re import sub, match
import logging
from os.path import join
from os import makedirs
from time import sleep
from datetime import datetime


from src.Bot import Bot


PLAINTEXT_REGEX = r"\b'?([A-Za-z]+(?:[-'][A-Za-z]+)*)'?\b"
URL_REGEX = r"https?:\/\/[A-Za-z0-9.-]+(?:\/[A-Za-z0-9._~\-\/]+)*"
SETTINGS_REGEX = r"^\w+(\s*)\:(\s*)(\w+)(\.\w+)?"
PROXY_REGEX = r"^((\d{1,3}\.){3}(\d{1,3})|\w+\.\w+(\.\w+)?):(\d{1,5})(:.+:.+)?"
ROTATE_RETRY_THRESH = 5





class DictionaryException(Exception):
    def __init__(self):
        super().__init__("Dictionary load failed. Please provide dictionary")
class SettingsException(Exception):
    def __init__(self):
        super().__init__("Settings load failed. Please provide settings")


def format_settings(raw:list[str]) -> dict[str, object]: ##tool
    s=dict[str, object]()

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


def format_dict(dicts:set[str]) -> dict[str, set[str]]: ##tool
    hsmp = dict[str, set[str]]()
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


def format_proxy(proxy:str) -> str: ##Tool
    split = proxy.split(':')
    f_proxy = ''

    if len(split) == 4:
        addr, port, user, pswd = split[0], split[1], split[2], split[3]
        f_proxy = f"https://{user}:{pswd}@{addr}:{port}"

    elif len(split) == 2:
        addr, port = split[0], split[1]
        f_proxy = f"https://{addr}:{port}"

    return f_proxy


class BotManager:
    
    #manage bot persistence, proxies and other settings, etc.
    def __init__(self, dict_file : str, settings_file : str, proxy_file : str, invalid_file : str, room_code : str, username : str = ''):
        
        
        self.dict_map = None
        self.proxy_list = None
        self.settings = None
        self.room_code = room_code
        self.username = username
        self.invalid = set[str]()
        self.invalid_file = invalid_file
        
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

        self.load_settings(settings_file)
        self.load_proxies(proxy_file)
        self.load_dicts(dict_file)

        if invalid_file:
            self.load_invalid(invalid_file)

#____ Load functions _____________________________________________

    def load_settings(self, settings_file:str) -> None:#init proc


        settings_raw = self.find_in_file(settings_file, SETTINGS_REGEX)

        if len(settings_raw) < 1:
            raise SettingsException
        
        self.settings = format_settings(settings_raw)
                
        self.console.info(f"loaded all {len(self.settings)} settings from {settings_file}")



    def load_proxies(self, proxy_file:str) -> None:#init proc

        self.proxy_list = self.find_in_file(proxy_file, PROXY_REGEX)

        if not self.proxy_list or len(self.proxy_list) < 1:
            self.proxy_list = ['']#use local IP
            self.console.info("No proxies provided. Using local machine IP")
        else:
            self.console.info(f"loaded {len(self.proxy_list)} proxies from {proxy_file}")
        

    def load_invalid(self, invalid_file:str) -> None: ## loads the non-working words at the start
        self.console = self.console
        try:
            self.invalid = {x.lower() for x in self.find_in_file(invalid_file, PLAINTEXT_REGEX)}
            self.console.info(f'loaded invalid word list from {invalid_file}. Contains {len(self.invalid)} words')
        except FileNotFoundError:
            self.console.warning(f"{invalid_file} could not be loaded because it does not exist")


    def load_dicts(self, dict_file:str) -> None:#init proc
        console = self.console

        dicts = set[str]()

        dict_urls = self.find_in_file(dict_file, URL_REGEX)
        console.info(f"loading {len(dict_urls)} dictionaries from urls in {dict_file}")
        dicts.update(self.parse_from_urls(dict_urls))
        dict_plain_text = {x.lower() for x in self.find_in_file(dict_file, PLAINTEXT_REGEX)}
        console.info(f"loading {len(dict_plain_text)} entries from plaintext in {dict_file}")
        dicts.update(dict_plain_text)

        if len(dicts) < 1:
            raise DictionaryException

        console.info(f"loaded {len(dicts)} words from {dict_file}")
        self.dict_map = format_dict(dicts)
        console.info(f"finished mapping all {len(self.dict_map)} (key,value) pairs")

        # for k, v in self.dict_map.items():
        #     if len(v) == 0:
        #         with open("unknowns.txt", "a") as file:
        #             file.write(k+"\n")
        # for mapping unknown syllables

#____ Main functions _____________________________________________      
 
    def persist_loop(self): 
        try:
            for proxy in self.proxy_list:
                if len (proxy) > 0:
                    proxy = format_proxy(proxy)

                if 'rotate' in proxy.lower():
                    rotate_retries = 0
                    while rotate_retries < ROTATE_RETRY_THRESH:
                        bot = Bot(dicts=self.dict_map, proxy=proxy, settings=self.settings, invalid=self.invalid)
                        if bot.join_room(room_code=self.room_code, username=self.username):
                            rotate_retries = 0

                            bot.main_loop()
                            bot.close()
                            self.console.info(f'Bot session with proxy {proxy} ended gracefully')
                            
                        else:
                            rotate_retries +=1
                        sleep(2)
                        self.console.info(f"reloading bot using rotating proxy {proxy}")

                else:
                    bot = Bot(dicts=self.dict_map, proxy=proxy, settings=self.settings, invalid=self.invalid)
                    if bot.join_room(room_code=self.room_code, username=self.username):

                        bot.main_loop()
                        bot.close()
                        self.console.info(f'Bot session with proxy {proxy} ended gracefully')

                sleep(2)
                self.console.info(f"using next proxy in the list")
        except KeyboardInterrupt:
            self.console.info("User aborted BotManager")

        self.console.info('Session ended. Goodbye!')
        
#____ Tool functions _____________________________________________

    def find_in_file(self, filename:str, ex:str) -> list[str]: # returns a list of strings matching ex from filename ##tool
        lst = []
        try:
            with open(filename, 'r') as file:
                out = file.readlines()
            lst = [sub(r'\s+', '', x) for x in out if match(ex,x)]
        except FileNotFoundError:
            self.console.warning(f"file {filename} not found")
        except Exception as e:
            self.console.warning(f"file {filename} could not be read because of Exception {e}")
        return lst

    def parse_from_urls(self, dict_urls:list[str]) -> set[str]:
        dicts = set[str]()
        if len(dict_urls) > 0:
            for url in dict_urls:
                try:
                    response = requests.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = str(soup.get_text(separator='\n', strip=True).lower().split('\n'))
                    dicts.update(content)
                except Exception as e:
                    self.console.warning(f'Cannot get url {url} because of Exception {e}')

        return dicts

