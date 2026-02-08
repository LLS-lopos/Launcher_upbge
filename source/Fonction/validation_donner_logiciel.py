# ici, on vérifie les données au démarrage du programme

import os
import sys

# Ajouter le répertoire source au PYTHONPATH si nécessaire
if not any("source" in p for p in sys.path):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)

from .construire_structure import preference_launcher, config_launcher, structure_config, structure_preference
from .manipuler_donner import charger, sauvegarder_preference, sauvegarder_config

## variable
L_fichier_preference = []
L_origin_preference = []
L_fichier_config = []
L_origin_config = []


## fonction
def voir_donner_preference():
    sous_liste = []
    info = charger("preference")

    for i in info:
        L_fichier_preference.append(i)
        if type(info[i]) == dict:
            sous_liste.append(i)
            for ii in info[i]:
                sous_liste.append(ii)
            L_fichier_preference.append(sous_liste.copy())
            sous_liste.clear()


def voir_origin_preference():
    sous_liste = []
    for i in preference_launcher:
        L_origin_preference.append(i)
        if type(preference_launcher[i]) == dict:
            sous_liste.append(i)
            for ii in preference_launcher[i]:
                sous_liste.append(ii)
            L_origin_preference.append(sous_liste.copy())
            sous_liste.clear()


def voir_donner_config():
    sous_liste = []
    info = charger("config_launcher")

    for i in info:
        L_fichier_config.append(i)
        if type(info[i]) == dict:
            sous_liste.append(i)
            for ii in info[i]:
                sous_liste.append(ii)
            L_fichier_config.append(sous_liste.copy())
            sous_liste.clear()


def voir_origin_config():
    sous_liste = []
    for i in config_launcher:
        L_origin_config.append(i)
        if type(config_launcher[i]) == dict:
            sous_liste.append(i)
            for ii in config_launcher[i]:
                sous_liste.append(ii)
            L_origin_config.append(sous_liste.copy())
            sous_liste.clear()


def comparer_cle(l1: list, l2: list) -> bool:
    return l1 == l2


def gestion_configuration_preference():
    voir_donner_preference()
    voir_origin_preference()
    pref = comparer_cle(L_fichier_preference, L_origin_preference)

    print(f"Pref: {pref}")

    if pref: preference_launcher = charger("preference")
    else: structure_preference()

    sauvegarder_preference()


def gestion_configuration_launch():
    voir_donner_config()
    voir_origin_config()
    launch = comparer_cle(L_fichier_config, L_origin_config)

    print(f"launch: {launch}")

    if launch: config_launcher = charger("config_launcher")
    else: structure_config()

    sauvegarder_config()


def gestion_configuration():
    gestion_configuration_preference()
    gestion_configuration_launch()
    


### si main
if __name__ == '__main__':
    gestion_configuration()
