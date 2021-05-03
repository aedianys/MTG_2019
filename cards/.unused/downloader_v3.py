#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''Script définissant une fonction de téléchargement de données de cartes depuis le site internet scryfall.com et leur stockage dans une base de données SQLite'''

from html.parser import HTMLParser
from urllib.request import urlopen, urlretrieve
import os
import sqlite3
from collections import OrderedDict

####################################

def cond_get(stack, stag1, sval1=None, stag2=None, sval2=None): # prend en paramètre la pile <stack> et les termes de la recherche (tag et attributs)
	'''Fonction vérifiant un critère de recherche dans la liste <stack> (1: trouvé ; 0: non trouvé)'''
	tag2, attr2 = stack[-2][0], stack[-2][1]
	tag1, attr1 = stack[-1][0], stack[-1][1]
	if stag2: # si la recherche porte sur les deux dernières balises et leurs attributs
		if stag1==tag1 and stag2==tag2 and ('class', sval2) in attr2: # vérification de la correspondance aux termes de la recherche <stag> et <sval>
			return 1
	else: # si la recherche porte uniquement sur la dernière balise et ses attributs
		if stag1==tag1 and ('class', sval1) in attr1: # vérification de la correspondance aux termes de la recherche <stag> et <sval>
			return 1
	return 0 


'''Classes suivantes : classes héritées de HTMLParser, permettant de parcourir le code HTML d'une page grâce à des méthodes repérant les balises'''

class IndexParser(HTMLParser):
	'''Classe récupérant les URLs des pages spécifiques à chaque carte à partir du code HTML d'une page index'''
	def __init__(self):
		super(IndexParser, self).__init__() # constructeur de la classe parent HTMLParser
		self.stack = [] # liste contenant les balises (et leurs attributs) ouvertes et pas encore refermées lors du parcours du code HTML
		self.urls = [] # liste contenant les urls obtenus

	def elems_stack(self):
		'''[DEBUG] Affichage de la pile des balises ouvertes'''
		print(' > '.join(x[0] for x in self.stack)) # affiche les tags contenus dans <stack>
		print(self.getpos()) # affiche le numéro de la ligne en parcours du code HTML

	def handle_starttag(self, tag, caracs):	# méthode traitant l'ouverture d'une balise
		'''Récupération de l'URL de chaque carte rencontrée''' 
											# <tag> : nom du tag ouvert ; <caracs> : liste de tuples (nom,valeur) correspondant à chaque attribut du tag
		self.stack.append([tag,caracs]) # ajout du nouvel élément et de ses attributs à <stack>

		try:
			if cond_get(self.stack, stag1='a', sval1='card-grid-item-card'): # vérification des conditions caractérisant un tag portant l'URL d'une carte
				for attr in caracs: # parcours des attributs du tag pour trouver l'attribut contenant l'URL
					if attr[0]=='href':
						self.urls.append(attr[1]) # ajout de l'URL rencontrée à la liste
						break
		except IndexError:
			pass

	def handle_endtag(self, tag): # méthode traitant la fermeture d'une balise
								  # <tag> : nom du tag fermé
		self.stack.pop() # suppression du dernier élément de <stack>


