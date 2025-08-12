# Revue de code : ui/zoomable_view.py

## Observations Générales
- Classe `ZoomableView` dérivée de `QGraphicsView` offrant zoom, drag & drop et superpositions d'outils.
- Code structuré mais volumineux, mélangeant construction d'UI et logique d'interaction.

## Points Positifs
- Utilisation de signaux dédiés (`zoom_requested`, `item_dropped`, etc.) pour découpler la vue du reste de l'application.
- Gestion de nombreux événements utilisateurs (souris, drag & drop, molette) avec prise en charge des modifiers.

## Problèmes Identifiés
1. Absence de docstrings sur la classe et la majorité des méthodes, rendant la compréhension difficile.
2. Méthodes `_build_overlay` et `_build_main_tools_overlay` très longues ; pourraient être factorisées en sous-fonctions.
3. `make_btn` interne dans `_build_overlay` et `_build_main_tools_overlay` crée des closures répétitives ; extraction possible.
4. Gestion d'erreurs génériques dans `dropEvent` (`except Exception`).
5. Aucun test automatisé pour ce composant malgré une logique complexe.

## Recommandations
- Ajouter des docstrings et commentaires pour expliquer la finalité de chaque méthode.
- Refactoriser la construction des overlays en composants réutilisables ou fonctions externes.
- Spécifier les exceptions attendues lors du parsing JSON dans `dropEvent`.
- Introduire des tests (unitaires ou d'intégration) pour valider le comportement des interactions principales.
