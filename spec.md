# Project specification

# Beam Designer

## Purpose
Beam Designer is a browser-based tool for exploring the behavior of a
single-span beam under point and uniform loads. Users select a simply
supported or cantilever beam, enter its span and loads, and choose a steel
W-shape or lumber size. The app displays the loaded beam and its shear,
moment, and deflection diagrams, and reports bending and deflection checks
against the specified criteria. It is intended for preliminary analysis and
learning, not as a substitute for a complete structural design. It does not
analyze continuous beams or check buckling.

## Platform
- Run directly in a modern browser as a single self-contained `index.html`
  file.
- Do not require a build step, server, package manager, or external runtime.
- Implement styling and application logic in the HTML file.

## Inputs
- Use US customary units: span and load positions in ft, point loads in kip,
  uniform loads in kip/ft, and deflection in inches.
- Select simply supported or cantilever and enter the span. Measure the span
  between supports for a simply supported beam, or from the fixed end to the
  free end for a cantilever.
- Enter one or more point loads with magnitude, direction, and position. For
  simply supported beams, measure position from the left end; for cantilevers,
  measure from the fixed end.
- Enter one or more uniform loads with intensity, direction, and start and end
  positions. Loads may cover all or part of the span.
- Select a steel W-shape or a lumber species, size, and grade. The selected
  member data must provide the section and material properties needed for the
  calculations, including section modulus, moment of inertia, elastic
  modulus, and allowable bending stress.
- Member self-weight is not added automatically; users may enter it as a
  uniform load.
- The deflection limit is fixed at L/360.

## Calculations
- Model the member as a straight, prismatic, linearly elastic Euler-Bernoulli
  beam with small deflections. Analyze the entered loads as given; do not
  apply load factors or load combinations.
- Use upward-positive loads and reactions, positive shear upward on the left
  face of a cut, positive sagging moment, and downward-positive deflection.
  Label the diagrams consistently with these sign conventions.
- Calculate support reactions from static equilibrium and calculate shear and
  moment along the span. Report the maximum absolute shear and moment and
  their locations.
- Calculate deflection using the selected member's elastic modulus and moment
  of inertia with the selected support conditions. Report the maximum
  absolute deflection and its location.
- Calculate bending stress as fb = |M|/S using the section modulus for the
  selected bending axis. Compare the maximum bending stress with the
  allowable bending stress for the selected member and grade.
- Compare the maximum absolute deflection with L/360, converting the span to
  inches for the comparison.
- Do not perform a shear-strength or bearing check; a shear diagram is not a
  shear-capacity check.

## Outputs
- Show the beam and its loads, plus shear, moment, and deflection diagrams.
  Label diagram axes, signs, and units.
- Report support reactions and the maximum absolute shear, moment, and
  deflection, including each maximum's location and units.
- Report the maximum bending stress and allowable bending stress, and the
  maximum deflection and L/360 limit, with units.
- Show a separate pass or fail result for bending and deflection.
- State clearly that shear strength and bearing are not checked.

## Look and feel
- Use a clean, professional visual style with forest green as the primary
  color and accessible contrast for text, diagrams, and status indicators.
- Organize inputs, the beam and loads, diagrams, and result summaries into a
  clear visual hierarchy, keeping the beam and diagrams prominent.
- Keep units visible in input labels and results, and use readable diagram
  axes and legends.
- Differentiate loads, supports, and check statuses with labels or symbols as
  well as color.
- Make the layout responsive for desktop and mobile while keeping diagrams
  readable.
- Clearly identify checks that are not performed.
- Place a simple, original mountain logo in the upper-right corner of the page
  header.
- Preserve the logo's proportions and provide appropriate alt text.
- Open the app with an example beam loaded.

## Validation
- Baseline: a 20 ft simply supported W12x26 with a 1 kip/ft full-span load
  has 10 kip reactions at each support, maximum absolute shear of 10 kip,
  maximum moment of 50.0 kip-ft at midspan, and maximum deflection of
  0.609 in at midspan. The L/360 limit is 0.667 in, so the deflection check
  passes. Verify bending status against the selected member's allowable
  stress.
- Hand-check a 20 ft simply supported beam with a 10 kip point load at
  midspan: each reaction is 5 kip and the maximum moment is 50 kip-ft at
  midspan.
- Hand-check a 10 ft cantilever with a 1 kip downward point load at its free
  end: the fixed-end reaction is 1 kip and the maximum absolute moment is
  10 kip-ft at the fixed end.
- Check a partial-span uniform load, multiple combined loads, and an upward
  load against independent hand calculations, including diagram signs and
  maximum locations.
- For a 30 ft simply supported beam with a 2 kip/ft uniform load from 0 to
  15 ft, verify reactions of 22.5 kip on the left and 7.5 kip on the right
  and a maximum moment of approximately 126.6 kip-ft at 11.25 ft.
- Verify bending and deflection pass and fail cases independently, reject
  invalid spans and load positions, and confirm the displayed member
  properties match their source data.

## Out of scope
Continuous beams, buckling, shear strength, and bearing.