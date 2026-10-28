# Audit R&D (2026-10-28): vérification de l'audit reçu, et ce qu'on en fait

Source de départ : un « audit R&D » collé par l'utilisateur (RigBridge, Staticaliza, Roqer, Willikk Mesh VFX, docs Roblox, RoClicks,
Motion Tools, frex…). Son dernier chapitre (« le nouveau prompt ») n'était pas dans le message : cet audit-ci en tient lieu.

Méthode : métadonnées GitHub (existence, licence, étoiles, dates) + lecture des pages/README/docs par un lecteur web, jamais de mémoire.
Étiquettes : **[vérifié]** lu sur la page citée, **[métadonnées]** vu seulement dans la fiche GitHub, **[non trouvé]** introuvable,
**[non vérifié]** affirmé par l'audit sans source retrouvée, **[inféré]** ma lecture.

## 1. Verdict en cinq lignes

1. Les dépôts principaux existent, mais **presque tous sont très récents ou confidentiels** (RigBridge : 0 étoile, 1 commit, créé le 16/08/2026).
2. **Licences : seules les briques MIT sont copiables** (Willikk, RoClicks, Chrrxs/robloxstudio-mcp). RigBridge et Motion Tools n'ont **aucune licence** (idées seulement) ; Staticaliza est **GPL-3.0+**, Roqer **AGPL-3.0+** (idées seulement, sauf à publier sous la même licence).
3. Deux affirmations de l'audit sont **plus faibles que présentées** : le piège « MeshPart transparent » (documenté pour Decals/Textures, pas nommément pour particules/Trails/Beams) et « AnimationConstraint remplace Motor6D » (rien de tel dans les pages lues).
4. Un fait Roblox **vérifié** change notre architecture : les modifications de `Motor6D.Transform` doivent se faire sur `RunService.PreSimulation`, sinon l'Animator les écrase à l'image suivante.
5. Ce qui manque encore est surtout **côté jeu** (faux membre, interruptions, réplication, mobile) : ça ne peut pas être validé hors Studio ; plan de test au §6.

## 2. Vérification, affirmation par affirmation

