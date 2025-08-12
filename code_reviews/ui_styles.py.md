# Revue de code : ui/styles.py

## Aperçu
Contient la feuille de style globale de l'application et une fonction utilitaire pour l'appliquer.

## Points forts
- Style unifié avec variables de couleur cohérentes.
- `apply_stylesheet` simple d'utilisation.

## Points à améliorer
- Duplication de la définition `DraggableHeader` dans la feuille de style.
- L'import de `QFont` n'est pas visible dans ce module (probablement dans un autre).

## Recommandations
1. Supprimer les règles redondantes pour `DraggableHeader` afin d'éviter les conflits.
2. Vérifier la présence de l'import `QFont` dans ce module ou le référencer explicitement.
3. Ajouter un commentaire expliquant l'origine du thème pour faciliter les mises à jour.
