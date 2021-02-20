import sys
import telnetlib
import psutil
import signal
import binascii
import random
import datetime
import re
import hashlib
import requests
import shlex
import os
import time
import pickle
import asyncio
import concurrent.futures
from pydicti import dicti
from threading import Thread
from texttable import Texttable
from math import *
from random import randrange
from termcolor import colored
from time import sleep
from os import path
import config as cfg

levels = {}
done = 0

def run(txn, command):
	cmd_s = command + "\n"
	txn.write(cmd_s.encode('utf-8'))
	sleep(0.005)

def steamid_to_64bit(steamid):
    steam64id = 76561197960265728 # I honestly don't know where
                                    # this came from, but it works...
    id_split = steamid.split(":")
    steam64id += int(id_split[2]) * 2 # again, not sure why multiplying by 2...
    if id_split[1] == "1":
        steam64id += 1
    return steam64id

def get_name(results):
    info_line 	= results[len(results) - 1]
    splitted    = info_line.split(" : ")
    name 		= splitted[len(splitted) - 1]

    if (len(name) <= 5):
        name = ""
    else:
        name = name[:len(name) - 6]

    return name

def get_players_and_map(name, tn):
    status_start = 0
    player_lines = []

    run(tn, "status")
    status = tn.expect([b"#end"], timeout=1)
    lines = status[2].decode("utf-8").splitlines()

    lines.pop(len(lines) - 1)

    j = 0
    for i in lines:
        if "# userid" in i.lower():
            status_start = j
        j = j + 1

    player_lines = lines[status_start + 1:]

    for i in lines:
        if "map" in i.lower():
            matching_map = i
    
    mapName = matching_map.split()
    mapName = mapName[2]

    return [player_lines, mapName]

def parse_name(player_line):
    line_split = shlex.split(player_line)
    name = line_split[3]
    name = name.replace('"', "")
    return name

def parse_steamId(player_line):
    line_split = shlex.split(player_line)
    playerId = None

    for j in line_split:
        if "steam_1" in j.lower():
            playerId = j
    return playerId

def get_faceit_lvl(i, levels):
    try:
        if "BOT" in i:
            raise

        name = parse_name(i)
        playerId = parse_steamId(i)
        playerId64 = steamid_to_64bit(playerId)

        level = "N/A"

        try:
            headers = {
                'accept': 'application/json',
                'Authorization': cfg.settings["faceit_api_key"],
            }

            params = (
                ('game', 'csgo'),
                ('game_player_id', playerId64),
            )

            response = requests.get('https://open.faceit.com/data/v4/players', headers=headers, params=params, timeout=5)
            response = response.json()
            level = response['games']['csgo']['skill_level']
        except:
            pass
    except:
        pass
    try:
        levels[name] = level
    except:
        pass

    return levels

def get_steam_stats(i, mapName, info_list):
    kdratio 	= "N/A" # Kill Death Ratio
    timeplayed 	= "N/A" # time played
    rounds 		= "N/A"
    hs 			= "N/A"

    info 		= "N/A"
    game_info 	= True
    hour_info 	= True
    no_info 	= False

    try:
        if "BOT" in i:
            raise
                
        name = parse_name(i)
        playerId = parse_steamId(i)
        
        playerId64 = steamid_to_64bit(playerId)

        key = cfg.settings["steam_api_key"]

        url 	= 'https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v0002/?appid=730&key=' + key + '&steamid='
        url2 	= 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=' + key + '&steamid='
        final_url 	= url + str(playerId64)
        final_url2 	= url2 + str(playerId64)

        try:
            r = requests.get(final_url).json()
            stats = {
                'total_kills' 	: "N/A",
                'total_deaths' 	: "N/A",
                'headshots' 	: "N/A",
                'map_rounds'	: "N/A",
            }

            for j in (r['playerstats']['stats']):
                id = j['name']
                if (id == "total_kills"):
                    stats['total_kills'] = j['value']

            for j in (r['playerstats']['stats']):
                id = j['name']
                if (id == "total_deaths"):
                    stats['total_deaths'] = j['value']
            
            for j in (r['playerstats']['stats']):
                id = j['name']
                if (id == "total_kills_headshot"):
                    stats['headshots'] = j['value']

            for j in (r['playerstats']['stats']):
                id = j['name']
                if ("rounds" in id) and (mapName in id):
                    stats['map_rounds'] = j['value']

            kd = stats['total_kills']/stats['total_deaths']
            hs = (stats['headshots']/stats['total_kills'])*100

            rounds 	= stats['map_rounds']
            kdratio = str("{:.2f}".format(kd))
            hs 		= str(floor(hs))
        except:
            game_info = False
            
        try:
            r2 = requests.get(final_url2).json()
            games = r2['response']['games'] #total time played

            for j in games:
                id = j['appid']
                if (id == 730):
                    time_played = j['playtime_forever']

            hours = time_played/60

            if (hours >= 1):
                timeplayed 	= str(floor(hours))
        except:
            hour_info = False
        
        if (not game_info) and (not hour_info):
            info = ("Game and hour info private")
            no_info = True
        elif (not game_info):
            info = ("Game info private")
            no_info = True
        elif (not hour_info):
            info = ("Hour info private")
            no_info = True

        if (no_info == False):
            info = ("Hours: " + str(timeplayed) + " K/D: " + str(kdratio) + " HS: " + str(hs) + "%" + " " + str(mapName) + ": " + str(rounds) + " rounds")
    except:
        pass
    try:
        info_list[name] = info
    except:
        pass
    return info_list

def getInfo(name, tn):
    threads     = []
    threads2    = []

    matching 	= []

    PlayersAndMap = get_players_and_map(name, tn)
    players = PlayersAndMap[0]
    mapName = PlayersAndMap[1]

    if (name == "*all* "):
        matching = players
    else:
        for i in players:
            if name.lower() in i.lower():
                matching.append(i)

    if (len(matching) == 0):
        run(tn, "say Error: Invalid name")
        print("Error: Invalid name")
    else:
        levels    = dicti()
        info_list = dicti()
        print("Getting info")
        try:
            table = Texttable()
            table.set_max_width(150)

            print("Fetching info from APIs...")
            for i in matching:
                try:
                    t1 = Thread(target=get_faceit_lvl, args=(i, levels))
                    threads.append(t1)
                    t2 = Thread(target=get_steam_stats, args=(i, mapName, info_list))
                    threads2.append(t2)
                except:
                    pass
        except:
            pass

        [ t1.start() for t1 in threads ]
        [ t2.start() for t2 in threads2 ]
        [ t1.join() for t1 in threads ]
        [ t2.join() for t2 in threads2 ]
    
        for i in info_list:
            info = info_list[i]
            for j in levels:
                try:
                    if str(i) == str(j):
                        info = info.split()
                        if (len(info) <= 5):
                            info = " ".join(info)
                            info = str(info) + " | Faceit lvl: " + str(levels[j])
                        else:
                            info = info[0] + " " + info[1] + " " + info[2] + " " + info[3] + " " + info[4] + " " + info[5] + " Faceit lvl: " + str(levels[j]) + " " + info[6] + " " + info[7] + " " + info[8]
                        info_list[i] = info
                        table.add_row([i, info])
                except:
                    pass
        
        print(table.draw())

        return info_list
    pass