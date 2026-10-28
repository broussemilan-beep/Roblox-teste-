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
* **Le sprint** : mes 11 poses se répètent ; la référence en montre 9 à 12 mais *différentes* et plus lisibles. Les poses sont tirées au hasard avec graine, pas dessinées une à une.
* **Le sabre** du macro est une boîte (prop), pas le maillage ; le héros n'a que le fourreau dans le dos.
* **Le contact** à 257-264 n'est pas résolu par `solver.reach_root` : héros et mannequin s'enchevêtrent plus qu'ils ne se touchent proprement.
* **Pas d'audio, pas de sous-titres, pas d'export Roblox** (non fait pour ce film).

## Lecture du film par mes propres yeux

`perception.perceive` sur nos 386 images trouve `PUNCT_NEGATIVE 63-65` (vrai) et `260-263` (décalé de 3 par rapport à 257-259) ; les négatifs de 149-150, 181-183 et 274-275 **ne sont pas vus** :
quand l'image est déjà claire (diagonales blanches), l'inversion ne se distingue plus. Le rappel du détecteur de négatifs est donc limité (3 sur 5 retrouvés sur la vidéo réelle,
2 sur 5 sur notre film), à ne pas surestimer.
