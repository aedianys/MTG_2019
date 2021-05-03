#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import deepcopy,shallowcopy

#####

class Game_manager():
	def __init__(self):
		self.cls = Game(self,5)
		self.cls.mainloop()
	def killchild(self):
		del self.cls

class Game():
	zone_names = ("lb","bf","gy","hd","st","ex")
	def __init__(self,boss,a):
		self.a = a
		self.boss = boss
		self.childs = [Card(self,0,10),Card(self,1,10)]
		self.previous_state = None
	def augm(self):
		self.a += 1
		print("augm a :",self.a)
	def augmchilds(self):
		for m in range(len(self.childs)):
			self.childs[m].augm(m)
	def mainloop(self):
		print("début")
		rep = input("augmenter a ?")
		while rep != "n":
			self.augm()
			rep = input("augmenter a ?")
		self.process_decision()
		print(self.a,self.childs[0].b,self.childs[1].b,sep="\n")
		print("fin")
	def process_decision(self):
		self.previous_state = deepcopy(self)
		self.augmchilds()
		print(self.previous_state.a,self.previous_state.childs[0].b,self.previous_state.childs[1].b,sep="\n")
		if self.a > 5:
			print("ok")
		else:
			print("not ok")
			self = self.previous_state

class Card():
	def __init__(self,boss,_id,b):
		self._id = _id
		self.b = b
		self.boss = boss
	def augm(self,m):
		self.b += m
		print("child",self._id,"augm b :",self.b)