# Revue de code : ui/icons.py

## Observations Générales
- Module centralisant la génération d'icônes SVG recolorisées selon les états (normal, hover, actif).
- Utilisation d'un cache pour éviter de recharger les icônes.

## Points Positifs
- Fonction `_render_svg` bien isolée pour le rendu.
- `get_icon` fournit une API unique, les anciennes fonctions restant pour compatibilité.

## Problèmes Identifiés
1. `ICON_CACHE[name] = QIcon(); return QIcon()` en cas de fichier manquant : l'icône mise en cache n'est pas retournée.
2. Pas de gestion d'erreurs lors de l'ouverture des fichiers SVG (ex. fichier corrompu).
3. Absence de docstring pour `get_icon` et les fonctions de compatibilité.
4. `icon_reset_ui` renvoie l'icône `rotate` (semble être un raccourci temporaire?).

## Recommandations
- Retourner l'icône mise en cache même si vide (`return ICON_CACHE[name]`).
- Ajouter des try/except avec logging pour la lecture des fichiers SVG.
- Documenter `get_icon` et envisager de déprécier les fonctions spécifiques.
- Vérifier la correspondance entre les noms d'icônes et leur usage (`icon_reset_ui`).
