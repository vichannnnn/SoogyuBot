# How to set up and run the bot locally
<hr>

## Setup
### Install requirements 
* Install Python 3.8 from https://www.python.org/downloads/
* When you're at the installer part, tick the PATH box. 
* Open Command Prompt from Windows, navigate to the directory using ``cd``
* For example, if your source code is in Desktop, you will need to ``cd desktop`` and ``cd {filename}`` before.

* Execute ``pip install -r requirements.txt`` (without the quotation mark)

### Bot Configuration
* Go to Discord's Developer Portal at https://discord.com/developers/applications
* Create an application if you haven't already, and navigate into it.
* On the settings bar at the side, you will see a Bot section, go to it and Build-A-Bot.
* After you're done building a Bot, name the bot and give it a profile picture.
* Reveal the token by clicking on it, then copy and replace the bot_token onto authentication.yml
* Under Privileged Gateway Intents, **toggle on Server Members Intent (THIS is very important!)**

### Getting the Invite Link

* In the same application in the Discord's Developer Portal, head to the OAuth2 section on the side.
* Under the Scopes, tick on Bot, another section below should appear, tick on Administrator, or whatever permissions you need.
* Copy the link generated in the middle, this is the invite link for your bot, just like how you used to invite other bots.

### Run the bot
* In the same command prompt window from earlier where you executed ``pip install -r requirements txt``, execute ``python3 main.py`` 
* The bot should be successfully running and you will see a bunch of lines saying the bot has started.

##### Thats it!

