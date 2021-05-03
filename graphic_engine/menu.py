#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pathlib
import pygame
import datetime
import sqlite3
import math
import config as cfg
from pygame.locals import *
import functions as fc
import classes as cls

NOIR         = (  0,   0,   0)
GRIS_FONCE   = ( 64,  64,  64)
GRIS         = (128, 128, 128)
GRIS_CLAIR   = (192, 192, 192)
BLANC        = (255, 255, 255)
BLEU_CIEL    = (185, 240, 240)
BLEU_MOYEN   = ( 46, 186, 254)
BLEU_NUIT    = (  5,   5,  30)
ROUGE        = (255,   0,   0)
ROSE         = (214,   0, 127)
ORANGE       = (255, 128,   0)
MARRON       = (145,  35,  30)
VERT         = (  0, 255,   0)
BLEU         = (  0,   0, 255)
JAUNE        = (255, 255,   0)
GOLD         = (255, 215,   0)
BLEU_LAVANDE = (  1,  97, 174)

GESTIONNAIRE = 'images/UI/gestionnaire/'
ACCUEIL = 'images/UI/accueil/'

def accueil():
	"""Écran d'accueil"""
	# Définition des boutons cliquables dans le menu
	Play = cls.MenuButton(ACCUEIL+'button', (800,300), 'Jouer')
	Deck = cls.MenuButton(ACCUEIL+'button', (800,400), 'Gestionnaire de decks')
	Options = cls.MenuButton(ACCUEIL+'button', (800,500), 'Options')
	Quit = cls.MenuButton(ACCUEIL+'button', (800,600), 'Quitter')
	#---------------------------------------------------------------------------------------------------------
	# Chargement de la musique
##	pygame.mixer.music.load(fc.path('music/accueil.mp3'))
##	pygame.mixer.music.play (-1, 0.0)
##	pygame.mixer.music.set_volume(1)
	# Fin du chargement de la musique
	#---------------------------------------------------------------------------------------------------------
	# Constantes de la boucle de menu
	continuer = True
	title = fc.screen_print(cfg.mtg_large, "Welcome to Magic !", NOIR, center=(800, 100))
	# Mise en place de l'affichage d'arrière-plan
	img_id = 0 # numéro de l'image d'arrière plan affichée
	ouverture = True # si l'image est en train d'apparaître (True) ou de disparaître (False)
	current = cfg.wallpapers[0] # image d'arrière plan affichée
	DURATION = 400 # durée d'affichage de chaque image d'arrière plan en millisecondes (faire fois 40)
	time = 0 # durée écoulée depuis le dernier changement d'image
	pygame.time.set_timer(USEREVENT, 40)
	#---------------------------------------------------------------------------------------------------------
	# Boucle de menu
	while continuer:
		mouse = pygame.mouse.get_pos()
		# Détection des événements
		for event in pygame.event.get():
			if event.type == QUIT: # détection de clic sur le bonton 'fermer'
				continuer = False

			elif fc.key_pressed(K_ESCAPE): # détection de changement de mode d'affichage
				if cfg.screen_surface.get_flags() and pygame.FULLSCREEN:
					cfg.screen_surface = pygame.display.set_mode((1600,900))
				else:
					cfg.screen_surface = pygame.display.set_mode((1600,900), pygame.FULLSCREEN)

			elif event.type == MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]: # détection de clic de la souris sur les boutons du menu
				if Play.in_button(mouse):
					return game_selection()
				elif Deck.in_button(mouse):
					return gestionnaire_deck()
				elif Options.in_button(mouse):
					return options()
				elif Quit.in_button(mouse):
					return

			elif event.type == USEREVENT: # détection d'évenement déclenchés à intervalle régulier pas l'objet Timer
								   #défini précedemment et gestion de l'affichage en fondu en arrière-plan
				if ouverture:
					time += 1
				else:
					time -= 1
				if time == int(DURATION/2):
					ouverture = False
				elif time == 0:
					ouverture = True
					img_id = (img_id + 1) % cfg.nb_wallpaper
					current = cfg.wallpapers[img_id]

		#---------------------------------------------------------------------------------------------------------
		# Affichage à l'écran des éléments
		cfg.screen_surface.fill(NOIR)
		cfg.screen_surface.blit(current, current.get_rect(center = (800, 450)))
		cfg.screen_surface.blit(fc.alpha_rect(cfg.taille_fenetre, max(256-6*time, 0), NOIR), (0, 0))
		cfg.screen_surface.blit(title[0], title[1])

		#Affichage des boutons
		Play.display(cfg.screen_surface, mouse)
		Deck.display(cfg.screen_surface, mouse)
		Options.display(cfg.screen_surface, mouse)
		Quit.display(cfg.screen_surface, mouse)

		pygame.display.flip()


