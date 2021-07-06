#imports
import discord
from discord.ext import commands
import asyncio
import os
import json
import multiprocessing as mp
os.chdir("..")

with open("botdata.json", "r") as f:
    data = json.load(f)

client = commands.Bot(command_prefix="!gc ")
client.remove_command("help")

async def register_server(guild, defaultChannelId):
    if str(guild.id) in data:
        return False
    else:
        data[str(guild.id)] = {}
        data[str(guild.id)]["messageChannelId"] = defaultChannelId
        data[str(guild.id)]["serverName"] = guild.name
    with open("botdata.json", "w") as f:
        json.dump(data,f,indent=2)
    return True

async def send_message(message):
    #send message to all clients here
    for serverId in data:
        try:
            channelId = data[str(serverId)]["messageChannelId"]
            channelObject = client.get_channel(channelId)
            await channelObject.send(message)
        except:
            print("Cannot send message to server")

@client.command(name='help')
async def help(ctx):
    em = discord.Embed(title = ("Groupchat Bot's Commands"),description = "Command prefix is `!gc`", color = discord.Color.gold())
    em.add_field(name="Bot Explanation", value = "When you send a message to group chat, it will send the same message to every server that has the bot in it, like a group chat where you can talk to people across different servers!", inline = False)
    em.add_field(name="Bot Usage", value = "To send a message to group chat, in your group chat channel, put $ before your message", inline = False)
    em.add_field(name="!gc setchannel", value = "Sets the channel where groupchat messages will come through, and can be sent through.", inline = False)
    em.add_field(name="!gc help", value = "Bring up this help dialog", inline = False)
    em.set_footer(text="Bot made by Jeremys556#9215")
    await ctx.send(embed=em)

@client.command(name='setchannel')
@commands.has_permissions(manage_channels=True)  
async def setchannel(ctx, arg):
    guild = ctx.message.guild
    channelId = arg[2:-1]
    print(f"New channel id attempt: {channelId}")
    if client.get_channel(int(channelId)) != None:
        data[str(guild.id)]["messageChannelId"] = int(channelId)
        with open("botdata.json", "w") as f:
            json.dump(data,f,indent=2)
        await ctx.send(f"Changed groupchat channel to {arg}!")
    else:
        await ctx.send(f"Not a valid channel: {arg}")

@client.event
async def on_ready():
    #when the bot powers on
    print("Bot online")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Type !gc help'))

@client.event
async def on_message(message):
    if message.content[0] == "$":
        guild_id = message.guild.id
        channel_id = message.channel.id
        messageContent = message.content
        if data[str(guild_id)]["messageChannelId"] == channel_id:
            if "@everyone" not in messageContent and "@here" not in messageContent:
                if "https://" in messageContent or "http://" in messageContent:
                    messageContent = messageContent.replace("https://", "")
                    messageContent = messageContent.replace("http://", "")
                sentMessage = f"{message.author.name}#{message.author.discriminator} > {messageContent[1:]}"
                print(sentMessage)
                await send_message(sentMessage)
                await message.delete()
    await client.process_commands(message) #makes normal commands work when typed

@client.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('Hello! This is my default channel. If you would like to change the channel, please type `!gc setchannel (channel)`. Type `!gc help` for all commands!')
            await register_server(guild, channel.id)
        break

#run client server
with open('token.txt') as tokentxt:
    token = tokentxt.read()
client.run(token)
tokentxt.close()