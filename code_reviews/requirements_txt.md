# Revue de code : requirements.txt

## Aperçu
Déclaration des dépendances Python du projet.

## Points positifs
- Liste concise facilitant l'installation.

## Points à améliorer
- Versions non épinglées, ce qui peut conduire à des incompatibilités futures.
- Absence de dépendances nécessaires aux tests ou au packaging éventuel.

## Suggestions
- Spécifier des versions minimales/maximum (ex: `PySide6>=6.5`).
- Ajouter les dépendances de développement ou créer un fichier `requirements-dev.txt` séparé.
