#!/usr/bin/python3
# -*- coding: utf-8  -*-

import sys
if sys.version_info[0] < 3:
    print("Bitte Python 3 nutzen.")
    exit()

import WS_funktionen
import re

Index_Seite = 'Index:Nicolaus Coppernicus aus Thorn über die Kreisbewegungen der Weltkörper'
Seiten_Bezeichner = 'Seite:Kreisbewegungen-Coppernicus-0.djvu/'
EINGABE_DIR = 'wikisource/'
AUSGABE_DIR = 'latex/'
BILDER_DIR = 'bilder/'

WS_funktionen.pruefe_verzeichnis(EINGABE_DIR)
WS_funktionen.pruefe_verzeichnis(AUSGABE_DIR)
WS_funktionen.pruefe_verzeichnis(BILDER_DIR)
WS_funktionen.lade_wikisource_seite(Index_Seite, EINGABE_DIR)

Index_Datei = open(EINGABE_DIR + str(Index_Seite), 'r')

Seiten = []

#for Zeilen_Nummer in range(84):
for Zeilen_Nummer in Index_Datei:
#    Zeile = Index_Datei.readline().strip()
    Zeile = Zeilen_Nummer.strip()
  #  print(Zeile)
    if re.findall(Seiten_Bezeichner, Zeile) != []:
        Seite = re.split('\|', re.split('\[\[', Zeile)[1])[0]
        Seiten.append(Seite)

print('{} Seiten wurden gefunden.'.format(len(Seiten)))
#exit()
Anmerkungen = {}

while len(Seiten) > 0:
    Seite = Seiten.pop(0)
    WS_funktionen.lade_wikisource_seite(Seite, EINGABE_DIR)
    Anmerkungen = WS_funktionen.erzeuge_latex_datei(Seite, EINGABE_DIR, AUSGABE_DIR, BILDER_DIR, Anmerkungen)

#print(Anmerkungen.keys())
#print(Anmerkungen['2'])

print()
print('Zur Erzeugung der PDF-Datei jetzt »xelatex Coppernicus.tex« aufrufen.')