def gestionnaire_deck():
	"""Écran du gestionnaire"""
	# Initialisation des decks par lecture des fichiers de deck
	global decklists
	decklists = {} # dictionnaire des decks (clef: nom du deck, valeur: deck sous la forme d'un dictionnaire
			    # (clef: nom de la carte, valeur: nombre d'exemplaires))
	for file in os.listdir(fc.path('../decks')): # chargement de chaque deck se trouvant dans le dossier "decks"
		decklists[file] = fc.decklist_load(file)
	# Initialisation des illustrations utilisées par les decks
	global illustrations
	illustrations = {} # dictionnaire des illustrations chargées par pygame (clef: nom de la carte, valeur: illustration)
	for decklist in decklists.values():
		for cardid in decklist:
			if not(cardid in illustrations):
				illustrations[cardid] = fc.illustration(cardid) # chargement des illustrations des cartes de chaque decklist
	#---------------------------------------------------------------------------------------------------------
	# Définition des boutons cliquables
	Return = cls.MenuButton(GESTIONNAIRE+'button', (160,100), 'Retour')
	global deck_buttons
	deck_buttons = [] # liste des boutons des decks
	for num, deck in enumerate(decklists):
		deck_buttons.append(cls.DeckButton(GESTIONNAIRE+'deck_button', (160,236+num*69), deck, deck)) # instanciation des boutons de deck
	New = cls.DeckButton(GESTIONNAIRE+'deck_button', (160, 236+len(deck_buttons)*69), 'Nouveau Deck', '+ Nouveau Deck')
	#---------------------------------------------------------------------------------------------------------
	# Constantes de la boucle
	title = fc.screen_print(cfg.mtg_large, "Gestionnaire de decks :", NOIR, center=(800, 100))
	wallpaper = pygame.image.load(fc.path('images/gestionnaire/wallpaper.jpg')).convert()
	continuer = True
	#---------------------------------------------------------------------------------------------------------
	# Boucle de la page
	while continuer:
		mouse = pygame.mouse.get_pos()
		# Détection des événements
		for event in pygame.event.get():
			if event.type == QUIT: # détection de clic sur le bonton 'fermer'
				continuer = False

			elif fc.key_pressed(K_ESCAPE): # détection de changement de mode d'affichage
				if cfg.screen_surface.get_flags() and pygame.FULLSCREEN:
					cfg.screen_surface = pygame.display.set_mode((1600,900))
				else:
					cfg.screen_surface = pygame.display.set_mode((1600,900), pygame.FULLSCREEN)

			elif event.type == MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]: # détection du clic de la souris sur un des boutons
				if Return.in_button(mouse):
					return accueil()

				elif New.in_button(mouse):
					return creation_deck('') # création d'un nouveau deck

				for deckbutton in deck_buttons:
					if deckbutton.in_button(mouse):
						return creation_deck(Button.name) # modification d'un deck existant

		#---------------------------------------------------------------------------------------------------------
		#Affichage à l'écran des éléments
		cfg.screen_surface.fill(NOIR)
		cfg.screen_surface.blit(wallpaper, wallpaper.get_rect(center = (800, 450)))
		cfg.screen_surface.blit(title[0], title[1])

		#Architecture du gestionnaire
		cfg.screen_surface.blit(fc.alpha_rect((300, 690), 128, GRIS_CLAIR), (10, 200))
		pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((10, 200), (300, 690)), 3)

		cfg.screen_surface.blit(fc.alpha_rect((900, 690), 128, GRIS_CLAIR), (350, 200))
		pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((350, 200), (900, 690)), 3)

		cfg.screen_surface.blit(fc.alpha_rect((300, 690), 128, GRIS_CLAIR), (1290, 200))
		pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((1290, 200), (300, 690)), 3)

		#Affichage des boutons
		Return.display(cfg.screen_surface, mouse)

		#Affichage des boutons de decks
		for Button in deck_buttons:
			Button.display(cfg.screen_surface, mouse)
		if len(deck_buttons) < 10: # si les 10 emplacements sont remplis, on ne peut plus créer de nouveau deck
			New.display(cfg.screen_surface, mouse)

		pygame.display.flip()

