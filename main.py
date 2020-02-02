from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TimedOut
import requests
import logging
import re
import os.path
import json
import time
import functools

subscriberChat = "-groupid" #(So the chat id should go here)
userIdsFile = "user-ids.json"
userIds = {}
groupMsg = "INFORMAÇÕES SOBRE O GRUPO\n\nSejam Bem-Vindos!\n\nGrupo para gamers, especialmente os apaixonados por Nintendo!\n\n1. Ambiente SFW (Safe for work. Sem pornô e gore aqui.)\n2. Discutir pode; xingar o coleguinha, não.\n3. Divulgue apenas se você postar com frequência.\n4. Temos lista de Switch Codes. Só pedir e enviar o código paraseradicionado.\n\nCanal de Notícias:\nhttps://t.me/joinchat/AAAAAFDiOImvA-VCqj63hQ\n.\nSubreddit:\nReddit.com/r/Switch_Brasil\n.\nDiscord:\nhttps://discord.gg/UXpZHaj\n"
commandsHelpMsg = "Para adicionar um Friend Code use o comando:\n/addCode <friend-code>\n\nex: /addCode SW-1234-546A-53SD"

def send_message_retry(bot, chat_id, message, retries=5):
	for nretries in range(retries):
		try:
			bot.send_message(chat_id, message, parse_mode='Markdown')
		except TimedOut:
			time.sleep(1)
			continue
		return
	
	raise TimedOut

def send_photo_retry(bot, chat_id, photo_path, retries=5):
	for nretries in range(retries):
		try:
			bot.send_photo(chat_id, photo_path)
		except TimedOut:
			time.sleep(1)
			continue
		return
	
	raise TimedOut

def showCommandsHelp(update):
	update.message.reply_text(commandsHelpMsg)

def readUserIds():
	global userIds
	with open(userIdsFile, "r") as infile:
		subscriberJson = json.load(infile)
		userIds = subscriberJson["userIds"]

def saveUserIds(bot, job):
	with open(userIdsFile, "w") as outfile:
		finalJson = {}
		finalJson["userIds"] = userIds
		json.dump(finalJson, outfile)
		
### COMMAND HANDLERS ###

def start(bot, update):
	update.message.reply_text(groupMsg)

def showCommands(bot, update):
	commands = "Comandos:\n"
	commands += "/start\n"
	commands += "/commands\n\n"

	commands += "/showCodes" + " - mostrar friend codes\n"
	commands += "/addCode <friend-code>" + " - adicionar código do seu usuário\n"
	commands += "/removeCode <friend-code>" + "- remover código do seu usuário\n\n"

	update.message.reply_text(commands)

def newMember(bot, update):
	send_message_retry(bot, update.message.chat_id, groupMsg)

def setId(bot, update):
	global userIds

	if not update.message or not update.message.text:
		showCommandsHelp(update)
		return

	splitText = update.message.text.split()

	if len(splitText) < 2:
		showCommandsHelp(update)
		return

	code = splitText[1]

	user = update.message.from_user
	userId = str(user.id)

	if user.username:
		username = "@"+user.username
	else:
		username = user.first_name + " " + user.last_name

	if userId not in userIds:
		userIds[userId] = {}

	setIdInList(userId, code, username)

	send_message_retry(bot, update.message.chat_id, "Código adicionado com sucesso!")

def removeId(bot, update):
	global userIds
	user = update.message.from_user
	userId = (str(user.id))

	if userId in userIds:
		setIdInList(userId, None, userIds[userId]["displayName"])
		send_message_retry(bot, update.message.chat_id, "Código removido com sucesso!")
	else:
		send_message_retry(bot, update.message.chat_id, "Não há este tipo de código registrado!")

def showIds(bot, update):	
	global userIds

	message = "*Switch Friend Codes*\n\n"
	for userId, userInfo in userIds.items():
		if userInfo["switchCode"]:
			message += userInfo['displayName'] + ": " + userInfo["switchCode"] + "\n========\n"

	send_message_retry(bot, update.message.chat_id, message)

def setIdInList(userId, code, username):
	global userIds
	userIds[userId]["displayName"] = username
	userIds[userId]["switchCode"] = code

def main():
	# First load our subscriber list if it exists:
	if os.path.isfile(userIdsFile):
		readUserIds()

	# Set up logging to stdout. Todo: Actually make a log file.
	logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	
	# Configure updater with our API token.
	updater = Updater("API-TOKEN")

	# Create dispatcher and register commands.
	dp = updater.dispatcher

	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", start))
	dp.add_handler(CommandHandler("commands", showCommands))


	dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, newMember))

	dp.add_handler(CommandHandler("addCode", setId))
	dp.add_handler(CommandHandler("removeCode", removeId))
	dp.add_handler(CommandHandler("showCodes", showIds))

	# Create scheduled job for saving the subscriber list to disk every minute.
	userIdsSavingJob = updater.job_queue.run_repeating(saveUserIds, interval=60, first=60)
	userIdsSavingJob.enabled = True

	# Start the bot.
	updater.start_polling()

	updater.idle()

	# Save the subscribers one last time before exiting.
	saveUserIds(updater.bot, userIdsSavingJob)

if __name__ == '__main__':
	main()