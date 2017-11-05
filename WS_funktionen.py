from pathlib import Path
import pywikibot, re
import requests
import json
import urllib
import shutil
import pprint

try:
    import wikitextparser
except ImportError:
    print('Modul »wikitextparser« wird benötigt, bitte mit »pip3 install wikitextparser« installieren.')
    exit()

def erzeuge_latex_datei(WS_Seite, EINGABE_DIR, AUSGABE_DIR, BILDER_DIR, Anmerkungen):
    """Parst eine Wikisource-Seite und erstellt daraus eine LaTeX-Seite.

    Erwartet einen Seitennamen (als String) als Eingabe.
    """
    Datei_Pfad_Eingabe = Path(EINGABE_DIR + re.sub('/', '_', WS_Seite))
    Datei_Pfad_Ausgabe = Path(AUSGABE_DIR + re.sub('/', '-', WS_Seite) + '.tex')
#    if Datei_Pfad_Ausgabe.is_file():
#        print('Seite »{}« wurde schon konvertiert.'.format(WS_Seite))
#    else:
        # Seite wird neu konvertiert
    Eingabe_Datei = open(str(Datei_Pfad_Eingabe), 'r')
    Datei_Inhalt = Eingabe_Datei.read()

    Datei_geparst = wikitextparser.parse(Datei_Inhalt)
#    pprint.pprint(Datei_geparst.tables[0].data(span=False))
#    pprint.pprint(Datei_geparst.tables[0].data(span=True))

    Datei_Inhalt = parse_Gliederung(Datei_Inhalt)
    Datei_Inhalt = parse_WS_HTML_Markup(Datei_Inhalt, EINGABE_DIR, AUSGABE_DIR, BILDER_DIR)

    while len(re.findall('{{', Datei_Inhalt)) > 0:
        Datei_Inhalt = parse_WS_Vorlagen(Datei_Inhalt)

    while len(re.findall('{\|', Datei_Inhalt)) > 0:
        Datei_Inhalt = parse_Tabellen(Datei_Inhalt)

    print(WS_Seite)
    Anmerkungen = extrahiere_Anmerkungen(Datei_Inhalt, Anmerkungen, AUSGABE_DIR, WS_Seite)

    
    Ausgabe_Datei = open(str(Datei_Pfad_Ausgabe), 'w')
    Ausgabe_Datei.write(Datei_Inhalt)
    Ausgabe_Datei.close()
    print('Seite »{}« wurde neu konvertiert.'.format(WS_Seite))
    return Anmerkungen

def extrahiere_Anmerkungen(Datei_Inhalt, Anmerkungen, AUSGABE_DIR, WS_Seite):
    """Extrahiert die Anmerkungen (<section begin ... section end />"""

    Anmerkungen_lokal = re.findall('<section begin=(.*?) />(.*?)<section end', Datei_Inhalt, flags=re.DOTALL)
    print('{} Anmerkungen gefunden.'.format(len(Anmerkungen_lokal)))

    while len(Anmerkungen_lokal) > 0:
        Anmerkung = Anmerkungen_lokal.pop(0)
        Nummer = Anmerkung[0]
        Text = Anmerkung[1]
        Datei_Pfad_Anmerkung = Path(AUSGABE_DIR + re.sub('/', '-', WS_Seite) + '-' + Nummer + '.tex')
        Anmerkung_Datei = open(str(Datei_Pfad_Anmerkung), 'w')
        Anmerkung_Datei.write(Text)
        Anmerkung_Datei.close()
        if Nummer in Anmerkungen:
#            print('{} ist schon enthalten'.format(Nummer))
            Anmerkungen[Nummer] = Anmerkungen[Nummer] + ' ' + Text
        else:
#            print('{} ist neu'.format(Nummer))
            Anmerkungen[Nummer] = Text

#    print(Anmerkungen)
    return Anmerkungen

    
