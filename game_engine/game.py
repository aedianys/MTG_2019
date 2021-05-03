#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random as rd
import functions_engine as fce
import functions_data as fcd
import objects as obs
from player import Player

#####

class Game():
	"""Classe principale, représentant une partie entre deux joueurs "A" et "B"."""
	
	# Attributs de classe : constantes des couleurs, zones et types du jeu
	colors = ("w","u","b","r","g")
	mana_types = colors + tuple("c") # "c" est le type "colorless", qui n'est pas une couleur
	zone_names = ("lb","bf","gy","hd","st","ex")
	subtypes = fcd.subtypes() # appel à <subtypes>, qui renverra un tuple contenant les très nombreux sous-types 
	types = ("creature","enchantment","artifact","land","instant","sorcery","planeswalker")
	supertypes = ("legendary","basic","tribal")
	
	# Dictionnaires suivis par le jeu pour effectuer les tours et les actions
	turn_structure = {"beginning phase":["untap step",	"upkeep step","draw step"],
						"precombat main phase":["main step"],
						"combat phase":["beginning of combat step","declare attackers step","declare blockers step","damage step","end of combat step"],
						"postcombat main phase":["main step"],
						"ending phase":["end step","cleanup step"]}
	
	TBAs = {"untap step":"self.players[0].nb_landed=0,self.players[1].nb_landed=0,self.active.untap()",
		"upkeep step":"self.stack_cycle('game')",
		"draw step":"self.process_effect({'effect':'draw','player':self.active.cardinal}),self.stack_cycle('game')",
		"main step":"self.stack_cycle('game')",
		"beginning of combat step":"self.stack_cycle('game')",
		"declare attackers step":"self.active.declare('declare attackers');self.stack_cycle('game')",
		"declare blockers step":"self.active.declar('declare attackers');self.dam();self.stack_cycle('game')",
		"damage step":"self.damages();self.stack_cycle('game')",
		"end of combat step":"self.stack_cycle('game')",
		"end step":"self.stack_cycle('game')",
		"cleanup step":"self.active.handsize();self.clean_damages();self.SBAs()"} #f : process(draw)
	
	final_effects = {"draw":"self.players[gf['player']].draw()",
			"gain mana":"self.players[gf['player']].mana_pool.append(gf['mana description'])",
			"lose mana":"self.players[gf['player']].lose_mana(gf['mana type'])",
			"gain life":"self.players[gf['player']].life_total+=gf['number']",
			"lose life":"self.players[gf['player']].life_total-=gf['number']",
			"":""} # dictionnaire associant, à chaque Fait de jeu final potentiel dans MTG, l'exécutable de ce Fait de jeu ; #f
	
	inter_effects = {}  # dictionnaire associant, à chaque Fait de jeu intermédiaire potentiel dans MTG, l'exécutable de ce Fait de jeu ; #f
		
	def __init__(self,decks,boss,starting_player): # <decks> : dictionnaire contenant les noms des fichiers de configuration des decks des joueurs, avec les lettres "A" ou "B" pour clé
		"""Initialisation : création des zones, des joueurs et des données globales."""
		
		self.boss = boss # référence à l'objet maître de la classe <Game_manager> ; servira uniquement lors de la fin de la partie
		
		# Tableaux les plus importants du jeu
		self.log = [] # liste de tout ce qui s'est déroulé durant l'exécution de la partie, servant au débug
		self.history = [] # liste de tous les faits de jeu passés, servant aux effets de certaines cartes
		
		self.objects = {} # dictionnaire contenant les objets créés durant le jeu, avec leur identifiant pour clé ; conserve aussi les objets n'existant plus dans le jeu (référencés dans aucune zone du jeu)
		self.active_objects = [] # liste des identifiants des objets créés durant le jeu et existant encore dans le jeu (référencés dans aucune zone du jeu)
		self.cardinal_objects = 0 # nombre d'objets (en comptant les dérivations) créés durant le jeu
		self.cardinal_basic_objects = 0 # nombre d'objets (sans compter les dérivations) créés durant le jeu
		
		self.players = [] # liste contenant les deux joueurs et représentant aussi l'ordre du tour
		
		self.pending_gfs = [] # liste des Faits de jeu appliqués en cours de réalisation, qui doivent être enregistrés tous ensemble en tant qu'évènements
		self.recurr_gfs = 0 # compteur de récurrence pour la méthode <process_effect>
		
		self.combat_roles = {"attacking":None,"blocking":None}
		self.attackers_repartition = None
		self.blockers_repartition = None
		self.declared_combat = False
		
		# Détermination de l'ordre du tour et création de la liste des joueurs dans cet ordre
		self.player_order = ["A","B"]
		if starting_player == "B": 
			self.payer_order.reverse()
		for i in (0,1): # instanciation des joueurs et affichage de la correspondance pour les joueurs
			self.players.append(Player(self,self.player_order[i],decks[self.player_order[i]],i)) # ajout à la liste des joueurs
			self.players[i].ext_com("You are player {0}.".format(self.player_order[i])) # communication de la correspondance aux joueurs eux_mêmes
				
		# Zones de jeu sous forme de listes des identifiants des objets qu'elles contiennent ;
		# zones collectives : "st" correspond à la pile "stack" et "ex" à l'exil "exile" ;
		# zones individuelles : reprises dans les instances de <Player> ;
		# zone non-officielle : "wt" correspond à l'emplacement "waiting triggers"
		self.zones = {"st":[],"ex":[],"bf":[],"wt":[],
				"lb0":self.players[0].zones["lb"],
				"gy0":self.players[0].zones["gy"],
				"hd0":self.players[0].zones["hd"],
				"lb1":self.players[1].zones["lb"],
				"gy1":self.players[1].zones["gy"],
				"hd1":self.players[1].zones["hd"]}
		
		# Effets du jeu (créés par les permanents sur le champ de bataille principalement)
		self.triggers = [] # liste contenant les identifiants des capacités déclenchées du jeu
		self.CEs_caracs = [] # liste des modifications de caractéristiques à appliquer aux caractéristiques des objets du jeu 
		self.CEs_rules = [] # liste des mdifications à apporter aux variables de règles
		self.CEs_process_decision = {"costs":[],
			  "constraint":[],
			  "allow":[],
			  "restraint":[],
			  "cost restraint":[],} # dictionnaire contenant les listes des effets continus intervenant dans la réalisation d'une décision d'un joueur
		self.CEs_process_effect = {"prevent":[],
			  "replace":[],
			  "cannot":[]} # dictionnaire contenant les listes des effets continus intervenant dans la réalisation d'un effet ponctuel
		#f : mettre les CEs de base en qqlle sorte : pas de rituel en tour adverse ; pas de pioche au premier tour par ex
		
		self.mainloop() # lancement de la partie
	
	##### MÉTHODES PRINCIPALES
	
	def mainloop(self):
		"""Démarre le jeu et effectue les tours de jeu indéfiniment."""
		
		# Démarrage : pioche d'une main de 7 cartes et mulligans éventuelles
		for p in self.players:
			p.draw(7) # pioche directe sans passer par <process_effect> car aucun effet continu n'existe en début de partie
			p.mulligan()
                 
		self.n_turns = 0 # nombre de tours depuis le début de la partie
        
		# Boucle des tours
		while 1:
			self.n_turns += 1
			
			# Définition du joueur actif et de l'ordre de priorité "Active Player Nonactive Player" ou "APNAP" selon le tour, par l'indice des joueurs dans la liste <self.players>
			if self.n_turns%2 == 0:
				self.APNAP = [1,0]
			else:
				self.APNAP = [0,1]
			self.active = self.players[self.APNAP[0]]
			self.passive = self.players[self.APNAP[0]]
			
			# Exécution des différentes étapes du tour par parcours du dictionnaire <turn_structure>
			for self.phase,self.phase_content in self.turn_structure.items():
				for self.step,self.step_content in self.phase_content.items():
					for TBA in self.step_content.split(";"):
						exec(TBA)
	
	def endgame(self,winner):
		"""Termine la partie par l'intermédiaire de l'objet maître <Game_manager>."""
		
		if winner=="=": # égalité : les deux joueurs perdent en même temps
			self.boss.end_and_new("=")
		else: # un joueur gagne
			self.boss.end_and_new(self.player_order[winner])
	
	##### MÉTHODES DE LA PILE
	
	def stack_cycle(self,init): # <init> : décrit ce qui a initié le nouveau tour de priorité (le jeu ou une action d'un joueur)
		"""Fait tourner la priorité et s'arrête lorsque la pile est vide et que tous passent. En agissant lorsqu'ils ont la priorité, les joueurs peuvent initier de nouveaux cycles de priorité avec alors comme <init> leur cardinal."""
		
		# Détermination du premier joueur à obtenir la priorité selon ce qui a initié le nouveau tour de priorité
		if init == 'game': # s'il s'agit d'un tour de priorité initié par les TBAs
			prio_player = self.APNAP[0]
		else: # s'il s'agit d'un tour de priorité initié par une action d'un joueur
			prio_player = init
		decision = ""
		former_decision = ""
		
		# Passage de la priorité
		self.boucle_SBAs()
		decision = self.players[prio_player].take_action(self.det_actions(prio_player))
		while not(former_decision=="pass" and decision=="pass"):
			# Vérifications obligatoires avant toute prise de priorité par un joueur
			self.boucle_SBAs()
			
			if decision=="cast" or decision=="active":
				self.stack_cycle(prio_player)
				prio_player = abs(prio_player-1)
			elif decision=="pass":
				prio_player = abs(prio_player-1)
			
			former_decision = decision
			decision = self.players[prio_player].take_action(self.det_actions(prio_player))
			
		# Une fois que tous les joueurs ont passés successivement, résolution du dernier objet placé sur la pile le cas échéant
		if len(self.zones["st"]) != 0:
			self.zones["st"][-1].resolve()
	
	def boucle_SBAs(self):
		"""Vérifie les SBAs et met les capacités déclecnchées en attente sur la pile, jusqu'à ce qu'il n'y ait plus de SBAs exécutées."""
		
		self.SBAs_executed = False
		self.SBAs() # application des actions basées sur un état
		while self.SBAs_executed==True or len(self.zones["wt"])>=1:
			self.no_SBAs_executed = False
			self.triggers_on_stack() # mise des capacités déclenchées sur la pile
			self.SBAs() # application des actions basées sur un état
	
	def SBAs(self):
		"""Vérifie les éventuelles actions basées sur un état, et les applique le cas échéant."""
		
		all_SBAs = []
		
		# Parcours des objets dans les différentes zones du jeu
		for zone in self.zones.keys():
			for obj_id in self.zones[zone]:
				obj = self.objects[obj_id]
				
				if zone=="bf":
					if "creature" in obj.pcaracs["types"]:
						if obj.pcaracs["thoughness"] <= 0: # mort si endurance inférieure à 0
							all_SBAs.append({"effect":"move zone","object":obj_id,"z0":"bf","z1":"gy"+str(obj.owner.cardinal)})
						if obj.count_damages() >= obj.pcaracs["thoughness"]: # destruction si le nombre de blessures sur l'objet est supérieur à l'endurance
							all_SBAs.append({"effect":"destroy","object":obj_id,"cause":"damage"})
							#f : contact mortel
					if "planeswalker" in obj.mcaracs["type"]:
						if obj.caracs["loyalty"] <= 0:
							all_SBAs.append({"effect":"destroy","object":obj_id,"cause":"loyalty"})
					if "legendary" in obj.mcaracs["supertype"]:
						if len(self.find_objects(self,"bf",caracs_crits={"name":obj.pcaracs["name"],"supertype":"legendary"}))>=2:
							all_SBAs.append({"effect":"destroy","object":obj_id,"cause":"legend rule"})
					if obj.counters["+1/+1"] >= 1 and obj.counters["-1/-1"] >= 1: # les marqueurs +1/+1 et -1/-1 s'annulent, sans passer par <process_effect>
						nb_counters_to_remove = abs(obj.counters["+1/+1"] - obj.counters["-1/-1"])
						obj.counters["-1/-1"] -= nb_counters_to_remove
						obj.counters["+1/+1"] -= nb_counters_to_remove
		
		# Parcours des joueurs
		for p in self.players:
			if p.life_total <= 0:
				all_SBAs.append({"effect":"defeat","player":p.cardinal,"cause":"life"})
			if p.poison_total >= 10:
				all_SBAs.append({"effect":"defeat","player":p.cardinal,"cause":"poison"})
			if p.empty_draw:
				p.empty_draw = False
				all_SBAs.append({"effect":"defeat","player":p.cardinal,"cause":"empty draw"})
		
		if all_SBAs:
			self.process_effect(all_SBAs)
			self.SBAs_executed = True # information nécessaire dans la méthode <stack_cycle>, qui appelle <SBAs>
		
		# Gestion de l'exception de la fin de tour : 
		if self.step=="cleanup step" and self.SBAs_executed:
			self.stack_cycle("game") # cycle de priorité en étape de nettoyage seulement si des SBAs y ont été effectuées
	
	def triggers_on_stack(self):
		"""Déverse les capacités déclenchées jusqu'ici en attente dans l'emplacement <self.zones["wt"]> sur la pile. Ceci ne correspond pas à un changement de zone (et donc pas à la création d'un nouvel objet <Effect_object>)."""
		
		# Tri selon leur contrôleur, des capacités déclenchées en attente
		pts = [[],[]] # listes des identifiants des capacités déclenchées en attente selon le joueur les contrôlant
		for trigger_id in self.zones["wt"]:
			trigger = self.objects[trigger_id]
			pts[trigger.controller.cardinal].append(trigger_id)
		
		# Tri par les joueurs des capacités déclenchées qu'ils contrôlent, pour être mises selon l'ordre voulu sur la pile
		ordered_pts = [[],[]] # listes des identifiants des capacités déclenchées en attente selon le joueur les contrôlant et triées par le joueur les contrôlant
		for p in (0,1):
			n = len(pts[p])
			if n>1:
				com_str = ""
				for pt_id in pts[p]: # construction de la chaîne de caractère d'informations
					com_str = com_str + " " + pt_id
				self.players[p].ext_com("You have to order on the stack the {0} triggers you control :".format(n)+com_str)
				ordered_pts[p] = [None]*n
				for pt_id in pts[p]: # ordonnement des capacités déclenchées
					rank = self.players[p].choice("You have to give the rank of triggered ability {0}.".format(pt_id),"Answer by the rank number.",list(i for i in range(n)))
					ordered_pts[p][rank] = pt_id
		
		# Ajout effectif à la pile et retrait de l'emplacement des capacités déclenchées en attente
		self.zones["st"] += ordered_pts[self.passive.cardinal]
		self.zones["st"] += ordered_pts(self.active.cardinal)
		self.zones["wt"] = []

	##### MÉTHODES TRAITANT LES DÉCISIONS
	
	def process_decision(self,decision,player):
		"""Traite les décisions prises par des joueurs, demandant éventuellement le paiement d'un coût : cast (lancement d'un sort), land (mise sur le champ de bataille d'un terrain), active (activation d'une capacité activée), active mana (activation d'une capacité activée de mana), lors des cycles de priorité / attackers (choix des attaquants), blockers (choix des bloqueurs), lors de la phase de combat / target (choix des cibles), lors du lancement d'un sort notamment."""
		
		self.log.append((self.n_turns,self.phase,self.step,self.cardinal_objects,decision))
		event = self.register_decision(decision,player)
		
		if decision["type"] == "cast":
			# Création d'un nouvel objet de Sort sur la pile
			spell_id = self.move_zone(decision["objects"],"st",player)
			spell = self.objects[spell_id]
			
			# Détermination des coûts, qui font partie de la décision car un sort peut être modal
			internal_cost = spell.modal() # choix de modalités faits au moment du lancer du sort, qui déterminent le coût du lancer du sort en lui même
			spell.targetting() # choix des cibles, qui appelera lui-même un <process_decision>
			locked_cost = fce.add_costs(internal_cost,self.det_decision_cost(decision,player,spell_id))
			
			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player,spell_id) and player.able_to_pay(locked_cost):
				self.perform_decision(locked_cost,event,player)
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeau avant la décision
				self.restore_previous_state(decision_type="cast",decision_object=decision["card in hand"],decision_creation=spell_id)
				return "illegal"
			
		elif decision["type"] == "land":
			# Création d'un nouvel objet de permanent terrain sur le champ de bataille
			land_id = self.move_zone(decision["objects"],"bf",player)
			land = self.objects[land_id]
			
			# Détermination des coûts, qui font partie de la décision car un terrain peut être modal
			internal_cost = land.modal() # choix de modalités faits au moment du lancer du sort, qui déterminent le coût du lancer du sort en lui même
			locked_cost = fce.add_costs(internal_cost,self.det_decision_cost(decision,player,land_id))
			
			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player,land_id) and player.able_to_pay(locked_cost):
				self.perform_decision(locked_cost,event,player)
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeu avant la décision
				self.restore_previous_state(decision_type="land",decision_object=decision["card in hand"],decision_creation=land_id)
				return "illegal"
			
		elif decision["type"] == "active":
			# Création d'un nouvel objet d'effet de pile sur la pile
			se_id = self.new_stack_effect(decision["activated abi"])
			se = self.objects[se_id]
			
			# Détermination des coûts, qui font partie de la décision car une capacité activée peut être modale
			internal_cost = se.modal() # choix de modalités faits au moment du lancer du sort, qui déterminent le coût du lancer du sort en lui même
			se.targetting() # choix des cibles, qui appelera lui-même un <process_decision>
			locked_cost = fce.add_costs(internal_cost,self.det_decision_cost(decision,player,se_id))
			
			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player,se_id) and player.able_to_pay(locked_cost):
				self.perform_decision(locked_cost,event,player)
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeu avant la décision
				self.restore_previous_state(decision_type="active",decision_object=decision["activated abi"],decision_creation=se_id)
				return "illegal"

		elif decision["type"] == "active mana":
			# Création directe (et sans référencement dans <game_objects>) d'un effet de pile que l'on ne place pas sur la pile
			perm_on = self.objects[decision["activated abi"].split("-")[0]]
			mse = obs.Stack_effect("0:0",self,player,{"text":perm_on.abis[decision["activated abi"]]["effect"]},perm_on._id)
			mse.modal()
			mse.targetting()

			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player,mse):
				mse.resolve()
				self.verify_triggers(event)
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeu avant la décision
				del mse
				return "illegal"

		elif decision["type"] == "declare attackers":
			# Engagement et détermination du joueur ou planeswalker attaqué
			repartition = {}
			tapping = []
			for attacker_id in decision["objects"]:
				attack_options = ["player {0}".format(player.opponent)] + self.find_objects(zone="bf",controller=self.players[player.opponent],caracs_crits={"type":"planeswalker"})
				attacked = player.choice("You have to choose which player or opponent the creature {0} attacks.".format(attacker_id),"Answer by giving the relevant player cardinal or planeswalker id.",attack_options)
				repartition[attacker_id] = attacked
				tapping.append({"effect":"tap","object":attacker_id})
			self.process_effect(tapping)
			
			# Détermination du coût total de l'attaque
			locked_cost = self.det_decision_cost(decision,player,repartition)

			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player,repartition) and player.able_to_pay(locked_cost):
				self.perform_decision(locked_cost,event,player)
				for attacker_id in decision["objects"]:
					self.objects[attacker_id].attacking = [True,repartition[attacker_id]]
				self.attackers_repartition = repartition
				self.combat_ongoing()
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeu avant la décision
				for attacker_id in decision["objects"]:
					attacker = self.objects[attacker_id]
					attacker.status["tap":"untapped"]
					del self.history[-1]
				return "illegal"

		elif decision["type"] == "declare blockers":
			# Détermination des attaquants bloqués
			repartition = {}
			for blocker_id in decision["objects"]:
				block_options = self.find_objects(zone="bf",controller=self.players[player.opponent],caracs_crits={"type":"creature"},attacking=True)
				blocked = player.choice("You have to choose which attacking creature(s) the creature {0} blocks.".format(blocker_id),"Answer by giving the creature(s) id, separated by commas.",block_options).split(",")
				repartition[blocker_id] = blocked

			# Détermination du coût total de bloquer
			locked_cost = self.det_decision_cost(decision,player,repartition)

			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player,repartition) and player.able_to_pay(locked_cost):
				self.perform_decision(locked_cost,event,player)
				for blocker_id in decision["objects"]:
					self.objects[blocker_id].blocking = [True,repartition[blocker_id]]
					self.blockers_repartition = repartition
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeu avant la décision
				for blocker_id in decision["objects"]:
					del self.history[-1]
				return "illegal"

		elif decision["type"] == "target":
			# Détermination du coût de cibler les objets ciblés
			locked_cost = self.det_decision_cost(decision)

			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player) and player.able_to_pay(locked_cost):
				self.perform_decision(locked_cost,event,player)
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeu avant la décision
				return "illegal"

		elif decision["type"] == "untap":
			# Détermination du coup de dégager les permanents
			locked_cost = self.det_decision_cost(decision)

			# Paiement du coût ou constatation de l'illégalité de la décision
			if self.is_legal_decision(decision,player) and player.able_to_pay(locked_cost):
				self.perform_decision(locked_cost,event,player)
				for to_untap_id in decision["untapping"]:
					self.objects[to_untap_id].status["tap"] = "untapped"
				return "performed"
			else:
				# Décision illégale : retour à l'état du jeu avant la décision
				return "illegal"
	
	def register_decision(self,decision,player):
		"""Enregistre une décision comme un évènement, qu'elle soit légale ou non."""
		event = {"action":"decision",
				 "player":player.cardinal,
				 "decision":decision,
				 "turn":{"cardinal":self.n_turns,"phase":self.phase,"step":self.step}} # évènement précis à rentrer dans l'historique
		self.history.append([event])
		return event
	
	def perform_decision(self,locked_cost,event,player):
		"""Termine la réaisation d'une décision légale."""
		player.pay_cost(locked_cost)
		self.verify_triggers([event])
	
	def restore_previous_state(self,decision_type,legal_obj=None,illegal_obj=None):
		"""Fait revenir le jeu à son état précédant une décision illégale d'un joueur (appelée seulement par "cast", "land", et "active", c'est-à-dire les trois décisions pouvant avoir créé un nouvel objet)."""
		
		# Déréférencement complet de l'objet créé par la décision illégale
		self.objects[illegal_obj].delete()
		del self.objects[illegal_obj]
		self.cardinal_objects -= 1
		
		# Réhabilitation en tant qu'objet actif de l'éventuelle instance ayant subi un <move_zone> à cause de la décision illégale
		if decision_type in ["cast","land"]: # seules les décisions de "cast" et "land" peuvent avoir provoqué un <move_zone>
			to_restore = self.objects[legal_obj] # récupération dans <self.objects> de l'objet qui a été sorti du jeu
			self.active_objects.append(legal_obj)
			zone_orig = "hd" + to_restore.owner.cardinal
			to_restore.zone == zone_orig
			self.zones[zone_orig].append(legal_obj)
		else:
			self.cardinal_basic_objects -= 1
		
		del self.history[-1]
	
	def is_legal_decision(self,decision,player,decision_mod):
		"""Indique si la décision est légale au vu des règles de base du jeu et des effets continus de permission et de restriction."""
		
		#f
		return True
	
	##### MÉTHODES DE RÉALISATION D'EFFETS
		
	def process_effect(self,effects):
		"""Traite la demande de réalisation de faits de jeu."""
		
		# Parcours des effets à appliquer
		for effect in effects:
			# Détermination du Fait de jeu après application des effets continus de préventions, de remplcement et d'impossibilité
			gf = self.replace(self.prevent(effect))
			
			if not self.cannot(gf):
				self.pending_gfs.append(gf)
				self.recurr_gfs += 1
				self.perform(gf)
				self.recurr_gfs -= 1
		
		# Occurrence effective des Faits de jeu issus des effets en tant qu'évènement
		if self.recurr_gfs == 0:
			events = []
			for pending_gf in self.pending_gfs:
				event = {"action":"gf",
					 "gf":pending_gf,
					 "turn":{"cardinal":self.n_turns,"phase":self.phase,"step":self.step}} # évènement précis à rentrer dans l'historique
				events.append(event)
				self.log.append(event)
			self.history.append(events)
			self.verify_triggers(events)
			self.pending_gfs = []
			self.reset_abis()
	
	def perform_gf(self,gf):
		"""Finalité d'une action passée par toutes les étapes de <process>."""
		
		if gf["effect"] in self.inter_effects.keys():
			exec(self.inter_effects[gf["effect"]])
		else:
			exec(self.final_effects[gf["effect"]])
	
	def replace(self,gf):
		"""Renvoie l'effet tel que modifié par les CEs de remplacement du jeu."""
		
		#f
		return gf
	
	def prevent(self,gf):
		"""Renvoie l'effet tel que modifié par les CEs de prévention du jeu."""
		
		#f
		return gf
	
	def cannot(self,gf):
		"""Renvoie une autorisation ou non du jeu pour l'effet."""
		
		#f
		return gf
	
	##### MÉTHODES APPELÉES PAR PROCESS
	
	def trigger(self,abi_id):
		"""Exécute les actions nécessaires lors du déclenchement d'une capacité déclenchée."""
		
		trigger_effect = self.new_stack_effect(abi_id)
		self.objects[trigger_effect].zone = "wt"
		self.zones["wt"].append(trigger_effect)
	
	def move_zone(self,obj_id,zone_dest,controller=None):
		"""Crée un objet dérivé de l'objet d'identifiant <obj_id> dans la zone <zone_dest>.Tous les changements de zone passeront par cette méthode, sauf pour les objets <Token> et <Stack_object> qui ne peuvent changer de zone."""
		
		to_move = self.objects[obj_id]
		
		if isinstance(to_move,obs.Token) or isinstance(to_move,obs.Stack_effect):
			to_move.delete()
			return "deleted token or stack effect"
		else:
			new_id = obj_id.split(":")[0] + ":" + str(int(obj_id.split(":")[1])+1) # modification de la deuxième partie de l'identifiant de départ
			self.cardinal_objects += 1
			
			if zone_dest=="st":
				self.objects[new_id] = obs.Spell(new_id,self,to_move.owner,controller,to_move.pcaracs)
			elif zone_dest=="bf":
				self.objects[new_id] = obs.Permanent(new_id,self,to_move.owner,controller,to_move.pcaracs)			
			elif "lb" in zone_dest:
				self.objects[new_id] = obs.Card(new_id,self,to_move.owner,"lb",to_move.pcaracs)
			else:
				self.objects[new_id] = obs.Card(new_id,self,to_move.owner,zone_dest,to_move.pcaracs)
			
			self.active_objects.append(new_id)
			self.zones[zone_dest].append(new_id)
			to_move.delete()
			return new_id
	
	#f
	
	##### VÉRIFICATIONS DES TRIGGERS
	
	def verify_triggers(self,events):
		"""Vérifie le déclenchement éventuel de capacités déclenchées du jeu par l'évènement <events>, et les applique le cas échéant."""
		
		for event in events:
			for trigger_id in self.triggers: # parcours des capacités déclenchées du jeu
				triggered_abi = self.objects[trigger_id.split("-")[0]].abis[trigger_id]
				if fce.event_corresp(triggered_abi["event"],event): # comparaison de l'évènement ayant occurré et de l'évènement attendu
					self.process([{"effect":"trigger","abi":triggered_abi,"id":trigger_id}])
					pass
	
	##### MÉTHODES UTILITAIRES
	
	def combat_ongoing(self):
		"""Définit les variables identifiant le combat."""
		
		self.declared_combat = True
		self.combat_roles["attacking"] = self.active.cardinal
		self.combat_roles["blocking"] = self.passive.cardinal
	
	def new_stack_effect(self,abi_id):
		"""Crée l'effet de la capacité déclenchée d'identifiant <trigger_id>."""
		
		perm_on = self.objects[abi_id.split("-")[0]]
		active_abi = perm_on.abis[abi_id]
		
		# Création d'un nouvel objet d'effet sur la pile <Stack_effect>
		self.cardinal_basic_objects += 1 # un nouvel objet qui n'est pas une dérivation d'un objet fondamental sera effectivement créé
		self.cardinal_objects += 1
		_id = str(self.cardinal_objects)+":0"
		self.objects[_id] = obs.Stack_effect(_id,self,perm_on.bossplayer,{"text":active_abi["effect"]},perm_on._id)
		self.active_objects.append(_id)
		
		return _id
	
	def find_objects(self,zone,owner=None,controller=None,caracs_crits={},status_crits={},attacking=None,blocking=None,is_token=None): #f : si on cherche un token
		"""Renvoie une liste des identifiants de tous les objets de la zone donnée correspondants au critères de contrôle/propriété et de caractéristiques."""
		
		relevant_objects = []
		
		for obj_id in self.zones[zone]:
			obj = self.objects[obj_id]
			if fce.obj_corresp(obj,zone,owner,controller,caracs_crits,status_crits,attacking,blocking,is_token):
				relevant_objects.append(obj_id)
		
		return relevant_objects
	
	def det_actions(self,player_id):
		"""Détermine (indicativement) toutes les actions possibles (même si elles sont illégales) pour le joueur <player> lorsqu'il a la priorité."""
		
		actions = {"cast":[],"land":[],"active":[],"active mana":[],"special":[]}
		
		actions["cast"] = self.find_objects("hd"+player_id,caracs_crits={"type":["creature","sorcery","instant","artifact","enchantment","planeswalker"]})
		actions["land"] = self.find_objects("hd"+player_id,caracs_crits={"type":["land"]})
		
		# Détermination des capacités activables (de mana ou non) et des capacités spéciale
		for zone_indiv in self.players[player_id].zones: # parcours des zones individuelles du joueur
			for obj_id in zone_indiv:
				obj = self.objects[obj_id]
				
				for abi_id,abi in obj.abis.items():
					if abi["val in"]==zone_indiv: # vérification du fait que la capacité est valable quand l'objet sur lequel elle se trouve est dans <zone>
						if abi["type"] == "active":
							actions["active"].append(abi_id)
						if abi["type"] == "active mana":
							actions["active mana"].append(abi_id)
						if abi["type"] == "special":
							actions["special"].append(abi_id)				
		for perm_id in self.zones["bf"]: # parcours du champ de bataille 
			perm = self.objects[perm_id]
			
			if perm.controller==player_id: # vérification du fait que le joueur concerné est contrôleur du permanent
				for abi_id,abi in perm.abis.items():
					if abi["val in"]=="bf":
						if abi["type"] == "active":
							actions["active"].append(abi_id)
						if abi["type"] == "active mana":
							actions["active mana"].append(abi_id)
						if abi["type"] == "special":
							actions["special"].append(abi_id)
		
		return actions
	
	##### CALCUL DES CAPACITÉS
	
	def reset_abis(self):
		"""Recommence toute la modification des caractéristiques des objets de jeu par les CEs de caractéristiques, puis recalcule les effets continus (n'étant pas de caractéristique) et capacités déclenchées à observer."""
		
		#f
		self.find_CEs()
		self.find_triggers()
	
	def find_CEs(self):
		"""Recherche parmi les objets de jeu actif toutes les capacités statiques valables dans la zone de leur objet de jeu et recalcule les CEs du jeu en conséquence."""
		
		#f
		pass
	
	def find_triggers(self):
		"""Recherche parmi les objets de jeu actif toutes les capacités déclenchées valables dans la zone de leur objet de jeu."""
		
		#f
		pass
	
	#f : faire aussi ce reset au début et à la fin de chaque phase
	#f : verify_triggers au début et à la fin de chaque phase
	
#####