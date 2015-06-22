#!/usr/bin/env python
# coding: utf8

from __future__ import unicode_literals
import requests, sqlite3, time, sys, datetime
import scrapy

"""def uprint(objects, sep=' ', end='\n', file=sys.stdout):
	enc = file.encoding
	if enc == 'UTF-8':
		print(objects, sep=sep, end=end, file=file)
	else:
		f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
		print(*map(f, objects), sep=sep, end=end, file=file)
"""
def uprint(hop):
	try:
		print(hop)
	except:
		pass


def requete_db(requete, params):
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	c.execute(requete, params)
	conn.commit()
	conn.close()

def requetes_db(requete, params):
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	c.executemany(requete, params)
	conn.commit()
	conn.close()

def refresh_db():
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	today = datetime.date.today()
	nom_table = "chiffres{:02}{:02}{}".format(today.day, today.month, today.year)
	print("Récupération des données Steamspy...")
	sql = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{}';".format(nom_table)
	if not(c.execute(sql).fetchone()[0]):
		print("Création de la table du {:02}/{:02}/{}".format(today.day, today.month, today.year))
		sql = "CREATE TABLE {}(id INTEGER PRIMARY KEY, steamID INT, owners INT, players INT, players_2weeks INT, average_pt INT, average_pt_2weeks INT, median_pt INT, median_pt_2weeks INT);".format(nom_table)
		c.execute(sql)
		data = requests.get("http://steamspy.com/api.php?request=all").json()
		applist = data.values()
		liste = []
		for x in applist:
			liste.append([x["appid"], x["owners"], x["players_forever"], x["players_2weeks"], x["average_forever"], x["average_2weeks"], x["median_forever"], x["median_2weeks"]])
		requetes_db("INSERT INTO {} VALUES(NULL,?,?,?,?,?,?,?,?);".format(nom_table), liste)
		print("Table du {:02}/{:02}/{} créée.".format(today.day, today.month, today.year))
	else:
		print("Table du {:02}/{:02}/{} déjà existante.".format(today.day, today.month, today.year))
	conn.commit()
	conn.close()
	
def read_jeux_db():
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	sql = "SELECT steamID from steam_full;"
	c.execute(sql)
	rows = c.fetchall()
	rows = [str(x[0]) for x in rows]

	conn.commit()
	conn.close()
	return rows

def read_nonjeux_db():
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	sql = "SELECT steamID from nonapp;"
	c.execute(sql)
	rows = c.fetchall()
	rows = [str(x[0]) for x in rows]

	conn.commit()
	conn.close()
	return rows

def add_nongame(appid):
	print("Insertion du non-jeu : {}".format(appid))
	requete_db("INSERT INTO nonapp VALUES(NULL,?)", (int(appid),))

def get_steam(appid):
	# Méthode qui chope le full package d'une app Steam
	# Renvoie False si rate limit exceeded, True si l'app n'est pas un jeu, et une liste de données si l'app est un jeu

	url = "http://store.steampowered.com/api/appdetails/"
	params = {}
	params["appids"] = appid
	params["cc"] = "FR"
	data = requests.get(url, params)
	time.sleep(1.7)
	
	try:
		data = data.json()
	except ValueError:
		return True
			
	if data != None:
		data = data[appid]
	else:
		return False 			#si pas de data, probablement rate limit de l'api atteint, on attend
	if data["success"]:
		data = data["data"]
	else:
		return True

	if data["type"] == "game" or data["type"] == "dlc":
		if data["steam_appid"] != int(appid):
			return True
		
		nom = data["name"]
		type_jeu = data["type"]
		if "developers" in data:
			dev = data["developers"][0]
		else:
			dev = "Inconnu"
		if "publishers" in data:
			editeur = data["publishers"][0]
		else:
			editeur = "Inconnu"
		if "recommendations" in data:
			reco = data["recommendations"]["total"]
		else:
			reco = 0
		if "is_free" in data:
			isFree = bool(data["is_free"])
		if "price_overview" in data:
			prix = data["price_overview"]["initial"]
		else:
			prix = 0
		if "metacritic" in data:
			metacritic = data["metacritic"]["score"]
		else:
			metacritic = None
		if "required_age" in data:
			required_age = data["required_age"]
		else:
			required_age = 0
		if "dlc" in data:
			dlc = data["dlc"]
		else:
			dlc = None
		if "header_image" in data:
			image = data["header_image"]
		else:
			image = None
		if "website" in data:
			website = data["website"]
		else:
			website = None
		if "demos" in data:
			demo = True
		else:
			demo = False
		if "categories" in data:
			categories = data["categories"]
		else:
			categories = None
		windows = False
		linux = False
		mac = False
		if "platforms" in data:
			windows = data["platforms"]["windows"]
			linux = data["platforms"]["linux"]
			mac = data["platforms"]["mac"]
		if "genres" in data:
			genres = data["genres"]
		else:
			genres = None
		date_sortie = data["release_date"]["date"]
		coming_soon = bool(data["release_date"]["coming_soon"])
		jeu = [int(appid), type_jeu, nom, dev, editeur, isFree, prix, metacritic, reco, date_sortie, required_age, image, website, demo, windows, linux, mac, coming_soon, genres, dlc, categories]
		return jeu
	else:
		return True

def put_categories_db(appid, categories):
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	sql = "SELECT id from categories;"
	c.execute(sql)
	rows = c.fetchall()
	cat = [int(x[0]) for x in rows]
	
	for x in categories:
		if not(x["id"] in cat):
			sql = "INSERT INTO categories VALUES('{}', '{}');".format(x["id"], x["description"])
			c.execute(sql)
		sql = "INSERT INTO categories_jeux VALUES('{}', '{}');".format(appid, x["id"])
		c.execute(sql)

	conn.commit()
	conn.close()

