#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Script définissant une fonction de téléchargement de données de cartes depuis le site internet scryfall.com et leur stockage dans une base de données SQLite"""

from html.parser import HTMLParser
from urllib.request import urlopen, urlretrieve
import os
from pathlib import Path
import sqlite3
from collections import OrderedDict
from .thumbnailer import global_tb

####################################

def path(strpath):
	"""Retourne le chemin au format de l'OS utilisé"""
	return str(Path(strpath))

def cond_get(stack, stag1, sval1=None, stag2=None, sval2=None): # prend en paramètre la pile <stack> et les termes de la recherche (tag et attributs)
	"""Fonction vérifiant un critère de recherche dans la liste <stack>"""
	tag2, attr2 = stack[-2][0], stack[-2][1]
	tag1, attr1 = stack[-1][0], stack[-1][1]
	if stag2: # si la recherche porte sur la dernière balise ouverte, sa balise parent et leurs attributs
		if stag1==tag1 and stag2==tag2 and ("class", sval2) in attr2: # vérification de la correspondance aux termes de la recherche <stag> et <sval>
			return True
	else: # si la recherche porte uniquement sur la dernière balise ouverte et ses attributs
		if stag1==tag1 and ("class", sval1) in attr1: # vérification de la correspondance aux termes de la recherche <stag> et <sval>
			return True
	return False


"""Classes suivantes : classes héritées de HTMLParser, permettant de parcourir le code HTML d'une page grâce à des méthodes repérant les balises"""

class IndexParser(HTMLParser):
	"""Classe récupérant les URLs des pages spécifiques à chaque carte à partir du code HTML d'une page index"""
	def __init__(self):
		super(IndexParser, self).__init__() # constructeur de la classe parent HTMLParser
		self.stack = [] # liste contenant un tuple (balise, attributs) pour chaque balise ouverte et pas encore refermée lors du parcours du code HTML

	def elems_stack(self):
		"""[DEBUG] Affichage de la pile des balises ouvertes"""
		print(" > ".join(x[0] for x in self.stack)) # affiche les tags contenus dans <stack>
		print(self.getpos()) # affiche le numéro de la ligne en parcours du code HTML

	def get_urls(self, index_html):
		"""Retourne à l'utilisateur les urls des pages des cartes dans l'index <index_html>"""
		self.urls = [] # liste contenant les urls obtenus
		self.feed(index_html) # appel de la méthode feed() (définie avec HTMLParser) qui active le parcours du code html <index_html>
		return self.urls

	def handle_starttag(self, tag, caracs):	# méthode traitant l'ouverture d'une balise
		"""Récupération de l'URL de chaque carte rencontrée"""
									# <tag> : nom du tag ouvert ; <caracs> : liste de tuples (nom,valeur) correspondant à chaque attribut du tag
		self.stack.append([tag,caracs]) # ajout du nouvel élément et de ses attributs à <stack>

		try:
			if cond_get(self.stack, stag1="a", sval1="card-grid-item-card"): # vérification des conditions caractérisant un tag portant l'URL d'une carte
				for attr in caracs: # parcours des attributs du tag pour trouver l'attribut contenant l'URL
					if attr[0]=="href":
						self.urls.append(attr[1]) # ajout de l'URL rencontrée à la liste
						break
		except IndexError:
			pass

	def handle_endtag(self, tag): # méthode traitant la fermeture d'une balise
						   # <tag> : nom du tag fermé
		self.stack.pop() # suppression du dernier élément de <stack>


class CardParser(HTMLParser):
	"""Classe permettant de récupérer les caractéristiques d"une carte dans le html de sa page consacrée."""
	def __init__(self):
		super(CardParser, self).__init__()
		self.stack = []

	def get_caracs(self, card_html):
		"""Stockage des caractéristiques de la carte dans un dictionnaire ordonné"""
		self.caracs = OrderedDict() # dictionnaire ordonné contenant les carctéristiques obtenues
		self.caracs["edition"] = ""
		self.caracs["title"] = ""
		self.caracs["cardid"] = "" # titre normalisé de la carte (miniscules et "_" uniquement)
		self.caracs["type"] = ""
		self.caracs["manacost"] = "" # coût de mana
