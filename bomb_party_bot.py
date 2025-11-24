import re
from os.path import exists, join
from src.BotManager import BotManager
if __name__ == "__main__" :

    config = "config"
    proxies = join(config, 'proxies.config') ##adjust to autorecognize?
    settings = join(config,'settings.config')
    dictionaries = join(config,'dictionaries.config')
    invalid = join(config,'invalid.config')
    if exists(config) and exists(proxies) and exists(settings) and exists(dictionaries) and exists(invalid):

        link = str(input("paste code: ")).upper()
        name = str(input("username: "))

        if re.match(link, r'^[a-zA-Z]{4}$'):
            print('ERROR: Must input valid room code !')
        else:
            manager = BotManager(dictFile=dictionaries, roomCode=link, proxyFile=proxies, username=name, settingsFile=settings, invalidFile = invalid)

            manager.persistLoop()

    else:
        print("Some config files not found!")

        
    
    print("Cleaning up")  # Graceful exit message
    quit()  # Ensure the script exits cleanly