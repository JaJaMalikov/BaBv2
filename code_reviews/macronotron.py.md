# Revue de code : macronotron.py

## Aperçu
Fichier d'entrée de l'application qui instancie `QApplication`, applique la feuille de style et affiche la `MainWindow`.

## Points forts
- Structure minimale et claire.
- Utilise une fonction d'application de style dédiée (`apply_stylesheet`).

## Points à améliorer
- Le module importe `logging` mais n'initialise aucune configuration.
- L'absence de fonction `main()` limite la testabilité et la réutilisation.

## Recommandations
1. Configurer un logger de base ou supprimer l'import inutile.
2. Envisager d'encapsuler la logique de démarrage dans une fonction `main()` pour faciliter les tests et l'appel externe.