| Affirmation de l'audit | Verdict | Détail et source |
|---|---|---|
| RigBridge : Claude pilote un rig Roblox dans Blender, poses, keyframes, aperçus, export KeyframeSequence | **[vérifié]** | github.com/chaseMckenzie88/rigbridge : outils `set_pose`, `get_pose`, `render_preview`, `export_animation`, `publish_animation`, `build_rig` (R6/R15), `run_python`… ; Blender 4.1 à 5.2 |
| RigBridge mesure les décalages d'articulations à l'export | **[vérifié]** | métrique `joint_slide_studs` (« how far each joint translates from its rest socket ») ; repos < 0,02, bob du torse 0,1-0,2 normal, > 0,3 sur un membre = avertissement ; `publish_animation` refuse si le contrôle échoue (`force=true`). **Formule exacte : [non trouvé]** |
| RigBridge « pépite » | **[non vérifié]** | 0 étoile, 0 fork, 1 commit, aucune release, aucune licence, chemins Windows personnels, chiffres issus d'un seul rig |
| Staticaliza : onion skinning, poses, caméra, impact frames exportables en PNG | **[vérifié]** | onglets Roblox Animator / Utils / Impact ; « anime-style linework… export PNG sequences ». Comment les images servent dans Roblox : **[non trouvé]**. 2 étoiles, releases vides, GPL-3.0+ |
| Roqer : agent Studio open source, construit, teste, vérifie visuellement | **[vérifié]** | captures, playtests solo et multi-clients, logs serveur/client, profilage ; 176 étoiles, 480 commits, CI. Skill d'animation : chemin **[non trouvé]** ; VFX : démos seulement. AGPL-3.0+ |
| Willikk : timeline commune, hitstop, caméra, pooling, réseau, animation procédurale | **[vérifié] en grande partie** | skill `roblox-mesh-vfx` : `Animator` (boucle partagée), `Hitstop`, `CameraShaker`, `ScreenFlash`, `Pool`, `VFXService`, `Net`. L'animation R6 procédurale est un **autre** skill (non ouvert). MIT |
| Piège : un MeshPart transparent ne cache pas particules, Trails, Beams, Decals | **[vérifié] à moitié** | texte : « tweening only `MeshPart.Transparency` leaves Decals/Textures visible ». Particules/Trails/Beams non nommés ; seul un commentaire dit que `Fade` « fades decals/beams too » |
| RoClicks `roblox-vfx` : Emit/Build/Capture/Shapes, textures, extracteur de frames | **[vérifié]** | `templates/` : `Emit.luau`, `Build.luau`, `Capture.luau`, `Shapes.luau` ; `scripts/` : `vfxtex.py` (textures numpy), `clip_frames.py` (clip → planche étiquetée + table temps/luminosité/couleur, ffmpeg), `vfxblender.py`, `bundle_runtime.py`. MIT. **Cadence d'échantillonnage de `clip_frames.py` : [non trouvé]** |
| Motion Tools : éditeur, poses, courbes, export KeyframeSequence ; VFX expérimentale | **[vérifié]** | « VFX (not production-ready) » ; R6 et R15 ; R6 sans coudes/genoux articulés ; **aucune licence** |
| Docs : `Motor6D.Transform` et Animator, `PreSimulation` | **[vérifié]** | guide task-scheduler : « Motor6D transform changes should be done on the PreSimulation event. If you don't, Animators will overwrite changes on the next frame. » / « PreSimulation is the last Luau event fired before Motor6D.Transform is applied to part positions. » |
| Docs : nouvelles `AnimationConstraint` | **[vérifié] à moitié** | « aligns two base parts with an animate-able kinematic or force-based joint » ; lien avec Motor6D/Animator, rigs R15/R6, remplacement de Motor6D : **[non trouvé]** |
| Hitstop dans Roblox | **[vérifié]** | pas d'API Pause/Freeze sur `AnimationTrack` ; l'astuce documentée est `AdjustSpeed(0)` (+ `TimePosition`). Willikk fait pareil : gèle chaque piste de `GetPlayingAnimationTracks()`, mémorise `Speed`, restaure sur `PreAnimation`, **sur chaque client dans ~90 studs** ; pas de hitstop serveur |
| Réplication des animations jouées côté client | **[non trouvé]** | les pages lues ne le disent pas ; propriétés `TimePosition/Speed/IsPlaying` marquées « Not Replicated » ; un client propriétaire peut « play arbitrary animations ». **À tester en Studio multi-clients** |
| RBXMonkey (import/export Blender ↔ Roblox) | **[non trouvé]** | aucune fiche GitHub trouvée par la recherche ; cité par Staticaliza comme plugin Studio recommandé. Traiter comme **[non vérifié]** |
| frex (inspection image par image), Claude Video, Claude Video Analyzer | **[non trouvé]** | introuvables par la recherche. La limite « quelques images/s » est exacte *en principe* pour tout échantillonneur ; chez nous : `tools/eyes.py ref --fps 60` + `hot` (§4) |
| Luna Runtime, Visual Director, Lumina, VFX Editor, OpenVFX, Spark, Cinematic Animation | **[non vérifié]** | non rouverts dans cet audit (Visual Director : 404 déjà noté) |
| Studio MCP : captures, playtests, logs, profilage | **[métadonnées]** | `Roblox/studio-rust-mcp-server` (MIT, 498 étoiles, **archivé**) ; `Chrrxs/robloxstudio-mcp` (MIT, 342 étoiles, actif ; « runtime debugging, playtest control, screenshots/input, multiplayer testing, per-peer server/client eval ») ; Roqer en est un fork pour son serveur MCP |
| Dépôts « Studio bridge » à éviter | **[inféré]** | quatre dépôts créés le même jour (22/09/2026), titres « Best … 2026 », langage HTML, ~70 étoiles chacun (`mcp-forge-studio-bridge`, `roblox-studio-agent-bridge`, `studio-bridge-mcp`, `mcp-rojo-bridge`) : ressemblent à de la promotion. **Ne pas installer** sans audit |

## 3. Licences et réutilisation

| Source | Licence | Ce qu'on peut faire |
|---|---|---|
| Willikk/Roblox, zriptic/roclicks-skills, Chrrxs/robloxstudio-mcp | MIT | copier avec la notice ; **créditer** |
| chaseMckenzie88/rigbridge, yansha-os/motion-tools | aucune trouvée | **idées seulement** (sans licence, tous droits réservés) |
| Staticaliza-Blender-Animation-Tools | GPL-3.0+ | idées ; copier = notre code devient GPL |
| S4US/Roqer | AGPL-3.0+ | idées ; copier = obligations réseau AGPL |

## 4. Ce que notre chaîne fait déjà, et ce qu'on ajoute

