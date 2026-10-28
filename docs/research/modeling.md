# Modélisation : de vrais maillages, pas des boîtes (2026-10-28)

Demande : « en plus de tes yeux, travaille sur de la vraie modélisation ». La 2ᵉ référence a des cheveux en pointes, des lunettes, un katana (lame, garde, manche,
fourreau), une ceinture, une tête de mannequin cylindrique : rien de cela ne se fait avec des boîtes.

## Ce qui existe maintenant

| Fichier | Rôle |
|---|---|
| `tsb_engine/modeling.py` | `Mesh` (triangles + matière par face) ; `bevel_box`, `cylinder`, `cone`, `sphere`, `torus`, `lathe` (révolution d'un profil), `prism`, `sweep` (section extrudée le long d'un chemin avec effilement) ; `merge`, `transform/rotate/scale/recolor`, `volume`, `stats` ; `to_obj` + `to_mtl` (Blender / Studio *3D Importer*), `parse_obj` pour vérifier l'export |
| `tsb_engine/secondary.py` | `Attach(name, parent, mesh, offset, tilt)` : colle un maillage à une partie R6 (repère local de la partie) ; `Outfit.meshes()` |
| `tsb_engine/scene.py` | `export_viewer_data` écrit `meshes` (sommets, faces, matières) ; `Character.hide` masque une partie du preview (la tête boîte du mannequin) |
| `viewer/viewer.template.html` | affiche les maillages (une face par triangle, couleur par face, même éclairage que les boîtes) |
| `examples/ronin_model.py` | personnage original « Ronin » : cheveux en pointes (≈ 45 cônes), lunettes (sangle, verres, monture), katana (manche enroulé, garde, lame courbe effilée, fourreau laqué), harnais, ceinture, bracelets, épaulière à plaques, jambières, mannequin à tête arrondie. `python examples/ronin_model.py DIR` écrit les OBJ+MTL et les nombres de triangles |
| `examples/ronin_showcase.py` | scène `ronin_showcase` (360 images) : face, orbite, accroupi lame sortie ; `python tools/build_viewer.py ronin_showcase` |

Tout est généré par code (aucun asset de jeu copié) ; les formes s'inspirent des **traits de silhouette observés** dans la référence, pas de ses modèles.

## Chiffres (mesurés)

Environ 6 900 triangles pour l'ensemble de la tenue (cheveux 866, lunettes 832, harnais 1 344, épaulière 964, bracelet 576, jambière 768, katana fourreau 816 / nu 462,
tête de mannequin 280). Chaque pièce est sous la limite d'environ 10 000 triangles par MeshPart **citée de mémoire et non vérifiée** : à relire dans la documentation
Roblox avant tout envoi. `Mesh.stats()["roblox_ok"]` applique cette limite.

## Ce qui n'est PAS fait / non vérifié

* Aucun import réel dans Studio n'a été testé (pas de Studio ici) : les OBJ sont valides (aller-retour testé), mais l'orientation, l'échelle et la matière par face dans le *3D Importer* sont à vérifier.
* Le preview colore par face (pas de texture, pas d'UV) ; sur Roblox, une couleur par face demande une texture ou des MeshParts séparées par matière.
* La boîte `bevel_box` est lourde (192 triangles par défaut) ; un modèle de production devrait en avoir 12-48.
* Les accessoires suivent le corps rigidement (pas de physique), sauf les brins `Strand` (écharpe).
