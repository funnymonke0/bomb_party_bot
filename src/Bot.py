
from collections.abc import Callable

from src.Client import Client
from logging import getLogger, DEBUG
from wordfreq import word_frequency, zipf_frequency
from collections import Counter

import random
from string import ascii_lowercase
from time import sleep, time
from selenium.webdriver.common.keys import Keys


LOCATORS = {
    "nickname_input": '//input[@class = "styled nickname"]',
    "submit_button": "//button[@class = 'styled']",
    "bombparty_iframe": "//iframe[contains(@src, 'bombparty')]",
    "disconnect_page": '//div[@class = "disconnected page"]',
    "neterror_page": "//body[@class = 'neterror']",
    "bonus_alphabet": '//div[@class="bonusAlphabetField"]//div[@class="letterField"]//input',
    "min_turn_duration": '//div[@class = "setting rule minTurnDuration"]//div[@class = "field range"]//input[@type="number" and @min = "1" and @max = "10"]',
    "start_lives": "//input[@class = 'starting']",
    "max_lives": '//input[@class="max" and @type="number" and @min="1" and @max="10"]',
    "join_round_button": "//button[@class = 'styled joinRound']",
    "self_turn": '//div[@class = "selfTurn"]',
    "syllable": "//div[@class = 'syllable']",
    "textbox": '//form//input[@maxlength = "30"]',
    "stats_table_rows": "//table[@class='statsTable']//tr",
    "self_lives": "//table[@class='statsTable']//tr[contains(@class, 'self')]//td[@class='lives']"
}

MAX_WAIT = 5

UPDATE_INTERVALS = {
        'disconnect' : 30,
        'join' : 10
    }

