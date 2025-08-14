  1. Gestion de scène et interaction avec les objets améliorées :
   * Panneau Calques/Ordre Z : Implémenter un panneau dédié (similaire à l'Inspecteur) permettant de visualiser et de réorganiser tous les objets de la scène et les pièces de marionnettes par ordre Z, via glisser-déposer. Cela offrirait un contrôle plus précis denl'empilement visuel qu'une simple spinbox.
   * Outil de regroupement/parentage : Introduire un outil d'interface utilisateur pour regrouper visuellement plusieurs objets ou parenté un objet à n'importe quelle pièce de marionnette (pas seulement la racine). Cela permettrait des objets composites et des animations plus complexes.
   * Améliorations de la sélection : Implémenter la multi-sélection avec manipulation de la boîte englobante pour la mise à l'échelle/rotation de plusieurs éléments simultanément. Ajouter une fonction "verrouiller" pour empêcher le mouvement ou la modification accidentelle d'éléments spécifiques.
   * Aperçus des ressources dans la bibliothèque : Au lieu de simples icônes, générer de petites vignettes d'aperçu des ressources SVG/image directement dans le panneau Bibliothèque pour une identification plus facile.

  2. Fonctionnalités d'animation avancées :
   * Courbes d'animation/Easing : Étendre le système d'images clés pour prendre en charge différents types d'interpolation (linéaire, ease-in, ease-out, courbes de Bézier) pour des animations plus fluides et plus expressives. Cela impliquerait de modifier StateApplier.
   * Timeline multi-pistes : Refactoriser la timeline pour prendre en charge plusieurs pistes d'animation, permettant un contrôle séparé de la position, de la rotation, de l'échelle et même de la visibilité pour chaque objet/pièce de marionnette. Cela améliorerait considérablement les flux de travail d'animation complexes.
   * Options de bouclage : Au-delà de la simple boucle, ajouter des options pour le bouclage en ping-pong ou des plages de bouclage spécifiques dans la timeline.
   * Copier/Coller des images clés : Permettre aux utilisateurs de copier et coller des images clés ou des sections d'animation sur la timeline.

  3. Exportation et sortie :
   * Exportation de séquences d'images : Implémenter une fonctionnalité pour exporter l'animation sous forme de séquence d'images PNG ou JPG, permettant aux utilisateurs de composer des vidéos dans un logiciel externe.
   * Exportation vidéo (GIF/MP4) : Intégrer une bibliothèque (par exemple, Pillow pour GIF, moviepy pour MP4) pour exporter directement l'animation sous forme de vidéo GIF ou MP4. Ce serait une fonctionnalité très demandée.

  4. Performance et optimisation :
   * Mise en cache/Optimisation SVG : Pour les marionnettes SVG complexes, explorer le pré-rendu ou la mise en cache des éléments SVG en QPixmaps pour améliorer les performances de lecture en temps réel, en particulier lors du défilement ou de l'onion skinning.
   * Mises à jour partielles de la scène : Optimiser update_scene_from_model pour ne mettre à jour que les éléments graphiques qui ont réellement changé entre les images, plutôt que d'itérer sur tous les éléments.

  5. Expérience utilisateur et finition :
   * Système Annuler/Rétablir : Implémenter une pile d'annulation/rétablissement robuste pour toutes les actions utilisateur majeures (déplacement, rotation, mise à l'échelle, ajout/suppression d'objets/images clés). C'est crucial pour toute application créative.
   * Dispositions d'interface utilisateur personnalisables : Permettre aux utilisateurs d'enregistrer et de charger des dispositions d'interface utilisateur personnalisées (positions des docks, visibilité/positions des overlays) au-delà des paramètres de base actuels.
   * Info-bulles et aide à l'écran : Améliorer les info-bulles pour tous les éléments de l'interface utilisateur et envisager d'ajouter une simple superposition d'aide à l'écran pour les nouveaux utilisateurs.
   * Internationalisation (i18n) : Préparer l'application pour plusieurs langues en externalisant toutes les chaînes visibles par l'utilisateur.

  6. Améliorations du code (au-delà du plan de refactorisation actuel) :
   * Injection de dépendances/Localisateur de services : Formaliser la façon dont les composants accèdent les uns aux autres (par exemple, MainWindow accédant à ObjectManager ou SceneController) en utilisant un modèle d'injection de dépendances plus explicite ou un localisateur de services. Cela découplerait davantage les composants et améliorerait la testabilité.
   * Bus d'événements/Système d'événements centralisé : Pour les interactions complexes, envisager un modèle de bus d'événements plus centralisé au lieu de connexions directes signal/slot, en particulier pour la communication entre composants.
   * Complétude du typage : Continuer à étendre et à affiner les annotations de type dans l'ensemble du code pour une meilleure analyse statique et une meilleure maintenabilité.
   * Couverture des tests unitaires : Augmenter la couverture des tests unitaires, en particulier pour la logique de base dans SceneModel, ObjectManager et SceneController, et pour les nouvelles fonctionnalités au fur et à mesure de leur ajout.

