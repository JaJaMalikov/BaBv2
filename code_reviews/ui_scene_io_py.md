# Revue de code : ui/scene_io.py

## Aperçu
Fonctions utilitaires pour exporter et importer des scènes au format JSON.

## Points positifs
- Séparation nette des opérations de sauvegarde, chargement et création de scène vierge.
- Utilisation de `logging` pour la sauvegarde et la gestion des erreurs.
- Persistance des données spécifiques aux pantins (`puppets_data`).

## Points à améliorer
- Mélange de `logging` et de `print` pour le reporting des erreurs (`import_scene`).
- Peu de validation des données importées ; un fichier corrompu peut provoquer des exceptions.
- Certaines fonctions manipulent directement l'interface (ex: ajout de keyframes) ce qui complique les tests unitaires.

## Suggestions
- Unifier le système de journalisation en remplaçant les `print` par `logging`.
- Introduire des vérifications des schémas JSON avant d'appeler `from_dict`.
- Envisager de séparer les fonctions pures (I/O) de celles qui modifient l'UI pour améliorer la testabilité.
