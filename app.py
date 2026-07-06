from flask import Flask, render_template, request, jsonify
from BotManager import BotManager
import os
import json
import threading

config = "config"
proxies_file = os.path.join(config, 'proxies.config') ##adjust to autorecognize?
settings_file = os.path.join(config,'settings.json')
dictionaries_file = os.path.join(config,'dictionaries.config')
invalid_file = os.path.join(config,'invalid.config')

app = Flask(__name__)
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = {}
    with open(settings_file, 'r') as f:
        settings = json.load(f)
    return jsonify(settings)

@app.route('/api/launch', methods=['POST'])
def launch_bot():
    try:
        # 1. Grab incoming data from the HTML form
        data = request.json or {}

        settings = {}
        with open(settings_file, 'r') as f:
            settings = json.load(f)

        # 2. Extract the necessary fields from the incoming data
        username = data["username"]
        room_code = data["roomcode"]
        invalid = data["invalid"]
        dictionaries = data["dictionaries"]
        proxies = data["proxies"]

        settings = {
            "selectMode": data["selectMode"] or settings["selectMode"],
            "regenIfNeeded": data["regenIfNeeded"] or settings["regenIfNeeded"],
            "sneakyRegen": data["sneakyRegen"] or settings["sneakyRegen"],
            "stockpile": data["stockpile"] or settings["stockpile"],
            "greedLong": data["greedLong"] or settings["greedLong"],
            "timeConstraint": data["timeConstraint"] or settings["timeConstraint"],
            "cyberbullying": data["cyberbullying"] or settings["cyberbullying"],
            "mistakes": data["mistakes"] or settings["mistakes"],
            "burstType": data["burstType"] or settings["burstType"],
            "spamType": data["spamType"] or settings["spamType"],
            "dynamicRate": data["dynamicRate"] or settings["dynamicRate"],
            "dynamicPauses": data["dynamicPauses"] or settings["dynamicPauses"],
            "dynamicMistakes": data["dynamicMistakes"] or settings["dynamicMistakes"],
            "minWait": data["minWait"] or settings["minWait"],
            "maxWait": data["maxWait"] or settings["maxWait"],
            "mistakePause": data["mistakePause"] or settings["mistakePause"],
            "miniPause": data["miniPause"] or settings["miniPause"],
            "minWpm": data["minWpm"] or settings["minWpm"],
            "maxWpm": data["maxWpm"] or settings["maxWpm"],
            "spamWpm": data["spamWpm"] or settings["spamWpm"],
            "burstChance": data["burstChance"] or settings["burstChance"],
            "minMistakeChance": data["minMistakeChance"] or settings["minMistakeChance"],
            "maxMistakeChance": data["maxMistakeChance"] or settings["maxMistakeChance"],
            "spamChance": data["spamChance"] or settings["spamChance"],
            "jitterPercent": data["jitterPercent"] or settings["jitterPercent"]
        }

        # 3. Overwrite the local config.json file
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        print(f"--> [SUCCESS] settings.json updated")

        if dictionaries and len(dictionaries) > 0:
            with open(dictionaries_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(dictionaries)+'\n')
            print(f"--> [SUCCESS] dictionaries.config updated")
        else:
            print(f"--> [WARNING] No dictionaries provided, skipping update and using defaults.")

        if invalid and len(invalid) > 0:
            with open(invalid_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(invalid)+'\n')
            print(f"--> [SUCCESS] invalid.config updated")
        else:
            print(f"--> [WARNING] No invalid words provided, skipping update and using defaults.")

        if proxies and len(proxies) > 0:
            with open(proxies_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(proxies)+'\n')
            print(f"--> [SUCCESS] proxies.config updated")
        else:
            print(f"--> [WARNING] No proxies provided, skipping update and using defaults (none).")


        # 4. Launch the bot in a separate thread to avoid blocking the Flask server
        manager = BotManager(dict_file=dictionaries_file, room_code=room_code, proxy_file=proxies_file, username=username,
                             settings_file=settings_file, invalid_file=invalid_file)
        bot_thread = threading.Thread(target=manager.persist_loop, daemon=True)
        bot_thread.start()

        return jsonify({"success": True, "message": "Configuration saved! Bot running."})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500 #server side error


if __name__ == '__main__':
    # Runs web server locally on http://127.0.0.1:5000
    app.run(debug=True, port=5000)