def creation_deck(deck):
	"""Fonction de création d'un deck dans le gestionnaire"""
	# Définition des boutons cliquables
	Return = cls.MenuButton(GESTIONNAIRE+'button', (160,100), 'Retour')
	if deck == '': # si un nouveau deck est créé, création d'un nouveau bouton au nom vide
		deck_buttons.append(cls.DeckButton(GESTIONNAIRE+'deck_button', (160,234+len(deck_buttons)*69), '', ''))
	New = cls.DeckButton(GESTIONNAIRE+'deck_button', (160, 234+len(deck_buttons)*69), 'Nouveau Deck', '+ Nouveau Deck')
	#---------------------------------------------------------------------------------------------------------
	# Constantes du créateur de deck
	title = fc.screen_print(cfg.mtg_large, "Création d'un deck :", NOIR, center=(800, 100))
	wallpaper = pygame.image.load(fc.path('images/gestionnaire/wallpaper.jpg')).convert()
	filters = fc.screen_print(cfg.mtg_high, "Filtres :", NOIR, center=(450,240))
	for button in deck_buttons: # Activation du bouton du deck actif
		if button.name == deck:
			button.switch()
	continuer = True
	#---------------------------------------------------------------------------------------------------------
	# Boucle de nommage du nouveau deck
	if deck == '':
		while continuer:
			deck_buttons[-1].texte = fc.screen_print(cfg.mtg_medium, deck, NOIR, center = deck_buttons[-1].position)
			mouse = pygame.mouse.get_pos()
			# Détection des événements
			for event in pygame.event.get():
				if event.type == QUIT: # détection de clic sur le bonton 'fermer'
					continuer = False

				elif fc.key_pressed(K_ESCAPE): # détection de changement de mode d'affichage
					if cfg.screen_surface.get_flags() and pygame.FULLSCREEN:
						cfg.screen_surface = pygame.display.set_mode((1600,900))
					else:
						cfg.screen_surface = pygame.display.set_mode((1600,900), pygame.FULLSCREEN)

				elif fc.key_pressed(K_RETURN) and deck.strip() != '' and not(deck in decklists): # si le nom est valide et que <K_RETURN> est appuyée
					decklists[deck] = {} # création de la decklist
					deck_buttons[-1].name = deck # nommage du bouton créé qui n'avait pas de nom
					continuer = False # on continue sur l'édition de ce nouvaeu deck

				elif event.type == MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]: # détection du clic de la souris sur un des boutons
					if Return.in_button(mouse):
						return accueil()

					for Button in deck_buttons:
						if Button.in_button(mouse): # si un deck est sélectionné par clic sur son bouton
							deck_buttons.pop() # suppression du nouveau deck car il est abandonné
							return creation_deck(Button.name) # modification du deck sélectionné

				elif event.type == KEYDOWN:
					key = fc.return_keycharac(event.key) # récupération du nom de la touche appuyée
					if fc.key_pressed(K_BACKSPACE) or fc.key_pressed(K_DELETE): # suppression du dernier caractère
						deck = deck[:-1]

					if cfg.mtg_medium.render(deck,True,NOIR).get_width()<250 and (key.isalpha() or key == ' ') and len(key) == 1:
						# si le nom ne dépasse pas du cadre du bouton et que la touche est un lettre, on modifie le nom du deck
						if fc.key_pressed(K_LSHIFT) or fc.key_pressed(K_RSHIFT):
							deck += key.upper()
						else:
							deck += key

			#---------------------------------------------------------------------------------------------------------
			# Affichage à l'écran des éléments
			cfg.screen_surface.fill(NOIR)
			cfg.screen_surface.blit(wallpaper, wallpaper.get_rect(center = (800, 450)))
			cfg.screen_surface.blit(title[0], title[1])

			# Architecture du gestionnaire
			cfg.screen_surface.blit(fc.alpha_rect((300, 690), 128, GRIS_CLAIR), (10, 200))
			pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((10, 200), (300, 690)), 3)

			cfg.screen_surface.blit(fc.alpha_rect((900, 690), 128, GRIS_CLAIR), (350, 200))
			pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((350, 200), (900, 690)), 3)

			cfg.screen_surface.blit(fc.alpha_rect((300, 690), 128, GRIS_CLAIR), (1290, 200))
			pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((1290, 200), (300, 690)), 3)

			# Affichage des boutons
			Return.display(cfg.screen_surface, mouse)

			#Affichage des boutons de decks
			for Button in deck_buttons:
				Button.display(cfg.screen_surface, mouse)
			if len(deck_buttons) < 10:
				New.display(cfg.screen_surface, mouse)

			pygame.display.flip()

	#---------------------------------------------------------------------------------------------------------
	# Définition des boutons cliquables
	card_buttons = {} # dictionnaire des cartes de la decklist
	for num, cardid in enumerate(decklists[deck]):
		card_title = fc.retrieve_card(cardid)['title'] # récupération du nom de la carte
		# instanciation du bouton de la carte dans la liste
		card_buttons[cardid] = cls.CardListButton(GESTIONNAIRE+'card_button', (1440,218+num*30), card_title, cardid, decklists[deck][cardid])

	Save = cls.MenuButton(GESTIONNAIRE+'button', (1440,100), 'Enregistrer')

	# Boutons de navigation dans le catalogue
	PageUp = cls.ArrowButton(GESTIONNAIRE+'arrow_up_button', (1180,225), GESTIONNAIRE+'arrow_button_highlight')
	PageUpUp = cls.ArrowButton(GESTIONNAIRE+'arrow_up_up_button', (1210,225), GESTIONNAIRE+'arrow_button_highlight')
	PageDown = cls.ArrowButton(GESTIONNAIRE+'arrow_down_button', (1180,255), GESTIONNAIRE+'arrow_button_highlight')
	PageDownDown = cls.ArrowButton(GESTIONNAIRE+'arrow_down_down_button', (1210,255), GESTIONNAIRE+'arrow_button_highlight')

	# Boutons interrupteurs des filtres
	Mana = {'B' : cls.ManaSwitchButton(GESTIONNAIRE+'mana_B', (900,240), GESTIONNAIRE+'mana_B_active', 'B'),
	'C' : cls.ManaSwitchButton(GESTIONNAIRE+'mana_C', (870,240), GESTIONNAIRE+'mana_C_active', 'C'),
	'G' : cls.ManaSwitchButton(GESTIONNAIRE+'mana_G', (930,240), GESTIONNAIRE+'mana_G_active', 'G'),
	'R' : cls.ManaSwitchButton(GESTIONNAIRE+'mana_R', (960,240), GESTIONNAIRE+'mana_R_active', 'R'),
	'U' : cls.ManaSwitchButton(GESTIONNAIRE+'mana_U', (990,240), GESTIONNAIRE+'mana_U_active', 'U'),
	'W' : cls.ManaSwitchButton(GESTIONNAIRE+'mana_W', (1020,240), GESTIONNAIRE+'mana_W_active', 'W')}

	Restriction = cls.RestrictionButton(GESTIONNAIRE+'restriction', (820,240), 'OU', 'ET')
	#---------------------------------------------------------------------------------------------------------
	# Constantes du créateur de deck
	color_filter = list(Mana.keys()) # filtre des couleurs de mana
	restriction = Restriction.message # restriction du filtre ("et"/"ou")
	editions = fc.editions('editions_used') # éditions utilisées dans le gestionnaire pour la créatino de decks
	page = 1 # page du catalogue active
	NBCARD = 8 # nombre de cartes maximum affichés en même temps par le catalogue
	COLUMNS = 4 # nombre de colonnes pour l'affichage des cartes du catalogue
	#---------------------------------------------------------------------------------------------------------
	# Initialisation des cartes à partir de la base de données
	global catalog
	global card_catalog
	global nb_catalog
	global card_catalog_buttons
	catalog = fc.card_catalog(NBCARD*(page-1), NBCARD, color_filter, Restriction.value, editions)
	card_catalog = catalog[0] # ensemble de <NBCARD> cartes correspondant aux filtres appliqués
	nb_catalog = catalog[1] # nombre total de cartes disponibles dans le catalogue
	card_catalog_buttons = [] # liste des <NBCARD> boutons des cartes du catalogue
	for num, card in enumerate(card_catalog):
		illustration_path = '../cards/illustrations/{0}/{1}'.format(fc.directory(card), fc.illustration_name(card))
		# instanciation d'un bouton correspondant à la carte <card>
		cardbutton = cls.CardCatalogButton(illustration_path, (466+222*(num%COLUMNS),426+306*(num//COLUMNS)), card['cardid'])
		card_catalog_buttons.append(cardbutton)
	# Autres constantes
	page_total = math.ceil(nb_catalog/NBCARD) # nombre de pages total du catalogue
	nb_card_buttons = len(card_buttons) # nombre de boutons de cartes dans la liste
	card_total = 0 # nombre de cartes du deck sélectionné
	for cardid in decklists[deck]: # calcul du nombre de cartes dans le deck
		card_total += decklists[deck][cardid]
	continuer = True
	#---------------------------------------------------------------------------------------------------------
	# Boucle de création de deck
	while continuer:
		# création de backup de certaines variables pour détecter un changement d'affichage du catalogue
		old_nb_card_buttons = nb_card_buttons
		old_page = page
		old_color_filter = color_filter[:]
		old_restriction = restriction
		mouse = pygame.mouse.get_pos()

		# Détection des événements
		for event in pygame.event.get():
			if event.type == QUIT: # détection de clic sur le bonton 'fermer'
				continuer = False

			elif fc.key_pressed(K_ESCAPE): # détection de changement de mode d'affichage
				if cfg.screen_surface.get_flags() and pygame.FULLSCREEN:
					cfg.screen_surface = pygame.display.set_mode((1600,900))
				else:
					cfg.screen_surface = pygame.display.set_mode((1600,900), pygame.FULLSCREEN)

			elif event.type == MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]: # détection du clic de la souris sur un des boutons
				if Return.in_button(mouse):
					return accueil()
				if Save.in_button(mouse):
					fc.decklist_save(decklists[deck], deck) # enregistrement du deck actif
				elif New.in_button(mouse):
					for button in deck_buttons:
						if button.name == deck:
							button.switch() # désactivation du deck actif
					return creation_deck('') # création d'un nouveau deck

				elif PageUp.in_button(mouse):
					page = max(page-1, 1) # une page en arrière
				elif PageUpUp.in_button(mouse):
					page = max(page-10, 1) # dix pages en arrière
				elif PageDown.in_button(mouse):
					page = min(page+1, page_total) # une page en avant
				elif PageDownDown.in_button(mouse):
					page = min(page+10, page_total) # dix pages en avant

				elif Restriction.in_button(mouse):
					Restriction.switch() # modification de la restriction de recherche
					restriction = Restriction.message

				for Button in deck_buttons:
					if Button.in_button(mouse) and Button.name != deck:
						for button in deck_buttons:
							if button.name == deck:
								button.switch() # désactivation du deck actif
						return creation_deck(Button.name) # modification du deck sélectionné

				for Button in card_catalog_buttons:
					if Button.in_button(mouse):
						cardid = Button.cardid
						card = fc.retrieve_card(cardid)
						if not cardid in card_buttons:
							card_total += 1 # augmentation du nombre de cartes dans la decklist de 1
							decklists[deck][cardid] = 1 # création de l'entrée de la carte dans la decklist
							nb_card_buttons += 1 # augmentation du nombre de boutons de cartes dans la liste
							illustrations[cardid] = fc.illustration(cardid) # chargement de l'illustration de la carte

						elif "supertype" in card:
							if "basic" in card["supertype"]:
								card_total += 1 # augmentation du nombre de cartes dans la decklist de 1
								decklists[deck][cardid] += 1 # augmentation du nombre d'exemplaires de la carte de 1
								card_buttons[cardid].nb += 1
								break

							elif card_buttons[cardid].nb < 4:
								card_total += 1 # augmentation du nombre de cartes dans la decklist de 1
								decklists[deck][cardid] += 1 # augmentation du nombre d'exemplaires de la carte de 1
								card_buttons[cardid].nb += 1
								break

						elif card_buttons[cardid].nb < 4: # si le nombre d'exemplaires vérifie les limites
							card_total += 1 # augmentation du nombre de cartes dans la decklist de 1
							decklists[deck][cardid] += 1 # augmentation du nombre d'exemplaires de la carte de 1
							card_buttons[cardid].nb += 1
							break

				for Button in card_buttons.values():
					if Button.in_button(mouse):
						card_total -=1 # diminution du nombre de cartes dans la decklist de 1
						cardid = Button.cardid
						decklists[deck][cardid] -= 1 # diminution du nombre d'exemplaires de la carte de 1
						card_buttons[cardid].nb -= 1
						if decklists[deck][cardid] == 0: # s'il n'y a plus d'exemplaires de cette carte dans la decklist
							nb_card_buttons -= 1 # diminution du nombre de boutons de la decklist
							decklists[deck].pop(cardid) # supression du bouton correspondant à cette carte
						break

				for Button in Mana.values():
					if Button.in_button(mouse):
						Button.switch() # changement du statut du bouton cliqué
						if Button.active:
							color_filter.append(Button.name) # ajout de la couleur au filtre
						else:
							color_filter.remove(Button.name) # suppression de la couleur du filtre

		#---------------------------------------------------------------------------------------------------------
		# Recalcul des cartes affichées dans le catalogue
		if old_page != page or old_color_filter != color_filter or restriction != old_restriction:
			# Recalcul du nombre de pages après le passage du nouveau filtre
			catalog = fc.card_catalog(NBCARD*(page-1), NBCARD, color_filter, Restriction.value, editions)
			nb_catalog = catalog[1]
			page_total = math.ceil(nb_catalog/NBCARD)
			page = min(page, max(page_total, 1)) # le numéro de page doit s'adapter à ce nouveau nombre de pages disponibles

			# Recalcul du catalogue affiché
			catalog = fc.card_catalog(NBCARD*(page-1), NBCARD, color_filter, Restriction.value, editions)
			card_catalog = catalog[0] # ensemble de <NBCARD> cartes correspondant aux filtres appliqués
			nb_catalog = catalog[1] # nombre total de cartes disponibles dans le catalogue
			card_catalog_buttons = [] # liste des <NBCARD> boutons des cartes du catalogue
			page_total = math.ceil(nb_catalog/NBCARD)
			for num, card in enumerate(card_catalog):
				illustration_path = '../cards/illustrations/{0}/{1}'.format(fc.directory(card), fc.illustration_name(card))
				# instanciation d'un bouton correspondant à la carte <card>
				cardbutton = cls.CardCatalogButton(illustration_path, (466+222*(num%COLUMNS),426+306*(num//COLUMNS)), card['cardid'])
				card_catalog_buttons.append(cardbutton)

		# Recalcul des boutons de cartes
		if old_nb_card_buttons != nb_card_buttons: # si le nombre de cartes total a changé
			card_buttons = {}
			for num, cardid in enumerate(decklists[deck]):
				card_title = fc.retrieve_card(cardid)['title']
				card_buttons[cardid] = cls.CardListButton(GESTIONNAIRE+'card_button', (1440,218+num*30), card_title, cardid, decklists[deck][cardid])

		#---------------------------------------------------------------------------------------------------------
		# Affichage à l'écran des éléments
		cfg.screen_surface.fill(NOIR)
		cfg.screen_surface.blit(wallpaper, wallpaper.get_rect(center = (800, 450)))

		# Architecture du gestionnaire
		cfg.screen_surface.blit(fc.alpha_rect((300, 690), 128, GRIS_CLAIR), (10, 200))
		pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((10, 200), (300, 690)), 3)

		cfg.screen_surface.blit(fc.alpha_rect((900, 690), 128, GRIS_CLAIR), (350, 200))
		pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((350, 200), (900, 690)), 3)

		cfg.screen_surface.blit(fc.alpha_rect((300, 690), 128, GRIS_CLAIR), (1290, 200))
		pygame.draw.rect(cfg.screen_surface, NOIR, pygame.Rect((1290, 200), (300, 690)), 3)

		# Affichage des textes
		cfg.screen_surface.blit(title[0], title[1])
		cfg.screen_surface.blit(filters[0], filters[1])
		if page_total != 0:
			page_location = fc.screen_print(cfg.mtg_small, 'Page : {0}/{1}'.format(page,page_total), NOIR, center=(1100,240))
			cfg.screen_surface.blit(page_location[0], page_location[1])
		else:
			warning = fc.screen_print(cfg.mtg_high, 'Aucun résultat', NOIR, center=(800,545))
			cfg.screen_surface.blit(warning[0], warning[1])
		# total des cartes affiché au bas de la liste du deck
		total = fc.screen_print(cfg.mtg_little, 'Total : ' + str(card_total), NOIR, center=(1440,880))
		cfg.screen_surface.blit(total[0], total[1])

		# Affichage des boutons
		Return.display(cfg.screen_surface, mouse)
		Save.display(cfg.screen_surface, mouse)
		Restriction.display(cfg.screen_surface, mouse)

		PageUp.display(cfg.screen_surface, mouse)
		PageUpUp.display(cfg.screen_surface, mouse)
		PageDown.display(cfg.screen_surface, mouse)
		PageDownDown.display(cfg.screen_surface, mouse)

		# Affichage des bouton de filtre
		for Button in Mana.values():
			Button.display(cfg.screen_surface, mouse)

		# Affichage des boutons de deck
		for Button in deck_buttons:
			Button.display(cfg.screen_surface, mouse)
		if len(deck_buttons) < 10:
			New.display(cfg.screen_surface, mouse)

		# Affichage des boutons de cartes dans le catalogue
		for Button in card_catalog_buttons:
			Button.display(cfg.screen_surface, mouse)

		# Affichage des boutons de cartes dans la liste
		for Button in card_buttons.values():
			Button.display(cfg.screen_surface, mouse)
		for Button in card_buttons.values():
			Button.illustration_display(cfg.screen_surface, mouse)

		pygame.display.flip()

def options():
	# Définition des boutons cliquables dans le menu
	Return = cls.MenuButton(GESTIONNAIRE+'button', (160,100), 'Retour')
	#---------------------------------------------------------------------------------------------------------
	# Constantes de la boucle des options
	title = fc.screen_print(cfg.mtg_large, "Options", NOIR, center=(800, 100))
	info = fc.screen_print(cfg.mtg_medium, "Pour l'instant, aucune option n'est disponible.", NOIR, center=(800, 400))
	continuer = True
	pygame.time.set_timer(USEREVENT, 5000)
	wallpaper = pygame.image.load(fc.path('images/options/wallpaper.jpg')).convert()
	#---------------------------------------------------------------------------------------------------------
	# Boucle des options
	while continuer:
		# Détection des événements
		mouse = pygame.mouse.get_pos()
		for event in pygame.event.get():
			if event.type == QUIT:
				continuer = False

			elif fc.key_pressed(K_ESCAPE):
				if cfg.screen_surface.get_flags() and pygame.FULLSCREEN:
					cfg.screen_surface = pygame.display.set_mode((1600,900))
				else:
					cfg.screen_surface = pygame.display.set_mode((1600,900), pygame.FULLSCREEN)

			elif event.type == MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
				if Return.in_button(mouse):
					return accueil()
		#---------------------------------------------------------------------------------------------------------
		# Affichage à l'écran des éléments
		cfg.screen_surface.fill(NOIR)
		cfg.screen_surface.blit(wallpaper, wallpaper.get_rect(center=(800, 450)))
		cfg.screen_surface.blit(title[0], title[1])
		cfg.screen_surface.blit(info[0], info[1])

		# Affichage des boutons
		Return.display(cfg.screen_surface, mouse)

		pygame.display.flip()

def game_selection():
	# Définition des boutons cliquables dans le menu
	Solo = cls.MenuButton(ACCUEIL+'button', (800,300), 'Solo')
	Multi = cls.MenuButton(ACCUEIL+'button', (800,400), 'Multijoueur')
	Return = cls.MenuButton(ACCUEIL+'button',(800,500), 'Retour')
	#---------------------------------------------------------------------------------------------------------
	# Constantes de la boucle de sélection du type de jeu
	continuer = True
	title = fc.screen_print(cfg.mtg_large, "Sélection du jeu :", NOIR, center=(800, 100))
	pygame.time.set_timer(USEREVENT, 5000)
	wallpaper = pygame.image.load(fc.path('images/game/wallpaper.jpg')).convert()
	#---------------------------------------------------------------------------------------------------------
	# Boucle de sélection du type de jeu
	while continuer:
		mouse = pygame.mouse.get_pos()
		for event in pygame.event.get():
			if event.type == QUIT:
				continuer = False

			elif fc.key_pressed(K_ESCAPE):
				if cfg.screen_surface.get_flags() and pygame.FULLSCREEN:
					cfg.screen_surface = pygame.display.set_mode((1600,900))
				else:
					cfg.screen_surface = pygame.display.set_mode((1600,900), pygame.FULLSCREEN)

			elif event.type == MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
				if Solo.in_button(mouse):
					return game()
				elif Multi.in_button(mouse):
					return accueil()
				elif Return.in_button(mouse):
					return accueil()

		#---------------------------------------------------------------------------------------------------------
		# Affichage à l'écran des éléments
		cfg.screen_surface.fill(NOIR)
		cfg.screen_surface.blit(wallpaper, wallpaper.get_rect(center=(800, 450)))
		cfg.screen_surface.blit(title[0], title[1])

		# Affichage des boutons
		Solo.display(cfg.screen_surface, mouse)
		Multi.display(cfg.screen_surface, mouse)
		Return.display(cfg.screen_surface, mouse)

		pygame.display.flip()

def game():
	pass