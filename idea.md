##Logiciel d'analyse des données VL
===================================

#Objectifs
* Faciliter la lecture et la classification des nibbles des trames CAN
* Recherche des ECU
* Sauvegarde des recherches pour continuer aisément les analyses
* Automatisation des actions
* Différents cas d'usage : recherche live, analyse à postériori, analyse forensic
* Transfert sécurisé de données vers DB externe

#Pistes
* Travail des modules en // ?
  - Utilisation mémoire
	+ Rapidité exécution
	- Suivi des actions en cours

* Affichage des données en cas de reset de session web (crash, F5....)
  -> IHM simpliste
	-> Variables d'état

* Gestion du format .dbc

#Specs techniques
* Module Plug-n-play
  Facilité d'utilisation coté utilisateur

* Données JSON & DB Mongo

* Entrées :
  * CAN x2
	* LIN ?
	* K-Line


#Noyau et modules
* Noyau
  Gestion serveur web basique
	Stockage et synchro des données
	Chargement des modules

* Appel module
  JSON {module:, action:, params:}
	Action cible une fonction précise, les params sont conservés à travers la classe
	A l'issue de l'appel de la fonction, un paramètre de retour doit être transmis pour permettre une nouvelle action
	Possibilité d'arrêter une action -> commande dédiée générique

## ALGO
-------

> Ouverture APP
  -> Identification ?
  > Choix action
    A: Démarrer analyse
    B: Charger logs
    C: Simuler équipement

    A:> Bus par défaut, analyse VIN et chargement DB
        -> Pas de flux
          > Chargement de bus autre
        -> Flux
          > Accès aux actions
            A.A : Classification des octets
            A.B : Enregistrement session
            A.C : Rejeu session
            A.D : Outils d'analyse (freq, )

## Tests
Id : 0x726
Id : 0x797
Id : 0x7D0
