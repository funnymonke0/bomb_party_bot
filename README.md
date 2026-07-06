# Bomb Party Bot  
> *hexakosioihexekontahexaphobia*

A (kinda) advanced Bomb Party training bot and Bot Manager built in Python with Selenium.  
Handles auto-reconnects, proxy rotation, human-like typing, and bonus-letter strategy.

---

## Features

- **Bot Manager**  
  Handles bot persistence, auto-reconnect, and proxy rotation. Tracks lives and adjusts behavior dynamically.

- **Custom & Multi-Source Dictionaries**  
  Load your own wordlists via plaintext or URLs. Supports multiple sources simultaneously.

- **Proxy Support**  
  Supports static and authenticated proxies.

   **Human-Like Typing**  
  - Dynamic typing delays based on word length, frequency, and typing randomness  
  - Burst typing, frantic typing (when low on lives or after mistakes), and typo simulation  
  - Spam typing for long answers or after losing lives  

- **Word Selection Options**  
  Modes include:
  - `'sneaky'`, `'short'`, `'average'`, `'regen'`, `'long'`, `'common'`
  - Special strategies like `sneakyRegen`, `regenIfNeeded`, and stockpiling bonus letters  

- **Configurable Mistakes**  
  Simulates typos with `mistakeChance` and adjacent-key selection via `MISTAKE_MAP`.

---

## Tech Stack

- Python  
- Selenium WebDriver  
- Selenium Wire (for proxy)  
- wordfreq (for frequency-based typing)

---

## Installation

```bash
# Clone the repo
git clone https://github.com/funnymonke0/bomb_party_bot.git

# Navigate to project folder
cd bomb_party_bot

# Install dependencies
pip install -r requirements.txt
```

---

## Settings (`settings.json`)

All settings are loaded from `settings.config`. Change only what you understand, make sure types and setting keys are correct as it will throw an exception otherwise.

```text
{
    "selectMode":"common",

    "regenIfNeeded":true,
    "sneakyRegen":true,
    "stockpile":false,
    "greedLong":false,
    "timeConstraint":true,
    "cyberbullying":false,
    "mistakes":true,
    "burstType":true,
    "spamType":true,
    "dynamicRate":false,
    "dynamicPauses":true,
    "dynamicMistakes":true,

    "minWait":1.0,
    "maxWait":3.2,
    "mistakePause":0.100,
    "miniPause": 0.330,
    "minWpm":70,
    "maxWpm":120,
    "spamWpm":1000,
    "burstChance":0.50,
    "minMistakeChance":0.01,
    "maxMistakeChance":0.15,
    "spamChance":0.10,
    "jitterPercent": 0.50
}

```

---

## Proxies (`proxies.config`)

```
ip:port:user:password
ip:port
```

Supports authenticated and unauthenticated proxies.

---

## Dictionaries (`dictionaries.config`)

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

## Invalid Words (`invalid.config`)

- Words that are outdated can be stored here.
- Bot avoids using these words again.

---

## Usage

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

## Quickstart (Simplified)

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

6. Enter your room code and username (leave username blank for random).

The bot will automatically handle typing, mistakes, bursts, spam, bonus letters, and reconnections.  

---

## Improvements
- Turn it into an actual app with something like Flask
- track room codes
