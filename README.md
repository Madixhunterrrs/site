# ScaleUp — Site agence Strategy & Growth

Site en **Python (Flask) + HTML/CSS/JS**, style premium sombre (glassmorphism, neon, dégradés bleu/violet/cyan/rose). L'agence sert deux domaines : **École privée** et **Cabinets médicaux**, chacun avec sa propre page.

## Structure

```
agence/
├── app.py                    # Serveur Flask, routes, panneau de contrôle
├── requirements.txt
├── data/                     # Créé automatiquement — demandes reçues (JSON)
├── templates/
│   ├── base.html              # Header, footer, nav
│   ├── landing.html           # Accueil COURT : choix du domaine (École / Médecin)
│   ├── ecole.html              # Page École privée (slider + 3 services + avantages)
│   ├── medecin.html            # Page Médecins (2 services + avantages)
│   ├── application.html        # Détail de l'application de gestion d'école
│   ├── marketing.html          # Détail Marketing Digital
│   ├── digitalisation.html     # Détail Digitalisation
│   ├── contact.html            # Formulaire de demande de démo (unique, réutilisé partout)
│   ├── admin_login.html        # Connexion au panneau de contrôle
│   └── admin.html              # Panneau de contrôle (liste des demandes)
└── static/
    ├── css/style.css          # Design system complet
    ├── js/main.js              # Interactions, slider, animations, particules
    └── img/                    # Logo, captures d'application
```

## Lancer le site en local

```bash
cd agence
pip install -r requirements.txt
python app.py
```

Puis ouvrez **http://127.0.0.1:5000** dans votre navigateur.

## Parcours du site

- `/` — accueil court : le visiteur choisit son domaine
- `/ecole` — page École privée (slider des captures + Application, Marketing, Digitalisation)
- `/medecin` — page Médecins (Marketing Digital + Digitalisation)
- `/application`, `/marketing`, `/digitalisation` — pages détaillées de chaque service
- `/contact` — formulaire de demande de démo, accessible depuis n'importe quelle page (bouton "Demander une démo")

## Panneau de contrôle (recevoir vos demandes)

Toute demande envoyée depuis `/contact` est :
1. **Toujours enregistrée** dans `data/demandes.json`
2. **Envoyée par email** si le SMTP est configuré (voir plus bas)
3. **Visible dans le panneau de contrôle**, à l'adresse **`/admin`**

### Se connecter au panneau de contrôle

1. Un mot de passe par défaut est déjà configuré pour que ça fonctionne immédiatement :
   **`ScaleUp-Fes-2026!`**
   Changez-le avant la mise en ligne réelle du site, soit dans `app.py` (`CONFIG["ADMIN_PASSWORD"]`), soit via variable d'environnement :
   ```bash
   export ADMIN_PASSWORD=votre-nouveau-mot-de-passe
   ```
2. Ouvrez `/admin` — vous serez redirigé vers `/admin/login` si vous n'êtes pas connecté.
3. Depuis le panneau, vous pouvez consulter chaque demande et la marquer comme **"traité"** une fois qu'un membre de l'équipe a recontacté la personne.
4. `/admin/logout` pour se déconnecter.

### Configurer l'envoi d'email (recommandé, en plus du panneau de contrôle)

Ouvrez `app.py` et remplissez le dictionnaire `CONFIG` en haut du fichier (ou définissez les variables d'environnement équivalentes) :

```python
CONFIG = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "SMTP_USER": "scaleupadministration@gmail.com",
    "SMTP_PASSWORD": "votre-mot-de-passe-application",  # jamais le mot de passe principal
    "CONTACT_TO": "scaleupadministration@gmail.com",
    "ADMIN_PASSWORD": "choisissez-un-mot-de-passe-secret",
}
```

Avec Gmail : activez la validation en 2 étapes puis créez un **mot de passe d'application** (Compte Google → Sécurité → Mots de passe des applications).

Ou, sans toucher au code :

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_USER=scaleupadministration@gmail.com
export SMTP_PASSWORD=xxxxxxxxxxxxxxxx
export CONTACT_TO=scaleupadministration@gmail.com
export ADMIN_PASSWORD=choisissez-un-mot-de-passe-secret
export SECRET_KEY=une-longue-chaine-aleatoire   # nécessaire pour les sessions du panneau de contrôle
python app.py
```

**Important :** changez `ADMIN_PASSWORD` et `SECRET_KEY` avant de mettre le site en ligne.

## Slider promotionnel de la page d'accueil

Tout en haut de `/`, un slider défile automatiquement pour mettre en avant vos services (ou une promotion ponctuelle).

- Tant qu'aucune promotion n'est ajoutée, **4 bannières par défaut** s'affichent (une par service : École, Marketing, Digitalisation, Médecins).
- Pour gérer vos propres bannières : connectez-vous au panneau de contrôle (`/admin`) puis cliquez sur **"Slider d'accueil"** (ou allez directement sur `/admin/promos`).
- Depuis cette page vous pouvez : ajouter une bannière (titre, sous-titre, étiquette, lien, image), l'activer/désactiver, ou la supprimer.
- **Dimensions recommandées pour l'image : 1600 × 700 px (ratio ~2.3:1)**, JPG/PNG/WebP, 2 Mo conseillé (6 Mo maximum absolu). L'image remplit toute la largeur de la bannière ; sans image, un fond dégradé de la marque est utilisé automatiquement.
- Dès qu'au moins une bannière active existe, elle remplace entièrement les 4 bannières par défaut.

## Personnalisation rapide

- Couleurs et tokens : variables CSS en haut de `static/css/style.css` (`--bg`, `--primary`, `--secondary`, `--accent`, `--pink`).
- Contenu des modules, avantages, étapes du process : listes Jinja (`{% set ... %}`) directement dans les templates.
- Logo : fichiers réels dans `static/img/logo-icon.png` (header/favicon) et `static/img/logo-full.png` (footer).
