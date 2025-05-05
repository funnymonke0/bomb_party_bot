# 💣 bomb_party_bot  
> *hexakosioihexekontahexaphobia🗣️🔥💯*

A (kinda) advanced Bomb Party bot and Bot Manager built in Python with Selenium.

---

## 🚀 Features

- 🤖 **Bot Manager**  
  Handles bot persistence, automatic reconnection, and proxy rotation.
- 📖 **Customizable Dictionary**  
  Load your own wordlists (plain text or URLs).
- 🛡️ **Proxy Support**  
  Optional Rotating or static proxy support to counter IP bans. Auto-rejoin lobbies after bans.
- 🛠️ **Dynamic Typing Simulation**  
  Adjustable typing rates, mistake generation, burst typing, and smart delays to mimic human behavior.
- ⚙️ **Custom Bot Settings**  
  Fine-tune everything from typing randomness to mistake rates with easy configuration files.

---

## 🛠️ Built With

- Python 🐍
- Selenium WebDriver
- Selenium Wire (for proxy)

---

## 🧩 Installation

```bash
# 1. Clone this repository
git clone https://github.com/funnymonke0/bomb_party_bot.git
cd bomb_party_bot

# 2. Install the requirements
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Settings

Settings are loaded from `settings.config` and can be customized. 
DISCLAIMER: Only change the ones you understand, otherwise some weird behavior might happen.

Example:

```
selectMode:avg
cyberbullying:False
maxOffset:0
rate:0.09
burstType:False
burstRate:0.04
burstChance:0
randomness:0.35
mistakes:True
mistakeChance:0.35
mistakePause:0.3
franticType:True
dynamicPauses:False
spam:True
spamRate:0.01
miniPause: 0.17
```

| Setting | Description |
| :------ | :----------- |
| `selectMode` | `'smart'`, `'short'`, `'avg'`, or `'long'` — how the bot picks answers |
| `cyberbullying` | Instant type if 1 player is remaining |
| `maxOffset` | Max delay before typing (simulates thinking before typing) |
| `rate` | Base typing speed (seconds per character) |
| `burstType` | Enable fast "burst" typing spurts |
| `burstRate` | Rate during bursts |
| `burstChance` | Chance of burst happening per character |
| `randomness` | Percent variance of typing rate |
| `mistakes` | Enable typo simulation |
| `mistakeChance` | Chance per character of mistake |
| `mistakePause` | Delay when correcting a typo |
| `franticType` | Type faster if answered wrong or if word is long |
| `dynamicPauses` | Adjust typing delay based on word frequency |
| `spam` | Spam type before answering long words to seem more realistic |
| `spamRate` | Rate of spam typing |
| `miniPause` | Realistic pause between spamming to model quick thinking |

---

### Proxies

Proxy format for `proxies.config` (with or without auth):

```
ip:port:user:password
ip:port
```

---

### Dictionaries

Add a combination of wordlists via URLs or plain words in `dictionaries.txt`.  
Example URLs:

```
https://raw.githubusercontent.com/YoungsterGlenn/bpDictionaryStatistics/master/dictionary.txt
https://norvig.com/ngrams/sowpods.txt
https://norvig.com/ngrams/enable1.txt
https://pastebin.com/raw/UegdKLq8
...
```

Plaintext:

```
hyperventilate
photosynthesis
xylophone
```

---

## 🏃 Usage

After setting up your configs, run:

```bash
python3 bomb_party_bot.py
```

You’ll be prompted to:

- Enter a **Room Code** (e.g., `ABCD`)
- Enter a **Username** (or leave blank for a random one)

The Bot Manager will:

- Load dictionaries
- Load proxies
- Spawn a bot
- Persist across disconnects and bans
- Cycle proxies if needed

---

## 🙏 Credits

- JKLM.fun for making Bomb Party
- Open wordlists
- Spring Break
- That one Youtube video
- Everyone who got mad and ragequit because of this bot 💀
