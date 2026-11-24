# AGENTS.md

## Project overview

This repository contains a browser-only Beam Designer application. The implementation is currently a single self-contained [index.html](/c:/CCE 270/beam_desktop/index.html) file; [spec.md](/c:/CCE 270/beam_desktop/spec.md) is the product specification.

The app models one-span beams under point and uniform loads and presents diagrams and capacity checks. It is for preliminary educational use, not a complete structural design.

## Working in this repository

- Preserve the existing single-file HTML/CSS/JavaScript architecture unless the user explicitly approves a build setup or framework.
- Keep changes self-contained and avoid new dependencies, package managers, build steps, or server requirements.
- Make surgical edits to `index.html` unless a task explicitly requires changing or adding a file.
- Treat `spec.md` as the requirements source. Update it only when product behavior is intentionally changed.
- Use US customary units in the interface and calculations.

## Engineering conventions

- Use upward-positive loads and reactions.
- Use positive shear as upward on the left face of a cut.
- Use positive sagging moment.
- Use downward-positive deflection.
- Model members as straight, prismatic, linearly elastic Euler-Bernoulli beams with small deflections.
- Do not apply load factors or load combinations.
- Do not add member self-weight automatically.
- Keep sign conventions consistent in calculations and diagram labels.
- Do not add shear-strength, bearing, buckling, or continuous-beam analysis unless explicitly requested.
- Use the fixed deflection limit `L/360`, with span converted to inches.

## UI and accessibility

- Maintain a clean, professional forest-green visual theme with accessible text contrast.
- Keep the beam and diagrams prominent and use clear axis labels, units, signs, and legends.
- Differentiate loads, supports, and status checks with labels or symbols in addition to color.
- Preserve responsive behavior for desktop and mobile layouts.
- Keep status results separate and clearly identify checks that are not performed.
- Preserve the original mountain logo and appropriate alt text if editing the header.

## Validation

Before completing changes:

1. Open the app in a browser and verify that it opens with an example beam.
2. Check the baseline 20 ft simply supported W12x26 beam under a 1 kip/ft full-span load:
   - reactions: 10 kip each
   - maximum absolute shear: 10 kip
   - maximum moment: 50.0 kip-ft at midspan
   - maximum deflection: approximately 0.609 in at midspan
   - L/360 limit: 0.667 in
3. Hand-check a midspan 10 kip point load on the same 20 ft simply supported beam.
4. Hand-check a 10 ft cantilever with a 1 kip downward point load at the free end.
5. Test partial-span uniform loads, combined loads, upward loads, invalid spans, and invalid load positions.
6. Verify bending and deflection pass/fail cases independently.
7. Confirm that displayed member properties match their source data.
