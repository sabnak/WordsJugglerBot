from libs.dbAdapter import DB
import re


class Word:

	ERROR_CODES = {
		"TOO_SHORT_WORD": "Ха! Вы только посмотрите! Какое маленькое, жалкое и скукоженное словцо! Минимальная длина словца - %d букв.",
		"INVALID_WORD": "Это не похоже на словцо! Не похоже! Словцо должно содержать только русские буквы, невежа.",
		"NOT_IN_TIME_WORD": "Ну ты и проныра! Ты уже втюхнул максимальное количество (%d) своих жалких словцов в этом раунде!",
		"EXISTED_WORD_NEW": "Ах ты ж маленькая слабоумная сковорода. Такое словцо уже предлагали!",
		"EMPTY_WORD": "Словцо-то введи, горемыка."
	}

	@staticmethod
	def add(params, wordsLimit, wordMinLength):
		params['word'] = params['word'].strip().lower()
		wordsForToday = DB.getList("""
			SELECT *
			FROM word
			WHERE player_id = %(player_id)s AND DATE(createDate) = DATE(NOW()) AND game_id = %(game_id)s AND round_id = %(round_id)s
		""", params)
		if len(wordsForToday) >= wordsLimit:
			return False, Word.ERROR_CODES['NOT_IN_TIME_WORD'] % wordsLimit
		status, response = Word.isWordValid(params['word'], wordMinLength)
		if not status:
			return False, response
		DB.execute("INSERT INTO word SET word = %(word)s, player_id = %(player_id)s, game_id = %(game_id)s, round_id = %(round_id)s", params)
		wordsForToday = DB.getList("SELECT * FROM word WHERE player_id = %(player_id)s AND DATE(createDate) = DATE(NOW())", params)
		additionalMsg = ""
		if len(wordsForToday) == wordsLimit:
			additionalMsg = " У тебя больше не осталось слов на сегодня."
		if len(wordsForToday) < wordsLimit:
			additionalMsg = " Ты можешь предложить ещё %d смешных словца" % (wordsLimit - len(wordsForToday))
		return True, "Твоё жалкое словцо \"%s\" принято, свинюшка! %s" % (params['word'], additionalMsg)

	@staticmethod
	def getIdByName(**params):
		word = DB.getOne("SELECT id FROM word WHERE word = %(word)s AND word.round_id = %(round_id)s AND word.game_id = %(game_id)s", params)
		return word['id'] if word else None

	@staticmethod
	def getListByGameId(game_id, player_id=None, fullAccess=False):
		condition = "player_id = %(player_id)s" if player_id else "status = 'ended'" if not fullAccess else ""
		return DB.getList("""
		SELECT word.*, round.id round_id, round.number
		FROM word
		JOIN round ON (round.id = word.round_id)
		WHERE word.game_id = %(game_id)s AND
		""" + condition, dict(game_id=game_id, player_id=player_id))

	@staticmethod
	def getListByRoundId(round_id, player_id=None, fullAccess=False):
		condition = " AND player_id = %(player_id)s" if player_id else " AND status = 'ended'" if not fullAccess else ""
		return DB.getList("""
		SELECT word.*, player.name, player.telegram_id, player.id player_id, round.number, round.id round_id
		FROM word
		JOIN round ON (round.id = word.round_id)
		JOIN player ON (player.id = word.player_id)
		WHERE word.round_id = %(round_id)s
		""" + condition, dict(round_id=round_id, player_id=player_id))

	@staticmethod
	def update(wordMinLength, **params):
		params['oldWord'] = params['oldWord'].lower()
		params['newWord'] = params['newWord'].lower()
		if params['newWord'] == params['oldWord']:
			return "И ты прислал два одинаковых слова... Зачем ты так глуп, а?"
		if not DB.getOne("""
			SELECT word.*, round.id round_id, round.number
			FROM word
			JOIN round ON (round.id = round_id)
			WHERE word = %(oldWord)s AND player_id = %(player_id)s AND status='preparation'
		""", params):
			return "У тебя нет такого словца в последнем раунде или он уже завершён, дурында!"
		status, response = Word.isWordValid(word=params['newWord'], wordMinLength=wordMinLength)
		if not status:
			return response
		affectedRows = DB.execute("""
			UPDATE word
			JOIN round ON (round.id = round_id)
			SET word = %(newWord)s
			WHERE word = %(oldWord)s AND player_id = %(player_id)s AND status='preparation'
		""", params).rowcount
		return "Хм... Я не смог обновить словцо. Интересно почему?" if not affectedRows else "Словцо успешно обновлено. Надеюсь, оно было получше прежнего"

	@staticmethod
	def isWordValid(word, wordMinLength):
		errorMsg = None
		if not word:
			errorMsg = Word.ERROR_CODES['EMPTY_WORD']
		elif Word._isWordExist(word):
			errorMsg = Word.ERROR_CODES['EXISTED_WORD_NEW']
		elif not re.match(r"^[А-яё]+$", word):
			errorMsg = Word.ERROR_CODES['INVALID_WORD']
		elif len(word) < wordMinLength:
			errorMsg = Word.ERROR_CODES['TOO_SHORT_WORD'] % wordMinLength
		if errorMsg:
			return False, errorMsg
		return True, None

	@staticmethod
	def isWordBelongToPlayer(**params):
		return True if DB.getOne("SELECT * FROM word WHERE round_id = %(round_id)s AND word = %(word)s AND player_id = %(player_id)s", params) else False

	@staticmethod
	def _isWordExist(word):
		return True if DB.getOne("SELECT * FROM word WHERE word = %(word)s ORDER BY createDate DESC LIMIT 1", dict(word=word)) else False