MISTAKE_MAP = {
    'q': ['w', 'a'],
    'w': ['q', 'e', 'a', 's'],
    'e': ['w', 'r', 's', 'd'],
    'r': ['e', 't', 'd', 'f'],
    't': ['r', 'y', 'f', 'g'],
    'y': ['t', 'u', 'g', 'h'],
    'u': ['y', 'i', 'h', 'j'],
    'i': ['u', 'o', 'j', 'k'],
    'o': ['i', 'p', 'k', 'l'],
    'p': ['o', 'l'],

    'a': ['q', 'w', 's', 'z'],
    's': ['a', 'w', 'e', 'd', 'z', 'x'],
    'd': ['s', 'e', 'r', 'f', 'x', 'c'],
    'f': ['d', 'r', 't', 'g', 'c', 'v'],
    'g': ['f', 't', 'y', 'h', 'v', 'b'],
    'h': ['g', 'y', 'u', 'j', 'b', 'n'],
    'j': ['h', 'u', 'i', 'k', 'n', 'm'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p'],

    'z': ['a', 's', 'x'],
    'x': ['z', 's', 'd', 'c'],
    'c': ['x', 'd', 'f', 'v'],
    'v': ['c', 'f', 'g', 'b'],
    'b': ['v', 'g', 'h', 'n'],
    'n': ['b', 'h', 'j', 'm'],
    'm': ['n', 'j', 'k']
}



class Bot:
    def __init__(self, dicts: dict[str, set[str]], settings : dict[str, object], invalid=None, proxy : str = ''):

        if invalid is None:
            invalid = set()
        self.console = getLogger('MANAGER-CONSOLE.BOT-CONSOLE')
        self.console.setLevel(DEBUG)


        self.dicts = dicts 
        self.invalid = invalid 

        self.bonus_alphabet = [] #temp bonus self.bonus_alphabet
        
       
        self.prompt_time = 5
        self.start_lives = 2
        self.max_lives = 3
        self.current_lives = 2

        ## list unpacking. do this for convenient use cuz we don't want to have to get the variables from the settings list in each method
        [# type: ignore
            self.select_mode,

            self.regen_if_needed,
            self.sneaky_regen,
            self.stockpile,
            self.greed_long,
            self.time_constraint,
            self.cyberbullying,
            self.mistakes,
            self.burst_type,
            self.spam_type,
            self.dynamic_rate,
            self.dynamic_pauses,
            self.dynamic_mistakes,

            self.min_wait,
            self.max_wait,
            self.mistake_pause,
            self.mini_pause,
            min_wpm,
            max_wpm,
            spam_wpm,
            self.burst_chance,
            self.min_mistake_chance,
            self.max_mistake_chance,
            self.spam_chance,
            self.jitter_percent
        ] = list(settings.values())

        self.min_rate = 5/min_wpm # type: ignore
        self.max_rate = 5/max_wpm # type: ignore
        self.spam_rate = 5/spam_wpm # type: ignore
        self.apply_jitter: Callable[[float], float] = lambda x: float(x*(1+random.uniform(-self.jitter_percent, self.jitter_percent)))# type: ignore

        self.is_correct = True #reset stopwatch at the start
        self.start = 0 #start time
        self.time_used = lambda: time()-self.start
        self.syllable = ''

        self.original_alphabet = [] #original bonus self.bonus_alphabet
        self.used = set[str]() #used words this session
        self.used.update(self.invalid) #add invalid words to used so they are not used again

        self.client = Client(proxy=proxy)


    def join_room(self, room_code: str, username: str = '') -> tuple[bool,bool]: return self.client.join_room(room_code=room_code, username=username)

    def close(self): self.client.close() #self close
       

    def main_loop(self, stop = lambda: False) -> bool: #main loop. returns if it was graceful or not

        try:
            while not stop():
                if self.client.disconnect_check() or self.client.neterr_check():
                    break


                if self.client.try_join_round(): #needs to be constant trying to click join because otherwise it will not have another indicator as to when to reset initial conditions
                    self.original_alphabet = self.client.get_bonus_alphabet()
                    self.prompt_time = self.client.get_prompt_time()
                    self.start_lives = self.client.get_start_lives()
                    self.current_lives = self.start_lives
                    self.max_lives = self.client.get_max_lives()
                    self.client.clear_life_trackers()

                    self.used = set[str]()
                    self.used.update(self.invalid) #reset used

                    self.is_correct = True



                if self.client.get_self_turn():
                    self.syllable = self.client.get_syllable()
                    typed = False
                    if self.is_correct:
                        self.start = time()


                    ans_set = self.dicts[self.syllable]
                    ans_set -= self.used

                    ans = '/suicide'
                    if ans_set and len(ans_set) > 0:
                        ans = self.eval(ans_set)

                    self.console.info(f"found answer {ans} for syllable {self.syllable}" if ans != "/suicide" else f"could not find answer for syllable: {self.syllable}")


                    if bool(self.cyberbullying) and self.client.get_players() < 3:# type: ignore
                        if self.client.get_self_turn() and self.client.safe_typer(ans):
                            typed = True

                    else:
                        wait = float(self.mini_pause)# type: ignore

                        if self.is_correct: #do normal wait if we were correct on our prev answer
                            rt: Callable[[str], float] = lambda w: float(581.39 + 467.81 / (1 + (2.718281828 ** (1.022 * (zipf_frequency(w, 'en') - 2.946))))) # type: ignore | tuff goony blud sigmoid regression function based on ELP data
                            base_min, base_max = 581.39, 581.39 + 467.81
                            func: Callable[[str], float] = lambda w: float(self.min_wait + (rt(w) - base_min) * (self.max_wait - self.min_wait) / (base_max - base_min)) # type: ignore | linear interpolation of wait time based on word freq

                            wait = func(ans) if bool(self.dynamic_pauses) else float(self.min_wait)# type: ignore
                        elif bool(self.spam_type) and (len(ans) >= 20 or random.random()<=float(self.spam_chance)): # type: ignore | wait minipause with a potential spam if was not correct
                            spam = self.format_spam()
                            self.client.safe_typer(spam)

                        if self.client.get_self_turn():
                            sleep(wait)
                        if self.client.get_self_turn() and self.client.safe_typer(self.format_sim_type(ans)):
                            typed = True

                    #change flags and update used words
                    self.is_correct = False
                    if typed:
                        self.used.add(ans)
                    if not self.client.get_self_turn():
                        self.is_correct = True #only reset stopwatch when no longer our turn

                        life_change = self.client.get_life_change()
                        self.current_lives += life_change


                        #if correct, prune bonus alphabet for letters in used answer
                        self.bonus_alphabet = list((Counter(self.bonus_alphabet) - Counter(ans)).elements())
                        self.console.info(f"remaining {self.bonus_alphabet} after pruning")

                        if len(self.bonus_alphabet) < 1: #no need to add to current_lives, since that updates automatically
                            self.bonus_alphabet = self.original_alphabet.copy()
                            self.console.info(f"{self.bonus_alphabet} after regen reset")


        except Exception as e:
            self.console.warning(f"unexpected exception: {e}")

        finally:
            self.close()

        if stop():
            self.console.info("stop signal received, exiting main loop")
            return True

        else:
            self.console.info("disconnect or neterror detected, exiting main loop")
            return False


            


    def eval(self, ans_set:set[str]) -> str: #eval
        alph = self.bonus_alphabet
        mode = str(self.select_mode)# type: ignore
        ans = ''

        long: Callable[[set[str]], str] = lambda aset: max(aset, key=len)
        short: Callable[[set[str]], str] = lambda aset: min(aset, key=len)

        avg: Callable[[set[str]], str] = lambda aset: min(aset, key = lambda w: abs(len(w) - round((len(short(ans_set)) + len(long(ans_set))) / 2)))# type: ignore | minimize difference from the averageLen
        common: Callable[[set[str]], str] = lambda aset: max(aset, key=lambda w: word_frequency(w, "en"))

        regen: Callable[[set[str]], str] = lambda aset: max(aset, key= lambda w: shared_letters[w]) #maximum shared letters
        sneaky: Callable[[set[str]], str] = lambda aset: max(aset, key= lambda w: zipf_frequency(w,"en")+shared_letters[w]) #maximum shared letters while also accounting for regen

        shared_letters = {w: len(set(w) & set(alph)) for w in ans_set}
        specific_wrapper: Callable[[Callable[[set[str]], str], set[str], int], str] = lambda func, aset, num: func({w for w in aset if shared_letters[w]<=num} or aset) # passes a pruned list where the shared words do not exceed num

        if (bool(self.time_constraint) and self.time_used()>=self.prompt_time) or not self.is_correct:# type: ignore
            ans = short(ans_set)

        elif bool(self.regen_if_needed) and self.current_lives == 1 and self.max_lives != 1:# type: ignore
            ans = regen(ans_set)

        elif bool(self.sneaky_regen) and self.current_lives < self.max_lives:# type: ignore
            ans = sneaky(ans_set)

        elif bool(self.stockpile) and self.max_lives != 1:# type: ignore
            if len(alph)>1:
                if bool(self.sneaky_regen):# type: ignore
                    ans = specific_wrapper(sneaky, ans_set, len(alph) - 1)
                else:
                    ans = specific_wrapper(regen, ans_set, len(alph) - 1)
            else:
                ans_set = {w for w in ans_set if alph[0] not in w} or ans_set

        if ans and len(ans) > 0: pass# type: ignore
        elif mode == 'long':
            ans =  long(ans_set)

        elif mode == 'short':
            ans =  short(ans_set)

        elif mode == "average":
            ans =  avg(ans_set)
        
        elif mode == 'regen':
            ans =  regen(ans_set)
        
        elif mode == "common":
            ans =  common(ans_set)
        
        elif mode == "sneaky":
            ans =  sneaky(ans_set)
        else:
            ans =  random.choice(list(ans_set))
        
        return str(ans)



    def format_spam(self) -> list[tuple[str, float]]:
        length = random.randint(7,15)
        txt = [random.choice(ascii_lowercase) for i in range(0,length)] # type: ignore | needed so that it does the choice each time
        rates_list = [float(self.spam_rate) for i in range(0,length)]# type: ignore
        return list(zip(txt, rates_list))



    def format_sim_type(self, txt : str) -> list[tuple[str, float]]: ##tool
        
        rates_list = list[float]()
        txt_list = list[str]()
        burst_counter = 0
    
        for letter in txt:        
            txt_list.append(letter)

            current_rate = 0
            #add delay
            if bool(self.dynamic_rate):# type: ignore
                current_rate = float(max(1, (self.time_used()+sum(rates_list)) / self.prompt_time) * self.max_rate)# type: ignore

            elif (bool(self.burst_type) and random.random() <= float(self.burst_chance)) or burst_counter > 0:# type: ignore
                current_rate = float(self.max_rate)# type: ignore
                if burst_counter > 0:
                    burst_counter-=1
                else:
                    burst_counter += random.choice((1,1,1,1,2,2,3))
                
            else:
                current_rate = float(self.min_rate)# type: ignore

            rates_list.append(self.apply_jitter(current_rate))

            mistake_chance = float(self.min_mistake_chance)# type: ignore
            if bool(self.dynamic_mistakes):# type: ignore
                mistake_chance = float(self.min_mistake_chance + (self.max_mistake_chance - self.min_mistake_chance) * (max(current_rate, self.min_rate) - self.min_rate) / (self.max_rate - self.min_rate))# type: ignore

            #add mistake (char and delay)
            if bool(self.mistakes) and (random.random() <= mistake_chance) and letter in MISTAKE_MAP.keys(): # type: ignore
                mistakechars = MISTAKE_MAP[letter]
                mistake_len = random.choice((1,1,1,1,2,2,3)) #good tuff diddy blud implementation

                for i in range(mistake_len):# type: ignore
                    txt_list.append(random.choice(mistakechars))
                    rates_list.append(self.apply_jitter(current_rate))

                txt_list.append('')
                rates_list.append(self.apply_jitter(float(self.mistake_pause)))# type: ignore

                for i in range(mistake_len):# type: ignore
                    txt_list.append(Keys.BACKSPACE)
                    rates_list.append(self.apply_jitter(float(self.max_rate))) # type: ignore | spam backspace

        return list(zip(txt_list, rates_list))