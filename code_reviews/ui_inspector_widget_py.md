# Revue de code : ui/inspector_widget.py

## Aperçu
Widget d'inspection permettant de sélectionner, modifier et attacher des objets de la scène.

## Points positifs
- Interface complète pour gérer échelle, rotation, z-order et attachements.
- Utilisation cohérente des signaux/slots pour synchroniser l'état avec la scène.
- Méthodes de rafraîchissement pour garder la liste et les combos à jour.

## Points à améliorer
- Méthode `_attached_state_for_frame` complexe et peu lisible (`si` comme nom de variable, multiples retours).
- Peu de docstrings pour les méthodes privées.
- La classe devient volumineuse ; certains comportements pourraient être déplacés dans l'`ObjectManager`.

## Suggestions
- Renommer les variables pour plus de clarté (ex: `kf_indices` au lieu de `si`).
- Ajouter des docstrings ou commentaires sur les callbacks internes.
- Factoriser les opérations d'attachement/détachement pour éviter la duplication et améliorer la testabilité.
