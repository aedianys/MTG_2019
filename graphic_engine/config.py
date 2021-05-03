#!/usr/bin/python3
# -*- coding: Utf-8 -*-

import os
import sys
import pygame
import sqlite3
from string import *
from pygame.locals import *
import functions as fc
import classes as cls

def init():
	global mtg_little
	global mtg_small
	global mtg_medium
	global mtg_high
	global mtg_large
	mtg_little = pygame.font.Font(fc.path('fonts/beleren.ttf'), 12)
	mtg_small = pygame.font.Font(fc.path('fonts/beleren.ttf'), 20)
	mtg_medium = pygame.font.Font(fc.path('fonts/beleren.ttf'), 32)
	mtg_high = pygame.font.Font(fc.path('fonts/beleren.ttf'), 50)
	mtg_large = pygame.font.Font(fc.path('fonts/beleren.ttf'), 80)
	#Création de la fenêtre d'affichage du jeu
	global taille_fenetre
	global screen_surface
	taille_fenetre = (1366, 768)
	screen_surface = pygame.display.set_mode(taille_fenetre)#, pygame.FULLSCREEN)
	pygame.display.set_caption("Magic The Gathering")
	pygame.key.set_repeat(80,80)


def image_loading():
	#chargement des images de fond d'écran des menus
	global wallpapers
	wallpapers = []
	global nb_wallpaper
	nb_wallpaper = int(len(os.listdir(fc.path('images/accueil'))))
	for i in range(1, nb_wallpaper+1):
		wallpapers.append(pygame.image.load(fc.path('images/accueil/wallpaper{}.jpg'.format(str(i)))).convert())