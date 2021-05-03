#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

#####

class Player():
	"""Représente et fait agir l'un des joueurs de la partie"""
	
	def __init__(self,bossgame,name,name_deck,cardinal):
		"""Initialisation : création du deck de cartes."""
		
		self.bossgame = bossgame
		self.name = name # "A" ou "B"
		self.cardinal = cardinal
		self.opponent_cardinal = abs(cardinal-1)
		
		# Zones de jeu individuelles sous la forme de dictionnaires, contenant les objets du jeu (avec leur identifiant pour clé) ;
		# "lb" correspond à la bibliothèque "library", "bf" au champ de bataille "battlefield", "gy" correspond au cimetière "graveyard", "hd" à la main "hand"
		self.zones = {"lb":[],"gy":[],"hd":[]}
		
		# Instanciation des cartes du joueur (son deck)
		cards_owned = fcd.decklist_load(name_deck) # liste contenant les noms anglais uniformisés des cartes du deck du joueur
		conn = sqlite3.connect("../cards/cards.db")
		for card_name,nb_card in cards_owned.items():
			for i in range(nb_card):
				self.bossgame.cardinal_objects += 1
				self.bossgame.cardinal_basic_objects += 1 # un nouvel objet fondamental sera effectivement créé
				_id = str(self.bossgame.cardinal_objects)+":1" # identifiant de la carte instanciée
				
				card_caracs = fcd.card_caracs(card_name,conn)
				self.bossgame.objects[_id] = obs.Card(_id,self.bossgame,self,"lb",card_caracs)
				self.bossgame.active_objects.append(_id)
				self.zones["lb"].append(_id) # ajout à la bibliothèque du joueur
		
		# Conditions de défaite du joueur
		self.life_total = 20 # si ce total atteint 0
		self.poison_total = 0 # si ce total atteint 10
		self.empty_draw = False # si le joueur a tenté de piocher une carte alors que sa bibliothèque était vide
		
		self.mana_pool = {"B":[], "C":[], "R":[], "U":[], "W":[], "G":[]} # réserve de mana ; les listes de manas de chaque couleur contiennent des tuples (nombre de manas, source de ce mana)
		self.nb_landed = 0 # nombre de terrains posés depuis la main durant le tour
	
    ##### DÉCISIONS DU JOUEUR
    
	def take_action_prio(self,actions): #f : les special actions
		"""Propose au joueur de réaliser une action proposée par le jeu lorsqu'il a la priorité (sans tenir compte du coût de l'action ni des effets du jeu) ; ces actions étant cast ou land ou active ou active mana ou special."""
		
		legal_decision = False # booléen indiquant si la dernière décision prise était légale
		
		# Boucle jusqu'à ce que le joueur prenne une décision légale
		while not(legal_decision):
			action = self.choice("You may take one of the following actions.","Answer by an action keyword and the id of the object or ability which you want to process.",actions).split(" ")
			
			if action[0] == "special": # (cas non-traité actuellement)
				self.bossgame.perform_special_action(self.cardinal,action)
				legal_decision = True
			elif action[0] in ["cast","land"]:
				legal_decision = self.bossgame.process_decision({"type":action[0],"card in hand":action[1]})
			elif action[0] in ["active","active mana"]:
				legal_decision = self.bossgame.process_decision({"type":action[0],"activated abi":action[1]})
			elif action[0] == "pass":
				legal_decision = True
			else:
				self.ext_com("Your answer could not be identified.")
			
			if not(legal_decision):
				self.ext_com("Your decision is illegal.")
		
		return action[0] # retour à l'intention de <Game.stack_cycle>
	
	
	def declare(self,attack_or_block):
		"""Demande au joueur de déclarer ses attaquants ou bloqueurs. Méthode appelée lors de la phase de combat."""
		
		aob = attack_or_block.split(" ")[1] # chaîne de caractère indicative déterminant s'il s'agit de déclarer les bloqueurs ou les attaquants (sinon c'est exactement la même procédure)
		legal_decision = False # booléen indiquant si la dernière décision prise était légale
		
		# Boucle jusqu'à ce que le joueur prenne une décision légale
		while not(legal_decision):
			potential_ab = self.bossgame.find_objects(zone="bf",controller=self,caracs_crits={"types":"creature"},status_crits={"tap":"untapped"}) # liste indicative des créatures pouvant attaquer ou bloquer
			ab = self.choice("You have to declare {0} creatures among these ones.".format(aob),"Answer by the ids of the creatures you want to have {0}, separated by commas.".format(aob),potential_ab).split(",")
			
			able_ab = True
			for ab_id in ab: # cérification du fait que tous les attaquants/bloqueurs sont bien dégagés
				if self.bossgame.objects[ab_id].status["tap"] != "untapped":
					able_ab = False
			
			if able_ab:
				legal_decision = self.bossgame.process_decision({"type":attack_or_block,"objects":ab})
			else:
				legal_decision = False
			
			if not(legal_decision):
				self.ext_com("Your decision is illegal or the creatures you identified are not able to be {0}.".format(aob))
	
	def untap(self): # attention : concerne seulement la décision de dégagement lors de l'étape de dégagement ; les effets de "untap" n'appellent pas cette méthode
		"""Demande au joueur lesquels de ses permanents il veut dégager. Méthode appelée lors de l'étape de dégagement du joueur."""
		
		legal_decision = False # booléen indiquant si la dernière décision prise était légale
		
		# Boucle jusqu'à ce que le joueur prenne une décision légale
		while not(legal_decision):
			potential_untap = self.bossgame.find_objects(zone="bf",status_crits={"tap":"tapped"}) # liste indicative des créatures à dégager
			untap = self.choice("You have to declare the permanents you want to untap among these ones.","Answer by the ids of the permanents you want to untap, separated by commas.",potential_untap).split(",")
			
			able_untap = True
			for to_untap_id in untap: # vérification du fait que tous les permanents à dégager sont bien dégagés
				if self.bossgame.objects[to_untap_id].status["tap"] != "tapped":
					able_untap = False
			
			if able_untap:
				legal_decision = self.bossgame.process_decision({"type":"untap","objects":untap})
			else:
				legal_decision = False
			
			if not(legal_decision):
				self.ext_com("Your decision is illegal or the permanents you identified are already untapped.")
	
	def target(self,nb_targets,conditions): #f : possibilité de cibler ("up to n targets") et obligation de cibler ("n targets")
		"""Demande au joueur quels objets du jeu il souhaite cibler. Méthode appelée lors du lancer de sorts ciblants ou de la mise sur la pile d'effet de pile ciblants."""
		
		legal_decision = False # booléen indiquant si la dernière décision prise était légale
		
		# Boucle jusqu'à ce que le joueur prenne une décision légale
		while not(legal_decision):
			targets = self.choice("You have to declare the {0} objects you want to target, with the conditions of the ability.","Answer by the ids of the objects you want to untap, separated by commas.").split(",")
			
			able_targets = True
			meets_conditions = True
			for target_id in targets: # vérification du fait que tous les permanents à dégager sont bien dégagés
				target = self.bossgame.objects[target_id]
				
				exec(conditions) # conditions["perm"] est une chaîne de caractère exécutable constituée d'un bloc de condition "if", qui réaffectera <meets_conditions> à False si l'objet <target> ne remplit pas les conditions, à l'aide de <fce.obj_corresp>
				target_nature = conditions["target nature"] # chaîne de caractère indiquant quelle doit être la nature de la cible : un joueur ou un objet de jeu (instance de <Game_objects>)
				if not(isinstance(target,{"player":obs.Player,"game object":obs.Game_object}[target_nature])):
					meets_conditions = False
				
				if not(meets_conditions):
					able_targets = False
			
			if able_targets and len(targets)==nb_targets:
				legal_decision = self.bossgame.process_decision({"type":"target","objects":targets})
			else:
				legal_decision = False
			
			if not(legal_decision):
				self.ext_com("Your decision is illegal or the objects you identified are not meeting the conditions.")
	
	def able_to_pay(self,cost):
		"""Indique si le joueur est capable de payer le coût donner au vu des ses ressources."""
		
		#f
		return True
	
	##### MÉTHODES FINALES (e rappelant pas elles-mêmes <process_effect>)
	
	def draw(self):
		"""Pioche d'une carte (depuis la bibliothèque dans la main)."""
		
		if len(self.zone["lb"]) != 0: # vérification de la présence d'au moins une carte dans la bibliothèque
			self.bossgame.move_zone(self.zones["lb"][-1],"hd"+str(self.cardinal))
		else: # la tentative de piocher une carte dans une bibliothèque vide est une condition de défaite
			self.empty_draw = True
			self.ext_com("You attempted to draw a card from empty library.")
	
	def discard(self,card_id):
		"""Défausse d'une carte (depuis la main dans le cimetiére)."""
		
		self.bossgame.move_zone(card_id,"gy"+str(self.cardinal))
		
	def gain_mana(self, source, colors):
		"""Ajout de manas à la réserve de mana"""
		for color in colors:
			self.mana_pool[color].append(source)
		
	def lose_mana(self, source, color):
		"""Supression d'un mana de la réserve de mana"""
		self.mana_pool[color].remove(source)
	
	def shuffle_lib(self):
		"""Mélange de la bibliothèque."""
		rd.shuffle(self.zones["lb"])
	
	def clearmana(self):
		pass
	
	def handsize(self):
		pass
	
	#f
	
	##### MÉTHODES INTERMÉDIAIRES (rappelant elles-mêmes <process_effect>)
	
	def has_to_discard(self,n,mod):
		"""Choix des cartes à défausser.."""
		
		for i in range(n):
			if len(self.zone["hd"]) != 0:
				if mod == "random": # défausse aléatoire
					to_discard_id = rd.choice(self.zones["lb"])
				else: # défausse choisie
					to_discard_id = self.choice("You have to discard one card from your hand.","Answer by the id of the card you want to discard.",self.zones["hd"])
				self.bossgame.process([{"effect":"discard","object":to_discard_id,"player":self.cardinal}])

	def pay_mana(self, manas):
		"""Paiement d'un coût de mana"""
		for source, color in manas:
			self.lose_mana(self, source, color)
	
	def pay_cost(self, life, colors, mod="auto"):
		"""Paiement d'un coût (sort ou capacité)"""
		self.pay_life(self, life)
		if mod == 'choice':
			for color in colors:
				source = self.choice("You have to choose the mana you want to spend", "Answer by the source of the mana you want to spend", self.mana_pool[color])
				self.pay_mana(self, (source, color))
		elif mod == "auto":
			for color in colors:
				self.pay_mana(self, (self.mana_pool[color][-1], color))
		
	def search_lib(self,cond,n):
		"""Permet au joueur de chercher dans sa bibliothèque <n> cartes remplissant les conditions <cond>."""
		
		#f
		pass
	
	#f
	
	##### MÉTHODES DE COMMUNICATION
	
	def observe(self,config="debug"): # <config> : donne accès à toutes les zones (même privées) si égal à "debug"
		"""Permet au joueur de se renseigner sur l'état du jeu par commandes."""
		
		print("Game observation for player {0}.".format(self.name))
		cmd = None
		
		while cmd != "end observe": # boucle permettant à l'utilisateur de rentrer des commandes pour se renseigner sur l'état du jeu, ou entrer son choix
			print("Type your command to have information on the game or 'end observe' to end.")				
			cmd = input()
			
			if config == "debug":
				if ":" in cmd: 
					print(self.bossgame.objects[cmd])
				elif cmd == "log":
					print(self.bossgame.log)
				else: 
					print(self.bossgame.zones[cmd])
			else:
				if "st" in cmd or "ex" in cmd or "bf" in cmd or "gy" in cmd:
					print(self.bossgame.zones[cmd])
				if "hd" in cmd:
					print(self.zones["hd"])
				#f : autres commandes
	
	def choice(self,description,answer,options=None): # <options> : dictionnaire des objets concernés parmi lesquels le joueur doit faire un choix d'action
		"""Méthode par laquelle passent tous les choix du joueur.Le dictionnaire <options> est un dictionnaire descriptif destiné à être affiché pour le joueur."""
				
		print("Player {0}-{1} :".format(self.name,self.cardinal))
		print(description)
		print(answer)
		if options:
			print("You have choice between :",options)
		else:
			print("You can observe the game to find the potential choices.")
			self.observe()
		ans = input("Votre choix : ")
		return ans
	
	def ext_com(self,com):
		"""Affiche un message du jeu."""
		
		print("Player {0}-{1} :".format(self.name,self.cardinal))
		print(com)
		
		self.observe()

#####