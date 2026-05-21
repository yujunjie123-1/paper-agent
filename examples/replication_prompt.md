# Replication Prompt (for Claude)

This is the checklist I (Claude) follow when the user hands me an image or a text description and asks for a faithful replica plus editable source files.

## Step 1 - Read the input

- If it is an image, open and view it. List every visible element first: panels, blocks, arrows, dashed guides, labels, legends, colored boxes, formulas, charts.
- If it is text, list every named module, sub-step, and relationship.

## Step 2 - Decide the module count, semantically

- Do **not** split by fixed regions or a uniform grid.
- Split by **semantic modules**: each module is one self-contained subpart that a human would describe with one short sentence.
- Examples of one module: "the 3D CNN backbone", "the lower micro-grid inset", "the fully-connected output network".
- Counter-example: do **not** split the same CNN body into "left half" and "right half".
- Hard upper bound: **12 modules**. If the input genuinely has more, merge the smallest adjacent ones.
- Lower bound: 1. A trivially simple input does not need to be padded out.
- Write `module_count_rationale` explaining why N (not N-1, not N+1).

## Step 3 - Assign a backend per module

| Module looks like... | Backend |
|----------------------|---------|
| A 3D convolution stack, perspective feature-map block, VGG/AlexNet/U-Net body | `plotneuralnet` |
| Any flat 2D module: block, lane, branch sub-net, training flow, dense connector cluster, legend, labels | `drawio` |
| A gated cell, attention gate, math-rich inset that needs crisp formulas | `tikz` |
| A probabilistic graph, full-connection node mesh, computation graph, dependency tree | `graphviz` |
| A high-fidelity visual that no code generator can match (texture-heavy icon, photographic element) | `image_to_image` |

Decide once per module and write the choice into `backend`. Do not leave it ambiguous.

## Step 4 - Fill `text_inventory`, `must_notice`, `relationships`

These three lists are the omission gate. Whatever I list here must end up visible in the rendered module.

- `text_inventory`: every word, number, or symbol that appears in this module of the original.
- `must_notice`: every colored box, arrow head, dashed guide, or non-obvious visual marker.
- `relationships`: every cross-module connection that originates in this module ("red pixel maps to lower 5x5 grid").

## Step 5 - Add `box_xyxy` for image inputs

Use **reference-image pixel coordinates**, not normalized. The renderer scales them into the master canvas automatically.

## Step 6 - Provide `figure_spec` when the default would lose fidelity

The auto-generated default per backend is intentionally minimal. For an actual replica, write the backend-specific data:

- `plotneuralnet`: a `layers` array describing every Conv/Pool/Dense block with shapes.
- `drawio` (`drawio_architecture`): `lanes` array; or set `kind` to `drawio_flow` for a left-to-right pipeline with `nodes` and `edges`.
- `tikz`: keep the canonical inputs/gates/outputs unless the inset is non-standard.
- `graphviz`: explicit `nodes` and `edges` with `rank` for layered layouts.

## Step 7 - Add `global_connectors`

If two modules connect on the master (skip lines, "this maps to that" arrows, dashed guides), encode them here. Always reference module `id`s.

## Step 8 - Write the JSON, then call `replicate`

Save the plan to an absolute path under `examples/` (or wherever the user prefers). Then run:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli replicate ^
  --plan ABSOLUTE_PATH\component_plan.json ^
  --reference ABSOLUTE_PATH\source_image.png ^
  --out-dir ABSOLUTE_PATH\outputs\<run_name>
```

PNG and three source formats (`.drawio`, `.svg`, `.vsdx`) end up under `<out_dir>/<workflow_id>/deliverables/`. `tool_plan.json` records every backend decision so the user can audit before regenerating.

## Step 9 - Omission pass

Before declaring the run done:

1. Open the deliverable PNG.
2. Re-scan each `text_inventory` and `must_notice` entry from every module - confirm it is visible.
3. Confirm every `global_connector` arrow lands on its target module.
4. If a module is visibly off, only **replace that module** (rewrite its `figure_spec` and rerun `replicate`). Do not redraw the whole figure.

## Common failure modes to avoid

- Splitting one CNN body into two modules because the image is wide. -> Merge.
- Assigning `drawio` to a clearly 3D feature-map stack. -> Use `plotneuralnet`.
- Skipping `module_count_rationale`. -> Always include it.
- Forgetting to list small but critical text like "5x5" or "Subsampling". -> Put them in `text_inventory`.
- Drawing global connectors as part of a module's `figure_spec`. -> Lift them out into `global_connectors` so Draw.io owns the final routing.
