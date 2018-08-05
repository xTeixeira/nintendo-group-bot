from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TimedOut
import requests
import logging
import re
import os.path
import json
import time
from functools import wraps

subscriberChat = "-groupid" #(So the chat id should go here)
userIdsFile = "user-ids.json"
userIds = {}
groupMsg = "*Informações Sobre o Grupo*\n\nSejam Bem-Vindos!\n\nGrupo dedicado à seção Nintendo do Fórum Uol Jogos. Da nostalgia às jogatinas, não há muitas regras além de:\n\n1. Ambiente SFW (Safe for work. Sem pornô aqui)\n2. Discutir pode; xingar o coleguinha, não.\n3. Inatividade por 2 meses resulta em ban. Dá um oi, custa nada xD\n4. Quer divulgar algo? Participe! Venda ou sei lá, mas faça parte da comunidade.\n\nPara os novatos no Telegram, saibam que:\n\n5. Não é necessário compartilhar o número do celular para acessar o grupo. Utilizem um nick no seu perfil do Telegram.\n6. Prezamos pela privacidade. Novos usuários não poderão ler as mensagens antigas, além disso, haverá zero tolerância com trolls. \n7. Esta mensagem será constantemente atualizada com os IDs e o nick do pessoal, assim como o console/portátil que a pessoa tem.  \n\nO grupo conta ainda com dois posts de friend codes: um com a tag #FriendCodes e o outro, #PokemonGo. Envie o seu código para ser adicionado! \n\nPor fim, abaixo está o link para o Discord, o que torna mais fácil marcar jogatinas e conversar por voz.\n\n*Discord do Grupo:*\nhttps://discord.gg/nE7hzh7"

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

def start(bot, update):
	update.message.reply_text(
		"Todo: make start message")

def readUserIds():
	global userIds
	with open(userIdsFile, "r") as infile:
		subscriberJson = json.load(infile)
		userIds = subscriberJson["subscribers"]

def saveUserIds(bot, job):
	with open(userIdsFile, "w") as outfile:
		finalJson = {}
		finalJson["subscribers"] = userIds
		json.dump(finalJson, outfile)

def newMember(bot, update):
	send_message_retry(bot, update.message.chat_id, groupMsg)

def addId(bot, update):
	if update.message.text.split().size() < 2:
		return

	isPoke = update.message.text.split()[0] == "/pokego"
	user = update.message['from']
	if isPoke:	
		userIds[user['id']]['pokeCode'] = update.message['text'].split()[1]
	else:
		userIds[user['id']]['switchCode'] = update.message['text'].split()[1]

	if 'username' in user:
		userIds[user['id']]['displayName'] = user['username']
	else:
		userIds[user['id']]['displayName'] = user['first_name'] + " " + user['last_name']


def main():
	# First load our subscriber list if it exists:
	if os.path.isfile(userIdsFile):
		readUserIds()

	# Set up logging to stdout. Todo: Actually make a log file.
	logging.basicConfig(level=logging.DEBUG,
					format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	
	# Configure updater with our API token.
	updater = Updater("Your API token should go here.")

	# Create dispatcher and register commands.
	dp = updater.dispatcher

	dp.add_handler(CommandHandler("start", start))
	dp.add_handler(CommandHandler("help", start))
	dp.add_handler(CommandHandler("commands", start))


	dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, newMember))
	dp.add_handler(CommandHandler("addid", addId))
	dp.add_handler(CommandHandler("addpoke", addId))

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