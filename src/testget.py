import requests
from bs4 import BeautifulSoup
import time

dictUrls = ['https://norvig.com/ngrams/sowpods.txt',
'https://norvig.com/ngrams/enable1.txt',

'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/chemicals.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/creatures.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/foods.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/fruit.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/games.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/generic.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/hobbies.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/hyphens.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/instruments.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/longs.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/minerals.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/insults.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/phobias.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/plants.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Main/professions.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Personal/apostrophe.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub1.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub2.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub3.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub4.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub5.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub6.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub7.txt',
'https://raw.githubusercontent.com/NachozQ/BombParty-Lists/refs/heads/main/Sub/sub8.txt',
'https://raw.githubusercontent.com/mannny7/BombPartyBotJKLM/refs/heads/main/wordlist',
'https://raw.githubusercontent.com/carreb/bombparty-practice/main/dict/hyphen-dict.txt']
for url in dictUrls:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    clean_text = soup.get_text(separator='\n', strip=True)
    if '404' in clean_text:
        with open('error_log.txt', 'a') as f:
            f.write(f"Error: The URL {url} returned a 404 error.\n")