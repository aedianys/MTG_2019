#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#####
#f : conservation d'informations sur l'objet quand il change de zone

class Game_object():
	"""Représente un objet de base dans le jeu. Classe parente des classes de carte, permanent, sort ou capacité sur la pile)."""
	
	caracs = ["name","manacost","color","supertype","type","subtype","text","power","thoughness","ccm"]
	
	def __init__(self,_id,bossgame,bossplayer,zone,pcaracs):
		"""Initialisation : définition du propriétaire de l'objet, de ses caractéristiques et de ses capacités."""
		
		# Définition de l'identifiant et des objets maîtres
		self._id = _id
		self.bossgame = bossgame
		self.owner = bossplayer
		
		# Emplacement actuel de l'objet dans une zone collective ou individuelle
		if zone in ("st","ex","bf"):
			self.zone = zone # emplacement actuel de la carte dans une zone commune
		else:
			self.zone = zone + str(self.owner.cardinal) # emplacement actuel de la carte dans une zone individuelle
		self.former_zone = self.zone
		
		# Détermination des caractéristiques et des capacités de l'objet
		self.pcaracs = pcaracs
		self.mcaracs = dict(self.pcaracs) # caractéristiques modifiées par les effets continus du jeu
		self.det_abis()
	
	#####
	
	def det_abis(self):
		"""Détermine les capacités de l'objet."""
		
		self.abis_text = {} # dictionnaire des textes anglais des capacités selon leur identifiant
		self.abis = {} # dictionnaire des capacités structurées selon leur identifiant
		abis_lines = fce.interpret_lines(self.pcaracs["text"]) # liste des textes des capacités en anglais
		
		cardinal_abis = 0
		for abi in abis_lines:
			cardinal_abis += 1
			abi_id = self._id + "-" + str(cardinal_abis)
			self.abis_text[abi_id] = abi
			self.abis[abi_id] = fce.interpret_abi(abi)
			
	#####
	
	def delete(self): #f
		"""Réalise les conséquences de la suppression de l'objet du jeu. Ne détruit pas la référence de l'objet dans <bossgame.objects>."""
		self.bossgame.active_objects.remove(self._id)
		self.bossgame.zones[self.zone].remove(self._id)
		self.former_zone = self.zone
		self.zone = None
		self.mcaracs = dict(self.pcaracs)

#####
"""Classes héritées de <Game_object>, décrivant des objets représentés par des cartes dans le jeu physique."""

class Card(Game_object):
	"""Représente une carte (objet dans les bibliothèques, les mains, les cimetières ou l'exil)."""
	
	def __init__(self,_id,bossgame,bossplayer,zone,pcaracs):
		"""Initialisation."""
		
		Game_object.__init__(self,_id,bossgame,bossplayer,zone,pcaracs)

class Spell(Game_object):
	"""Représente un sort (objet sur la pile, attendant d'être résolu)."""
	
	def __init__(self,_id,bossgame,bossplayer,controller,pcaracs):
		"""Initialisation : définition du contrôleur."""
		
		Game_object.__init__(self,_id,bossgame,bossplayer,"st",pcaracs)
		
		self.controller = controller
	
	def resolve(self): #f : vérifs des targets
		"""Résolution du sort : application des instructions de résolution (capacités de sort) et création éventuelle du permanent correspondant."""
#########################
		if fce.is_permanent(self.mcaracs["type"]): # sort de permanent : mise sur le champ de bataille
			#f : self.entering_modalities ! il y a une différence
			#f : self.choice_as_entering() # traitement des choix à faire par le joueur lors de l'arrivée sur le champ de bataille, et des informations sur les statuts et compteurs que doit avoir le permanent à son arrivée sur le champ de bataille
			
			for abi_id,abi in self.abis.items(): # modification des capacités déclenchées du jeu de façon à y inclure celles du futur permanent (exception aux procédures de changements de zone habituelles)
				if abi["type"] == "trigger":
					future_abi_id = str(int(abi_id.split(":")[0])+1) + ":" + abi_id.split(":")[1] # anticipation de l'identifiant du futur permanent
					self.bossgame.triggers.append(future_abi_id) # ajout direct aux capacités déclenchées du jeu
			
			self.bossgame.process({"action":"move zone","z1":"st","z2":"bf"+str(self.controller.cardinal),"object":self.cardinal})
		else: # sort non-permanent : réalisation des capacités de sort du sort
			if self.abis:
				#f :
				pass
###########################
class Permanent(Game_object):
	"""Représente un permanent (objet sur le champ de bataille)."""
	
	def __init__(self,_id,bossgame,bossplayer,controller,pcaracs):
		"""Initialisation : définition du contrôleur et des attributs physiques du permanent."""
		
		Game_object.__init__(self,_id,bossgame,bossplayer,"bf",pcaracs)
		
		self.controller = controller
		#f : caractéristiques acquises/changées en tant que sort à cause de CEs restent sur le permanent
		
		# Attributs "physiques" du permanent
		self.status = {"tap":"untapped","flip":"unflipped","face":"up","phase":"in"} # statuts du permanent
		self.counters = {"+1/+1":0,"-1/-1":0} # compteurs et marqueurs divers placés sur le permanent
		self.damages = [] # blessures infligés à la créature ; contiendra des tuples (nombre de blessures, source de ces blessures)
		
		# Rôles du permanent lors des phases de combat :
		self.attacking = [False,None] # cardinal ou identifiant de l'objet attaqué (un joueur ou un planeswalker)
		self.blocking = [False,None] # objet(s) bloqués (un ou plusieurs permanents de type créature)
		self.damage_assignment_order = None

#####
"""Classes héritées de Game_object, décrivant des objets n'étant pas représentés par des cartes dans le jeu physique."""

class Token(Game_object):
	"""Représente un jeton (objet sur le champ de bataille créé par un effet et non joué par le joueur). Est aussi considéré comme un permanent mais ne peut pas changer de zone."""
	
	def __init__(self,_id,bossgame,bossplayer,controller,pcaracs):
		"""Initialisation : définition du contrôleur et des attributs physiques du permanent."""
		
		Game_object.__init__(self,_id,bossgame,bossplayer,"bf",pcaracs)
		
		self.controller = controller
			
		# Attributs "physiques" du permanent jeton
		self.status = {"tap":"untapped","flip":"unflipped","face":"up","phase":"in"} # statuts du permanent
		self.counters = {"+1/+1":0,"-1/-1":0} # compteurs et marqueurs divers placés sur le permanent
		self.damages = [] # blessures infligés à la créature ; contiendra des tuples (nombre de blessures, source de ces blessures)
		
		# Rôles du permanent jeton lors des phases de combat :
		self.blocking = [False]
		self.attacking = [False]
		self.damage_assignment_order = None

class Stack_effect(Game_object):
	"""Représente un effet (issu d'une capacité activée ou déclenchée) sur la pile, attendant d'être résolu. Différent d'un sort car il n'a que des capacités de sort et ne pourra pas donner lieu à un objet de permanent."""
	
	def __init__(self,_id,bossgame,bossplayer,pcaracs,source):
		"""Initialisation différente des autres objets : définition de la source, du contrôleur et de la seule caractéristique du texte."""
		
		Game_object.__init__(self,_id,bossgame,bossplayer,"st",pcaracs)
		
		self.source = source # source de l'effet (nécessairement une carte)
		self.controller = self.source.controller # on admet que le contrôleur d'un effet est le contrôleur de sa source
		
	def resolve(self): #f : vérifs des targets
		"""Résolution de l'effet sur la pile : application des instructions de résolution (capacités de sort)."""
################################
		pass
################################

#####