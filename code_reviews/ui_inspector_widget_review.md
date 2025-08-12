# Revue de code : ui/inspector_widget.py

## Observations Générales
- Widget d'inspection permettant de gérer objets et pantins (échelle, rotation, attache...).
- Construction et connexion des widgets regroupées dans `__init__`.

## Points Positifs
- Interface utilisateur complète avec signaux/connecteurs appropriés.
- Méthodes helpers pour resynchroniser l'état selon la frame courante.

## Problèmes Identifiés
1. Peu de docstrings : seules les méthodes publiques `refresh` et `_attached_state_for_frame` sont documentées.
2. `__init__` est long et mélange création d'UI, layout et connexions ; difficile à maintenir.
3. Certains blocs `try/except` sans log (`except Exception: pass`) masquent des erreurs potentielles.
4. Utilisation de noms de variables peu explicites (`si` pour `sorted indices`).
5. Aucune gestion de nettoyage/fermeture des ressources graphiques.

## Recommandations
- Factoriser la construction de l'UI en méthodes privées distinctes pour clarifier `__init__`.
- Ajouter des docstrings aux méthodes principales et aux callbacks pour améliorer la compréhension.
- Remplacer les `except Exception` génériques par des exceptions ciblées accompagnées de logs.
- Renommer les variables ambiguës (`si` -> `sorted_indices` par exemple).