class CardParser(HTMLParser):
	'''Classe permettant de récupérer les caractéristiques d'une carte dans le html de sa page consacrée.'''
	def __init__(self):
		super(CardParser, self).__init__()
		self.stack = []

		# Stockage des caractéristiques d'une carte dans un dictionnaire ordonné
		self.caracs = OrderedDict() # dictionnaire ordonné contenant les carctéristiques obtenues
		self.caracs['edition'] = []
		self.caracs['title'] = []
		self.caracs['cardid'] = [] # titre de la carte sans espaces ni apostrophes
		self.caracs['type'] = [] 
		self.caracs['manacost'] = [''] # liste des nombres et types de manas nécessaires
		self.caracs['cmanacost'] = [] # coût converti de mana (nombre total de manas de tout type nécessaires)
		self.caracs['color'] = []
		self.caracs['oracle'] = [''] # texte de capacités de la carte (version human-readable)
		self.caracs['stats'] = [''] # force et endurance de la carte (vide si non-créature non-planeswalker)
		self.caracs['rarity'] = []
		self.caracs['setnumber'] = [] # numéro de série de la carte dans son édition
		self.caracs['backside'] = [''] # nom de la carte au dos (carte double-face uniquement)
		self.caracs['image'] = [] # URL de l'image
		
		self.backside = True # indique si l'on se trouve dans les données de la face verso (carte double-face uniquement)

	def elems_stack(self):
		'''[DEBUG] Affichage de la pile des balises ouvertes'''
		print(' > '.join(x[0] for x in self.stack)) # affiche les tags contenus dans <stack>
		print(self.getpos()) # affiche le numéro de la ligne en parcours du code HTML

	def handle_starttag(self,tag,caracs):
		'''Récupèration de l'URL de l'image de la carte''' 
		self.stack.append([tag,caracs])

		try:
			if cond_get(self.stack, stag2='div', sval2='card-image-front', stag1='img'): # vérification des conditions caractérisant le tag portant l'URL de l'image
				for attr in caracs: # parcours des attributs de la balise img pour trouver l'URL de l'image
					if attr[0] == 'src': 
						str_img_front = attr[1].replace('.jpg','.png').replace('/large/','/png/') # modification de l'URL d'image (image avec transparence)
						self.caracs['image'].append(str_img_front) # ajout de l'URL de l'image aux caractéristiques
						break
			
			if cond_get(self.stack, stag2='div', sval2='card-image-back', stag1='img'): # conditions pour <self.caracs['image']> (carte double-face uniquement)
				for attr in caracs: # parcours des attributs de la balise img pour trouver l'URL de l'image
					if attr[0] == 'src': 
						str_img_back = attr[1].replace('.jpg','.png').replace('/large/','/png/') # modification de l'URL d'image (image avec transparence)
						self.caracs['image'].append(str_img_back) # ajout de l'URL de l'image aux caractéristiques
						break

			if cond_get(self.stack, stag1='h1', sval1='card-text-title'): # conditions pour <self.caracs['title']>
				self.backside = not(self.backside) # False après la première balise 'card-text-title' et True après la deuxième

		except IndexError:
			pass

	def handle_data(self,data): # méthode traitant les données entre les balises (<data>)
		try: # vérification des conditions correspondant à chaque caractéristique
			if cond_get(self.stack, stag1='h1', sval1='card-text-title') and data.strip() != '' : # conditions pour <self.caracs['title']>
				self.caracs['title'].append(data)

			if cond_get(self.stack, stag1='p', sval1='card-text-type-line') and data.strip() != '': # conditions pour <self.caracs['type']>
				self.caracs['type'].append(data)

			if cond_get(self.stack, stag1='span', sval1='prints-current-set-name'): # conditions pour <self.caracs['edition']>
				self.caracs['edition'].append(data)

			if cond_get(self.stack, stag1='span', sval1='prints-current-set-details'): # conditions pour le groupe <self.caracs['setnumber']>·<self.caracs['rarity']>
				self.caracs['setnumber'].append(data.split('·')[0])
				self.caracs['rarity'].append(data.split('·')[1])

			if cond_get(self.stack, stag1='div', sval1='card-text-stats'): # conditions pour <self.caracs['stats']>
				if self.backside:
					self.caracs['stats'].append(data)
				else:
					self.caracs['stats'][0] = data

			if cond_get(self.stack, stag2='span', sval2='card-text-mana-cost', stag1='abbr'): # conditions pour <self.caracs['manacost']>
				self.caracs['manacost'][0] += data

			if cond_get(self.stack, stag2='p', sval2='card-text-type-line', stag1='abbr'): # conditions pour <self.caracs['color']> (carte avec indicateurs de couleur uniquement)
				for attr in self.stack[-1][1]:
					if attr[0] == 'class':
						colors = attr[1].split('-')[-1]
				if self.backside and self.caracs['color'] == []:
					self.caracs['color'].append('')
				self.caracs['color'].append(''.join('{'+ color +'}' for color in colors))

			if ['div',[('class','card-text-oracle')]] in self.stack and ['p', []] in self.stack: # condition pour <self.caracs['oracle']> (le texte peut se trouver dans différentes balises)
				if self.backside:
					if len(self.caracs['oracle']) != 1:
						self.caracs['oracle'][1] += data
					else:
						self.caracs['oracle'].append(data)
				else:
					self.caracs['oracle'][0] += data
		except IndexError:
			pass

	def handle_endtag(self,tag):
		'''Traitement des données de <self.caracs>'''
		try: # ajout d'un retour à la ligne au texte de capacités <self.caracs[oracle]> si un tag paragraphe se ferme
			if ['div',[('class', 'card-text-oracle')]] in self.stack and self.stack[-1][0] == 'p':
				if self.backside:
					self.caracs['oracle'][1] += '\n'
				else:
					self.caracs['oracle'][0] += '\n'
		except IndexError:
			pass

		self.stack.pop()

		# Finalisation du traitement des données à la fin du parcours du code HTML
		if self.stack[-1][0] == 'html':
			# Détermination de la couleur de la carte
			colors = sorted(list(set(self.caracs['manacost'][0].replace('}','').replace('{','')))) # réduction du coût de mana aux seules couleurs et nombres
			try: # exclusion des nombres (manas génériques) et des X éventuels de <colors>
				if colors[0].isnumeric():
					colors.pop(0)
				colors = [c for c in colors if c != 'X']
			except (IndexError,ValueError):
				pass
			if self.caracs['color'] == []:
				self.caracs['color'].append('')
			if self.caracs['color'][0] == '':
				for color in colors: # définition de <self.caracs['colors']> à partir de <colors>
					self.caracs['color'][0] += ('{' + color + '}')
				if colors == []: # si <colors> est vide, la carte est incolore
					self.caracs['color'][0] = '{C}'
			if self.backside and len(self.caracs['color']) != 2:
				self.caracs['color'].append('{C}')

			# Détermination du coût converti de mana de la carte
			cmc = self.caracs['manacost'][0].replace('}','').replace('{','')
			cmanacost = 0
			for mana in cmc:
				if mana.isnumeric():
					cmanacost += int(mana)
				elif mana in 'WGRBU':
					cmanacost += 1
			self.caracs['cmanacost'].append(str(cmanacost))
			self.caracs['cardid'].append('')

			if self.backside:
				self.caracs['manacost'].append('')
				self.caracs['cmanacost'].append('0')
				self.caracs['cardid'].append('')
				if len(self.caracs['stats']) != 2:
					self.caracs['stats'].append('')

				self.caracs['edition'].append(self.caracs['edition'][0])
				self.caracs['rarity'].append(self.caracs['rarity'][0])
				self.caracs['setnumber'].append(self.caracs['setnumber'][0])

				self.caracs['backside'][0] = self.caracs['title'][1]
				self.caracs['backside'].append(self.caracs['title'][0])
				
			for key in self.caracs.keys():
				try :
					self.caracs[key][0] = self.caracs[key][0].strip().replace('  ',' ').replace('  ',' ') # supressions des doubles-espaces et des sauts de ligne
					if self.backside:
						self.caracs[key][1] = self.caracs[key][1].strip().replace('  ',' ').replace('  ',' ') # supressions des doubles-espaces et des sauts de ligne
				except (IndexError,AttributeError):
					pass
			
			self.caracs['cardid'][0] = self.caracs['title'][0].replace(' ','_').replace(',','').replace("'",'').replace('-','_').lower() # titre normalisé
			if self.backside:
				self.caracs['cardid'][1] = self.caracs['title'][1].replace(' ','_').replace(',','').replace("'",'').replace('-','_').lower() # titre normalisé

