# Revue de code : ui/timeline_widget.py

## Aperçu
Widget de timeline personnalisé avec dessin manuel des ticks, keyframes et contrôle de lecture.

## Points positifs
- Code bien structuré avec constantes regroupées en tête de fichier.
- Gestion complète des interactions utilisateur (souris, clavier, zoom).
- Émission de signaux clairs pour communiquer avec le reste de l'application.

## Points à améliorer
- Méthodes de dessin et de gestion d'événements très denses (`paintEvent`, `mouseMoveEvent`).
- Quelques conversions implicites et calculs magiques (ex: `steps * 0.1`).
- Pas de docstrings pour les méthodes privées.

## Suggestions
- Factoriser les parties de dessin (ticks, playhead, HUD) en sous-fonctions pour améliorer la lisibilité.
- Documenter les formules de conversion pixel/frame pour faciliter la maintenance.
- Envisager l'internationalisation des libellés (boutons, infobulles).
