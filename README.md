# 💣 Bomb Party Bot  
> *hexakosioihexekontahexaphobia🗣️🔥💯*

A (kinda) advanced Bomb Party bot and Bot Manager built in Python with Selenium.  
Handles auto-reconnects, proxy rotation, human-like typing, and bonus-letter strategy.

---

## 🚀 Features

- 🤖 **Bot Manager**  
  Handles bot persistence, auto-reconnect, and proxy rotation. Tracks lives and adjusts behavior dynamically.

- 📖 **Custom & Multi-Source Dictionaries**  
  Load your own wordlists via plaintext or URLs. Supports multiple sources simultaneously.

- 🛡️ **Proxy Support**  
  Supports static and authenticated proxies with automatic fallback if a proxy fails.

- 🛠️ **Human-Like Typing**  
  - Dynamic typing delays based on word length, frequency, and typing randomness  
  - Burst typing, frantic typing (when low on lives or after mistakes), and typo simulation  
  - Spam typing for long answers or after losing lives  

- ⚙️ **Fine-Grained Settings**  
  Configure detailed behavior for typing, word selection, and bonus-letter strategy.  

- 🧠 **Intelligent Word Selection**  
  Modes include:
  - `'smart'`, `'short'`, `'average'`, `'regen'`, `'long'`, `'common'`, `'realistic'`  
  - Special strategies like `sneakyRegen`, `regenIfNeeded`, and stockpiling bonus letters  

- 🧩 **Configurable Mistakes**  
  Simulates typos with `mistakeChance` and adjacent-key selection via `MISTAKE_MAP`.

---

## 🛠️ Built With

- Python 🐍  
- Selenium WebDriver  
- Selenium Wire (for proxy)  
- wordfreq (for frequency-based typing)

---

## 🧩 Installation

```bash
# Clone the repo
git clone https://github.com/funnymonke0/bomb_party_bot.git

# Navigate to project folder
cd bomb_party_bot

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Detailed Settings (`settings.config`)

All settings are loaded from `settings.config`. Change only what you understand.

```text
selectMode:               # word selection mode: smart/short/average/regen/long/common/realistic
regenIfNeeded:            # trigger regen mode on last life
sneakyRegen:              # prioritize less common letters when under max lives
timeConstraint:           # pick shortest word if typing time is tight
stockpile:                # conserve bonus letters
greedLong:                # prioritize long words when stockpiling
dynamicRate:              # adjust typing speed per letter
cyberbullying:            # auto-type if <3 players
burstType:                # enable burst typing
mistakes:                 # enable simulated typos
dynamicPauses:            # adjust typing delay based on word length/frequency
spamType:                 # spam typing after long answers or mistakes
saveInvalid:              # save invalid words to defunct file
defaultWait:              # base wait time before typing
minWait:                  # minimum wait time
rate:                     # base typing speed per character
burstRate:                # speed during bursts
burstChance:              # chance of burst per character
rateJiggle:               # typing randomness multiplier
mistakeChance:            # chance of a typo per character
mistakePause:             # delay for correcting a typo
spamRate:                 # speed for spam typing
miniPause:                # short pause after spam/mistakes
jiggle:                   # extra randomness for dynamic pauses
```

---

## 📖 Proxies (`proxies.config`)

```
ip:port:user:password
ip:port
```

Supports authenticated and unauthenticated proxies.

---

## 📖 Dictionaries (`dictionaries.config`)

- Add word sources by URL:

```
https://raw.githubusercontent.com/YoungsterGlenn/bpDictionaryStatistics/master/dictionary.txt
https://norvig.com/ngrams/sowpods.txt
https://norvig.com/ngrams/enable1.txt
```

- Or add individual words:

```
hyperventilate
photosynthesis
xylophone
```

---

## 📖 Invalid Words (`invalid.config`)

- Words the bot has already used incorrectly are stored here if `saveInvalid` is enabled.  
- Bot avoids using these words again.

---

## 🏃 Usage

```bash
cd src
python3 bomb_party_bot.py
```

You’ll be prompted for:

- **Room Code** (e.g., `ABCD`)  
- **Username** (leave blank for random)

The Bot Manager will:

- Load your settings, proxies, and dictionaries  
- Spawn and manage the bot  
- Reconnect automatically if disconnected  
- Handle bonus letters, typing, mistakes, and spam automatically  

---

## ⚡ Quickstart (Simplified)

1. Clone repo and install dependencies:

```bash
git clone https://github.com/funnymonke0/bomb_party_bot.git
cd bomb_party_bot
pip install -r requirements.txt
```

2. Configure your proxies (optional) in `proxies.config`.

3. Add dictionaries in `dictionaries.config`. Defaults are safe.

4. (Optional) Adjust typing and bot behavior in `settings.config`. Defaults are safe.

5. Run the bot:

```bash
cd src
python3 bomb_party_bot.py
```

6. Enter your room code and username (or leave blank for random).

The bot will automatically handle typing, mistakes, bursts, spam, bonus letters, and reconnections.  

---

## 🙏 Credits

- [JKLM.fun](https://jklm.fun) for Bomb Party  
- Open source wordlists  
- Summer break  
- hexakosioihexekontahexaphobia  
