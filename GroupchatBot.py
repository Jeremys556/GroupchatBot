#imports
import discord
from discord.ext import commands
from discord.ext import tasks
import asyncio
import os
import json
from contextlib import suppress

os.chdir("..")
with open("botdata.json", "r") as f:
    data = json.load(f)
with open("muteData.json", "r") as f:
    muteData = json.load(f)
with open('slurList.txt') as slurListFile:
    slurList = slurListFile.readlines()
    slurList = [x.strip() for x in slurList] #removes whitespace between words
    slurList.append(' coon') #add this separately due to the above code removing whitespace, and incase people want to use the word "raccoon", it would count as a slur if there wasn't a space before the word
    slurListFile.close()

mod_ids = [240963309266927616, 481472501621456916]
unsendableServers = []
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix="!gc ", intents=intents)
client.remove_command("help")

async def register_server(guild, defaultChannelId):
    if str(guild.id) in data:
        return False
    else:
        data[str(guild.id)] = {}
        data[str(guild.id)]["messageChannelId"] = defaultChannelId
        data[str(guild.id)]["serverName"] = guild.name
        data[str(guild.id)]["prefix"] = "$"
    with open("botdata.json", "w") as f:
        json.dump(data,f,indent=2)
    return True

async def remove_unsendable_servers():
    with suppress(RuntimeError): #Suppresses dictionary changed size during iteration error, as this can cause the error to happen sometimes as it calls while iterating in send_message()
        for serverId in unsendableServers:
            data.pop(str(serverId))
            with open("botdata.json", "w") as f:
                json.dump(data,f,indent=2)
            print(f"Removed server id {serverId} from botdata.json")

#Function to send message to every server which has the bot
async def send_message(message):
    for serverId in data:
        try:
            channelId = data[str(serverId)]["messageChannelId"]
            channelObject = client.get_channel(channelId)
            await channelObject.send(message)
        except:
            #Error happens if bot is kicked from server (may be other cases but this is only known case)
            print(f"Cannot send message to server with server id {serverId}")
            unsendableServers.append(serverId)
            await remove_unsendable_servers()       

#Function to mute users from using the bot
async def mute_user(userObject, time): #time in minutes
    username = userObject.name
    userfull = f"{username}#{userObject.discriminator}"
    muteData[userfull] = {}
    muteData[userfull]["userId"] = userObject.id
    muteData[userfull]["time"] = int(time)
    with open("muteData.json", "w") as f:
        json.dump(muteData,f,indent=2)

#Ticks down the time on mutes by 1 minute every minute
@tasks.loop(seconds=60)
async def timeTicker():
    with open("muteData.json", "r") as f:
        muteData = json.load(f)
    for username in muteData:
        if muteData[username]["time"] == 0:
            print(f"{username} has been unmuted. User id: {muteData[username]['userId']}")
            userObject = client.get_user(muteData[username]['userId'])
            dmChannel = await userObject.create_dm()
            await dmChannel.send("Your mute from the groupchat bot has expired! Welcome back. Remember to follow the rules.")
            muteData.pop(username)
            break
        else:
            muteData[username]["time"] -= 1
    with open("muteData.json", "w") as f:
        json.dump(muteData,f,indent=2)

#Discord bot command to open the help message
@client.command(name='help')
async def help(ctx):
    em = discord.Embed(title = ("Groupchat Bot's Commands"),description = "Command prefix is `!gc`", color = discord.Color.gold())
    em.add_field(name="Bot Explanation", value = "When you send a message to group chat, it will send the same message to every server that has the bot in it, like a group chat where you can talk to people across different servers!", inline = False)
    guild = ctx.guild
    channelName = f"<#{data[str(guild.id)]['messageChannelId']}>"
    if data[str(guild.id)]['prefix'] != "none":
        serverPrefix = data[str(guild.id)]['prefix']
        em.add_field(name="Bot Usage", value = f"To send a message to group chat, send a message in {channelName} with {serverPrefix} before your message.", inline = False)
    else:
        em.add_field(name="Bot Usage", value = f"To send a message to group chat, send a message in {channelName}.", inline = False)
    em.add_field(name="!gc setchannel (channel ping)", value = "Sets the channel where groupchat messages will come through, and can be sent through.", inline = False)
    em.add_field(name="!gc stats", value = "Shows statistics about the bot.", inline = False)
    em.add_field(name="!gc setprefix (prefix)", value = "Use 'none' to have no prefix. Sets the prefix for **sending messages to GroupChat** only. Does not change !gc.", inline = False)
    em.add_field(name="!gc help", value = "Bring up this help dialog.", inline = False)
    em.set_footer(text="Bot made by Jeremys556#9215\nOfficial discord: https://discord.gg/npNkr2gNgr")
    await ctx.send(embed=em)

#Discord bot command to show bot statistics
@client.command(name='stats')
async def info(ctx):
    serverCount = len(data)
    em = discord.Embed(title = ("Groupchat Bot Statistics"), color = discord.Color.gold())
    em.add_field(name="Servers", value=f"I am in {serverCount} servers")
    await ctx.send(embed=em)

@client.command(name='setprefix')
@commands.has_permissions(manage_channels=True)
async def setprefix(ctx, arg):
    if arg != "":
        guild = ctx.message.guild
        triedPrefix = str(arg).lower()
        if arg == "none":
            data[str(guild.id)]["prefix"] = "none"
            with open("botdata.json", "w") as f:
                json.dump(data,f,indent=2)
            await ctx.send("Prefix set to none")
        else:
            if len(triedPrefix) == 1:
                data[str(guild.id)]["prefix"] = triedPrefix
                with open("botdata.json", "w") as f:
                    json.dump(data,f,indent=2)
                await ctx.send(f"Prefix set to {triedPrefix}")
            else:
                await ctx.send("Prefix must be only 1 character")
    else:
        await ctx.send("You need to add an argument to this command. Use 'none'. Proper usage: `!gc setprefix`")
    

