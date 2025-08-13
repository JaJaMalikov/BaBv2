# Revue de code: ui/icons.py

## Analyse
Fournit une fonction de création d'icônes basée sur des SVG monochromes avec changement de couleur selon l'état (normal, hover, actif). Utilise un cache global.

## Recommandations
- Factoriser les couleurs de thème dans un fichier de configuration partagé.
- Gérer la lecture des fichiers SVG avec un bloc `try/except` pour capturer les erreurs d'I/O.
- Envisager d'exposer une API orientée objet pour les icônes afin de limiter l'utilisation d'un grand nombre de fonctions wrappers.
- Ajouter des tests pour vérifier l'existence des icônes et l'application des couleurs.