def put_genres_db(appid, genres):
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	sql = "SELECT id from genres;"
	c.execute(sql)
	rows = c.fetchall()
	genre_full = [int(x[0]) for x in rows]
	
	for x in genres:
		if not(int(x["id"]) in genre_full):
			sql = "INSERT INTO genres VALUES('{}', '{}');".format(x["id"], x["description"])
			c.execute(sql)
		sql = "INSERT INTO genre_jeux VALUES('{}', '{}');".format(appid, x["id"])
		c.execute(sql)

	conn.commit()
	conn.close()

def put_dlc_db(appid, dlc):
	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	sql = "INSERT INTO DLC VALUES('{}', '{}');".format(dlc, appid)
	c.execute(sql)
	conn.commit()
	conn.close()

def put_jeu_db(jeu, update = None):
	if not(update):
		categories = jeu.pop(len(jeu) - 1)
		if categories != None:
			put_categories_db(jeu[0], categories)
		dlc = jeu.pop(len(jeu) - 1)
		if dlc != None:
			for x in dlc:
				put_dlc_db(jeu[0], x)
				jeu_x = get_steam(str(x))
				if not(jeu_x):
					dlc.append(x)
					print("Rate limit exceeded... 5 min d'attente depuis {}".format(datetime.datetime.now().time()))
					time.sleep(300)
				elif jeu_x != True:
					put_jeu_db(jeu_x, False)
			
		genres = jeu.pop(len(jeu) - 1)
		if genres != None:
			put_genres_db(jeu[0], genres)
	else:
		void = jeu.pop(len(jeu) - 1)
		void = jeu.pop(len(jeu) - 1)
		void = jeu.pop(len(jeu) - 1)

	placeholders = ', '.join("?" * len(jeu))
	sql = "REPLACE INTO steam_full VALUES(NULL, {})".format(placeholders)
	if not(update):
		fonc = "Insertion"
	else:
		fonc = "Mise à jour"
	uprint("{} de {}".format(fonc, jeu[2]))

	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	c.execute(sql, jeu)
	conn.commit()
	conn.close()
	
def get_applist():

	#db = "steam.db"
	#create_tables(db)
	liste_ban = read_nonjeux_db()
	print("Déjà " + str(len(liste_ban)) + " apps dans la ban list")
	liste_jeux = read_jeux_db()
	print("Déjà " + str(len(liste_jeux)) + " jeux dans la liste Steam")
	liste_upcoming_jeux = scrapy.scrap_upcoming()
	print(str(len(liste_upcoming_jeux)) + " jeux à venir recensés")

	print("Récupération de la liste des apps...")
	data = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v0001/").json()
	applist = data["applist"]["apps"]["app"]
	applist = [str(x["appid"]) for x in applist]
	applist += liste_upcoming_jeux
	counter = 0
	print("Filtrage de la liste...")
	app_filtered = [x for x in applist if not((x in liste_ban) or (x in liste_jeux))]
	print("Liste des apps constituée.")
	print("Apps à insérer dans la base : {} trouvées".format(len(app_filtered)))

	for x in app_filtered:
		#counter += 1
		#if counter > 190:
		#	print("190 apps scannées, 5 min d'attente... depuis {}".format(datetime.datetime.now().time()))
		#	time.sleep(300)
		#	counter = 0
		appid = x
		jeu = get_steam(appid)
		if not(jeu):
			app_filtered.append(x)
			print("Rate limit exceeded... 5 min d'attente depuis {}".format(datetime.datetime.now().time()))
			time.sleep(300)
		elif jeu != True:   #Teste si steam_get a renvoyé un jeu ou juste "True", donc une app non-jeu
			put_jeu_db(jeu, False)
		else:
			add_nongame(appid)

	print("Insertion terminée.")


def annonce_jour(delta):

	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()

	today = datetime.date.today() + datetime.timedelta(days = delta)
	nom_table = "{} {}, {}".format(today.day, datetime.date(1900, today.month, 1).strftime("%b"), today.year)
	sql = "SELECT nom, prix, isFree FROM steam_full WHERE date_sortie = '{}' ORDER BY date_sortie desc;".format(nom_table)
	c.execute(sql)
	jeux = c.fetchall()
	print ("Sortie du {} :".format(nom_table))
	for x in jeux:
		prix = x[1] / 100
		isFree = x[2]
		if not(isFree):
			if not(prix):
				prix = "Non renseigné"
		else:
			prix = "Free to play"
		uprint ("{} - Prix : {}".format(x[0], prix))

	conn.commit()
	conn.close()
	
def update_a_venir():
	
	# Update les infos des jeux pas encore sortis

	conn = sqlite3.connect("steamspy.db")
	c = conn.cursor()
	sql = "SELECT steamID FROM steam_full WHERE coming_soon = '1'"
	c.execute(sql)
	rows = c.fetchall()
	deja_sortis = [x[0] for x in rows]

	conn.commit()
	conn.close()

	for x in deja_sortis:
		jeu = get_steam(str(x))
		put_jeu_db(jeu, True)

		
def annonce_today():

	annonce_jour(-1)
	time.sleep(2)
	annonce_jour(0)
	time.sleep(2)
	annonce_jour(1)

def main():
	# Update les jeux à venir déjà dans la base
	update_a_venir()

	# Crée une nouvelle table Steamspy du jour si elle n'existe pas
	refresh_db()

	# Récupère la liste des apps de Steam et ajoute dans la base les apps non-existantes
	get_applist()

	# Liste les jeux sortis hier, aujourd'hui et demain
	annonce_today()
	
main()