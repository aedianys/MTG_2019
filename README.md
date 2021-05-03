# Projet d'informatique 2019 : Magic the gathering (MTG) en Python3

## Objectif

L'objectif de ce projet en Python est de permettre à deux joueurs (sur le même ordinateur) de jouer une partie du jeu de cartes à collectionner Magic The Gathering (MTG) l'un contre l'autre en format modern (c'est-à-dire avec un deck de 60 cartes relativement récentes), en respectant les nombreuses règles contraignantes de MTG. Sans application graphique, le dialogue avec les joueurs se fait en console Python par des commandes spécifiques. Mais l'objectif final est que ce moteur de jeu sous-tende l'application de jeu graphique utilisant Pygame, en lui fournissant les informations sur l'état du jeu, et en recevant d'elle les choix effectués par les joueurs.

Les règles de MTG sont au premier abord assez simples, mais les nombreux mécanismes et spécificités du jeu ainsi que le grand nombre de cartes parues en ont fait un ensemble très complexe, mais aussi très logique et parfaitement adapté à l'orientation objet de Python (cf. le fichier *documents/regles_completes*, les règles officielles de MTG). Seules les applications de Magic les plus élaborées (telles MTG Arena, développée par l'entreprise productrice du jeu, Wizards of the Coast Inc.) peuvent implémenter cette complexité. Mais puisqu'elle est constitutive de MTG, l'objectif fut de créer un programme capable d'intégrer la plus grande partie des mécanismes de MTG que nous-mêmes n'avons pas codés. De nombreux éléments importants de la structure du moteur n'ont donc pas d'utilité visible, mais serviraient en cas de futures améliorations. Cependant, ce choix n'a pas suffisamment réduit la quantité de fonctionnalités à organiser et à programmer, de sorte que le moteur de jeu n'est pas encore fonctionnel.

## Fonctionnalités

### Moteur de jeu (/game_engine)

La Partie est représentée par une instance de la classe *Game*, qui aura comme Joueurs des instances de la classe *Player*. Toute communication de la Partie avec ses Joueurs se fait par l'intermédiaire des méthodes de communication en console de Player. La notion d'objet existe déjà dans MTG, aussi les cartes sont des objets, dont la nature dépend en fait de la zone dans laquelle ils se trouvent. Toute action des joueurs ou effet viennent donc altérer ces objets. Pour plus de précision, consulter la partie I du Rapport du projet.

### Téléchargement des cartes (/cards)

Les caractéristiques et les images des cartes sont téléchargées par *parsing* des pages du site de référence [Scryfall](https://www.scryfall.com) et sont ensuites, pour les caractéristiques, stockées dans une base de données, et pour les images, redimensionnées pour ne pas prendre trop de place et pouvoir être utilisées en jeu.

### Partie graphique (/graphic_engine)

La partie graphique a été conçue pour une résolution 1600×900. Elle comprend un écran d'accueil ainsi qu'un outil de création de deck graphique utilisant les cartes préalablement téléchargées et répertoriées dans la base de données */cards/cards.db*. La recherche des cartes se fait grâce à des requêtes SQL, et permet pour l'instant de filtrer selon la couleur.

![Deck editor screenshot](https://github.com/pierreayanides/MTG_2019/blob/main/documents/examples/deck_editor.png)

## Requirements

La partie graphique fonctionne avec Pygame qui s'installe facilement avec :

```
pip install pygame
```

Le créateur de deck utilise `urllib` pour télécharger les images et `Pillow` pour les redimensionner.

```
pip install urllib
pip install Pillow
```

## Usage

Pour lancer la partie graphique :

```
python3 /graphic_engine/main.py
```

## License

Les images utilisées ne nous appartiennent pas.

License GPLv3.

## Authors

Pierre Ayanides (Téléchargement, partie graphique)

Antoine Bedin (Moteur de jeu)

Gabriel Farago (Partie graphique)
