#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys
import datetime
import pygame
import pathlib
import classes as cls
import config as cfg
from pygame.locals import *

#### RACCOURCIS D'ACCÈS AU SYSTÈME DE FICHIER

def path(strpath):
	"""Retourne le chemin au format de l'OS utilisé"""
	return str(pathlib.Path(strpath))

#### FONCTIONS D'AFFICHAGE A L'ÉCRAN

def screen_print(font, text, color, **position):
	"""Retourne un tupple contenant une Surface (objet pygame) et le rectangle correspondant à la localisation sur l'écran sur laquelle s'affichera la surface, pour pouvoir afficher un texte spécifique."""
	surface = font.render(text, True, color)
	rect = surface.get_rect(**position)
	return surface, rect

def alpha_rect(dimension, alpha, color):
	surface = pygame.Surface(dimension)
	surface.set_alpha(alpha)
	surface.fill(color)
	return surface

#### ÉVÈNEMENTS CLAVIER

def key_pressed(inputKey):
	"""Permet de savoir si une touche spécifique donnée en argument a été enfoncée par l'utilisateur."""
	keysPressed = pygame.key.get_pressed()
	if keysPressed[inputKey]:
		return True
	else:
		return False

def return_keycharac(event_key):
	"""gestion des erreurs de touches de clavier sur un système windows"""
	if sys.platform == "win32" or sys.platform == "win64":
	    exceptions = [(K_q, 'a'),
	                  (K_w, 'z'),
	                  (K_a, 'q'),
	                  (K_SEMICOLON, 'm'),
	                  (K_z, 'w'),
	                  (K_m, ',')]
	elif sys.platform == 'linux':
	    exceptions = [(K_LSHIFT, ""),
				(K_RSHIFT, "")]
	for element in exceptions:
	    if event_key in element:
	        return element[1]
	return pygame.key.name(event_key)

##### RÉCUPÉRATION D'INFORMATIONS

def decklist_load(file):
	"""Retourne le dictionnaire contenant le nombre de chaque carte du deck <file>."""
	decklist = {}
	location = path('../decks/' + file)
	with open(location,'r') as deckfile:
		deck = deckfile.read()
		deck = deck.split('\n')
		deck.pop()
		for line in deck:
			card = line.split(' ')
			decklist[card[1]] = int(card[0])
	deckfile.close()
	return decklist

def decklist_save(decklist, file):
	location = path('../decks/' + file)
	with open(location,'w') as deckfile:
		for card in decklist:
			deckfile.write(str(decklist[card])+' '+card+'\n')
	deckfile.close()

def editions(file):
	edition_list = []
	location = path('../cards/'+file)
	with open(location,'r') as edition_file:
		edition_set = edition_file.read()
		edition_set = edition_set.split('\n')
		edition_set.pop()
		for edition in edition_set:
			edition_list.append(edition.lower())
	edition_file.close()
	return edition_list

def color_filter(colors, restriction):
	str_filter = ''
	if colors != []:
		str_filter += " AND ("
	first = True
	for color in colors:
		if first:
			first = False
		else:
			str_filter += ' {0} '.format(restriction)
		str_filter += """color LIKE '%{0}%'""".format(color)
	if colors != []:
		str_filter += ")"
	return str_filter

def edition_filter(editions):
	str_filter = '('
	first = True
	for edition in editions:
		if first:
			first = False
		else:
			str_filter += ' OR '
		str_filter += """edition LIKE '%({0})%'""".format(edition)
	str_filter += ')'
	return str_filter

def card_catalog(rank, total, colors, color_restriction, editions='(M10)', db='../cards/cards.db'):
	"""Retourne le catalogue des <number> cartes à partir de <rank> depuis <db>"""
	conn = sqlite3.connect(path(db))
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()
	ranks = []
	for num in range(1, total+1):
		ranks.append(rank+num)
	ranks = tuple(ranks)
	cur.execute("""SELECT * FROM card WHERE {0}{1} ORDER BY edition, setnumber""".format(edition_filter(editions), color_filter(colors, color_restriction)))
	table = cur.fetchall()
	nb_result = len(table)
	catalog = []
	for i, row in enumerate(table):
		if rank <= i and i < rank+total:
			catalog.append({})
			for key, val in zip(row.keys(), tuple(row)):
				catalog[-1][key] = val
	conn.close()
	return catalog, nb_result

def card_caracs(cardid, conn):
	"""Retourne le dictionnaire contenant les caractéristiques de la carte de nom <name_card> si une connexion à la base de donnée est ouverte."""
	conn.row_factory = sqlite3.Row
	cur = conn.cursor()
	cur.execute('SELECT * FROM card WHERE cardid=:id;', {'id':cardid})
	row = cur.fetchone()
	caracs = {}
	for key, val in zip(row.keys(), tuple(row)):
		if val != "":
			if key == "manacost":
				manacost = val.replace("}","").replace("{","")
				caracs["manacost"] = {"B":0, "C":0, "G":0, "R":0, "U":0, "W":0, "Q":0, "X":0}
				for mana in manacost:
					if mana.isnumeric():
						caracs["manacost"]["Q"] += int(mana)
					elif mana in "BCGRUWX":
						caracs["manacost"][mana] += 1

			elif key == "type":
				types = val.lower().split("—")
				if len(types) == 2:
					for word in types[1].split():
						if not "subtype" in caracs:
							caracs["subtype"] = []
						caracs["subtype"].append(word)
				for word in types[0].split():
					if word in ("legendary","basic","tribal"):
						if not "supertype" in caracs:
							caracs["supertype"] = []
						caracs["supertype"].append(word)
					else:
						if not "type" in caracs:
							caracs["type"] = []
						caracs["type"].append(word)

			elif key == "stats":
				if "Loyalty" in val:
					caracs["loyalty"] = int(val.split()[1])
				else:
					caracs["power"] = int(val.split("/")[0])
					caracs["thoughness"] = int(val.split("/")[1])

			elif key == "color":
				caracs["color"] = val[1]
			else:
				caracs[key] = val
	cur.close()
	return caracs

def retrieve_card(cardid, db='../cards/cards.db'):
	"""Se connecte à la base de données et retourne le dictionnaire contenant les caractéristiques de la carte de nom <name_card>"""
	conn = sqlite3.connect(path(db))
	card = card_caracs(cardid, conn)
	conn.close()
	return card

def illustration(cardid):
	"""Retourne l'image pygame d'une carte"""
	card = retrieve_card(cardid)
	illustration_name = '{0} {1}'.format(card['setnumber'], card['cardid'])
	edition = card['edition'].split('(')[-1][:-1].lower()
	illustration_path = '../cards/illustrations/{0}/{1}.png'.format(edition, illustration_name)
	return(pygame.image.load(path(illustration_path)).convert_alpha())

def illustration_name(card):
	return '{0} {1}'.format(card['setnumber'], card['cardid'])

def directory(card):
	return card['edition'].split('(')[-1][:-1].lower()

def subtypes():
	"""Renvoie un tuple de tous les sous-types du jeu à partir d'un fichier dans le répertoire "data"."""

	file_subtypes = open("data/subtypes","r")
	subtypes  = file_subtypes.read()
	subtypes_list = subtypes.split("\n")
	subtypes_list.pop() # enlève le dernier élément, une chaîne de caractère vide à cause du dernier caractère "\n" dans le fichier
	file_subtypes.close()
	return tuple(subtypes_list)