'''Fonction principale du module'''

def add_db(extensions, database='carddb.db'): # <extensions> : identifiants (code de 3 à 4 caractères) des extensions à télécharger ; <database> : nom de la base de données
	'''Charge les données et les images des cartes des extensions <extensions>'''
	extensions = extensions.split(' ') # liste des codes des extensions à charger
	db = './'+database # chemin du fichier de base de données 
	conn = sqlite3.connect(db) # création de la connexion à la base de données
	cur = conn.cursor() # création du curseur
	req = '''CREATE TABLE IF NOT EXISTS card (edition TEXT, title TEXT, cardid TEXT, type TEXT, manacost TEXT, cmanacost TEXT, color TEXT, oracle TEXT, stats TEXT, rarity TEXT, setnumber TEXT, backside TEXT)'''
	cur.execute(req) # crétion éventuelle de la table des caractéristiques de cartes, dont les champs sont dans le même ordre que dans <CardParser.caracs>

	print('\n################## DOWNLOAD ##################') # affichage du log

	for extension in extensions: # parcours des <extensions>
		if not os.path.exists('./'+extension): # création du dossier d'images de l'<extension>, dont le nom est l'identifiant de l'extension
			os.mkdir('./'+extension)

		page = urlopen('https://scryfall.com/sets/{0}'.format(extension)) 
		edition = IndexParser() # instanciation du parser de la page d'index
		edition.feed(page.read().decode('utf-8')) # décodage et lecture de la page pour alimenter le parser 

		cardtotal = len(edition.urls) # nombre de cartes de l'édition <extension> à ajouter à la database
		print('\n----------- DOWNLOADING {0} ({1}) -----------'.format(extension.upper(),cardtotal)) # affichage du log

		for rank,url in enumerate(edition.urls,1): # parcours des cartes de <extension>, avec <rank> le numéro de la carte dans l'ordre de téléchargement
			card = CardParser() # instanciation du parser de la page de la carte
			card.feed(urlopen(url).read().decode('utf-8')) # décodage et lecture de la page pour alimenter le parser

			urlretrieve(card.caracs['image'][0],'{0}/{1} - {2}.png'.format(extension, card.caracs['setnumber'][0], card.caracs['title'][0])) # téléchargement et enregistrement de l'image
			req = '''INSERT INTO card VALUES ("{0}")'''.format('", "'.join(card.caracs[key][0] for key in card.caracs.keys() if key != 'image')) # insertion des caractéristiques dans le curseur
			cur.execute(req) # insertion des caractéristiques dans la table card 

			if len(card.caracs['backside']) == 2: # si la carte est double-face
				urlretrieve(card.caracs['image'][1],'{0}/{1} - {2}.png'.format(extension, card.caracs['setnumber'][1], card.caracs['title'][1])) # téléchargement et enregistrement de l'image verso
				req = '''INSERT INTO card VALUES ("{0}")'''.format('", "'.join(card.caracs[key][1] for key in card.caracs.keys() if key != 'image')) # insertion des caractéristiques du verso dans le curseur
				cur.execute(req)

			conn.commit() # insertion du contenu du curseur dans la base de données
			print('RECEIVED : {0}/{1} {2}'.format(rank, cardtotal, card.caracs['title'][0])) # affichage du log

		print('----------- RECEIVED {0} ({1}) --------------\n'.format(extension.upper(),cardtotal)) # affichage du log

	print('################## DOWNLOAD ENDED ##################\n') # affichage du log

	cur.close()
	conn.close() # fermeture du curseur et de la connexion avec la base de données

if __name__ == '__main__':
	sets = 'pgp1'
	add_db(sets, 'db_test.db')
