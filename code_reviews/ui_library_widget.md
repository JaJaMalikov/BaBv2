# Revue de code: ui/library_widget.py

## Analyse
Widget de bibliothèque affichant arrière‑plans, objets et pantins disponibles. Offre le glisser‑déposer et un menu contextuel pour ajouter des éléments à la scène.

## Recommandations
- Externaliser les chemins d'accès aux assets pour éviter les chemins codés en dur.
- Ajouter une gestion d'erreurs plus fine lors du chargement des icônes pour informer l'utilisateur.
- Paramétrer la taille des icônes/grilles via des constantes ou paramètres utilisateur.
- Tester la fonctionnalité de drag & drop pour chaque type d'asset.
