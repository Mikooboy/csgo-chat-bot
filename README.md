# CS:GO Chat Bot (WIP)

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

Add your Steam Web API key to the `cscb.py` file to get the `!info` command to work:

    api_key = '' # Insert your Steam Web API key here

## Commands

    !help        - Prints out the list of avaible commands to the chat
    
    <name> !info - Tries to get <name>'s game stats including: K/D ratio, Play time and 
                   total rounds played on the current map.
                 - Example:
                     miko !info
                   returns: 
                     miko | K/D: 1.13 Hours: 1595 cs_italy: 86 rounds
                      
    <math> !calc - Calculates the math expression in <math> and returns the answer
                 - Example:
                     (5 + 5) * 2 !calc
                   returns:
                     (5 + 5) * 2 = 20
  
    !swquote     - Prints out a random Star Wars quote
