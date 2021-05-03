#!/usr/bin/env python3
# -*- coding: utf-8 -*-		

##### INTERPRÉTATION

def interpret_lines(card_text):
	"""Divise le texte en les différentes capacités qui le composent."""
	
	#f
	return []

def interpret_abi(abi_text):
	"""Extrait du texte anglais de la capacité ses différentes composantes et retourne un tableau les contenant pour une future exécution."""
	
	#f
	pass

def interpret_effect(effect_text):
	"""Extrait du texte anglais d'un effet son action et ses paramètres."""
	
	#f
	pass

##### MANAS ET COÛTS

# Paiement d'un coût
# en mana -> dictionnaire avec couleurs en clés et nombre en valeur
# en points de vie -> nombre
# en marqueurs poison -> nombre
# en défausse de cartes -> dictionnaire avec conditions en clé et nombre en valeur
# en sacrifice de permanents -> dictionnaire avec conditions en clé et nombre en valeur
# en engagement de créature -> dictionnaire avec conditions en clé et nombre en valeur
# en exil de cartes depuis une zone -> liste de dictionnaire avec "zone","conditions","nombre" en clés

def add_mana_costs(mc1,mc2):
	"""Additionne les deux coùts en mana."""
	
	mcs = {}
	for color in ("B", "C", "R", "U", "W", "G", "Q"):
		mcs[color] = mc1[color] + mc2[color]
	return mcs

def add_costs(c1,c2):
	"""Additione deux coûts dans leurs diverses composantes."""
	
	cs = {}
	for cost in ("mana","life","poison","discard","sacrifice","exile","tap"):
		if cost=="mana":
			cs[cost] = add_mana_costs(c1[cost],c2[cost])
		elif cost in ("discard","poison"):
			cs[cost] = c1[cost] + c2[cost]
		elif cost=="exile":
			cs[cost] = c1[cost].extend(c2[cost])
		else:
			cs[cost] = {}
			for cond in c1[cost].keys:
				if cond in c2[cost].keys():
					cs[cost][cond] = c1[cost][cond] + c2[cost][cond]
				else:
					cs[cost][cond] = c1[cost][cond]
			for cond in c2[cost].keys:
				if not(cond in c1[cost].keys()):
					cs[cost][cond] = c2[cost][cond]
	return cs

#f

##### CORRESPONDANCES

def event_corresp(event_comp,event_part):
	"""Vérifie si <event_part> correspond à <event_comp>."""
	#f
	pass

def obj_corresp(obj,zone=None,owner=None,controller=None,caracs_crits={},status_crits={},attacking=None,blocking=None,is_token=None):
	"""Vérifie si un objet correspond aux critères donnés."""
	
	corresp = True
	
	if owner:
		if not(owner == obj.owner):
			corresp = False
	if controller:
		if not(controller == obj.controller):
			corresp = False
	if zone:
		if not(obj.zone in zone):
			corresp = False
	
	for crit,val in caracs_crits.items(): # parcours du dictionnaire des critères sur les caractéristiques
		if crit in obj.mcaracs.keys():
			if crit in ("ccm","power","thoughness"):
				modval = {"<":-1,">":1,"=":0}[val[0]] + val[1:]
				if not(stats_corresp(obj.mcaracs[crit],modval)):
					corresp == False
			else:
				crits_corresp = False
				for v in val:
					if v in obj.mcaracs[crit]:
						crits_corresp = True
				if not(crits_corresp):
					corresp = False
	
	if obj.mcaracs["type"][0] in ("planeswalker","creature","enchantment","artifact","land"): # vérifications des statuts seulement si l'objet est un permanent
		for status,crit in status_crits.items(): # parcours du dictionnaire des critères sur les statuts
			if not(obj.status[status]==crit):
				corresp = False
		if is_token == None:
			if not(isinstance(obj,obs.Token)):
				corresp = False
		if attacking != None:
			if not(obj.attacking[0] == attacking):
				corresp = False
		if blocking != None:
			if not(obj.blocking[0] == blocking):
				corresp = False
	
	return corresp
	#f : plusieurs possibilités de critères, liées ou non (difficile)
	#f : conditions de compteurs

def stats_corresp(stat,cond): # <cond> doit être une liste [mode,nombre] avec un mode de -1 (inférieur à), 1 (supérieur à), ou 0 (égal à)
	"""Vérifie si la statistique (une force, un pouvoir ou un coût de mana) correspond à la condition."""
	
	if cond[0] == 0:
		return (stat == cond[1])
	else:
		return ((cond[0]*(stat+cond[0]*0.5-cond[1])/(abs(stat+cond[0]*0.5-cond[1])))==True)

##### AUTRES UTILITAIRES

def is_permanent(types):
	"""Vérifie si au moins l'un des types fournis est un type de permanent."""
	
	perm_types = ("creature","enchantment","artifact","land","planeswalker")
	is_perm = False
	
	for t in perm_types:
		if t in types:
			is_perm = True
	
	return is_perm

#####