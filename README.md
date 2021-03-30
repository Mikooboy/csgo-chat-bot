# CS:GO Chat Bot

A chat bot for CS:GO that reads the CS:GO console over telnet. The chat commands can be sent using the chat or using `echo <command>` in the console.

Huge thanks to [@403-Fruit](https://github.com/403-Fruit) for sharing [this project](https://github.com/403-Fruit/csctl)! The project helped me a lot when figuring out how to do things.

## Setup

    git clone https://github.com/Mikooboy/csgo-chat-bot
    cd csgo-chat-bot
    pip3 install -r requirements.txt

Add the following to the CS:GO launch options:

    -netconport 2121  

Run the chat bot:

    python cscb.py

Add your Steam and faceit API keys to the `config.py` file to get the `!info` command to work fully:

    steam_api_key = '' # Steam web API key here to get steam/game stats
    faceit_api_key = '' # Faceit API key here to get faceit levels
    
**Note**: Use the full authorization string for the faceit_api_key: `'Bearer <api_key>'`

## Commands

    !help        - Prints out the list of avaible commands to the chat
    
    <name> !info - Tries to get <name>'s game stats including: K/D ratio, Play time and 
                   total rounds played on the current map.
                 - Example:
                     miko !info
                   returns: 
                     Miko | Hours: 1595 K/D: 1.13 HS: 42% cs_italy: 86 rounds Faceit: lvl 3

    *all* !info  - Get the info table containing all the players in the game
                 - This prints the whole table in easy to read format to the cmd
                      
    <math> !calc - Calculates the math expression in <math> and returns the answer
                 - Example:
                     (5 + 5) * 2 !calc
                   returns:
                     (5 + 5) * 2 = 20
  
    !swquote     - Prints out a random Star Wars quote

    !bot         - Prints info about the bot to the chat

    !clan        - Starts cycling through the clans listed in the `config.py` file
                 - Used for animating the steam group on scoreboard
                 - You need to be a member of the groups in the `config.py` file
    
    !abort_clan  - Stops cycling through the clans

    !clear       - Sends a long empty chat message that "clears" the chat
                 - Run this through the console or a keybind
