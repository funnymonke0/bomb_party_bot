import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
import keyboard
from time import sleep


class BPB():
    def __init__(self, dicts):
        # self.dicts = dicts
        # self.blob = self.load()
        
        options = webdriver.FirefoxOptions()
        self.driver = webdriver.Firefox(options=options)
    
    def load(self):
        blob = []
        for url in self.dicts:
            r = requests.get(url)
            soup = BeautifulSoup(r.content, 'html.parser')
            blob += [*soup.get_text().lower().split()]
        blob.sort()
        return blob
    
    def find(self, suffix):
        list = []
        for wrd in self.blob:
            if suffix.lower() in wrd:
                list.append(wrd)
        return list
    

    
    def join(self, roomCode):
        browser = self.driver
        browser.get("https://jklm.fun/"+roomCode)
        iFrame = None
        WebDriverWait(browser, 5)
        submit = browser.find_element(By.XPATH, "/html/body/div[2]/div[3]/form/div[2]/button")
        submit.click()
        WebDriverWait(browser, 5)
        
        try:
            iFrame = browser.find_elements(By.XPATH, "/html/body/div[2]/div[4]/div[1]/iframe") [0]
        except NoSuchElementException:
            print("not found")
            pass
        else:
            print("found")
            browser.switch_to.frame(iFrame)
            
        try:
            autojoin = browser.find_element(By.CLASS_NAME, "autojoinButton styled")
            autojoin.click()
        except NoSuchElementException:
            print("no autojoin found")
            pass
        try:
            join = browser.find_element(By.CLASS_NAME, "styled joinRound")
            join.click()
        except NoSuchElementException:
            print("no join button found")
            pass
        browser.switch_to.default_content()
        
        
        while not keyboard.is_pressed("q"):
            # try:
            #     browser.switch_to.frame(iFrame)
            #     textbox = browser.find_element(By.XPATH, "/html/body/div[2]/div[3]/div[2]/div[2]/form/input")
            #     textbox.click()
            #     textbox.send_keys("a")
            #     browser.switch_to.default_content()
            #     # textbox.send_keys(ans+Keys.ENTER)
            # except NoSuchElementException:
            #     print("no txt found")
            #     pass
            try:
                browser.switch_to.frame(iFrame)
                syllable = browser.find_element(By.CLASS_NAME, "syllable").text
                browser.switch_to.default_content()
                print(syllable)
                # ans = self.find(syllable)[0] 
            except NoSuchElementException:
                print("no syllable found")
                pass
            
        browser.quit()
        

            
        

bot = BPB(["https://norvig.com/ngrams/sowpods.txt", "https://norvig.com/ngrams/enable1.txt","https://pastebin.com/raw/UegdKLq8"])
##bot = BPB(["https://norvig.com/ngrams/sowpods.txt"])

link = str(input("paste code: ")).upper()
bot.join(link)

    