| Besoin | État |
|---|---|
| Export fidèle (aller-retour) | **Nouveau** `tsb_engine/export_check.py` + `tools/check_export.py` : exporte en `.rbxmx`, relit le fichier, rejoue avec les règles de Roblox (Linear = `CFrame:Lerp`, FK Motor6D) et mesure l'écart en studs contre le moteur. Équivalent offline de `joint_slide_studs`, mais mesure l'écart *de rendu*, pas seulement le glissement |
| Cuts/téléportations/maintiens survivent à un export clairsemé | **Corrigé** : `keyframe_times` garde toutes les clés authored et ajoute une clé juste avant la fin d'un segment *constant*. Avant : un dash de 60 studs devenait un glissement lisse (35 studs d'erreur au pas 2) |
| Fewest keys pour une tolérance | **Nouveau** `optimize_keys` : pour le héros du court métrage, 546 clés sur 660 images à ≤ 0,05 stud (les rotations rapides exigent des clés denses ; un pas régulier de 2 donnait 0,69 stud d'erreur, de 4 donnait 3,6) |
| « Joint slide » intentionnel (déboîtement) | Mesuré à part (`dislocation`, 0,60 stud dans le court métrage) : RigBridge avertit au-delà de 0,3 parce qu'il le traite comme un défaut ; chez nous c'est un choix de style, plafonné par le linter (TSB006) |
| Analyse vidéo à haute fréquence | **Nouveau** `eyes.py hot` : repère les pics d'énergie puis sort **toutes** les images autour (pas d'échantillonnage) ; `ref --fps 60` extrait à 60 fps. Les flashs/impacts de 1-2 images ne sont plus manqués |
| Impact frames | Déjà dans le viewer (`screen_fx bw/black/glint`), jugés optionnels en jeu (contrainte « pas d'impact frame ») ; Staticaliza montre la voie « PNG en séquence » (GPL : idée seulement) |
| Pooling, nettoyage, secousse caméra | Pas de code Luau côté jeu dans ce dépôt ; à reprendre de Willikk (MIT) si on construit le runtime |

## 5. Conséquences d'architecture (faits vérifiés)

* **Offsets procéduraux** (faux membre, déboîtement, tilt) : écrire `Motor6D.Transform` dans `RunService.PreSimulation`, jamais ailleurs. [vérifié]
* **Hitstop par animation** : pas d'API de pause ; `AdjustSpeed(0)` sur chaque piste jouée, restaurer ensuite, sur **chaque client** concerné. Le hitstop est donc *par client*, pas global côté serveur. [vérifié]
* **Priorités** : `Idle 0, Movement 1, Action 2, Action2 3, Action3 4, Action4 5, Core 1000` : identiques à notre table d'export. [vérifié]
* **Marqueurs** : lus par `GetMarkerReachedSignal(nom)` ; les noms de nos marqueurs d'événement (`Hit`, `Windup`…) doivent correspondre. [vérifié] Leur création depuis un `.rbxmx` écrit à la main n'est **pas vérifiée**.
* **Effets** : l'intention (action, variante, graine) part du client, le serveur valide et rediffuse de petits enregistrements en `UnreliableRemoteEvent`, chaque client simule localement ; **ne pas répliquer les particules**. [vérifié sur Willikk, pas sur Roblox]
* **Faux membre** : masquer le membre réel, animer un substitut, restaurer : **aucun dépôt lu ne le documente**. À concevoir et tester ici.

## 6. Tests à faire dans un vrai Studio (non exécutables dans ce conteneur)

1. **Import** d'un `.rbxmx` et d'un script Luau du dépôt : l'animation joue-t-elle ? les marqueurs existent-ils ? [non vérifié depuis le début du projet]
2. **Réplication** : joueur A lance l'animation sur son Animator ; B et le serveur la voient-ils (état, `TimePosition`) ? Test à 2-3 clients.
3. **Interruption** : esquive, stun, mort, changement d'arme en plein effet ; vérifier que `Stopped`, nettoyage (Janitor/Pool) et restauration du membre se déclenchent à chaque fois.
4. **Hitstop** : attaquant, cible et spectateur voient le même gel ? la latence (mesurée) décale-t-elle les clients ?
5. **Mobile** : budget de particules/meshes/lumières avec N combattants ; profilage (microprofiler) sur un appareil bas de gamme.
6. **Outils** : un serveur MCP de Studio avec playtest multi-clients permettrait d'automatiser 2 à 4 (`Chrrxs/robloxstudio-mcp`, MIT, **à auditer avant installation** ; ne pas en brancher plusieurs en parallèle).

## 7. Backlog proposé (ordre de valeur / coût)

1. (fait) Contrôle d'aller-retour d'export + optimiseur de clés + analyse haute fréquence.
2. Module Luau de **hitstop par piste** et de **nettoyage d'effet** (inspiré de Willikk, MIT, avec crédit) + tests Studio 3 et 4.
3. Faux membre (prototype Luau + test d'interruption).
4. Si on veut Blender : s'inspirer de `joint_slide_studs` (RigBridge, idée) pour un contrôle *avant* import ; ne rien copier.
5. Runtime de lecture/blending : comparer Luna Runtime *après* l'avoir rouvert (non vérifié ici).

Rien n'est installé ni copié depuis ces dépôts dans cette étape.
