# Revue de code : core/svg_loader.py

## Aperçu
Charge un fichier SVG, extrait les groupes, pivots et bounding boxes, et offre des utilitaires pour exporter des groupes ou translater des paths.

## Points forts
- Utilisation de `QSvgRenderer` pour récupérer précisément les informations géométriques.
- Méthodes claires pour extraire des groupes et pivots.

## Points à améliorer
- Gestion d'erreurs limitée : plusieurs méthodes supposent que le groupe existe.
- Les fonctions d'export et de parsing utilisent `print`/`logging` de manière mixte.
- `translate_path` repose sur une expression régulière complexe peu documentée.

## Recommandations
1. Ajouter des exceptions explicites ou des valeurs de retour claires lorsque les groupes sont absents.
2. Harmoniser la journalisation en utilisant systématiquement le module `logging`.
3. Documenter ou simplifier la logique de `translate_path` pour améliorer la maintenabilité.
