# 💣 bomb_party_bot  
> *hexakosioihexekontahexaphobia🗣️🔥💯*

A (kinda) advanced Bomb Party bot and Bot Manager built in Python with Selenium.  
Designed to reconnect automatically, cycle proxies, and mimic realistic human typing.

---

## 🚀 Features

- 🤖 **Bot Manager**  
  Handles bot persistence, auto-reconnect, and proxy rotation.
- 📖 **Custom Dictionary**  
  Load your own wordlists (plaintext or URLs).
- 🛡️ **Proxy Support**  
  Optional rotating or static proxy support to counter IP bans.
- 🛠️ **Human-Like Typing**  
  Adjustable typing rates, mistake generation, burst typing, and smart delays to mimic human behavior.
- ⚙️ **Easy Configuration**  
  Fine-tune settings with simple config files.

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
```

Alternatively, go to releases and download the compressed source code, then extract it to your desired file location.

```bash
# 2. navigate to the project folder
cd path_to_folder

# 3. Install requirements
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Settings (`settings.config`)

Settings are loaded from `settings.config` and can be customized. 

DISCLAIMER: Only change the ones you understand, otherwise some weird behavior might happen. 

Settings should stay in the order they appear.

Example:

```
selectMode:regen
cyberbullying:False
defaultWait:1.5
minWait:0.8
rate:0.08
burstType:True
burstRate:0.05
burstChance:0.07
randomness:0.3
mistakes:True
mistakeChance:0.05
mistakePause:0.5
franticType:True
franticRate:0.06
dynamicPauses:True
scaleFactor:0.02
spamType:True
spamRate:0.015
miniPause: 0.2
useDefunct:True
```

| Setting | Description |
| :------ | :----------- |
| `selectMode` | `'smart'`, `'short'`, `'avg'`, `'regen'`, or `'long'` — the bot prioritizes words according to the selected mode |
| `cyberbullying` | Instant type if only one player remains |
| `defaultWait` | Default delay before typing if dynamic type is not selected |
| `minWait` | Minimum delay before typing if dynamic type is selected |
| `rate` | Base typing speed (seconds per character) |
| `burstType` | Enable fast “burst” typing |
| `burstRate` | Typing speed during bursts |
| `burstChance` | Chance of burst per character |
| `randomness` | Variance in typing rate (percentage aaaas decimal) |
| `mistakes` | Enable typo simulation |
| `mistakeChance` | Chance of typo per character |
| `mistakePause` | Delay when fixing a typo |
| `franticType` | Type faster after mistakes or with long words |
| `franticRate` | Typing speed during frantic |
| `dynamicPauses` | Adjust typing delay by word frequency and length of word |
| `scaleFactor` | Internal variable used in dynamic pause function |
| `spamType` | Spam type before long answers |
| `spamRate` | Typing speed during spam |
| `miniPause` | Short pause after spam or mistake correction |
| `useDefunct` | Ignores used words saved in defunct.config |

---

### Proxies (`proxies.config`)

Format:

```
ip:port:user:password
ip:port
```

Both authenticated and unauthenticated proxies are supported.

---

### Dictionaries (`dictionaries.config`)

Add word sources by URL or directly as plaintext words.

Example URLs:

```
https://raw.githubusercontent.com/YoungsterGlenn/bpDictionaryStatistics/master/dictionary.txt
https://norvig.com/ngrams/sowpods.txt
https://norvig.com/ngrams/enable1.txt
```

Example words:

```
hyperventilate
photosynthesis
xylophone
```

---

### Defunct Words (`defunct.config`)

Set the useDefunct flag in settings.config to enable saving and loading incorrect words.

The bot will ignore words in the defunct.config file.

---

## 🏃 Usage

Navigate to the src folder:

```bash
cd src
```

Run the bot:

```bash
python3 bomb_party_bot.py
```

You’ll be prompted for:

- **Room Code** (e.g. `ABCD`)  
- **Username** (leave blank for random or type your own)

The Bot Manager will then:

- Load your configs  
- Load proxies & dictionaries  
- Spawn and manage the bot (Bot.py)  
- Reconnect automatically if banned/disconnected  

---

## 🙏 Credits

- [JKLM.fun](https://jklm.fun) for Bomb Party  
- Open source wordlists  
- Summer break  
- hexakosioihexekontahexaphobia  
