# Revue de code : ui/main_window.py

## Aperçu
Fenêtre principale orchestrant la scène, les widgets de timeline, bibliothèque, inspecteur et la gestion des pantins/objets.

## Points forts
- Centralise efficacement les interactions entre modèles et widgets.
- Utilise un `PlaybackHandler` pour déléguer la logique de lecture de la timeline.
- Mise en place d'overlays modulaires pour la bibliothèque et l'inspecteur.

## Points à améliorer
- Fichier très volumineux (>1000 lignes) rendant la maintenance difficile.
- Certaines méthodes dépassent largement la taille recommandée et mélangent logique UI et métier.
- Usage répété de blocs try/except vides qui masquent des erreurs potentielles.

## Recommandations
1. Refactoriser en sous-modules ou classes dédiées (gestion du fond, onion skin, import/export…).
2. Ajouter des docstrings et commenter les sections complexes pour faciliter la compréhension.
3. Limiter l'utilisation des `try/except` silencieux et journaliser clairement les erreurs.
