#Audit et Refactoring de l'Architecture MVC

##Objectifs Clés

1. Réduction de la Duplication : Éliminer les doublons de code et les logiques métiers éparpillées dans les différentes couches.

2. Séparation Stricte : Rétablir une séparation claire entre les couches Modèle, Vue et Contrôleur, en adhérant aux définitions originales :

**core/ : Logique métier pure et modèles de données, sans aucune dépendance à PySide6.

**controllers/ : Orchestration des interactions, connexion des signaux et slots.

**ui/ : Implémentation de l'interface graphique et émission des signaux d'intention.

3. Amélioration de la Maintenabilité : Rendre le codebase plus facile à comprendre, à modifier et à étendre.


##Contraintes Clés

1. Respect du Plan de Répartition : Chaque fichier doit être déplacé dans le répertoire correspondant (core/, controllers/, ui/) en fonction de sa responsabilité architecturale.

2. Aucune Dépendance PySide6 dans core/ : Toute dépendance à PySide6 dans le dossier core/ doit être supprimée. La communication avec l'interface doit se faire exclusivement via des signaux et slots orchestrés par les contrôleurs.

3. Utilisation de typing.Protocol : Mettre en œuvre le typing.Protocol pour réduire le couplage entre les couches, comme recommandé dans les guidelines.md.
