#!/usr/bin/python3
# -*- coding: Utf-8 -*-

import os
import sys
import pygame
import sqlite3
import config as cfg
from string import *
from pygame.locals import *
import functions as fc
import classes as cls
import menu

BLANC = (255, 255, 255)

def main():
	# Initialisation de pygame
	pygame.init()
	#---------------------------------------------------------------------------------------------------------
	# Chargement et affichage de l'écran de chargement
	cfg.init()
	charge_screen = pygame.image.load(fc.path('images/loading/wallpaper.jpg')).convert()
	Welcome = fc.screen_print(cfg.mtg_large, 'Magic The Gathering', BLANC, center = (800, 300))
	Charging = fc.screen_print(cfg.mtg_medium, 'Veuillez patienter, chargement des images...', BLANC, center = (800, 500))
	cfg.screen_surface.blit(charge_screen, charge_screen.get_rect(center=(800,450)))
	cfg.screen_surface.blit(Welcome[0], Welcome[1])
	cfg.screen_surface.blit(Charging[0], Charging[1])
	pygame.display.flip()
	#---------------------------------------------------------------------------------------------------------
	# Chargement des images de fond de l'accueil
	cfg.image_loading()
	# Affichage de l'écran d'accueil
	menu.accueil()
	#---------------------------------------------------------------------------------------------------------
	# Fermeture des modules utilisés
	pygame.quit()
	sys.exit(0)

if __name__ == '__main__':
	main()