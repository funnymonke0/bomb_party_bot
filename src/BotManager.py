from logging import fatal

import requests
from bs4 import BeautifulSoup

from string import ascii_lowercase
from re import sub, match
import logging
from os.path import join
from os import makedirs
from time import sleep
from datetime import datetime
import json


from src.Bot import Bot


PLAINTEXT_REGEX = r"\b'?([A-Za-z]+(?:[-'][A-Za-z]+)*)'?\b"
URL_REGEX = r"https?:\/\/[A-Za-z0-9.-]+(?:\/[A-Za-z0-9._~\-\/]+)*"
PROXY_REGEX = r"^((\d{1,3}\.){3}(\d{1,3})|\w+\.\w+(\.\w+)?):(\d{1,5})(:.+:.+)?"
ROTATE_RETRY_THRESH = 5
MODES = ['long','short',"average",'regen',"common","sneaky"]




class DictionaryException(Exception):
    def __init__(self, message:str = "Dictionary load failed. Please provide dictionary"):
        super().__init__(message)
class SettingsException(Exception):
    def __init__(self, message:str = "Settings load failed. Please provide settings"):
        super().__init__(message)

def _format_dict(dicts:set[str]) -> dict[str, set[str]]: ##tool
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


def _format_proxy(proxy:str) -> str: ##Tool
    f_proxy = ''
    split = proxy.split(':')


    if len(split) == 4:
        addr, port, user, pswd = split[0], split[1], split[2], split[3]
        f_proxy = f"https://{user}:{pswd}@{addr}:{port}" #any issues will be handled by bot defaulting

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
        self.self_destruct = False
        self.bot = None

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

        self._load_settings(settings_file)
        self._load_proxies(proxy_file)
        self._load_dicts(dict_file)

        if invalid_file:
            self._load_invalid(invalid_file)