def parse_Tabellen(Datei_Inhalt):
    """Findet Tabellen."""

    Datei_Inhalt = re.sub('\{\|((?:(?!{\|).)*?)\|}', '\\\\Tabelle{\\1}', Datei_Inhalt, flags=re.DOTALL)
    return Datei_Inhalt

def parse_Gliederung(Datei_Inhalt):
    """Sucht nach Büchern und Kapitel."""

    Datei_Inhalt = re.sub("\{\{LineCenterSize.*?'''(Nicolaus.*?)'''.*?'''(.*?Buch\.)'''}}", '\Buch{\\1}{\\2}', Datei_Inhalt, flags=re.DOTALL)
    Datei_Inhalt = re.sub("\{\{LineCenterSize.*?Anmerkungen\.}}", '\Buch{}{Anmerkungen.}', Datei_Inhalt, flags=re.DOTALL)
    Datei_Inhalt = re.sub('\{\{SeiteLST\|[0-9]+?\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)}}', '\\\\SeiteLST{\\1}{\\2} ', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{CRef\|WS\|((?:(?!{{).)*?)}}', '\\\\footnote{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{CRef\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)\|([a-z0-9]+?)}}', '\\\\CRef{\\1}{\\2}{\\3}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{CRef\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)}}', '\\\\CRef{\\1}{\\2}{}', Datei_Inhalt)
    Datei_Inhalt = re.sub("\{\{LineCenterSize.*?Capitel.*?'''((?:(?!{{).)*?)'''((?:(?!{{).)*?)}}", '\Kapitel{\\1\\2}', Datei_Inhalt, flags=re.DOTALL)
    return Datei_Inhalt
    

def parse_WS_Vorlagen(Datei_Inhalt):
    """Wandelt die WS-Vorlagen in LaTeX-Befehle um."""

    Datei_Inhalt = re.sub('\{\{0\|((?:(?!{{).)*?)}}', '\\\\hphantom{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{1\|((?:(?!{{).)*?)}}', '\\\\parbox{0cm}{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Polytonisch\|((?:(?!{{).)*?)}}', '\\\\Polytonisch{\\1}', Datei_Inhalt, flags=re.IGNORECASE)
    Datei_Inhalt = re.sub('\{\{SperrSchrift\|((?:(?!{{).)*?)\|.[0-9]+?}}', '\\\\SperrSchrift{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{SperrSchrift\|((?:(?!{{).)*?)}}', '\\\\SperrSchrift{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Nowrap\|((?:(?!{{).)*?)}}', '\\\\Nowrap{\\1}', Datei_Inhalt, flags=re.IGNORECASE)
    Datei_Inhalt = re.sub('\{\{Unicode\|((?:(?!{{).)*?)}}', '\\\\Unicode{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Anker\|((?:(?!{{).)*?)}}', '\\\\Anker{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Right\|((?:(?!{{).)*?)}}', '\\\\Right{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Bruch\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)}}', '\\\\Bruch{\\1}{\\2}', Datei_Inhalt)
#    Datei_Inhalt = re.sub('\{\{SeiteLST\|[0-9]+?\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)}}', '\\\\SeiteLST{\\1}{\\2}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{CRef\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)\|([a-z0-9]+?)}}', '\\\\CRef{\\1}{\\2}{\\3}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{CRef\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)}}', '\\\\CRef{\\1}{\\2}{}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Center\|((?:(?!{{).)*?)}}', '\\\\begin{center}\\1\\\\end{center}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{PageDefEinzV\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)\|((?:(?!{{).)*?)}}((?:(?!{{).)*?)</div>', '\\\\PageDefEinzV{\\1}{\\2}{\\3}{\\4}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Kapitaelchen\|((?:(?!{{).)*?)}}', '\\\\textsc{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{LineCenterSize\|([0-9]*?)\|([0-9]*?)\|((?:(?!{{).)*?)}}', '\\\\LineCenterSize{\\1}{\\2}{\\3}', Datei_Inhalt)
#    Datei_Inhalt = re.sub("\{\{LineCenterSize.*?Capitel.*?'''((?:(?!{{).)*?)'''}}", '\chapter{\\1}', Datei_Inhalt, flags=re.DOTALL)
#    Datei_Inhalt = re.sub('\{\{((?:(?!{{).)*?)}}', '\\\\WSVorlage{\\1}', Datei_Inhalt, flags=re.DOTALL)
    return Datei_Inhalt

