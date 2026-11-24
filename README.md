# Beam Designer

Desktop beam analysis app built with Python and Tkinter.

## Launch

Run from this directory:

```powershell
python main.py
```

The app opens to a 40 ft simply supported W12x26 with a downward 1 kip/ft
full-span load. At 40 ft this example exceeds both displayed checks; the
20 ft version remains the reference calculation in `spec.md`.

## Files

- `main.py` builds the Tkinter interface and connects inputs to analysis.
- `beam_analysis.py` validates loads and calculates reactions, diagrams,
  deflection, maxima, and check results.
- `member_data.py` contains the section and material property values and their
  stated assumptions.
- `diagrams.py` draws the beam and response diagrams on Tkinter canvases.
- `beam_io.py` validates and saves/loads versioned `.beam.json` files.
- `beam_csv.py` exports sampled beam response data to Excel-friendly CSV.
- `beam_pdf.py` writes the print-ready vector calculation sheet as PDF.

## Save and open

Use **File → Save** to choose a `.beam.json` file the first time; subsequent
Save commands update that file. Use **File → Open** to load a saved beam.
Ctrl+S and Ctrl+O are available as shortcuts. The file stores the support,
span, member selection, L/360 policy, and all point and uniform loads. Analysis
results are recalculated when a file opens. The app prompts before discarding
unsaved edits.

## Export results

Use the **Export results CSV** button on the right side of the Results summary
panel. The app recalculates current inputs, then saves `x`, shear, moment, and
downward-positive deflection values with units in the column headers. Interior
point loads have two rows at the same x coordinate, marked left and right, to
show the shear jump. The UTF-8 CSV opens in Excel.

## Export report PDF

Use **Export report PDF** beside the CSV button in the Results summary panel.
The app recalculates the current inputs and saves a landscape Letter sheet with
the beam/member inputs and load schedule first, followed by the diagrams,
reactions, maxima, properties, and separate checks. Longer load schedules are
paginated without dropping loads. The PDF is generated with the standard
library and labels the analysis as preliminary.

## Assumptions

This is an educational, single-span Euler-Bernoulli beam model. It does not
apply load combinations or member self-weight, and it does not check shear
strength, bearing, buckling, lateral stability, or other design requirements.
Steel allowable bending stress is the app's simplified `0.66 Fy` reference.
Wood properties use baseline No. 2 reference values without size-specific,
duration, wet-service, or other NDS adjustments. Neither is a complete design
check.

## Property references

- Steel section properties: [AISC Shapes Database v16.0](https://www.aisc.org/aisc/publications/steel-construction-manual/shapes-database-v160/).
- Lumber reference properties: [American Wood Council 2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/), dimension-lumber tables 4A and 4B.
