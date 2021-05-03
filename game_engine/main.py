#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import random as rdm
from game import Game

#####

class Game_manager():
	"""Représente une table de jeu à la quelle les jouers peuvent jouer plusieurs parties."""
	
	def __init__(self):
		"""Initialisation : information aux joueurs."""
		
		print("New game table with players A and B.")
		self.wins = {"A":0,"B":0,"=":0}
		self.decks = {"A":None,"B":None}
		self.opponents = {"A":"B","B":"A"}
		
		self.game = None
		self.starting_player = None
		self.new_game()
	
	def new_game(self):
		"""Crée l'objet <Game> de partie s'il n'existe pas ou le réinitialise s'il existe, pour une nouvelle partie."""
		
		self.deck_choice()
		if not(self.starting_player):
			self.starting_player = rdm.choice(["A","B"])
		
		if not(self.game): # vérification du fait qu'encore aucune partie n'a été créée
			self.game = Game(self.decks,self,self.starting_player)
		else:
			self.game.__init__(self.decks,self,self.starting_player)
	
	def end_and_new(self,win):
		"""Enregistre la victoire éventuelle d'un joueur durant la partie s'étant terminée et relance."""
		
		self.wins[win] += 1
		self.starting_player = self.opponents[win] # le perdant sera premier jouer de la prochaine partie
		
		if "o" in input("The result of last game has been {0}. New game ? (y or n) : ".format(win)).lower():
			self.new_game()
		else:
			print("Table closed. Final results :",self.wins)
			sys.exit() # fin brutale de l'exécution des méthodes de <Game_manager> et de l'instance de <Game> courante
	
	def deck_choice(self):
		"""Permet de modifier les decks joués par A et B."""
		
		if "o" in input("Modify decks ? (y or n) : ").lower():
			self.starting_player = None # l'avantage d'être premier joueur pour le perdant n'a pas de sens avec de nouveaux decks
			self.decks["A"] = input("Name of new deck for player A :")
			self.decks["B"] = input("Name of new deck for player B :")

#####