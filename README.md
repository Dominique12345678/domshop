# DomShop - Plateforme E-commerce Moderne 🛍️

DomShop est une application web e-commerce complète, développée avec Django, offrant une expérience utilisateur fluide et une interface d'administration puissante de type SaaS.

## ✨ Fonctionnalités Clés

### 👤 Espace Client
- **Accueil Dynamique** : Section HERO avec vidéo en arrière-plan et produits phares.
- **Catalogue de Produits** : Affichage dynamique avec filtrage par catégorie et recherche instantanée.
- **Panier intelligent** : Ajout et mise à jour des quantités via AJAX (sans rechargement de page) avec notifications Toast.
- **Authentification Hybride** : Connexion classique ou via **Google OAuth 2.0**.
- **Dashboard Client** : Historique des commandes, statistiques de dépenses et téléchargement de **factures en PDF**.

### 🛠️ Administration (Dashboard SaaS)
- **Analytics Dashboard** : Visualisation des ventes via des graphiques (Chart.js) et KPIs en temps réel.
- **Gestion des Produits & Catégories** : Interfaces modernes pour créer, modifier et supprimer des articles.
- **Gestion des Stocks** : Système d'inventaire avec alertes visuelles pour les stocks faibles ou en rupture.
- **Gestion des Factures** : Consultation et génération de factures pour tous les utilisateurs.

## 🚀 Technologies Utilisées

- **Backend** : Python / Django 5.x
- **Frontend** : HTML5, CSS3 (Vanilla), JavaScript (AJAX/Fetch API)
- **UI Framework** : Bootstrap 5 + FontAwesome 6
- **Bibliothèques Clés** :
  - `django-allauth` (Authentification sociale)
  - `Chart.js` (Graphiques dynamiques)
  - `xhtml2pdf` (Génération de PDF)
  - `SweetAlert2` (Pop-ups interactifs)
  - `Animate.css` (Animations fluides)

## 📦 Installation

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/votre-utilisateur/domshop.git
   cd domshop/shop_project
   ```

2. **Créer un environnement virtuel** :
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   ```

3. **Installer les dépendances** :
   ```bash
   pip install django django-allauth pyjwt cryptography xhtml2pdf reportlab
   ```

4. **Appliquer les migrations** :
   ```bash
   python manage.py migrate
   ```

5. **Lancer le serveur** :
   ```bash
   python manage.py runserver
   ```

## 🔐 Configuration Google OAuth
Pour activer la connexion Google, créez un projet sur la [Google Cloud Console](https://console.cloud.google.com/) et remplacez les clés `client_id` et `secret` dans le fichier `settings.py`.

---
*Développé avec ❤️ pour DomShop.*
