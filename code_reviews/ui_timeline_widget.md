# Revue de code: ui/timeline_widget.py

## Analyse
Widget personnalisé de timeline gérant l'affichage des keyframes, la lecture et les contrôles de plage/FPS. Utilise de nombreux événements Qt pour le dessin et l'interaction.

## Recommandations
- Extraire les constantes (couleurs, tailles) dans un module dédié pour faciliter le thème.
- Scinder la classe en sous-composants (toolbar, ruler, tracks) pour réduire la taille du fichier.
- Ajouter des commentaires sur les calculs de coordonnées lors du dessin pour clarifier la logique.
- Tester les interactions clavier/souris critiques via des tests unitaires ou d'intégration.