#		self.caracs["cmanacost"] = "" # coût converti de mana (nombre total de manas de tout type nécessaires)
		self.caracs["color"] = ""
		self.caracs["oracle"] = "" # texte de capacités de la carte (version human-readable)
		self.caracs["stats"] = "" # force et endurance de la carte (vide si non-créature)
		self.caracs["rarity"] = ""
		self.caracs["setnumber"] = 0 # numéro de série de la carte dans son édition
		self.caracs["image"] = "" # URL de l'image jpg
		self.feed(card_html)
		return self.caracs

	def elems_stack(self):
		"""[DEBUG] Affichage de la pile des balises ouvertes"""
		print(" > ".join(x[0] for x in self.stack)) # affiche les tags contenus dans <stack>
		print(self.getpos()) # affiche le numéro de la ligne en parcours du code HTML

	def handle_starttag(self, tag, caracs):
		"""Récupèration de l'URL de l'image de la carte"""
		self.stack.append([tag,caracs])

		try:
			if cond_get(self.stack, stag2="div", sval2="card-image-front", stag1="img"): # vérification des conditions caractérisant le tag portant l'URL de l'image
				for attr in caracs: # parcours des attributs de la balise img pour trouver l'URL de l'image
					if attr[0] == "src":
						str_img = attr[1].replace(".jpg",".png").replace("/large/","/png/") # modification de l'URL d'image (image avec transparence)
						self.caracs["image"] = str_img # ajout de l'URL de l"image aux caractéristiques
						break
		except IndexError:
			pass

	def handle_data(self, data): # méthode traitant les données entre les balises (<data>)
		try: # vérification des conditions correspondant à chaque caractéristique
			if self.caracs["title"] == "" and cond_get(self.stack, stag1="h1", sval1="card-text-title"): # conditions pour <self.caracs["title"]>
				self.caracs["title"] = data

			if self.caracs["type"] == "" and cond_get(self.stack, stag1="p", sval1="card-text-type-line"): # conditions pour <self.caracs["type"]>
				self.caracs["type"] = data

			if self.caracs["edition"] == "" and cond_get(self.stack, stag1="span", sval1="prints-current-set-name"): # conditions pour <self.caracs["edition"]>
				self.caracs["edition"] = data

			if self.caracs["setnumber"] == 0 and cond_get(self.stack, stag1="span", sval1="prints-current-set-details"): # conditions pour le groupe #<self.caracs["setnumber"]> · <self.caracs["rarity"]>
				self.caracs["setnumber"] = int(data.split("·")[0].strip()[1:])
				self.caracs["rarity"] = data.split("·")[1]

			if self.caracs["stats"] == "" and cond_get(self.stack, stag1="div", sval1="card-text-stats"): # conditions pour <self.caracs["stats"]>
				self.caracs["stats"] = data

			if cond_get(self.stack, stag2="span", sval2="card-text-mana-cost", stag1="abbr"): # conditions pour <self.caracs["manacost"]>
				self.caracs["manacost"] += data

			if cond_get(self.stack, stag2="p", sval2="card-text-type-line", stag1="abbr"): # conditions pour <self.caracs["color"]> (cartes avec indicateur de couleur uniquement)
				for attr in self.stack[-1][1]:
					if attr[0] == "class":
						colors = attr[1].split("-")[-1]
				self.caracs["color"].append("".join("{"+ color +"}" for color in colors))

			if ["div",[("class","card-text-oracle")]] in self.stack: # condition pour <self.caracs["oracle"]> (le texte peut se trouver dans différentes balises)
				self.caracs["oracle"] += data
		except IndexError:
			pass

	def handle_endtag(self, tag):
		"""Traitement des données de <self.caracs>"""
		try: # ajout d'un retour à la ligne au texte de capacités <self.caracs[oracle]> si un tag paragraphe se ferme
			if ["div",[("class", "card-text-oracle")]] in self.stack and self.stack[-1][0] == "p":
				self.caracs["oracle"] += "\n"
		except IndexError:
			pass

		self.stack.pop()

		# Finalisation du traitement des données à la fin du parcours du code HTML
		if self.stack[-1][0] == "html":
			for key in self.caracs.keys():
				if type(self.caracs[key]) == str:
					self.caracs[key] = self.caracs[key].strip().replace("  "," ").replace("  "," ") # supressions des doubles-espaces des données de type chaîne de caractère

			# Détermination de la couleur de la carte
			colors = sorted(list(set(self.caracs["manacost"].replace("}","").replace("{","")))) # réduction du coût de mana aux seules couleurs et nombres
			try: # exclusion des nombres (manas génériques) et des X éventuels de <colors>
				if colors[0].isnumeric():
					colors.pop(0)
				colors = [c for c in colors if c != "X"]
			except (IndexError,ValueError):
				pass
			for color in colors: # définition de <self.caracs["colors"]> à partir de <colors>
				self.caracs["color"] += "{" + color + "}"
			if self.caracs["color"] == "": # si <colors> est vide, la carte est incolore
				self.caracs["color"] += "{C}"

			# Détermination du coût converti de mana de la carte
