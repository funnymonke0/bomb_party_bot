
from src.Client import Client
from logging import getLogger, DEBUG
from wordfreq import word_frequency, zipf_frequency
from collections import Counter


import random
from string import ascii_lowercase
from time import sleep
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
    def __init__(self, dicts: dict, settings : dict, invalid : set, proxy : str = ''):

        self.console = getLogger('MANAGER-CONSOLE.BOT-CONSOLE')
        self.console.setLevel(DEBUG)


        self.dicts = dicts 



        self.invalid = invalid #invalid words (to be written to invalid file)
        self.bonusAlphabet = [] #temp bonus self.bonusAlphabet
        

        self.timeUsed = 0 #time used this turn
        
        self.spamToggle = False

        
        self.promptTime = 5 
        self.startLives = 2
        self.maxLives = 3
        self.currentLives = 2 




        ## list unpacking. do this for convenient use cuz we dont want to have to get the variables from the settings list in each method
        [
            self.selectMode,
            self.regenIfNeeded,
            self.sneakyRegen,
            self.timeConstraint,
            self.stockpile,
            self.greedLong,
            self.dynamicRate,
            self.cyberbullying,
            self.burstType,
            self.mistakes,
            self.dynamicPauses,
            self.spamType,
            self.saveInvalid,
            self.defaultWait,
            self.minWait,
            self.rate,
            self.burstRate,
            self.burstChance,
            self.rateJiggle,
            self.mistakeChance,
            self.mistakePause,
            self.spamRate,
            self.miniPause,
            self.jiggle
        ] = list(settings.values())

        self.client = Client(proxy=proxy)


        

    def joinRoom(self, roomCode: str, username: str = '') -> bool:
        return self.client.joinRoom(roomCode=roomCode,username=username)
       

    def main_loop(self):
        originalAlphabet = [] #original bonus self.bonusAlphabet
        originalBurstChance = self.burstChance
        used = set() #used words this session
        used.update(self.invalid) #add invalid words to used so they are not used again
        
        while True:
            try:
                if self.client.disconnect_check():
                    break

                if self.client.try_join_round():
                    originalAlphabet = self.client.get_bonus_alphabet()
                    self.promptTime = self.client.get_prompt_time()
                    self.startLives = self.client.get_start_lives()
                    self.currentLives = self.startLives
                    self.maxLives = self.client.get_max_lives()
                    self.client.clear_life_trackers()
                    
                    used = set()
                    used.update(self.invalid)

                    self.franticToggle = False
                    self.spamToggle = False


                if self.client.get_self_turn(): 
                    #get answer
                    syll = self.client.get_syllable()
                    discontinuity = False

                    ans = self.eval(syll, used)
                    if ans == "/suicide":
                        self.console.info(f"could not find answer for syllable: {syll}")
                    else:
                        self.console.info(f"found answer {ans} for syllable {syll}")
                    

                    if self.cyberbullying and self.client.get_players() < 3 and (not self.client.safe_typer(ans) or self.client.get_syllable() != syll): #checks if cyberbullying is active, then performs safetyper and/or detects discont.
                        discontinuity = True
                    else:
                        #waiting logic

                        wait = self.defaultWait

                        if self.dynamicPauses:
                            func = lambda w: min(
                                max(0, 
                                    self.promptTime-self.timeUsed if self.dynamicRate else self.promptTime-self.timeUsed-(self.rate)*(1+self.rateJiggle/3**0.5)*len(ans)), #capped at remaining time or remaining time - time taken to type if not dynamicRate
                                (self.minWait + self.burstRate*len(w) + 0.5*self.promptTime*((max(0, 7 - zipf_frequency(w,"en")))/6)**1.5) * (1 + random.choice((-1, 1))*random.uniform(0, self.jiggle))) 
                            wait = func(ans)

                        sleep(wait)
                        self.timeUsed += wait
                        

                        if self.spamType and len(ans) >= 20 or self.spamToggle:
                            self.console.info('spam on')
                            spam = self.formatSpam()
                            if not self.client.safe_typer(spam):
                                discontinuity = True
                            else:
                                sleep(self.miniPause)
                                self.timeUsed+=self.miniPause
                            self.timeUsed+=self.spamRate*len(spam)
                        

                        if self.dynamicRate:
                            self.rate = min(self.burstRate, (self.promptTime-self.timeUsed)/((1 + self.rateJiggle / (3**0.5))*len(ans))) #margin of error for each letter is accounted for

                        if self.client.get_syllable() == syll:
                            if not self.client.safe_typer(self.formatSimType(ans)):
                                discontinuity = True 
                        else:
                            discontinuity = True
                        
                    
                    #change flags and update used words
                    if not discontinuity:
                        used.add(ans)

                        self.burstChance = originalBurstChance
                        self.spamToggle = False

                        lifeChange = self.client.get_life_change() 
                        self.currentLives += lifeChange

                        wrong = bool(self.client.get_syllable() != syll)

                        if (self.currentLives == 1 or wrong): ##if you are on the verge of dying or answered wrong
                            self.burstChance = min(1.0, originalBurstChance* 2)
                            self.console.info('frantic on')

                        if lifeChange < 0 and self.spamType:#if life lost this round, spam next round
                            self.spamToggle = True
                            self.console.info('spam on')

                        if wrong: #if incorrect, add to invalid list
                            self.invalid.add(ans)
                        else:
                            self.timeUsed = 0 #only reset timeUsed if correct
                            #if correct, prune bonus alphabet for letters in used answer
                            self.bonusAlphabet = list((Counter(self.bonusAlphabet) - Counter(ans)).elements())
                            self.console.info(f"remaining {self.bonusAlphabet} after pruning")

                            if len(self.bonusAlphabet) < 1: #no need to add to currentLives, since that happens automatically
                                self.bonusAlphabet = originalAlphabet.copy()
                                self.console.info(f"{self.bonusAlphabet} after regen reset")
            except KeyboardInterrupt:
                self.console.info("User aborted Bot")
                break



    def eval(self, syll:str, used:set): #eval
        ans = '/suicide'
        alph = self.bonusAlphabet
        mode = self.selectMode
        ansSet = self.dicts[syll].copy() #set
        ansSet -= used

        if ansSet and len(ansSet) < 1:
            return ans

        long = lambda: max(ansSet, key=len)
        short = lambda: min(ansSet, key=len)
        avgLen = round((len(short())+len(long()))/2)
        avg = lambda: min(ansSet, key = lambda word: abs(len(word)-avgLen))#minimize difference from the averageLen
        common= lambda: max(ansSet, key=lambda word: word_frequency(word, "en"))
        regen = lambda: max(ansSet, key= lambda word: len(set(word) & set(alph))) #maximum shared letters
        regenSpec = lambda num: max(ansSet, key= lambda word: (len(set(word) & set(alph))<=num,len(set(word) & set(alph))))#returns the one that will give the most number of shared letters possible without going over the threshold
        sneakyRegenSpec = lambda num: max(ansSet, key= lambda word: (len(set(word) & set(alph))<=num,zipf_frequency(word,"en")+len(set(word) & set(alph))))
        realistic = lambda: max(ansSet, key= lambda word:zipf_frequency(word,"en")+len(set(word) & set(alph))) #maximum shared letters while also accounting for regen

        
        if self.timeConstraint and ((len(ans)*self.rate if not self.dynamicRate else len(ans)*self.rate*(1 + self.jiggle / (3**0.5))) > self.promptTime-self.timeUsed):
            self.console.info('time constraint; using shortest')
            ans = short()

        elif self.regenIfNeeded and self.currentLives == 1 and self.maxLives != 1:
            ans = regen()

        elif self.sneakyRegen and self.currentLives < self.maxLives:
            ans = realistic()

        elif self.stockpile and self.maxLives != 1:
            if len(alph)>1:
                if self.sneakyRegen:
                    ans = sneakyRegenSpec(len(alph)-1)
                else:
                    ans = regenSpec(len(alph)-1)
            elif alph[0] not in syll:
                temp = {word for word in ansSet if alph[0] not in word} #its possible in niche circumstances that no solve exists that doesnt include a certain letter, even if it isnt required by the syll
                ansSet = temp if len(temp)>0 else ansSet #probably a terrible way to do it but oh well
            
        elif mode == 'long':
            ans = long()

        elif mode == 'short':
            ans = short()

        elif mode == "average":
            ans = avg()
        
        elif mode == 'regen':
            ans = regen()
        
        elif mode == "common":
            ans = common()
        
        elif mode == "realistic":
            ans = realistic()
        else:
            ans = random.choice(ansSet)

        return ans
        


    def formatSpam(self) -> list:
        length = random.randint(7,15)
        txt = [random.choice(ascii_lowercase) for i in range(0,length)] #needed so that it does the choice each time
        ratesList = [self.spamRate for i in range(0,length)]
        return list(zip(txt, ratesList))



    def formatSimType(self, txt : str) -> list: ##tool
        rand = lambda x: x*(1+random.choice((-1, 1))*random.uniform(0, self.rateJiggle))
        ratesList = []
        txtList = []
    
        for letter in txt:
            #add mistake (char and delay)
            if self.mistakes and (random.random() <= self.mistakeChance) and letter in MISTAKE_MAP.keys(): #think about having mistakechance scale with typespeed
                mistakechars = MISTAKE_MAP[letter]

                txtList.append(random.choice(mistakechars))
                ratesList.append(self.mistakePause)
                self.timeUsed+=self.mistakePause

                txtList.append(Keys.BACKSPACE)
                ratesList.append(self.miniPause) 
                self.timeUsed+=self.miniPause
            txtList.append(letter)

            #add delay
            if self.burstType and (random.random() <= self.burstChance) and not self.dynamicRate:
                ratesList.append(self.burstRate)
                self.timeUsed += self.burstRate
            else:
                ratesList.append(rand(self.rate))
                self.timeUsed+=self.rate

        return list(zip(txtList, ratesList))
