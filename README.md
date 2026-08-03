# ScaleUp — Site agence Strategy & Growth

Site en **Python (Flask) + HTML/CSS/JS**, style premium sombre (glassmorphism, neon, dégradés bleu/violet/cyan), avec l'application de gestion d'école comme produit phare.

## Structure

```
agence/
├── app.py                  # Serveur Flask + routes
├── requirements.txt
├── templates/
│   ├── base.html            # Header, footer, nav
│   ├── index.html           # Accueil (hero, services, showcase, avantages, process, CTA, démo)
│   ├── application.html     # Landing page de l'application de gestion d'école
│   ├── marketing.html       # Page Marketing Digital
│   └── digitalisation.html  # Page Digitalisation
└── static/
    ├── css/style.css        # Design system complet
    └── js/main.js           # Interactions, animations, particules
```

## Lancer le site en local

```bash
cd agence
pip install -r requirements.txt
python app.py
```

Puis ouvrez **http://127.0.0.1:5000** dans votre navigateur.

## Pages disponibles

- `/` — Accueil
- `/application` — Application de gestion d'école (fonctionnalités, comparatif avant/après, tarifs, FAQ)
- `/marketing` — Marketing digital
- `/digitalisation` — Digitalisation des entreprises

## Recevoir les demandes de démo / contact

Le formulaire de la page d'accueil (`#demo`) envoie chaque demande au serveur, qui :

1. **Enregistre toujours** la demande dans `data/demandes.json` (créé automatiquement) — vous ne perdez jamais une demande, même sans configurer d'email.
2. **Envoie un email de notification** si vous avez configuré un compte SMTP (voir ci-dessous).
3. Vous pouvez consulter toutes les demandes reçues sur une page dédiée : **`/admin/demandes?key=VOTRE_CLE`**.

### Configurer l'envoi d'email (recommandé)

Ouvrez `app.py` et remplissez le dictionnaire `CONFIG` en haut du fichier (ou définissez les variables d'environnement équivalentes) :

```python
CONFIG = {
    "SMTP_HOST": "smtp.gmail.com",       # ou smtp.office365.com, etc.
    "SMTP_PORT": 587,
    "SMTP_USER": "scaleupadministration@gmail.com",
    "SMTP_PASSWORD": "votre-mot-de-passe-application",  # jamais le mot de passe principal
    "CONTACT_TO": "scaleupadministration@gmail.com",              # où recevoir les demandes
    "ADMIN_KEY": "choisissez-une-cle-secrete",
}
```

Avec Gmail : activez la validation en 2 étapes puis créez un **mot de passe d'application** (Compte Google → Sécurité → Mots de passe des applications) — n'utilisez jamais votre mot de passe Gmail habituel ici.

Ou, sans toucher au code, définissez les variables d'environnement avant de lancer le site :

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_USER=scaleupadministration@gmail.com
export SMTP_PASSWORD=xxxxxxxxxxxxxxxx
export CONTACT_TO=scaleupadministration@gmail.com
export ADMIN_KEY=choisissez-une-cle-secrete
python app.py
```

Tant que rien n'est configuré, les demandes sont quand même sauvegardées dans `data/demandes.json` et visibles sur `/admin/demandes?key=...` — l'email est un plus, pas une obligation.

**Important :** changez `ADMIN_KEY` avant de mettre le site en ligne. Par défaut (`changeme`), la page `/admin/demandes` reste bloquée pour votre sécurité.

## Personnalisation rapide

- Couleurs et tokens : variables CSS en haut de `static/css/style.css` (`--bg`, `--primary`, `--secondary`, `--accent`).
- Contenu des modules, avantages, étapes du process : listes Jinja (`{% set ... %}`) directement dans les templates.
- Logo : SVG inline dans `templates/base.html` — remplaçable par votre propre fichier dans `static/img/`.
