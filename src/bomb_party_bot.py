import asyncio
import re
from os.path import exists, join
from BotManager import BotManager
if __name__ == "__main__" :
    config = "config"
    proxies = join(config, 'proxies.config') ##adjust to autorecognize
    settings = join(config,'settings.config')
    dictionaries = join(config,'dictionaries.config')
    defunct = join(config,'defunct.config')
    if exists(config) and exists(proxies) and exists(settings) and exists(dictionaries) and exists(defunct):
        
        

        
        
        try:
            link = str(input("paste code: ")).upper()
            name = str(input("username: "))

            if re.match(link, r'^[a-zA-Z]{4}$'):
                print('ERROR: Must input valid room code !')
                quit()
            if len(name) < 1:
                name = None
                
            manager = BotManager(dictFile=dictionaries, roomCode=link, proxyFile=proxies, username=name, settingsFile=settings, defunctFile = defunct)

            asyncio.run(manager.persistLoop())
        except KeyboardInterrupt:
            print("Session interrupted by user")
        except asyncio.exceptions.CancelledError:
            print("Session cancelled")
        except Exception as e:
            print(f"Exception occurred")


        
    
    print("Cleaning up bot...")  # Graceful exit message
    quit()  # Ensure the script exits cleanly