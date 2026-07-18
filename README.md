# DomShop

DomShop est une application e-commerce développée avec Django. Elle propose une boutique en ligne simple, une authentification utilisateur et une intégration OAuth Google.

## Fonctionnalités principales

- catalogue de produits et pages de détail
- panier utilisateur
- authentification locale et via Google OAuth
- interface d'administration Django
- gestion des commandes, coupons et produits

## Technologies utilisées

- Python
- Django
- django-allauth
- SQLite par défaut
- Bootstrap et templates HTML/CSS/JS

## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/Dominique12345678/domshop.git
   cd shop_project
   ```

2. Créer et activer un environnement virtuel :
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Configurer les variables d'environnement :
   - copier le fichier .env.example vers .env
   - remplir les valeurs nécessaires

5. Appliquer les migrations :
   ```bash
   python manage.py migrate
   ```

6. Lancer le serveur :
   ```bash
   python manage.py runserver
   ```

## Configuration des variables d'environnement

Le projet charge les valeurs sensibles depuis un fichier .env local. Créez un fichier .env à la racine du projet avec le contenu suivant :

```env
SECRET_KEY=replace-with-a-long-random-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-app-password
DEFAULT_FROM_EMAIL=DomShop <your-email@example.com>
```

Le fichier .env doit rester local et ne jamais être commit.

## Configuration Google OAuth

Pour activer la connexion Google, créez un projet sur Google Cloud Console et renseignez les valeurs Google dans le fichier .env.

## Notes importantes

- le fichier .env est ignoré par Git
- les secrets ne doivent jamais être ajoutés au dépôt
- en production, utilisez une vraie clé secrète et des valeurs d'environnement sécurisées