#init funcs

    def _load_settings(self, settings_file:str) -> None:#init proc

        with open(settings_file, 'r') as f:
            settings_raw = json.load(f)

        if len(settings_raw) < 1:
            raise SettingsException

        settings_raw["selectMode"] = str(settings_raw["selectMode"]).strip().lower()
        try:
            if not( #integrity check
                settings_raw["selectMode"] in MODES
                and isinstance(settings_raw["regenIfNeeded"], bool)
                and isinstance(settings_raw["sneakyRegen"], bool)
                and isinstance(settings_raw["stockpile"], bool)
                and isinstance(settings_raw["greedLong"], bool)
                and isinstance(settings_raw["timeConstraint"], bool)
                and isinstance(settings_raw["cyberbullying"], bool)
                and isinstance(settings_raw["mistakes"], bool)
                and isinstance(settings_raw["burstType"], bool)
                and isinstance(settings_raw["spamType"], bool)
                and isinstance(settings_raw["dynamicRate"], bool)
                and isinstance(settings_raw["dynamicPauses"], bool)
                and isinstance(settings_raw["dynamicMistakes"], bool)
                and isinstance(settings_raw["minWait"], (int, float))
                and isinstance(settings_raw["maxWait"], (int, float))
                and isinstance(settings_raw["mistakePause"], (int, float))
                and isinstance(settings_raw["miniPause"], (int, float))
                and isinstance(settings_raw["minWpm"], int)
                and isinstance(settings_raw["maxWpm"], int)
                and isinstance(settings_raw["spamWpm"], int)
                and isinstance(settings_raw["burstChance"], (int,float))
                and isinstance(settings_raw["minMistakeChance"], (int,float))
                and isinstance(settings_raw["maxMistakeChance"], (int,float))
                and isinstance(settings_raw["spamChance"], (int,float))
                and isinstance(settings_raw["jitterPercent"], (int,float))
                ):
                raise SettingsException('Settings file contains invalid characters. Please check that all values are of the correct type and that no extra characters are present.')
        except KeyError as e:
            raise SettingsException(f"Settings file is missing required key: {e}")

        self.settings = settings_raw
        self.console.info(f"loaded all {len(self.settings)} settings from {settings_file}")



    def _load_proxies(self, proxy_file:str) -> None:#init proc

        proxy_list_raw = self.find_in_file(proxy_file, PROXY_REGEX)
        #must be len > 0, element must be len > 0, format element must be len > 0
        if len(proxy_list_raw) > 0 and any(proxy_list_raw): #checks if list is not empty and if any elements are not empty
            proxy_list_raw = [_format_proxy(proxy) for proxy in proxy_list_raw if len(proxy) > 0] # formats all non-empty proxies
            if len(proxy_list_raw) > 0 and any(proxy_list_raw):
                proxy_list_raw = [f_proxy for f_proxy in proxy_list_raw if len(f_proxy) > 0] #removes any empty after format
                if len(proxy_list_raw) > 0 and any(proxy_list_raw):
                    self.proxy_list = proxy_list_raw
                    self.console.info(f"loaded {len(self.proxy_list)} proxies from {proxy_file}")
                    return
        self.proxy_list = ['']  # use local IP
        self.console.info("No proxies provided. Using local machine IP")  # not critical


    def _load_invalid(self, invalid_file:str) -> None: ## loads the non-working words at the start
        self.console = self.console
        try:
            self.invalid = {x.lower() for x in self.find_in_file(invalid_file, PLAINTEXT_REGEX)}
            self.console.info(f'loaded invalid word list from {invalid_file}. Contains {len(self.invalid)} words')
        except FileNotFoundError:
            self.console.warning(f"{invalid_file} could not be loaded because it does not exist") #not critical


    def _load_dicts(self, dict_file:str) -> None:#init proc
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
        self.dict_map = _format_dict(dicts)
        console.info(f"finished mapping all {len(self.dict_map)} (key,value) pairs")

        # for k, v in self.dict_map.items():
        #     if len(v) == 0:
        #         with open("unknowns.txt", "a") as file:
        #             file.write(k+"\n")
        # for mapping unknown syllables


    def do_bot(self, proxy) -> bool | None:
        self.bot = Bot(dicts=self.dict_map, proxy=proxy, settings=self.settings, invalid=self.invalid)
        expected, continue_action = self.bot.join_room(room_code=self.room_code, username=self.username)
        if continue_action:
            if self.bot.main_loop() and not self.self_destruct:
                self.console.info(f'Bot session with proxy {proxy} ended gracefully')
                return True
            else:
                self.console.warning(f'Bot session with proxy {proxy} ended unexpectedly')
                return False
        else:
            if expected:
                self.console.warning(f'Bot session with proxy {proxy} was banned from the room')
                return True
            else:
                self.console.warning(f'Bot session with proxy {proxy} could not join room')
                return False


    def close(self):
        self.console.info('closing botmanager')
        self.self_destruct = True
        if self.bot:
            self.bot.close()
        self.bot = None


#mainloop
    def persist_loop(self) -> None:
        try:
            for proxy in self.proxy_list:
                if 'rotate' in proxy.lower():
                    rotate_retries = 0
                    while rotate_retries < ROTATE_RETRY_THRESH: #this should only end when there are too many unexpected issues
                        graceful = self.do_bot(proxy)
                        if graceful: #expected end or ban vs unexpected join-room error or bot exception
                            rotate_retries = 0
                        else:
                            if self.self_destruct:
                                return
                            rotate_retries +=1
                        sleep(2)
                        self.console.info(f"reloading bot using rotating proxy {proxy}")

                else:
                    if not self.do_bot(proxy) and self.self_destruct:
                        return

                sleep(2)
                self.console.info(f"using next proxy in the list")
        except (KeyboardInterrupt, SystemExit):
            self.console.info(f'Manager session ended gracefully')
        except Exception as e:
            self.console.error(f"Unexpected exception occurred, ending manager session: {e}")

        finally:
            self.console.info('Session ended. Goodbye!') #kills self. I wish
        
#tool
    def find_in_file(self, filename:str, ex:str) -> list[str]: # returns a list of strings matching ex from filename ##tool
        lst = ['']
        try:
            with open(filename, 'r') as file:
                out = file.readlines()
            lst = [sub(r'\s+', '', x) for x in out if match(ex,x)] #removes all whitespace anywhere and matches
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
                    content = str(soup.get_text(separator='\n', strip=True).lower().split('\n')) #shouldnt have any whitespaces inside of words if from source so we dont need sub
                    dicts.update(content)
                except Exception as e:
                    self.console.warning(f'Cannot get url {url} because of Exception {e}')

        return dicts


    def __del__(self):
        self.console.info("BotManager is deleted")
        self.console.handlers = []