def parse_WS_HTML_Markup(Datei_Inhalt, EINGABE_DIR, AUSGABE_DIR, BILDER_DIR):
    """Wandelt Wiki- und HTML-Markup in LaTeX-Befehle um."""

    Datei_Inhalt = re.sub('<noinclude>.*?</noinclude>', '', Datei_Inhalt, flags=re.DOTALL)
    Datei_Inhalt = re.sub('^:+', '\\\\indent ', Datei_Inhalt, flags=re.MULTILINE)
    Datei_Inhalt = re.sub('<br />', ' \\\\\\\\ ', Datei_Inhalt)
    Datei_Inhalt = re.sub('%', '\\\\%', Datei_Inhalt)
    Datei_Inhalt = re.sub('&frac12;', '\\\\Bruch{1}{2}', Datei_Inhalt)
    Datei_Inhalt = re.sub('&nbsp;', '~', Datei_Inhalt)
    Datei_Inhalt = re.sub('&', '\\\\&', Datei_Inhalt)
    Datei_Inhalt = re.sub('<math>(.*?)</math>', '$\\1$', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{Linie}}', '\\\\Linie', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{em}}', '\\\\hspace{1em}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{PRZU}}', '\\\\PRZU', Datei_Inhalt)
    Datei_Inhalt = re.sub('\{\{0}}', '\\\\hphantom{0}', Datei_Inhalt)

    for bild in re.findall('\[\[Datei:(.*?)\|', Datei_Inhalt):
        lade_bild(bild, BILDER_DIR)

    for seite in re.findall('\[\[\{\{.*?:(.*?)}}\|', Datei_Inhalt):
        lade_wikisource_seite(seite, EINGABE_DIR)
        extrahiere_bild_code(seite, EINGABE_DIR, AUSGABE_DIR)

    Datei_Inhalt = re.sub('\[\[\{\{.*?:(.*?)}}\|(.*?)\|(.*?)\|.*?]]', '\\\\Bildsvg{\\1}{\\2}{\\3}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\[\[Datei:(.*?)\|(.*?)\|([a-z]+?)]]', '\\\\Bild{\\1}{\\2}{\\3}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\[\[Datei:(.*?)\|(.*?)]]', '\\\\Bild{\\1}{\\2}{}', Datei_Inhalt)
    Datei_Inhalt = re.sub('\[\[.*?\|(.*?)]]', '\\1', Datei_Inhalt)
    Datei_Inhalt = re.sub('\[(http:.*?)\ (.*?)]', '\\\\link{\\1}{\\2}', Datei_Inhalt)
    Datei_Inhalt = re.sub('<center>(.*?)</center>', '\\\\begin{center}\\1\\\\end{center}', Datei_Inhalt)
    Datei_Inhalt = re.sub('<ref>(.*?)</ref>', '\\\\footnote{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub('<sup>(.*?)</sup>', '\\\\textsuperscript{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub("'''(.*?)'''", '\\\\textbf{\\1}', Datei_Inhalt)
    Datei_Inhalt = re.sub("''(.*?)''", '\\\\textit{\\1} ', Datei_Inhalt)
    Datei_Inhalt = re.sub('djvu/', 'djvu-', Datei_Inhalt)
    Datei_Inhalt = re.sub('<poem .*?>(.*?)</poem>', '\\\\begin{verse}\\1\\\\end{verse}', Datei_Inhalt, flags=re.DOTALL)
#    Datei_Inhalt = re.sub('\{\|(.*?)\|}', '\\\\Tabelle{\\1}', Datei_Inhalt, flags=re.DOTALL)
#    Datei_Inhalt = re.sub('^(\\\\LineCenterSize.*?)$\\n\\n^(\\\\LineCenterSize.*?)$', '\\1\\n\\\\vfill\\n\\2', Datei_Inhalt, flags=re.MULTILINE)
#    Datei_Inhalt = re.sub('^(\\\\LineCenterSize.*?)$\\n\\n^(\\\\LineCenterSize.*?)$', '\\1\\n\\\\vfill\\n\\2', Datei_Inhalt, flags=re.MULTILINE)
    return Datei_Inhalt

def lade_wikisource_seite(WS_Seite, EINGABE_DIR):
    """Lädt eine Wikisource-Seite runter, wenn sie noch nicht existiert.

    Erwartet einen Seitennamen (als String) als Eingabe.
    """
    Datei_Pfad = Path(EINGABE_DIR + re.sub('/', '_', WS_Seite))
    if Datei_Pfad.is_file():
        print('Seite »{}« existiert schon.'.format(WS_Seite))
    else:
        # Seite wird neu geladen
        Datei = open(str(Datei_Pfad), 'w')
        site = pywikibot.Site()
        Page = pywikibot.Page(site, WS_Seite)
        Text = Page.text
        #print('zuletzt bearbeitet am: ', Page.editTime())
        # Kopf- und Fußzeile wird entfernt
        Datei.write(Text)
        Datei.close()
        print('Seite »{}« wurde neu geladen.'.format(WS_Seite))

def lade_bild(bild_name, BILDER_DIR):
    """Lädt ein Bild von Commons runter, wenn es noch nicht existiert.

    Erwartet den Bildnamen (als String) als Eingabe.
    """
    Datei_Pfad = Path(BILDER_DIR + bild_name)
    if Datei_Pfad.is_file():
        print('Bild »{}« existiert schon.'.format(bild_name))
    else:
        print('Bild »{}« wurde neu geladen.'.format(bild_name))
        apiurl = ('https://commons.wikimedia.org/w/api.php?action=query&titles=File:'
            + bild_name + '&prop=imageinfo&&iiprop=url&format=json')
        response = requests.get(apiurl)
        response_content = json.loads(response.content.decode())
        downloadurl = re.findall("'url': '(.*?)'", str(response_content))[0]
        urllib.request.urlretrieve(downloadurl, Datei_Pfad.as_posix())

def extrahiere_bild_code(bild_seite, EINGABE_DIR, AUSGABE_DIR):
    """Extrahiert aus einer Bild-Seite den LaTeX-Quellcode.

    Sucht nach einer tikzpicture-Umgebung 
    und schreibt diese in eine tex-Datei.
    """
    Bild_Pfad_Eingabe = Path(EINGABE_DIR + bild_seite)
    Bild_Pfad_Ausgabe = Path(AUSGABE_DIR + bild_seite + '.tex')
    if Bild_Pfad_Ausgabe.is_file():
        print('Bild-Code für »{}« existiert schon.'.format(bild_seite))
    else:
        # Bild-Code wird neu extrahiert
        Eingabe_Datei = open(str(Bild_Pfad_Eingabe), 'r')
        Datei_Inhalt = Eingabe_Datei.read()
        Bild_Code = re.findall('\\\\begin\{tikzpicture}.*?\\\\end{tikzpicture}', Datei_Inhalt, flags=re.DOTALL)[0]
        Ausgabe_Datei = open(str(Bild_Pfad_Ausgabe), 'w')
        Ausgabe_Datei.write(Bild_Code)
        Ausgabe_Datei.close()
        print('Bild-Code aus »{}« wurde neu extrahiert.'.format(bild_seite))

def pruefe_verzeichnis(verzeichnis):
    """Prüft, ob das angegebene Verzeichnis existiert.

    Erstellt das Verzeichnis wenn notwendig.
    """
    Pfad = Path(verzeichnis)
    if not Pfad.is_dir():
        os.mkdir(verzeichnis)
        print('Verzeichnis »{}« wurde neu erstellt.'.format(verzeichnis))



