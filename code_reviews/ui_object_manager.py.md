# Revue de code : ui/object_manager.py

## Aperçu
Gère la création, duplication, suppression et capture d'état des objets et pantins dans la scène.

## Points forts
- Centralisation des interactions avec `SceneModel` et `QGraphicsScene`.
- Méthodes de snapshot des états des objets/pantins utiles pour les keyframes.

## Points à améliorer
- Fichier long regroupant de nombreuses responsabilités (chargement SVG, scaling, drag&drop…).
- Quelques méthodes utilisent des types `Any` ou omettent les annotations, ce qui réduit la lisibilité.
- Certaines erreurs sont simplement loggées sans retour à l'appelant, rendant le flux de contrôle implicite.

## Recommandations
1. Scinder en sous-modules (gestion des pantins, gestion des objets) pour réduire la complexité.
2. Renforcer les annotations de types et ajouter des docstrings explicites.
3. Propager les erreurs critiques vers l'interface utilisateur pour informer l'utilisateur des échecs d'import ou de création.
