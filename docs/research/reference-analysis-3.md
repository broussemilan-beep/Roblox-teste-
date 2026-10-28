# Référence n°3 : « VFX Practice Day2 » (SuisyouVFX, TikTok) - lecture et reproduction (2026-10-28)

Source : enregistrement d'écran fourni par l'utilisateur (`ScreenRecording_10-28-2026_18-58-08`), non redistribué. Portrait 1170×2532 ; la fenêtre Roblox Studio occupe les 686 pixels du bas
(y 420-1106) ; interface TikTok à droite et en haut (texte « VFX Practice Day2 ? »). 253 images à 30 fps extraites, **toutes regardées** (planches, puis gros plans sur le personnage).

## Ce que c'est
* Un **test de VFX dans Roblox Studio**, caméra **fixe** (FOV 70 par défaut, tangage ≈ 28° : l'horizon est à 83 px du haut de la fenêtre), sol gris sans grille, brume claire à l'horizon, ombre portée.
* Le personnage est le **mannequin R6 « face test »** : chaque face de chaque pièce a sa couleur - FRONT rouge (avec l'inscription), BACK bleu, RIGHT vert (« R »), LEFT orange, dessus bleu clair,
  dessous jaune ; tête ronde claire. Les couleurs disent comment chaque membre est tourné.
* L'animation est **une boucle** d'environ 5 s répétée (images 48-196, puis 200 : le personnage revient à gauche) : debout de face à gauche, charge (aura violette), dash accroupi vers la droite avec traînée de
  fumée grise, vrille avec arcs blancs fins (76), saut (124-132, l'ombre se détache), rafale d'anneaux magenta empilés (108-116), impact au sol (136-142) avec nuage de particules violettes, faisceau violet
  vers la droite (150-156), roulé / glissade, retour debout (180-196).
* Les premières images (0-10) sont un aperçu de la fin dans l'éditeur (VFX violets) avec le texte « Work in progress, not proud of the end » ; les dernières (236+) le centre de contrôle iPhone.

## Reproduction (examples/practice.py, `python tools/build_viewer.py practice`)
1. **Poses copiées, pas inventées** : `tools/copy_poses_color.py` cherche, pour chaque image, les 16 angles du rig + position + échelle dont le rendu coloré (algorithme du peintre, faces colorées) recouvre le mieux la carte
   de couleurs de l'image (score = 0,6 × IoU de silhouette + 0,4 × accord des classes de couleur). 147 images sur 149 calées, **score moyen 0,50** (min 0,18) ; 21 images (VFX violets qui teintent le rig, ou rig caché)
   sont sous 0,40 et **interpolées**.
2. **Caméra calibrée** : FOV 70, tangage 28°, distance fixée par la taille apparente du rig (29,7 px par stud en médiane -> profondeur 16,5 studs).
3. **Position dans le monde** : le point au sol du rig (pixel donné par le calage) est dé-projeté sur un plan vertical passant par ses positions debout à gauche et à droite : la hauteur de saut sort toute seule.
4. **VFX reconstruits à l'œil** : fumée grise (émetteurs sur les pieds), aura violette, anneaux blancs fins de vrille, piles d'anneaux magenta + particules, faisceau ; ombre et brume par Blender.
5. **Rendu** : Blender (Cycles), `look = "studio"`, composité avec les effets 2D (`tools/composite.py`).

## Limites (dites une fois)
Calage grossier (score 0,50) : le mouvement général et le timing sont ceux de la vidéo mais les détails des membres ne sont pas fiables ; sur les 21 images interpolées le geste est lissé.
Les VFX sont une ressemblance, pas une copie ; les teintes magenta du rig pendant les flashs ne sont pas reproduites ; la deuxième itération de la boucle (200+) n'est pas rendue ;
les inscriptions « FRONT », « BACK », « R » ne sont pas dessinées.
