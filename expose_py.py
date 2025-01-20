import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import requests
from dotenv import load_dotenv
from urllib.parse import parse_qs
from middleware import log_request

load_dotenv()

class ConsultMeteo(BaseHTTPRequestHandler):
    CLE_API = os.getenv('API_KEY')
    URL_METEO = "https://api.openweathermap.org/data/2.5/weather"
    URL_PAYS = "https://restcountries.com/v3.1/name/"

    def do_GET(self):
        log_request(self)  
        routes = {
            '/': 'acceuil.html',
            '/meteo': 'ville.html',
            '/pays': 'pays.html'
        }

        if self.path in routes:
            self.afficher_html(routes[self.path])
        elif self.path.startswith('/resultat'):
            self.afficher_resultat(self.path)
        else:
            self.send_error(404, 'Page non trouvée')

    def do_POST(self):
        log_request(self)  # Interception de la requête
        if self.path in ['/submit', '/soumettre']:
            self.gerer_formulaire()
        else:
            self.send_error(404, 'Route non trouvée')

    def afficher_html(self, chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                contenu = fichier.read()
            self._envoyer_reponse(200, contenu, 'text/html')
        except FileNotFoundError:
            self.send_error(404, 'Fichier introuvable')

    def gerer_formulaire(self):
        longueur_contenu = int(self.headers.get('Content-Length', 0)) #recuperer la taille des données envoyes
        donnees_post = self.rfile.read(longueur_contenu).decode('utf-8') #lire et décoder les données envoyées
        params = parse_qs(donnees_post) #changer les données en dico
        ville, pays = params.get('city', [None])[0], params.get('pays', [None])[0]
        if ville:
            self.recuperer_meteo(ville)
        elif pays:
            self.recuperer_info_pays(pays)
        else:
            self.send_error(400, 'Aucun paramètre fourni')

    def recuperer_meteo(self, ville):
        url = f"{self.URL_METEO}?q={ville}&appid={self.CLE_API}&units=metric"
        try:
            reponse = requests.get(url)
            reponse.raise_for_status() #vérifier s'il y a une erreur
            donnees = reponse.json()
            requete = f"city={ville}&temperature={donnees['main']['temp']}&weather={donnees['weather'][0]['description']}&humidity={donnees['main']['humidity']}"
            self.rediriger(f'/resultat?{requete}')
        except requests.exceptions.RequestException:
            self.send_error(500, 'Erreur lors de la récupération des données météo')

    def recuperer_info_pays(self, pays):
        url = f"{self.URL_PAYS}{pays}"
        try:
            reponse = requests.get(url)
            reponse.raise_for_status()
            donnees = reponse.json()[0]
            requete = (
                f"pays={pays}&capital={donnees.get('capital', ['Inconnu'])[0]}&"
                f"population={donnees.get('population', 'Inconnue')}&"
                f"languages={', '.join(donnees.get('languages', {}).values())}&" #recuperer la clé langauge avec ses valeurs et les transformer en une liste avec join avec l'espage et la virgule
                f"region={donnees.get('region', 'Inconnue')}&"
                f"area={donnees.get('area', 'Inconnue')}"
            )
            self.rediriger(f'/resultat?{requete}')
        except requests.exceptions.RequestException:
            self.send_error(404, 'Pays non trouvé')

    def afficher_resultat(self, path):
        try:
            requete = parse_qs(path.split('?')[1])
            modele = 'reponse_meteo.html' if 'city' in requete else 'reponse_pays.html'
            
            with open(modele, 'r', encoding='utf-8') as fichier:
                contenu = fichier.read()

            for cle, valeurs in requete.items():
                contenu = contenu.replace(f'{{{{{cle}}}}}', valeurs[0])

            self._envoyer_reponse(200, contenu, 'text/html')
        except Exception as e:
            self.send_error(500, f'Erreur lors du traitement des résultats: {str(e)}')

    def rediriger(self, location):
        self.send_response(303)
        self.send_header('Location', location)
        self.end_headers()

    def _envoyer_reponse(self, code, contenu, type_contenu):
        self.send_response(code)
        self.send_header('Content-Type', f'{type_contenu}; charset=utf-8')
        self.end_headers()
        self.wfile.write(contenu.encode('utf-8'))

if __name__ == '__main__':
    server_address = ('127.0.0.1', 5001)
    httpd = HTTPServer(server_address, ConsultMeteo)
    print(f'Serveur démarré sur http://{server_address[0]}:{server_address[1]}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        httpd.server_close()
