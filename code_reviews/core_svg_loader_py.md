# Revue de code : core/svg_loader.py

## Aperçu
Charge et manipule des fichiers SVG : extraction de groupes, pivots, bounding boxes et export de sous-parties.

## Points positifs
- API cohérente pour récupérer informations géométriques d'un SVG.
- Utilisation de `QSvgRenderer` et d'`ElementTree` pour combiner rendu et parsing.
- Fonction `translate_path` bien isolée pour modifier les coordonnées des `path`.

## Points à améliorer
- Peu de gestion d'erreurs lors du parsing ou de la lecture des fichiers.
- Les `print` devraient être remplacés par `logging` pour un meilleur contrôle.
- Certaines méthodes renvoient des tuples génériques sans type dédié.

## Suggestions
- Envelopper les opérations de lecture/écriture dans des blocs `try/except` pour fournir des messages d'erreur explicites.
- Remplacer les sorties console par `logging`.
- Définir des types alias pour les tuples de coordonnées afin d'améliorer la lisibilité.
