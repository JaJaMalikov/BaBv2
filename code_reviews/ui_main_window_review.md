# Revue de code : ui/main_window.py

## Observations Générales
- Fichier central de l'application (718 lignes) gérant la fenêtre principale, les overlays, la timeline et l'orchestration des actions.
- Combine logique d'interface, gestion de scène et fonctionnalités avancées (onion skin, sauvegarde, etc.).

## Points Positifs
- Utilisation cohérente de classes spécialisées (`ObjectManager`, `PlaybackHandler`, `TimelineWidget`).
- Nombreux paramètres configurables (onion skin, overlays, raccourcis).

## Problèmes Identifiés
1. Taille du module très importante rendant la maintenance difficile.
2. Peu de docstrings ou commentaires explicatifs pour les méthodes privées/publics.
3. Multiples blocs `try/except Exception: pass` qui masquent les erreurs.
4. Mélange de responsabilités : gestion de l'UI, de la logique métier et du stockage des paramètres dans un même fichier.
5. Utilisation de variables/attributs instanciés directement dans `__init__` sans encapsulation.
6. Certaines méthodes (ex. gestion de l'onion skin) sont très longues et pourraient être extraites.

## Recommandations
- Refactoriser en plusieurs modules/classes pour séparer les responsabilités (ex. gestion des overlays, onion skin, persistance).
- Ajouter des docstrings et commentaires pour clarifier l'intention des méthodes.
- Remplacer les `try/except` génériques par des exceptions spécifiques avec logging.
- Introduire des tests unitaires ou d'intégration pour les fonctionnalités clés.
