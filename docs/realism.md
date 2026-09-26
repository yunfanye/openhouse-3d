# Detail checklist for photorealistic house reconstruction

Use this at blockout, architectural review, material review and final delivery.
Fix the most visible structural mismatches before spending time on small props.

| Area | What to inspect | Frequent failure |
| --- | --- | --- |
| Scale and perspective | Measured anchors, eye height, lens/sensor, room proportions | Enlarging a room to compensate for a wide-angle photograph |
| Silhouette | Roof heights, rake/hip/gable lines, parapets, chimney, eaves | A polished front view with a wrong side/rear roof |
| Roof integrity | Deck coverage, intersections, outward falls, flashing, gutters | Tiles visually conceal a hole; water falls into a wall |
| Openings | Wall attachment, sill height, jamb/reveal depth, sash divisions, arch curvature | Door only fits after reducing its appliance neighbor |
| Circulation | Door leaves/hardware/swing, stair rise/headroom, furniture envelopes | Camera clips a jamb or passes through a chair |
| Permanent fixtures | Correct type, size, orientation, location and wall backing | Floating plates, incorrect vanity/window alignment |
| Surfaces | Real-world texture scale, roughness response, beveled edges, clean normals | Huge wood grain, plastic plaster, razor-sharp cabinetry |
| Glass and mirrors | Thickness, IOR, frame depth, reflective surface in front of backing | A mirror is a wooden panel; glass behaves like opaque black paint |
| Soft goods | Continuous drape, thickness, seams, plausible folds and contact | Bedding resembles stacked boards; pillows float |
| Vegetation | Individual leaf silhouettes, upper-face normals, trunks at grade, natural variation | Solid spherical canopy, brown leaf backs, trees floating over empty space |
| Lighting | Credible sky/sun, exposed fixtures, practical falloff, interior/exterior balance | Colored stucco caused by lighting mistaken for its paint color |
| Staging | Contact shadows, gravity, plausible clearances and scale | Objects near surfaces but not touching them |
| Animation | Camera speed, angular speed, focus/exposure continuity, doors | Smooth position path with abrupt aim changes |
| Temporal finish | Native/filtered pairs, disocclusion edges, reflections, windows | Noise reduction introduces faint duplicate edges |
| Delivery | All-photo coverage, truthful captions, correct audio and frame count | Beautiful video obscures unresolved architectural assumptions |

## Work at the scale visible in the output

A bevel should catch light at the expected viewing distance; its physical size
must fit the material and object. Cabinet panels and painted trim need different
edge treatment from a stone countertop. Micro-bump should perturb highlights,
not visibly deform a wall. Wood grain follows construction and board direction;
UV/mapping scale must remain consistent when an object is stretched.

Check the base-color map under neutral light and inspect roughness independently.
Normal-map strength is not a substitute for geometric depth at silhouettes.
For hero furniture, use the silhouette, seams, cushion bulge and grounding before
adding fabric weave. For plants, leaf normal direction and layered silhouettes
matter more than simply increasing triangle count.

## Measure the final camera path

Use camera world transforms after animation evaluation. Position, aim, focus and
exposure should be sampled at the delivered frame rate. For a turn, inspect angular
velocity as well as translational speed. Test the actual animated door rather than
an artificially opened static version. Raycast proximity flags near glass or trim
need inspection; a forward lens intersection is a blocking error.

## Distinguish evidence from presentation

A staged room can still preserve original fixtures and connections. Keep the
reference architecture stable unless the task explicitly changes it. For uncertain
roof junctions, concealed closets and unseen backs of rooms, document the chosen
interpretation and what measurement or photo would resolve it. High rendering
quality does not increase the evidential certainty of that interpretation.

Webster's kitchen correction preserved appliance dimensions and door locations,
then recessed the entire cabinet/appliance run and its backing. The lesson is to
model a complete assembly and its circulation envelope, not to shrink the object
that happens to obscure a camera. Its electrical correction similarly moved plates
onto actual walls instead of hiding them from the film.
