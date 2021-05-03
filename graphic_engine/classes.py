#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
from pygame.locals import*
import functions as fc
import config as cfg
import menu

class Button():
	"""Objet correspondant aux boutons dans les menus graphiques."""
	def __init__(self, file_path, position,):
		"""Crée un objet 'bouton' à afficher dans un menu."""
		self.position = position
		self.file_path = file_path
		self.surface = pygame.image.load(fc.path(self.file_path + '.png')).convert_alpha()
		self.size = self.surface.get_size()
		self.rect = self.surface.get_rect(center=self.position)
		self.flag = False

	def display(self, screen_surface, mouse):
		"""Permet l'affichage d'une instance de la classe 'bouton' et, selon la position de la mouse, de souligner un bouton."""
		if not(self.flag):
			screen_surface.blit(self.surface, self.rect)
		self.flag = True

	def in_button(self, mouse):
		"""Permet de savoir si la mouse est positionnée sur un bouton"""
		if self.position[0] - int(self.size[0]/2) <mouse[0]< self.position[0] + int(self.size[0]/2) and self.position[1] - int(self.size[1]/2) <mouse[1]< self.position[1] + int(self.size[1]/2):
			return True
		else:
			return False

#---------------------------------------------------------------------------------------------------------

class TextButton(Button):
	"""Objet correspondant à un bouton avec du textet"""
	def __init__(self, file_path, position, message, font, color):
		Button.__init__(self, file_path, position)
		self.texte = fc.screen_print(font, message, color, center=position)
		self.font = font
		self.message = message
		self.color = color

	def display(self, screen_surface, mouse):
		Button.display(self, screen_surface, mouse)
		screen_surface.blit(self.texte[0], self.texte[1])


class HighlightButton(Button):
	"""Objet correspondant à un bouton avec un halo"""
	def __init__(self, file_path, position, highlight_path):
		Button.__init__(self, file_path, position)
		self.highlight = pygame.image.load(fc.path(highlight_path+'.png')).convert_alpha()
		self.highlight_rect = self.highlight.get_rect(center=position)

	def display(self, screen_surface, mouse):
		Button.display(self, screen_surface, mouse)
		if self.in_button(mouse):
			screen_surface.blit(self.highlight, self.highlight_rect)


class SwitchButton(Button):
	"""Objet correspondant à un interrupteur"""
	def __init__(self, file_path, position):
		Button.__init__(self, file_path, position)
		self.active = False

	def display(self, screen_surface, mouse):
		Button.display(self, screen_surface, mouse)

	def switch(self):
		self.active = not(self.active)

#---------------------------------------------------------------------------------------------------------

class ImageSwitchButton(SwitchButton):
	def __init__(self, file_path, position, active_path):
		SwitchButton.__init__(self, file_path, position)
		self.active_path = active_path

	def display(self, screen_surface, mouse):
		SwitchButton.display(self, screen_surface, mouse)

	def switch(self):
		SwitchButton.switch(self)
		if self.active:
			self.surface = pygame.image.load(fc.path(self.active_path + '.png')).convert_alpha()
		else:
			self.surface = pygame.image.load(fc.path(self.file_path + '.png')).convert_alpha()


class TextSwitchButton(TextButton, SwitchButton):
	def __init__(self, file_path, position, message1, message2, font, color):
		TextButton.__init__(self, file_path, position, message1, font, color)
		SwitchButton.__init__(self, file_path, position)
		self.message1 = message1
		self.message2 = message2

	def display(self, screen_surface, mouse):
		TextButton.display(self, screen_surface, mouse)
		SwitchButton.display(self, screen_surface, mouse)

	def switch(self):
		SwitchButton.switch(self)
		if self.active:
			self.message = self.message2
		else:
			self.message = self.message1
		self.texte = fc.screen_print(self.font, self.message, self.color, center=self.position)

#---------------------------------------------------------------------------------------------------------

