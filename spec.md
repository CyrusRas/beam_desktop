# Project specification

# Beam Designer

## Purpose
Beam Designer is a desktop educational tool for exploring a single-span beam
under point and uniform loads. Users select a simply supported or cantilever
beam, enter its span and loads, and choose a steel W-shape or lumber size. The
app displays the loaded beam and its shear, moment, and deflection diagrams,
and reports bending and deflection checks. It is intended for preliminary
analysis and learning, not as a substitute for complete structural design. It
does not analyze continuous beams or check buckling.

## Platform
- Run as a Python Tkinter desktop application with `python main.py`.
- Use Python's standard library only; no build step, package manager, server,
  or external runtime is required.
- Keep the calculation model independent from the Tkinter interface.

## Saving and opening beam files
- Provide a File menu with Save and Open commands, plus Ctrl+S and Ctrl+O
  shortcuts.
- Save the beam inputs to a versioned UTF-8 JSON file with a `.beam.json`
  extension. Include support type, span, member type and section/material
  selection, the fixed L/360 limit policy, and every point and uniform load
  with its direction, magnitude, and position or interval.
- Store the limit as the L/360 span-ratio policy, not as a rounded inch value.
  Recalculate the displayed limit from the beam span when opening a file.
- On the first Save, show a Save dialog; later Saves update the current file.
  Open uses a file picker. Show the current file and indicate unsaved edits.
- Prompt to save, discard, or cancel before replacing a modified beam or
  closing the app. Validate a complete file before applying any of its values.
- Reject malformed JSON, unsupported file versions or member selections,
  unsupported deflection limits, and invalid spans or load positions with a
  clear error. Do not save calculated results; recalculate after opening.

## Exporting response data
- Provide an **Export results CSV** button at the right side of the Results
  summary panel. Recalculate current inputs before export; do not export stale
  results or continue when the current inputs are invalid.
- Use a Save dialog with `.csv` as the default extension and write UTF-8 CSV
  suitable for opening in Excel.
- Include `x (ft)`, `V (kip)`, `M (kip-ft)`, and downward-positive deflection
  in inches. Add a side indicator to distinguish left and right shear values
  at point loads. Use paired rows at each interior point load so the shear
  jump is represented while moment and deflection remain continuous.
- Export the analysis sample points, including span ends and load positions.

## PDF calculation sheet
- Provide an **Export report PDF** button beside the CSV export button on the
  right side of the Results summary panel. Recalculate the current inputs
  before export and stop if the inputs are invalid.
- Save a print-ready US Letter landscape PDF with the beam and member inputs
  and complete applied-load schedule at the top, followed by the loaded-beam,
  shear, moment, and deflection diagrams, support reactions, maxima and
  locations, member properties, and separate bending and deflection checks.
- Label axes, signs, units, load directions, and check statuses. Include the
  L/360 comparison and clearly state the preliminary-analysis assumptions and
  checks not performed.
- Use one page for a short load schedule. Paginate longer schedules without
  omitting loads, and keep an input summary on the analysis page.
- Generate the PDF with the Python standard library; do not add a runtime
  dependency.

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
- Select a steel W-shape or a lumber species, size, and grade. Member data
  includes section modulus, moment of inertia, elastic modulus, and allowable
  bending stress.
- Member self-weight is not added automatically; users may enter it as a
  uniform load.
- The deflection limit is fixed at L/360.
- Open with a 40 ft simply supported W12x26 and a 1 kip/ft downward full-span
  load.

## Calculations
- Model the member as a straight, prismatic, linearly elastic Euler-Bernoulli
  beam with small deflections. Analyze loads as entered; do not apply load
  factors or load combinations.
- Use upward-positive loads and reactions, positive shear upward on the left
  face of a cut, positive sagging moment, and downward-positive deflection.
  Label diagrams consistently with these sign conventions.
- Calculate support reactions from static equilibrium and calculate shear and
  moment along the span. Report maximum absolute shear and moment and their
  locations.
- Calculate deflection using the selected member's elastic modulus and
  moment of inertia with the selected support conditions. Report maximum
  absolute deflection and its location.
- Calculate bending stress as fb = |M|/S using the section modulus for the
  selected bending axis. Compare maximum bending stress with the member's
  stated allowable bending stress.
- Steel allowables use the educational approximation Fb = 0.66 Fy. Lumber
  strengths and moduli are baseline No. 2 reference values; the app does not
  apply size-specific, duration, wet-service, or other NDS adjustments. The
  application does not apply lateral-bracing factors.
- Compare maximum absolute deflection with L/360, converting span to inches.
- Do not perform a shear-strength or bearing check; the shear diagram is not a
  shear-capacity check.

## Outputs
- Show the beam and its loads, plus shear, moment, and deflection diagrams.
  Label diagram axes, signs, and units.
- Report support reactions and maximum absolute shear, moment, and deflection,
  including each maximum's location and units.
- Report maximum and allowable bending stress, and maximum deflection and the
  L/360 limit, with units.
- Show separate pass or fail results for bending and deflection.
- State clearly that shear strength and bearing are not checked.

## Look and feel
- Use a clean, professional visual style with forest green as the primary
  color and accessible contrast.
- Organize inputs, beam and loads, diagrams, and results in a clear hierarchy.
  Keep diagrams prominent and readable as the window is resized.
- Keep units visible in input labels and results, and use readable diagram
  axes and legends.
- Differentiate loads, supports, and check statuses with labels or symbols
  as well as color.
- Include a simple original mountain logo in the upper-right of the header.
- Preserve the logo's proportions and provide appropriate accessible text.
- Open the app with the example beam and load above.

## Validation
- Reference case: a 20 ft simply supported W12x26 with a 1 kip/ft full-span
  load has 10 kip reactions at each support, maximum absolute shear of 10 kip,
  maximum moment of 50.0 kip-ft at midspan, maximum deflection of about
  0.609 in at midspan, and an L/360 limit of 0.667 in. Check bending against
  the selected member's stated allowable stress.
- Hand-check a 20 ft simply supported beam with a 10 kip point load at
  midspan: each reaction is 5 kip and maximum moment is 50 kip-ft at midspan.
- Hand-check a 10 ft cantilever with a 1 kip downward point load at its free
  end: fixed-end reaction is 1 kip and maximum absolute moment is 10 kip-ft at
  the fixed end.
- Check partial-span uniform loads, multiple combined loads, and upward loads
  against independent hand calculations, including signs and maximum locations.
- For a 30 ft simply supported beam with a 2 kip/ft load from 0 to 15 ft,
  verify reactions of 22.5 kip at A and 7.5 kip at B and a maximum moment of
  about 126.6 kip-ft at 11.25 ft.
- Verify bending and deflection pass and fail cases independently, reject
  invalid spans and load positions, and confirm displayed member properties
  match their source data.
- Save and reopen steel and lumber beams with both support types, multiple
  loads, upward loads, and partial-span uniform loads. Confirm inputs and
  results round-trip, and reject malformed, unsupported, or invalid files.
- Export CSVs for simply supported and cantilever beams, checking units,
  signs, load points, duplicate-x shear jumps, and agreement with the analysis.
- Inspect exported PDFs for the example, mixed point and uniform loads, upward
  loads, and long schedules. Check layout, legibility, pagination, and that
  each reported result agrees with the analysis.

## Out of scope
Continuous beams, buckling, shear strength, bearing, lateral stability checks,
and complete code-compliant member design.
