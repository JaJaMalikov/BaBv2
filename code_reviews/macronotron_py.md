# Revue de code : macronotron.py

## Aperçu
Point d'entrée de l'application PySide6.

## Points positifs
- Structure claire : création de `QApplication`, application du thème puis ouverture de la fenêtre principale.
- Utilise une fonction dédiée (`apply_stylesheet`) pour les styles.

## Points à améliorer
- Le module `logging` est importé mais n'est pas utilisé.
- Aucun bloc `try/except` n'encadre la création de l'application ou la boucle principale.

## Suggestions
- Supprimer l'import inutilisé ou ajouter une configuration de journalisation.
- Envisager d'entourer le lancement de la fenêtre d'un bloc de gestion d'erreurs pour capturer les exceptions au démarrage.
