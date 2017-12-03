from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from game.typeA import Game
import re
import configparser

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

config = configparser.ConfigParser()
config.read("./config/local.cfg")

updater = Updater(token=config['TELEGRAM']['token'])
dispatcher = updater.dispatcher
game = Game()


def start(bot, update):
	logging.info(update)
	sendMsg(
		bot,
		update,
		"""
		Ну что ж, карапузы, готовте ваши словцы!
		Просто пиши своё словцо мне. Я сам догадаюсь куда его впихнуть.
		Поддерживаемые комманды:
		/game_info, /i, /и - информация о текущей игре
		/my_words_by_game, /wg, /си - твои словцы за текущую игру
		/my_words_by_round, /wr, /ср - твои словцы за текущий раунд
		/update, /u, /о - обнови своё словцо!
		/random, /r, /р - случайное словцо. Вдохновись!
		/candidates, /c, /к - посмотреть список словцов-кандидатов.
		/ready, /готов - говорит мне, что вы готовы/не готовы к мясорубке.
		/vote /v /голос /г - проголосовать за понравившиеся словцы.
		/vote_info, /vi, /голос_инфо, /ги - посмотреть информацию о своих баллах
		/fight, /f, /битва, /б - инициировать выбор лучшего словца. Бой не начнётся, пока все, предложившие словцы, не потратят все баллы.
		"""
	)


def catchWord(bot, update):
	logging.info(update)
	response = game.addWord(update)
	sendMsg(bot, update, response)


def iAmSoStupid(bot, update):
	sendMsg(bot, update, "Говори на понятном мне языке. Используй понятные слова.\nВот тебе инструкция: /help")


def showMyWordsPerGame(bot, update, args):
	logging.info(update)
	game_id = int(args[0]) if args else None
	wordsList = game.getPlayerWordsByGame(update, game_id)
	if not wordsList:
		response = "Какой стыд. Ты не смог предложить ни одного словца за всю игру!"
		sendMsg(bot, update, response)
		return
	response = """Вон они, твои словцы. Делай с ними теперь что хочешь:\n%s""" % " ".join(w['word'] for w in wordsList)
	sendMsg(bot, update, response)


def showMyWordsPerRound(bot, update, args):
	logging.info(update)
	round_id = int(args[0]) if args else None
	wordsList = game.getPlayerWordsByRound(update, round_id)
	if not wordsList:
		response = "Какой стыд. Ты не смог предложить ни одного словца за целый раунд!"
		sendMsg(bot, update, response)
		return
	response = """Вон они, твои словцы. Делай с ними теперь что хочешь:\n%s""" % " ".join(w['word'] for w in wordsList)
	sendMsg(bot, update, response)


def updateMyWord(bot, update, args):
	logging.info(update)
	if len(args) != 2:
		response = "Слева - старое словцо, справа - новое словцо. ДЕЛАЙ ТАК!"
		sendMsg(bot, update, response)
		return
	response = game.updateWord(args[0], args[1], update)
	sendMsg(bot, update, response)


def getRandomWord(bot, update):
	logging.info(update)
	word = game.getRandom('ushakov')
	if not word:
		response = "Очень странно. Не могу получить случайное словцо!"
	else:
		response = "Вот твоё случайное словцо: %s" % word.lower()
	response += "Попробуй ещё: /r"
	sendMsg(bot, update, response)


def getGameInfo(bot, update, args):
	if not args:
		game_id = None
	else:
		if not re.match(r"^[\d]+$", args[0]):
			response = """Очень плохой game_id. Просто отвратительный! game_id состоит только из цифр, болван!
			Если хочешь посмотреть информацию о текущей игре, то не передавай ничего."""
			sendMsg(bot, update, response)
			return
		game_id = int(args[0])
	gameInfo = game.get(game_id)
	if not gameInfo:
		sendMsg(bot, update, "Невероятно! До сих пор не было запущено ни одной игры!")
		return
	response = """
	Сейчас идёт игра, начатая %(createDate)s. ID игры: %(id)d
	Всего предложено: %(words)s слов
	Всего инициировано: %(roundsCount)s раундов. Номера раундов: %(roundsNumber)s
	Последний раунд: %(lastRoundNumber)s, запущенный в %(lastRoundCreateDate)s. В нём предложено %(lastRoundWords)s слов
	Участники последнего раунда:\n%(lastRoundPlayersPlain)s
	""" % gameInfo
	sendMsg(bot, update, response)


def setState(bot, update):
	logging.info(update)
	response = game.setPlayerState(update)
	sendMsg(bot, update, response)


def fight(bot, update):
	logging.info(update)
	response = game.start()
	sendMsg(bot, update, response)


def getCandidates(bot, update):
	logging.info(update)
	response = game.getCandidates(update)
	sendMsg(bot, update, response)


def vote(bot, update, args):
	logging.info(update)
	string = ' '.join(args).lower()
	if not string:
		response = """
			Ну ты чё. Скинь непустую строчку со своими баллами в формате: \"Словцо 1 Словцо 5 Словцо 2\".
			Где \"Словцо\" - название словца, а циферки - твои баллы.
		"""
	else:
		response = game.vote(update, string)
	sendMsg(bot, update, response)


def getMyVotes(bot, update):
	logging.info(update)
	response = game.getSelfVotes(update)
	sendMsg(bot, update, response)


def sendMsg(bot, update, msg):
	msg = re.sub(r"(?<=\n)[\s]+", "", msg) if msg else "Мне нечего тебе сказать, чёрт возьми!"
	bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode="html")

[
	dispatcher.add_handler(handler) for handler in [
		CommandHandler(['start', 'help', 'h', 'помощь', 'п'], start),
		CommandHandler(['game_info', 'i', 'и'], getGameInfo, pass_args=True),
		CommandHandler(['my_words_by_game', 'wg', 'си'], showMyWordsPerGame, pass_args=True),
		CommandHandler(['my_words_by_round', 'wr', 'ср'], showMyWordsPerRound, pass_args=True),
		CommandHandler(['update', 'u', 'о'], updateMyWord, pass_args=True),
		CommandHandler(['random', 'r', 'р'], getRandomWord, pass_args=False),
		CommandHandler(['fight', 'f', 'битва', 'б'], fight, pass_args=False),
		CommandHandler(['candidates', 'c', 'к'], getCandidates, pass_args=False),
		CommandHandler(['ready', 'готов'], setState, pass_args=False),
		CommandHandler(['vote', 'v', 'голос', 'г'], vote, pass_args=True),
		CommandHandler(['vote_info', 'vi', 'голос_инфо', 'ги'], getMyVotes),
		MessageHandler(Filters.text, catchWord),


		MessageHandler(Filters.command, iAmSoStupid)
	]
]
# dispatcher.add_handler(word_handler)
# dispatcher.add_handler(gameInfo_handler)
# dispatcher.add_handler(selfWordsByGame_handler)
# dispatcher.add_handler(selfWordsByRound_handler)
# dispatcher.add_handler(updateMyWord_handler)
# dispatcher.add_handler(word_handler)


if __name__ == "__main__":
	updater.start_polling()

# DELETE FROM words.word WHERE id >= 1;
# DELETE FROM words.game WHERE id >= 1;
# DELETE FROM words.player WHERE id >= 1;
# DELETE FROM words.round WHERE id >= 1;
# DELETE FROM words.groups WHERE id >= 1;
# DELETE FROM words.player_state WHERE id >= 1;
# INSERT INTO player SET name = "Жорж", telegram_id = -1;
