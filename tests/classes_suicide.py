#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

class Wrapper():
	def __init__(self):
		self.cls = Game(self,5)
	def process(self):
		self.cls.mainloop()
	def killchild(self):
		del self.cls

class Game():
	def __init__(self,boss,a):
		self.a = a
		self.boss = boss
		self.childs = [Card(self,0),Card(self,1)]
	def augm(self):
		self.a += 1
		print("augm a :",self.a)
	def mainloop(self):
		print("début")
		self.augm()
		self.suicide()
		self.augm()
		print("fin")
	def suicide(self):
		print("Réfs restantes :",sys.getrefcount(self))
		for c in self.childs:
			c.forgetmaster()
		print(sys.getrefcount(self))
		self.boss.killchild()
		print(sys.getrefcount(self))
		del self
		print("fin du suicide")

class Card():
	def __init__(self,boss,b):
		self.b = b
		self.boss = boss
	def forgetmaster(self):
		del self.boss
