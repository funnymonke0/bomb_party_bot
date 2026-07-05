
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



class Bot():
    def __init__(self, dicts: dict[str, set[str]], settings : dict[str, object], invalid : set[str] = set(), proxy : str = ''):

        self.console = getLogger('MANAGER-CONSOLE.BOT-CONSOLE')
        self.console.setLevel(DEBUG)


        self.dicts = dicts 
        self.invalid = invalid 

        self.bonusAlphabet = [] #temp bonus self.bonusAlphabet
        
       
        self.promptTime = 5 
        self.startLives = 2
        self.maxLives = 3
        self.currentLives = 2 

        ## list unpacking. do this for convenient use cuz we dont want to have to get the variables from the settings list in each method
        [# type: ignore
            self.selectMode,

            self.regenIfNeeded,
            self.sneakyRegen,
            self.stockpile,
            self.greedLong,
            self.timeConstraint,
            self.cyberbullying,
            self.mistakes,
            self.burstType,
            self.spamType,
            self.dynamicRate,
            self.dynamicPauses,
            self.dynamicMistakes,

            self.minWait,
            self.maxWait,
            self.mistakePause,
            self.miniPause,
            minWpm,
            maxWpm,
            spamWpm,
            self.burstChance,
            self.minMistakeChance,
            self.maxMistakeChance,
            self.spamChance,
            self.jitterPercent
        ] = list(settings.values())

        self.minRate = 5/minWpm # type: ignore
        self.maxRate = 5/maxWpm # type: ignore
        self.spamRate = 5/spamWpm # type: ignore
        self.applyJitter: Callable[[float], float] = lambda x: float(x*(1+random.uniform(-self.jitterPercent, self.jitterPercent)))# type: ignore

        self.isCorrect = True #reset stopwatch at the start
        self.start = 0 #start time
        self.timeUsed = lambda: time()-self.start
        self.syllable = ''

        self.originalAlphabet = [] #original bonus self.bonusAlphabet
        self.used = set[str]() #used words this session
        self.used.update(self.invalid) #add invalid words to used so they are not used again

        self.client = Client(proxy=proxy)


    def joinRoom(self, roomCode: str, username: str = '') -> bool: return self.client.joinRoom(roomCode=roomCode,username=username)

    def close(self): self.client.close()
       

    def main_loop(self):
        
        

        while True:
            try:
                if self.client.disconnect_check() or self.client.neterr_check():
                    break

                if self.client.try_join_round(): #needs to be constant trying to click join because otherwise it will not have another indicator as to when to reset initial conditions
                    self.originalAlphabet = self.client.get_bonus_alphabet()
                    self.promptTime = self.client.get_prompt_time()
                    self.startLives = self.client.get_start_lives()
                    self.currentLives = self.startLives
                    self.maxLives = self.client.get_max_lives()
                    self.client.clear_life_trackers()
                    
                    self.used = set[str]()
                    self.used.update(self.invalid) #reset used

                    self.isCorrect = True


                
                if self.client.get_self_turn(): 
                    self.syllable = self.client.get_syllable()
                    typed = False
                    if self.isCorrect:
                        self.start = time()
                    

                    ansSet = self.dicts[self.syllable]
                    ansSet -= self.used

                    ans = '/suicide'
                    if ansSet and len(ansSet) > 0:
                        ans = self.eval(ansSet)

                    self.console.info(f"found answer {ans} for syllable {self.syllable}" if ans != "/suicide" else f"could not find answer for syllable: {self.syllable}")
                    
                    
                    if bool(self.cyberbullying) and self.client.get_players() < 3:# type: ignore
                        if self.client.get_self_turn() and self.client.safe_typer(ans): 
                            typed = True

                    else:
                        wait = float(self.miniPause)# type: ignore

                        if self.isCorrect: #do normal wait if we were correct on our prev answer
                            rt: Callable[[str], float] = lambda w: float(581.39 + 467.81 / (1 + (2.718281828 ** (1.022 * (zipf_frequency(w, 'en') - 2.946))))) # type: ignore | tuff goony blud sigmoid regression function based on ELP data
                            base_min, base_max = 581.39, 581.39 + 467.81
                            func: Callable[[str], float] = lambda w: float(self.minWait + (rt(w) - base_min) * (self.maxWait - self.minWait) / (base_max - base_min)) # type: ignore | linear interpolation of wait time based on word freq

                            wait = func(ans) if bool(self.dynamicPauses) else float(self.minWait)# type: ignore
                        elif (bool(self.spamType) and (len(ans) >= 20 or random.random()<=float(self.spamChance))): # type: ignore | wait minipause with a potential spam if was not correct
                            spam = self.formatSpam()
                            self.client.safe_typer(spam)

                        if self.client.get_self_turn():
                            sleep(wait)
                        if self.client.get_self_turn() and self.client.safe_typer(self.formatSimType(ans)):
                            typed = True

                    #change flags and update used words
                    self.isCorrect = False
                    if typed:
                        self.used.add(ans)
                    typed = False
                    if not self.client.get_self_turn():
                        self.isCorrect = True #only reset stopwatch when no longer our turn

                        lifeChange = self.client.get_life_change()
                        self.currentLives += lifeChange

                        
                        #if correct, prune bonus alphabet for letters in used answer
                        self.bonusAlphabet = list((Counter(self.bonusAlphabet) - Counter(ans)).elements())
                        self.console.info(f"remaining {self.bonusAlphabet} after pruning")

                        if len(self.bonusAlphabet) < 1: #no need to add to currentLives, since that updates automatically
                            self.bonusAlphabet = self.originalAlphabet.copy()
                            self.console.info(f"{self.bonusAlphabet} after regen reset")
                    
                        
            except Exception as e:
                self.console.warning(f"unexpected exception: {e}")
                break
            


    def eval(self, ansSet:set[str]) -> str: #eval
        alph = self.bonusAlphabet
        mode = str(self.selectMode)# type: ignore
        ans = ''

        long: Callable[[set[str]], str] = lambda aset: max(aset, key=len)
        short: Callable[[set[str]], str] = lambda aset: min(aset, key=len)

        avg: Callable[[set[str]], str] = lambda aset: min(aset, key = lambda w: abs(len(w)- round((len(short(ansSet))+len(long(ansSet)))/2) ))# type: ignore | minimize difference from the averageLen
        common: Callable[[set[str]], str] = lambda aset: max(aset, key=lambda w: word_frequency(w, "en"))

        regen: Callable[[set[str]], str] = lambda aset: max(aset, key= lambda w: shared_letters[w]) #maximum shared letters
        sneaky: Callable[[set[str]], str] = lambda aset: max(aset, key= lambda w: zipf_frequency(w,"en")+shared_letters[w]) #maximum shared letters while also accounting for regen

        shared_letters = {w: len(set(w) & set(alph)) for w in ansSet}
        specificWrapper: Callable[[Callable[[set[str]], str], set[str], int], str] = lambda func, aset, num: func({w for w in aset if shared_letters[w]<=num} or aset) # passes a pruned list where the shared words do not exceed num

        if (bool(self.timeConstraint) and self.timeUsed()>=self.promptTime) or not self.isCorrect:# type: ignore
            ans = short(ansSet)

        elif bool(self.regenIfNeeded) and self.currentLives == 1 and self.maxLives != 1:# type: ignore
            ans = regen(ansSet)

        elif bool(self.sneakyRegen) and self.currentLives < self.maxLives:# type: ignore
            ans = sneaky(ansSet)

        elif bool(self.stockpile) and self.maxLives != 1:# type: ignore
            if len(alph)>1:
                if bool(self.sneakyRegen):# type: ignore
                    ans = specificWrapper(sneaky, ansSet, len(alph)-1)
                else:
                    ans = specificWrapper(regen, ansSet, len(alph)-1)  
            else:
                ansSet = {w for w in ansSet if alph[0] not in w} or ansSet

        if ans and len(ans) > 0: pass# type: ignore
        elif mode == 'long':
            ans =  long(ansSet)

        elif mode == 'short':
            ans =  short(ansSet)

        elif mode == "average":
            ans =  avg(ansSet)
        
        elif mode == 'regen':
            ans =  regen(ansSet)
        
        elif mode == "common":
            ans =  common(ansSet)
        
        elif mode == "sneaky":
            ans =  sneaky(ansSet)
        else:
            ans =  random.choice(list(ansSet))
        
        return str(ans)



    def formatSpam(self) -> list[tuple[str, float]]:
        length = random.randint(7,15)
        txt = [random.choice(ascii_lowercase) for i in range(0,length)] # type: ignore | needed so that it does the choice each time
        ratesList = [float(self.spamRate) for i in range(0,length)]# type: ignore
        return list(zip(txt, ratesList))



    def formatSimType(self, txt : str) -> list[tuple[str, float]]: ##tool
        
        ratesList = list[float]()
        txtList = list[str]()
        burst_counter = 0
    
        for letter in txt:        
            txtList.append(letter)

            current_rate = 0
            #add delay
            if bool(self.dynamicRate):# type: ignore
                current_rate = float(max(1,(self.timeUsed()+sum(ratesList))/self.promptTime)*self.maxRate)# type: ignore

            elif ((bool(self.burstType) and random.random() <= float(self.burstChance)) or burst_counter > 0):# type: ignore
                current_rate = float(self.maxRate)# type: ignore
                if burst_counter > 0:
                    burst_counter-=1
                else:
                    burst_counter += random.choice((1,1,1,1,2,2,3))
                
            else:
                current_rate = float(self.minRate)# type: ignore

            ratesList.append(self.applyJitter(current_rate))

            mistake_chance = float(self.minMistakeChance)# type: ignore
            if bool(self.dynamicMistakes):# type: ignore
                mistake_chance = float(self.minMistakeChance + (self.maxMistakeChance - self.minMistakeChance) * (max(current_rate, self.minRate) - self.minRate) / (self.maxRate - self.minRate))# type: ignore

            #add mistake (char and delay)
            if bool(self.mistakes) and (random.random() <= mistake_chance) and letter in MISTAKE_MAP.keys(): # type: ignore
                mistakechars = MISTAKE_MAP[letter]
                mistakeLen = random.choice((1,1,1,1,2,2,3)) #good tuff diddy blud implementation

                for i in range(mistakeLen):# type: ignore
                    txtList.append(random.choice(mistakechars))
                    ratesList.append(self.applyJitter(current_rate))

                txtList.append('')
                ratesList.append(self.applyJitter(float(self.mistakePause)))# type: ignore

                for i in range(mistakeLen):# type: ignore
                    txtList.append(Keys.BACKSPACE)
                    ratesList.append(self.applyJitter(float(self.maxRate))) # type: ignore | spam backspace

        return list(zip(txtList, ratesList))