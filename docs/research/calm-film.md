# Film « calm » : reproduction de la 2ᵉ référence (2026-10-28)

`python tools/build_viewer.py calm` puis `node tools/render_video.js viewer/output/calm.html DIR 1 0 385 737` (386 images, 30 fps) ;
`viewer/output/calm.mp4` est le rendu encodé. **Même numérotation que la référence** : l'image N du film se compare à l'image N de `docs/research/reference-analysis-2.md`.

## Ce qui est reproduit (vérifié en regardant des planches « nous / référence » sur ~60 images)

| Images | Référence | Film |
|---|---|---|
| 0-14, 370-385 | tenue calme, même plan au début et à la fin | oui (début de face, fin de dos avec le katana) |
| 22-36 | roulade avant avec arcs blancs fins | oui (cercles blancs fins) |
| 37-47 | atterrissage accroupi, poussière | oui |
| 48-62 | macro puis flou sombre | macro oui ; flou = fumée noire (la référence a un vrai flou de mouvement) |
| 63-65, 149-150, 181-183, 257-259, 274-275 | images négatives | oui (inversion + teinte cyan/violet de l'image) |
| 66-256 | bulle de vitesse, lignes de vitesse au sol en éventail, longues diagonales, sprint en poses distinctes à chaque image, caméra qui roule, mini-anneaux | oui ; la bulle est un demi-dôme translucide avec bord clair et anneaux pointillés |
| 240-256 | le mannequin apparaît au loin, trait de visée, plongeon | oui |
| 257-281 | choc, étincelles rouges, héros roulé en bulle, accroupi à côté | oui (rouge = seule couleur chaude) |
| 306-309 | silhouette noire sur blanc ×3, puis sur rouge ×1 | oui |
| 310-341 | macro sur le sabre, éclats blancs puis rouges | composition approchante (sabre en travers, héros au-dessus, mannequin couché en bas) |
| 342-349 | le mannequin éclate en blocs | oui |
| 350-369 | course, roulé, plan haut | oui |

## Ce qui diffère (honnêtement)

* **Lumière et matières** : la référence est très sombre, avec ombres rosées et flou de mouvement ; le viewer est plat, sans flou, avec un sol plus clair.
* **Cadrages** : ils suivent la liste de plans mais pas pixel pour pixel (héros plus petit et plus centré qu'en référence, au début et à la fin).
* **Le sprint** : 10 poses de plongeon horizontal, enchaînées dans un ordre fixe (changement toutes les 2 images) ; la référence en montre 9 à 12 mais plus variées. Première version : poses tirées au hasard **et** rotation de la racine appliquée dans l'ordre X-Y-Z du monde, donc le corps basculait de côté au lieu de plonger : c'était illisible (retour de l'utilisateur : « c'est n'importe quoi »). Corrigé : `root()` utilise maintenant une attitude intrinsèque (cap, tangage, roulis), caméra latérale proche, héros qui court vers la gauche comme en référence, bulle en demi-dôme devant lui, traînée grise.
* **Le sabre** du macro est une boîte (prop), pas le maillage ; le héros n'a que le fourreau dans le dos.
* **Le contact** à 257-264 n'est pas résolu par `solver.reach_root` : héros et mannequin s'enchevêtrent plus qu'ils ne se touchent proprement.
* **Pas d'audio, pas de sous-titres, pas d'export Roblox** (non fait pour ce film).

## Lecture du film par mes propres yeux

`perception.perceive` sur nos 386 images trouve `PUNCT_NEGATIVE 63-65` (vrai) et `260-263` (décalé de 3 par rapport à 257-259) ; les négatifs de 149-150, 181-183 et 274-275 **ne sont pas vus** :
quand l'image est déjà claire (diagonales blanches), l'inversion ne se distingue plus. Le rappel du détecteur de négatifs est donc limité (3 sur 5 retrouvés sur la vidéo réelle,
2 sur 5 sur notre film), à ne pas surestimer.

## v3 : corrections après le diagnostic externe (2026-10-28)

Un diagnostic visuel externe a noté le rendu v2 à 2,5/10 en 6 points. Chaque point a été **vérifié contre les images de la référence** avant application :

| Point du diagnostic | Vérifié contre la réf ? | Décision |
|---|---|---|
| Bulle : sphère lisse à bord lumineux, **sans pointillés**, orientée dans l'axe de la course ; pas de demi-dôme au sol ni de roue plate | oui (images 96-235 : ovale lisse, centre clair, bord blanc ; seules les images 68-72 ont des hachures radiales) | **appliqué** : `bubble` v2 (dégradé Fresnel, étirée dans la direction du cap, hachures seulement les 6 premières images), anneau fin perpendiculaire, plus de pointillés |
| Aiguilles fines (30-45) derrière la bulle, pas de poutres | oui pour les aiguilles (éventail fin vers le coin bas-gauche) | **appliqué** : 35 aiguilles de 32 studs derrière la bulle ; diagonales fines |
| Aucune ligne ne passe devant le visage | **non** : la réf a une ligne blanche qui traverse le corps en 116 et 130 | **partiellement** : les diagonales évitent le héros (zone de 22 % de la hauteur), sauf mention contraire elles ne le barrent plus ; la ligne blanche traversante de la réf n'est pas reproduite |
| Caméra dans l'axe du déplacement, FOV 110-120° | **non** : toutes les images 68-252 de la réf sont des vues latérales / trois quarts bas, jamais dans l'axe | **refusé** ; la caméra reste latérale basse, mais le roll claque à chaque virage |
| Zig-zag toutes les 8-10 images, ±45° et roll ±28° en 1 image | plausible (la réf montre des inclinaisons qui changent) ; non mesuré | **appliqué** : virage net toutes les 10 images, 8 paires ±35-45°, 162 studs parcourus, roll ±22→28° qui change de signe à chaque virage |
| Leg smear au départ latéral (3 images) | non vérifié sur la réf | **appliqué** (traînée sombre + blanche sur les jambes, images 66-72) ; à contrôler |
| Impact frame blanc / silhouettes noires / éclats cyan et jaunes sur 3 images | oui (réf 257-259 : flash blanc avec taches cyan/noir/jaune) | **appliqué** : image 257 en `bw` blanc + 12 prismes cyan/jaunes + 10 éclats noirs ; cône de souffle de 30 aiguilles (260-269) ; traits noirs et blancs sur les bords des gros plans |
| Fin : dérapage 6 studs, bloc de débris, roll -22°, recul de 4 à 16-18 studs, roll 0 | oui, cohérent avec la réf 366-385 (héros qui arrive de loin, petit) | **appliqué** : 366-374 dérapage accroupi dissymétrique, bloc kické, poussière ; 375-385 il se redresse, la caméra recule de 20 à 24 studs et le roll revient à 0 |

Les consignes « Blender / lens 14 mm / Emission = 10 » du diagnostic ne s'appliquent pas à ce viewer (canvas 2D) : traduites en effets équivalents, sans moteur 3D.

### Ce qui reste faux (v3)
* La macro du sabre (310-341) est toujours dominée par des blocs du mannequin ; le rendu est loin de la photo de la réf.
* Pas de vrai flou de mouvement ni de ligne jaune au sol (la réf en a).
* Les poses du sprint sont à peine lisibles à cette distance (le héros est petit, comme en réf, mais mes poses ne sont pas aussi nettes).
* Contact du choc : toujours pas résolu avec `solver.reach_root`.

## v4 : vrai moteur de rendu (Blender / Cycles) + effets 2D composités (2026-10-28)

Retour de l'utilisateur sur v3 : « l'animation ne va pas du tout et le rendu est moche ». Deux causes de fond :

* **Rendu** : le viewer dessinait des polygones plats en 2D (pas de lumière, d'ombres, de matières, de flou). Remplacé par `bpy` (Blender 5.2 en module Python, installé dans un venv à part :
  `pip install bpy` sous Python 3.13) : `tools/render_blender.py` construit le monde 3D (sol à quadrillé et brume, ciel, soleil + lumière de contre-jour, corps en boîtes biseautées,
  maillages d'accessoires avec une matière par face, props, débris, caméra clés par image, flou de mouvement réel) ; `tools/render_layers.js` rend les effets 2D du viewer en deux calques
  transparents (monde / écran) ; `tools/composite.py` assemble, ajoute bloom + grain et applique les effets qui lisent l'image (négatif, silhouette noir/blanc + éclats cyan).
  Coût : ~13 s par image à 10 échantillons (≈ 85 min les 386 images, 4 cœurs).
* **Sprint** : je l'avais compris de travers (profil + plongeons horizontaux). Relu en grand : caméra basse **derrière/3/4 arrière**, horizon quasi de niveau (le roll de ±25° venait
  d'un diagnostic externe, absent de cette vidéo), héros accroupi qui s'éloigne le long des lignes du sol, bulle presque ronde, grand halo fantôme en retard.
  Correction : `chase_cam` (caméra qui suit le cap avec retard), poses de course accroupie, palette sombre (manches brun sombre au lieu d'orange).

Tentative d'erreur reconnue : j'avais d'abord refusé le point « caméra dans l'axe » de la fiche externe sur la foi d'images de profil ; les images 72-134 en grand lui donnent en partie raison.

### Toujours faux (v4)
* Le héros est trop petit dans sa bulle pour que ses poses se lisent ; la référence montre un corps plus grand, avec un sabre en travers du dos lisible.
* La macro du sabre (310-341) est dominée par le mannequin couché au premier plan.
* De grosses traînées blanches (tubes) apparaissent près de la caméra pendant le sprint (images ~110-130).
* Les poses sont toujours choisies à la main dans une bibliothèque de 11 poses, pas recalées image par image sur la référence.

## v5 (2026-10-28): after "ce n'est pas ce qui se passe dans la vidéo, la course est une marionnette, le suivi est bizarre"

* **Story**: the end re-read (reference-analysis-2.md §6). He runs **toward** the mannequin (side view, real gait), draws the blade during the run (the sheathed katana turns into an empty saya + a blade in the hand,
  `Attach.vis`), strikes once with the hand **solved** onto the mannequin's neck (`solver.reach_root`), and that one blow is shown three times: A 300-309 (low side + silhouettes), B 310-341 (macro, flash, red),
  C 342-355 (wide, the mannequin bursts into blocks). Before it, a second exchange (274-283): he kneels on the felled mannequin.
* **Run**: `tsb_engine/gait.py`. The sprint (72-239) is a crouched gait on the zig-zag path with an accent pose every ninth image pair; the finale run is a gait at stride speed.
* **Follow**: cameras built from the tracked reference (`chase_framed` for the sprint, `framed_cam` for the run at the mannequin); measured error 0.02-0.05 picture heights.
* **Still wrong**: the sprint's accent poses are my own, not matched to the reference silhouettes; the macro's composition is approximate; only two shots were tracked (the rest of the framing is hand-set);
  the katana in the hand has no hand/grip fit; no dust/skid animation under the feet in the run.

## v6 (2026-10-28): "copie une autre animation" - the poses are now extracted from the reference

User advice after v5: the animation is incomprehensible; copy an existing animation; when you do not know how to do something, pivot instead of scribbling.
`tsb_engine/posefit.py` + `tools/copy_poses.py`: the hero is tracked (SAM 2) and the 16 joint angles of the R6 rig are searched so that its orthographic silhouette overlaps the mask (cross-entropy search, warm-started and
pulled toward the previous image). Result files: `docs/research/reference-poses/hero_284_299.json` (run at the mannequin, mean IoU 0.77) and `hero_72_148.json` (sprint, mean IoU 0.70, min 0.37).
Used in `examples/calm.py`: 284-299 fully, 72-148 on the 58 images with IoU >= 0.62 (the others - hero tiny or hidden in the shell - fall back to the gait). Limits, said plainly:
a silhouette is ambiguous (left/right limbs swap, depth is lost); the heading and the position are ours, not copied; the body's pitch/roll depend on the view angle assumed by the fit and are damped by half;
the hero is framed 1.4x larger than the raw track in the sprint (otherwise unreadable). The strike (306-309) is still solved by hand (the black-on-white frames merge hero and mannequin in one mask).
Not done: copying the poses of the other shots (roll 22-36, crouch 37-62, approach and slam 240-283), a perspective fit, a fit that includes the hair/blade.

