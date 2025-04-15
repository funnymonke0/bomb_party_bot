import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import keyboard
from time import sleep
from random import randint
import threading




class BPB():
    def __init__(self, dicts):
        self.dicts = dicts
        self.blob = self.load()
        self.username = 'monke'
        
        self.typeDelay = 0.075
        self.randomness = 0.0375

        # self.RUIN = True
        self.RUIN = False

        chrome_options = webdriver.ChromeOptions()
        service = webdriver.ChromeService()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def load(self):
        blob = []
        for url in self.dicts:
            r = requests.get(url)
            soup = BeautifulSoup(r.content, 'html.parser')
            blob += [*soup.get_text().lower().split()]
        
        blob = list(set(blob))

        return blob
    
    def find(self, suffix):
        lst = []
        for wrd in self.blob:
            if suffix.lower() in wrd:
                lst.append(wrd)
        return lst
    
    def findLongest(self, suffix):
        lst = self.find(suffix)
        longest = ''
        for wrd in lst:
            if len(wrd) > len(longest):
                longest = wrd
        self.blob.remove(longest)
        return longest

    def findShortest(self, suffix):
        lst = self.find(suffix)
        shortest = lst[0]
        for wrd in lst:
            if len(wrd) < len(shortest):
                shortest = wrd
        self.blob.remove(shortest)
        return shortest
    
    def waitForLoad(self):
        browser = self.driver
        wait = WebDriverWait(browser, 5)
        try:
            wait
        except TimeoutException:
            print("page took too long to load")
            pass
    
    def joinRoom(self, roomCode):
        browser = self.driver
        wait = WebDriverWait(browser, 5)

        browser.get("https://jklm.fun/"+roomCode)

        self.waitForLoad()

        textbox = browser.find_element(By.XPATH, '//input[@class = "styled nickname"]')
        textbox.send_keys(Keys.BACKSPACE + self.username)

        submit = browser.find_element(By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button")
        submit.click()

        self.waitForLoad()

        try: 
            iFrame = wait.until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'bombparty')]")))
            browser.switch_to.frame(iFrame)
            
        except TimeoutException:
            print("could not find iFrame")
            pass


    def join(self):
        
        browser = self.driver
        wait = WebDriverWait(browser, 5)
        try:
            join = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class = 'styled joinRound']")))
            join.click()
        except TimeoutException:
            print("no join found. Autojoining next round.")
            try:
                autojoin = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class = 'autojoinButton styled']")))
                autojoin.click()
            except:
                print("no autojoin found :(")
                pass
            pass

        print("new: "+ browser.page_source)
            
    def getSyll(self):
        browser = self.driver
        try:
            syllable = browser.find_element(By.XPATH, "//div[@class = 'syllable']")
            syllable = syllable.text
            print(syllable)
            return syllable
        except NoSuchElementException:
            print('waiting for syllable')
            return None
    def mainLoop(self):
        
        browser = self.driver
        wait = WebDriverWait(browser, 5)
        self.join()
        while not keyboard.is_pressed('q'):
            self.rejoin()
            

            syllable = self.getSyll()
            textbox = None
            ans = ''

            try:
                textbox = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/div[3]/div[2]/div[2]/form/input")))
                if self.RUIN:
                    ans = self.findLongest(syllable)
                else:
                    ans = self.findShortest(syllable)
                self.simType(textbox, ans)
                textbox.send_keys(Keys.ENTER)
                # textbox.send_keys(ans+Keys.ENTER) ##if you wanna get hackusated
            except TimeoutException:
                print('waiting for textbox')
                continue
            except ElementNotInteractableException:
                print('waiting for textbox')
                continue

                
        browser.quit()
        
    def rejoin(self):
        browser = self.driver
        medal = browser.find_element(By.XPATH, '//div[@class = "medal"]')
        if medal.is_displayed():
            print("rejoining")
            self.join()
            self.blob = self.load()

    def simType(self, obj, txt):
        txtArr = list(txt)
        for letter in txtArr:
            obj.send_keys(letter)
            sleep((randint(-10,10)*0.1)*self.randomness+self.typeDelay)
        



            
        
if __name__ == "__main__" :
    bot = BPB(["https://norvig.com/ngrams/sowpods.txt", "https://norvig.com/ngrams/enable1.txt","https://pastebin.com/raw/UegdKLq8"])

    link = str(input("paste code: ")).upper()
    # link = "nfue" hardcoded test room
    name = str(input("username: "))
    if name != '':
        bot.username = name
    bot.joinRoom(link)
    bot.mainLoop()