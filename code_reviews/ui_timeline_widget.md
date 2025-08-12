# Code Review : ui/timeline_widget.py

## Points positifs
- Widget de timeline complet avec lecture, gestion de keyframes et zoom.
- Signalisation riche (`frameChanged`, `addKeyframeClicked`, etc.) permettant l'intégration avec d'autres composants.
- Rendu personnalisé via `paintEvent` pour visualiser la timeline.

## Points d'amélioration
- Le fichier mêle UI, logique de timeline et gestion des raccourcis clavier dans une seule classe.
- Absence quasi totale de docstrings sur les méthodes privées, rendant l'algorithme difficile à appréhender.
- Certaines constantes (`RULER_H`, `TRACK_H`) pourraient être regroupées dans une configuration ou une énumération.
- Gestion manuelle des conversions coordonnées↔frames; une abstraction pourrait réduire la complexité.

## Recommandations
- Documenter les méthodes clés (`_draw_ticks`, `_frame_to_x`, `_x_to_frame`) avec des exemples.
- Envisager de séparer la logique de timeline (calculs, conversion) de la vue pour faciliter les tests.
- Ajouter des tests unitaires couvrant la navigation de frames et la manipulation de keyframes.
