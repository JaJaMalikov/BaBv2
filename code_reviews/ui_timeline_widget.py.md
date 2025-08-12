# Revue de code : ui/timeline_widget.py

## Aperçu
Widget de timeline personnalisé permettant la navigation, l'ajout de keyframes et le contrôle de la lecture.

## Points forts
- Interface utilisateur riche avec gestion du zoom, scroll et raccourcis clavier.
- Signaux Qt bien définis pour la communication avec le reste de l'application.

## Points à améliorer
- Logique de dessin assez dense dans `paintEvent`, ce qui complique la lecture.
- Certains calculs (zoom/scroll) pourraient être extraits dans des méthodes utilitaires.
- Le widget mélange beaucoup de responsabilités (toolbar, ruler, timeline).

## Recommandations
1. Décomposer `paintEvent` et la gestion des interactions en sous-fonctions pour améliorer la clarté.
2. Documenter les formules utilisées pour la conversion frame/pixel.
3. Envisager de séparer la toolbar dans un composant distinct pour alléger le widget principal.
