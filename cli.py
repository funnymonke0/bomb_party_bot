import re
from os.path import exists, join
from pathlib import Path
from bomb_party_bot.BotManager import BotManager


def run() -> None:
    root_dir = Path(__file__).resolve().parent
    config_dir = root_dir / "config"
    proxies = str(config_dir / 'proxies.config') ##adjust to autorecognize?
    settings = str(config_dir / 'settings.json')
    dictionaries = str(config_dir / 'dictionaries.config')
    invalid = str(config_dir / 'invalid.config')
    if exists(config_dir) and exists(proxies) and exists(settings) and exists(dictionaries) and exists(invalid):

        link = str(input("paste code: ")).upper()
        name = str(input("username: "))

        if not link or len(link) != 4 or not re.match(r'^[a-zA-Z]{4}$', link):
            print('ERROR: Must input valid room code !')
        else:
            manager = BotManager(dict_file=dictionaries, room_code=link, proxy_file=proxies, username=name, settings_file=settings, invalid_file=invalid)

            manager.persist_loop()

    else:
        print("Some config files not found!")

        
    
    print("Cleaning up")  # Graceful exit message
    quit()  # Ensure the script exits cleanly

if __name__ == "__main__" :
    run()