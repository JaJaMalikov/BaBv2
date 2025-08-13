# Revue de code: ui/actions.py

## Analyse
Centralise la création des `QAction` et la connexion des signaux UI au `MainWindow`. Facilite la gestion des actions de scène, des overlays et de la timeline.

## Recommandations
- Remplacer le type `Any` pour `win` par un protocole décrivant les méthodes utilisées.
- Séparer la création des actions et la connexion des signaux dans deux modules pour limiter la taille du fichier.
- Prévoir la localisation des libellés et des raccourcis clavier.
- Ajouter des tests sur les connexions principales pour éviter des régressions.
