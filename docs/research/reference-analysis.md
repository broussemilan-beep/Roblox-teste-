# Reference study: a 11.5 s Roblox TikTok animation (user-supplied screen recording)

Source: a phone screen recording of a TikTok post ("Short animation bc i was bored", account `dayume`, Roblox
animation hashtags). It is **not** redistributed here: only measurements and written observations. The author's
choreography is not copied; the *craft techniques* are what we reproduce.

Method: ffmpeg crop of the video band (882 x 364 px inside the 888 x 1920 recording), 60 fps -> frame-difference
analysis (`measured`), then every frame at 30 fps viewed on contact sheets (`observed`). `inferred` = my reading.

## What the models are (the user's point)

Plain Roblox characters: a white R6 dummy and a black-clothed avatar with hat, long white hair and a coat with tails
(accessories, with cloth/hair secondary motion). **The level comes from the animation, camera and effects, not the
modelling.** The monochrome palette (black / white / grey grid floor) is one accent colour (cyan) away from
looking "designed".

## Measured

* 346 frames at 30 fps (the recording duplicates frames to 60 Hz: 278 of 326 pose-update gaps are exactly 2 frames).
  So the piece is animated **at 30 fps, with every pose, camera and effect on the same clock**.
* Shot lengths (at 30 fps) are extremely uneven: runs of 1-2 frame shots in the lightning storm and the last strike,
  against holds of 10-34 frames (macro close-ups, the smirk, the final hold ~58 frames).
* Only ~11% of pose updates are 1 video frame apart on the 60 Hz timeline (VFX and camera whips); the rest advance every video frame.

## Observed timeline (frame numbers at 30 fps)

| frames | what happens | technique |
|---|---|---|
| 0-10 | crouched, gathering, hat and coat tails drifting | 11-frame anticipation, secondary motion always alive |
| 11-12 | three tall black ink ellipses on the character | "ink slice multiples" = the dash smear |
| 13-18 | **empty stage** (a thin vertical line, dust), dummy walks in | blink cut: the travel is never shown |
| 19-23 | contact: body stretched flat, a thick tapered black brush arc behind it, black speed line, white comic star on the dummy, thin white wind arcs | extreme contact pose + ink smear + star + air arcs |
| 24-58 | ~6 more contacts: kick with a fan of white speed streaks, cartwheel/ball spin with a broad ink arc, dummy tumbling like a stiff board, dummy ghost copies along a streak | variety of silhouettes; reactions are rigid and large |
| 59-74 | whip-in to a macro close-up of coat and a white block, ragged grey shards overlaid, then a slow drift | camera lunge + 16-frame hold |
| 75-95 | ground-level camera, spin kick, ink arcs + glassy white shards, dummy launched out of frame | low angle, negative space |
| 96-131 | juggle: dummy alternates 2-3 poses every 3-4 frames while faint ink swirls persist | **pose-cycle loop** for a machine-gun combo |
| 137-138 | a long black brush streak across the whole frame + comic star | graphic punctuation |
| 144-164 | lull: character slides to the frame edge and coils (20 frames) | anticipation before the payoff |
| 165-168 | **manga impact frame**: pure black/white shards (red/orange/yellow hatching on the face in the last frames) | 4 frames |
| 169-178 | smirk close-up with glasses and a speech bubble, held | acting beat |
| 179-194 | aerial shot against clouds, character leaps up | sky background change |
| 195-228 | **slash storm**: dozens of thick white brush strokes with cyan glow, re-posed every frame (~5 distinct layouts) | 34 frames, ends in a white-out |
| 229-254 | strokes thin out; hat close-up with micro-motion | decay, then a 16-frame hold |
| 255-260 | white comic spikes (2f), **black (2f)**, a 4-point star glint on black (1f), reveal | blink rhythm |
| 264-281 | slow push-in on the coat sweeping over the dummy | quiet beat |
| 282-286 | black, a white diagonal slash, second b/w impact frame (3f) | |
| 287-345 | final macro hold (~2 s) | |

## Rules we derive (all `inferred` from the above unless marked)

1. **Pace as contrast**: bursts of 1-4 frame shots next to holds of 10-30 frames. Never uniform.
2. **Never show the travel**: hide dashes behind slices + an empty-stage blink (`measured`: 6 empty frames).
3. **Cut to the contact**: the strike enters on its most extreme pose, with the smear already drawn.
4. **Every hit gets 4 layers**: star, tapered ink/brush smear on the limb path, speed streaks, thin air arcs.
5. **Rigid, large reactions** for the victim (a board tumbling), rather than limp ragdoll limbs.
6. **Reuse poses**: a 2-3 pose cycle at 7-8 Hz plus persistent smear swirls reads as a flurry (`observed` 36 frames).
7. **Camera**: wide static for readability, macro whip-ins with shard overlays, ground-level and sky shots, negative space.
8. **Impact frames and black frames** are punctuation: 4f b/w, 2f black, 1f star glint, then the reveal.
9. **Acting beat**: a held close-up (10 frames) of the face between action blocks.
10. **Secondary motion** (hair, hat, coat tails) never stops, even in holds.
11. **One accent colour** (cyan) for the big move; red/orange only inside the impact frame.
12. **Animate on a 30 fps clock** (poses, camera, effects together).

What we cannot see in the recording: the rig (R6 vs R15 for the avatar), the tools used, the camera data. These
are `unverified`.
