# Revue de code : ui/styles.py

## Aperçu
Fournit la feuille de style Qt globale et une fonction pour l'appliquer à l'application.

## Points positifs
- Styles organisés par section (fenêtres, boutons, timeline…).
- Fonction `apply_stylesheet` simple pour appliquer les styles et la police.

## Points à améliorer
- Bloc CSS `DraggableHeader` dupliqué avec des valeurs différentes, ce qui peut créer de la confusion.
- Aucun mécanisme pour charger dynamiquement une feuille de style externe ou adapter le thème.

## Suggestions
- Supprimer le doublon dans la définition de `DraggableHeader` ou clarifier leur intention.
- Ajouter une option pour personnaliser la feuille de style via un fichier externe.
- Vérifier la présence de la police "Poppins" et fournir un fallback dans la documentation.
