#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Script créant une thumbnail de chaque image contenue dans le répertoire cible"""

from PIL import Image
import os
from pathlib import Path

def path(strpath):
	"""Retourne le chemin au format de l'OS utilisé"""
	return str(Path(strpath))

def tb(file1, file2, size=(212,296)):
	"""Créé une miniature <file2> de l'image <file1> à la taille <size>"""
	img = Image.open(path(file1)) # chargement de l'image à télécharger
	img.thumbnail(size) # création de la miniature
	img.save(path(file2)) # enregistrement de la miniature

def global_tb(directory1, directory2, target_directory):
	"""Pour chaque <edition> dans <target_directory>, créé une miniature dans <directory2>/<edition> de chaque image se trouvant dans <directory1><edition>"""

	print('\n################## THUMBNAILING ##################') # affichage du log

	if not os.path.exists(directory2): # création du dossier de destination s'il n'existe pas
		os.mkdir(directory2)

	for edition in os.listdir(directory1):
		if edition in target_directory:
			print('\n----------- THUMBNAILING {0} ({1}) -----------'.format(edition.upper(), len(os.listdir(path(directory1+'/'+edition))))) # affichage du log

			if not os.path.exists(path('{0}/{1}'.format(directory2, edition))): # création du dossier de l'édition s'il n'existe pas
				os.mkdir(path('{0}/{1}'.format(directory2, edition)))

			for image in os.listdir(path('{0}/{1}'.format(directory1, edition))):
				tb('{0}/{1}/{2}'.format(directory1, edition, image),'{0}/{1}/{2}'.format(directory2, edition, image)) # création et enregistrement de la miniature

				print('THUMBNAILED : {0}'.format(image)) # affichage du log

			print('----------- THUMBNAILED {0} ({1}) ------------\n'.format(edition.upper(), len(os.listdir(path(directory1+'/'+edition))))) # affichage du log

	print('############### THUMBNAILING ENDED ###############\n') # affichage du log