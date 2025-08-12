# Revue de code : ui/zoomable_view.py

## Aperçu
Vue `QGraphicsView` personnalisée gérant le zoom, le pannement et un overlay d'outils flottant.

## Points positifs
- Séparation nette des overlays (outils de vue et outils principaux).
- Gestion du glisser-déposer pour importer des éléments depuis la bibliothèque.
- Utilisation de signaux personnalisés pour notifier le reste de l'application (zoom, handles, onion, drop…).

## Points à améliorer
- Quelques méthodes longues combinent création d'UI et logique (ex: `_build_overlay`, `_build_main_tools_overlay`).
- Pas de commentaires sur le format de `payload` reçu lors des drops.
- Variables privées créées dynamiquement (`_panning`, `_overlay`) sans initialisation explicite dans `__init__`.

## Suggestions
- Factoriser la création de boutons dans des fonctions utilitaires pour éviter la duplication.
- Documenter la structure attendue du `payload` et des signaux émis.
- Initialiser toutes les variables d'état dans le constructeur pour plus de clarté.