class ArrowButton(HighlightButton):
	def __init__(self, file_path, position, highlight_path):
		HighlightButton.__init__(self, file_path, position, highlight_path)

	def display(self, screen_surface, mouse):
		HighlightButton.display(self, screen_surface, mouse)
		self.flag = False


class ManaSwitchButton(ImageSwitchButton):
	def __init__(self, file_path, position, active_path, name):
		ImageSwitchButton.__init__(self, file_path, position, active_path)
		self.name = name
		self.active = True
		self.surface = pygame.image.load(fc.path(self.active_path + '.png')).convert_alpha()

	def display(self, screen_surface, mouse):
		ImageSwitchButton.display(self, screen_surface, mouse)
		self.flag = False

	def switch(self):
		ImageSwitchButton.switch(self)


class RestrictionButton(TextSwitchButton):
	def __init__(self, file_path, position, message1, message2):
		TextSwitchButton.__init__(self, file_path, position, message1, message2, cfg.mtg_small, menu.NOIR)
		self.value = 'OR'

	def display(self, screen_surface, mouse):
		TextSwitchButton.display(self, screen_surface, mouse)
		self.flag = False

	def switch(self):
		TextSwitchButton.switch(self)
		self.value = {'ET':'AND', 'OU':'OR'}[self.message]


class MenuButton(TextButton, HighlightButton):
	"""Objet correspondant à un bouton de menu"""
	def __init__(self, file_path, position, message):
		TextButton.__init__(self, file_path, position, message, cfg.mtg_medium, menu.NOIR)
		HighlightButton.__init__(self, file_path, position, file_path+'_highlight')

	def display(self, screen_surface, mouse):
		TextButton.display(self, screen_surface, mouse)
		HighlightButton.display(self, screen_surface, mouse)
		self.flag = False


class DeckButton(TextButton, HighlightButton, ImageSwitchButton):
	"""Objet correspondant à un deck dans la liste du gestionnaire"""
	def __init__(self, file_path, position, name, message):
		TextButton.__init__(self, file_path, position, message, cfg.mtg_medium, menu.NOIR)
		HighlightButton.__init__(self, file_path, position, file_path+'_highlight')
		ImageSwitchButton.__init__(self, file_path, position, file_path+'_active')
		self.name = name

	def display(self, screen_surface, mouse):
		ImageSwitchButton.display(self, screen_surface, mouse)
		TextButton.display(self, screen_surface, mouse)
		HighlightButton.display(self, screen_surface, mouse)
		self.flag = False

	def switch(self):
		ImageSwitchButton.switch(self)


class CardCatalogButton(HighlightButton):
	"""Objet correspondant à une carte du catalogue du gestionnaire"""
	def __init__(self, file_path, position, cardid):
		HighlightButton.__init__(self, file_path, position, 'images/UI/gestionnaire/card_highlight')
		self.cardid = cardid

	def display(self, screen_surface, mouse):
		HighlightButton.display(self, screen_surface, mouse)
		self.flag = False


class CardListButton(TextButton, HighlightButton):
	"""Objet correspondant à une carte dans la liste du gestionnaire"""
	def __init__(self, file_path, position, message, cardid, nb):
		TextButton.__init__(self, file_path, position, message, cfg.mtg_little, menu.NOIR)
		HighlightButton.__init__(self, file_path, position, file_path+'_highlight')
		self.cardid = cardid
		self.nb = nb

	def display(self, screen_surface, mouse):
		self.texte = fc.screen_print(self.font, str(self.nb)+' '+self.message, self.color, midleft=(self.position[0]-int(self.size[0]/2)+10, self.position[1]))
		TextButton.display(self, screen_surface, mouse)
		HighlightButton.display(self, screen_surface, mouse)
		self.flag = False

	def illustration_display(self, screen_surface, mouse):
		if self.in_button(mouse):
			self.illustration = menu.illustrations[self.cardid]
			self.illustration = pygame.transform.scale(self.illustration,(212,296))
			self.illustration_rect = self.illustration.get_rect(topright=mouse)
			screen_surface.blit(self.illustration, self.illustration_rect)