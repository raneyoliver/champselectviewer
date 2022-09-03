from lcu_driver import Connector
import json
import requests

req_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": "RGAPI-01fb97bd-731d-4f83-85a6-da99fe519d04"
}

file = "C:\\Users\\Oliver\\Documents\\PythonProjects\\champselect\\browsersource\\champselectsite\\content\\description.md"
previous_players = ["-1", "-1", "-1", "-1", "-1"]
prev_description = ""
connector = Connector()

# fired when LCU API is ready to be used
@connector.ready
async def connect(connection):
    print('LCU API is ready to be used.')


# fired when League Client is closed (or disconnected from websocket)
@connector.close
async def disconnect(_):
    print('The client have been closed!')
    await connector.stop()

@connector.ws.register(f'/lol-champ-select/v1/summoners/', event_types=('UPDATE',))
async def select_started(connection, event):
    global prev_description  # To keep track of what's there already

    summoner_ids = ["", "", "", "", ""]
    summoner_puuids = ["", "", "", "", ""]
    display_names = ["", "", "", "", ""]
    ranks = ["", "", "", "", ""]
    games_played = ["", "", "", "", ""]
    winrates = [-1.0, -1.0, -1.0, -1.0, -1.0]
    for i in range(5):
        # Get Summoner IDs (lol-champ-select/v1/summoners/slotId)
        id_info = await connection.request('get', f'/lol-champ-select/v1/summoners/{i}')
        data = await id_info.json()
        summoner_ids[i] = data['summonerId']

        # No Summoner in slot i
        if summoner_ids[i] == 0:
            continue

        # Get Display Names and PUUIDs (lol-summoner/v1/summoners/id)
        puuid_info = await connection.request('get', f'/lol-summoner/v1/summoners/{summoner_ids[i]}')
        data = await puuid_info.json()
        summoner_puuids[i] = data['puuid']
        display_names[i] = data['displayName']

        # Get Ranks, Winrates, Games Played (lol-ranked/v1/ranked-stats/puuid)
        encrypted_info = requests.get(f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{display_names[i]}', headers=req_headers)
        data = json.loads(encrypted_info.text)
        #print(json.dumps(data, indent=4))
        encrypted_summoner_id = data["id"]
        #print(encrypted_summoner_id)
        
        
        ranked_info = requests.get(f'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}', headers=req_headers)
        #ranked_info = await connection.request('get', f'/lol-ranked/v1/ranked-stats/{summoner_puuids[i]}')
        data = json.loads(ranked_info.text)
        #data = await ranked_info.json()
        wins = int(data[0]["wins"])
        losses = int(data[0]["losses"])
        tier = data[0]["tier"]
        division = data[0]["rank"]
        lp = data[0]["leaguePoints"]

        ranks[i] = f"{tier} {division} {lp} LP"
        games_played[i] = wins + losses
        winrates[i] = round(float(wins / games_played[i]) * 100, 1)

    # Return & empty description if not in Champ Select
    if summoner_ids[0] == "0":
        prev_description = ""
        with open(file, "w") as f:
            f.write(prev_description)
        return

    # Don't update if not necessary
    global previous_players # global: use the one defined outside this function
    if previous_players == summoner_ids:
        return
    else:
        previous_players = summoner_ids
    
    description = ""
    if not summoner_ids[0] == 0:
        description = "IN CHAMP SELECT\n\n"

    for k in range(5):
        if summoner_ids[k] == 0:
            continue

        description += f"{display_names[k]}: {ranks[k]}\n"
        description += f"WR: {winrates[k]}% ({games_played[k]} games)\n\n"

    # Check if nothing changed
    if description == prev_description:
        return
    else:
        prev_description = description

    # Write to champselectdata.txt in this folder
    with open(file, "w") as f:
        f.write(description)

connector.start()