#			cmc = self.caracs["manacost"].replace("}","").replace("{","")
#			cmanacost = 0
#			for mana in cmc:
#				if mana.isnumeric():
#					cmanacost += int(mana)
#				elif mana in "WGRBU":
#					cmanacost += 1
#			self.caracs["cmanacost"] = str(cmanacost)

			self.caracs["cardid"] = self.caracs["title"].replace(" ","_").replace(",","").replace("'","").replace("-","_").lower() # titre normalisé




"""Fonction principale du module"""
def add_db(extensions, database="cards.db", thumb_repository="illustrations", image_repository="illustrations_large"):
	# <extensions> : identifiants (code de 3 à 4 caractères) des extensions à télécharger ; <database> : nom de la base de données
	"""Charge les données et les images des cartes des extensions <extensions>"""
	extensions = extensions.split(" ") # liste des codes des extensions à charger
	if not os.path.exists(image_repository): # création du dossier d'images de l'<extension>, dont le nom est l'identifiant de l'extension
			os.mkdir(image_repository)
	conn = sqlite3.connect(database) # création de la connexion à la base de données
	cur = conn.cursor() # création du curseur
	req = """CREATE TABLE IF NOT EXISTS card (edition TEXT, title TEXT, cardid TEXT, type TEXT, manacost TEXT, color TEXT, oracle TEXT, stats TEXT, rarity TEXT, setnumber INTEGER)"""
	cur.execute(req) # crétion éventuelle de la table des caractéristiques de cartes, dont les champs sont dans le même ordre que dans <CardParser.caracs>
	index_parser = IndexParser() # instanciation de l'objet qui servira au parsing de chaque extension
	card_parser = CardParser() # insatnciation de l'objet qui servira au parsing de chaque carte

	print("\n################### DOWNLOAD ###################") # affichage du log

	for extension in extensions: # parcours des <extensions>
		if not os.path.exists(path(image_repository+"/"+extension)): # création du dossier d'images de l'<extension>, dont le nom est l'identifiant de l'extension
			os.mkdir(path(image_repository+"/"+extension))

		page = urlopen("https://scryfall.com/sets/{0}".format(extension))
		urls = index_parser.get_urls(page.read().decode("utf-8")) # décodage et lecture de la page pour récupérer les urls grâce à <index_parser>

		cardtotal = len(urls) # nombre de cartes de l"édition <extension> à ajouter à la database
		print("\n----------- DOWNLOADING {0} ({1}) -----------".format(extension.upper(),cardtotal)) # affichage du log

		for rank,url in enumerate(urls,1): # parcours des cartes de <extension>, avec <rank> le numéro de la carte dans l'ordre de téléchargement
			card = urlopen(url)
			caracs = card_parser.get_caracs(card.read().decode("utf-8")) # décodage et lecture de la page pour récupérer les caractéristiques grâce à <card_parser>
			urlretrieve(caracs["image"],"{0}/{1}/{2} {3}.png".format(image_repository, extension, caracs["setnumber"], caracs["cardid"])) # téléchargement et enregistrement de l'image
			req = """INSERT INTO card VALUES ("{0}", {1})""".format('", "'.join(caracs[key] for key in caracs.keys() if (key != "image" and type(caracs[key]) == str)), caracs["setnumber"])
			cur.execute(req) # insertion des caractéristiques dans la table card
			conn.commit() # insertion du contenu du curseur dans la base de données

			print("RECEIVED : {0}/{1} {2}".format(rank, cardtotal, caracs["title"])) # affichage du log

		print("------------ RECEIVED {0} ({1}) ----------------\n".format(extension.upper(),cardtotal)) # affichage du log

	print("################ DOWNLOAD ENDED ################\n") # affichage du log
	cur.close()
	conn.close() # fermeture du curseur et de la connexion avec la base de données
	global_tb(image_repository, thumb_repository, extensions)

if __name__ == "__main__":
	extensions = "ktk tktk"
	add_db(extensions)