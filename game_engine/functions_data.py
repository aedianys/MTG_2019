#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import pathlib

#####

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

def card_caracs(cardid, conn):
	"""Retourne le dictionnaire contenant les caractéristiques typées de façon pertinente de la carte de nom <name_card> si une connexion à la base de donnée est ouverte."""
	
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
				types = val.lower().split('—')
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

def subtypes():
	"""Renvoie un tuple de tous les sous-types du jeu à partir d'un fichier dans le répertoire "data"."""
	
	file_subtypes = open("../documents/subtypes","r")
	subtypes  = file_subtypes.read()
	subtypes_list = subtypes.split("\n")
	subtypes_list.pop() # enlève le dernier élément, une chaîne de caractère vide à cause du dernier caractère "\n" dans le fichier
	file_subtypes.close()
	return tuple(subtypes_list)

#####