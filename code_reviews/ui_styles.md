# Code Review : ui/styles.py

## Points positifs
- Centralisation du thème via une feuille de style exhaustive.
- Mise en place d'une fonction `apply_stylesheet` pour appliquer les paramètres globaux.

## Points d'amélioration
- L'import de `QFont` manque alors qu'il est utilisé dans `apply_stylesheet`.
- Certaines règles CSS sont dupliquées (par exemple `DraggableHeader` est défini deux fois avec des styles différents).
- La constante `ICON_COLOR` n'est pas utilisée dans le fichier.

## Recommandations
- Ajouter l'import manquant et gérer le cas d'absence de police plus élégamment (logging plutôt que `print`).
- Factoriser les règles CSS répétées afin d'éviter les incohérences.
- Retirer ou utiliser `ICON_COLOR` pour éviter les constantes mortes.