#Discord bot command to set the messages the bot sends to a different channel
@client.command(name='setchannel')
@commands.has_permissions(manage_channels=True)  
async def setchannel(ctx, arg):
    guild = ctx.message.guild
    channelId = arg[2:-1]
    if client.get_channel(int(channelId)) != None:
        data[str(guild.id)]["messageChannelId"] = int(channelId)
        with open("botdata.json", "w") as f:
            json.dump(data,f,indent=2)
        await ctx.send(f"Changed groupchat channel to {arg}!")
    else:
        await ctx.send(f"Not a valid channel: {arg}")

@client.command(name='mute')
async def mute(ctx, arg1, arg2): #arg1 is full username, arg2 is time
    if ctx.author.id in mod_ids: #my id
        if "#" in arg1:
            if arg2.isdigit():
                splitUser = arg1.split("#")
                nameArgument = splitUser[0]
                discriminatorArgument = splitUser[1]
                user = discord.utils.get(client.get_all_members(), name=nameArgument, discriminator=discriminatorArgument)
                await mute_user(user, arg2)
                await send_message(f"Server > {arg1} has been muted by {ctx.author} for {arg2} minutes.")
            else:
                await ctx.send(f"Time argument (Second argument) must be an integer. You put: {arg2}")
        else:
            await ctx.send("Make sure to put their full username, including the # before their discriminator")
    else:
        await ctx.send("You must be a GroupChat moderator to use this command.")

#Discord on ready event, runs when bot is turned online
@client.event
async def on_ready():
    #when the bot powers on
    print("Bot online")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Type !gc help'))
    timeTicker.start()

#Discord on message event, runs when a message is sent in a server where the bot exists
@client.event
async def on_message(message):
    with suppress(IndexError): #When messages such as embedded messages from other bots are sent, it technically is considered to have no characters, meaning it returns a meaningless index error. This is just here to suppress it to keep console cleaner. 
        if message.author.bot != True:
            guild_id = message.guild.id
            channel_id = message.channel.id
            prefix = data[str(guild_id)]["prefix"]
            if prefix != "none":
                if message.content[0].lower() == prefix.lower():
                    messageContent = message.content[1:]
                    sentMessageChannel = client.get_channel(channel_id)
                    if data[str(guild_id)]["messageChannelId"] == channel_id:
                        for username in muteData:
                            if muteData[username]["userId"] == message.author.id:
                                dmChannel = await message.author.create_dm()
                                await dmChannel.send(f"You are currently muted from using the Groupchat bot. Your mute expires in {muteData[username]['time']} minutes.")
                                return #exits function by returning nothing
                        if "@everyone" not in messageContent and "@here" not in messageContent:
                            #Check for slurs
                            if any(word in messageContent for word in slurList):
                                await mute_user(message.author, 180)
                                await send_message(f"Server > {message.author} has been automatically muted by the server for 180 minutes.")
                            else:
                                await message.delete()
                                if "https://" in messageContent or "http://" in messageContent:
                                    messageContent = messageContent.replace("https://", "")
                                    messageContent = messageContent.replace("http://", "")
                                sentMessage = f"{message.author.name}#{message.author.discriminator} > {messageContent}"
                                print(sentMessage)
                                await send_message(sentMessage)
                        #if @everyone or @here in message:
                        else:
                            sentMessageChannel.send(f"You cannot use everyone or here pings in Groupchat, {message.author.name}#{message.author.discriminator}!")
            else:
                #repeat of above code, except not needing prefix. i feel there should be a better way but idk what it is, and functions would (supposedly) slow it down
                messageContent = message.content
                sentMessageChannel = client.get_channel(channel_id)
                if data[str(guild_id)]["messageChannelId"] == channel_id:
                    for username in muteData:
                        if muteData[username]["userId"] == message.author.id:
                            dmChannel = await message.author.create_dm()
                            await dmChannel.send(f"You are currently muted from using the Groupchat bot. Your mute expires in {muteData[username]['time']} minutes.")
                            return #exits function by returning nothing
                    if "@everyone" not in messageContent and "@here" not in messageContent:
                        #Check for slurs
                        if any(word in messageContent for word in slurList):
                            await mute_user(message.author, 180)
                            await send_message(f"Server > {message.author} has been automatically muted by the server for 180 minutes.")
                        else:
                            if "https://" in messageContent or "http://" in messageContent:
                                messageContent = messageContent.replace("https://", "")
                                messageContent = messageContent.replace("http://", "")
                            sentMessage = f"{message.author.name}#{message.author.discriminator} > {messageContent}"
                            print(sentMessage)
                            await send_message(sentMessage)
                            await message.delete()
                    #if @everyone or @here in message:
                    else:
                        sentMessageChannel.send(f"You cannot use everyone or here pings in Groupchat, {message.author.name}#{message.author.discriminator}!")

    await client.process_commands(message) #makes normal commands work when typed

#Discord on guild join event, runs when the bot joins a new server
@client.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('Hello! This is my default channel. If you would like to change the channel, please type `!gc setchannel (channel)`. Type `!gc help` for all commands!')
        break
    await register_server(guild, channel.id)

#Grabs the token and starts the bot
with open('token.txt') as tokentxt:
    token = tokentxt.read()
tokentxt.close()
client.run(token)