# Revue de code: ui/scene_settings.py

## Analyse
Fournit une boîte de dialogue pour modifier la taille de la scène et met à jour les composants associés (`scene_rect`, visuels, zoom...).

## Recommandations
- Vérifier la cohérence des valeurs saisies (valeurs minimum/maximum raisonnables).
- Déplacer la logique de mise à jour dans une méthode dédiée du `MainWindow` pour centraliser la gestion de scène.
- Internationaliser les textes affichés afin de préparer la localisation.
