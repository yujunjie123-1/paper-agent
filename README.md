# AI Diagram Factory

`ai-diagram-factory` is a manifest-driven batch tool for making academic and AI-industry diagrams from text specs or Codex-interpreted reference images.

It coordinates these backends:

- `cli-anything-plotneuralnet` for 3D CNN / stacked feature-map sources.
- `cli-anything-drawio` for flowcharts, system architecture diagrams, and complex block topologies.
- Graphviz `.dot` for probabilistic graph models and node-link computation graphs.
- TikZ-style `.tex` templates for LSTM / gated cell diagrams.
- A Python/Pillow fallback renderer so PNG previews are still produced when optional desktop exporters are unavailable.

## Quick Start

Use absolute paths on Windows:

```powershell
cd E:\多软件协作\ai-diagram-factory
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m pip install -e E:\多软件协作\ai-diagram-factory
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli catalog
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli init --preset deep-learning-gallery -o E:\多软件协作\ai-diagram-factory\examples\gallery.yaml
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli render E:\多软件协作\ai-diagram-factory\examples\gallery.yaml --out-dir E:\多软件协作\ai-diagram-factory\outputs
```

Each rendered figure gets:

- a PNG preview.
- its source file, such as `.drawio`, `.tex`, `.dot`, or PlotNeuralNet project `.json`.
- a small metadata JSON file describing the renderer path used.

## Workflow With Codex

Give Codex a paragraph or a reference image and ask it to create a manifest. Codex chooses the backend:

- 3D CNN / VGG / AlexNet layer stacks use `plotneuralnet_cnn`.
- Complex flat architectures, training flows, and multi-branch systems use `drawio_architecture` or `drawio_flow`.
- LSTM, GRU, gated cells, and formula-heavy unit diagrams use `tikz_lstm`.
- Probabilistic graphical models, computation graphs, trees, and node-link networks use `graphviz_graph`.

Then render the manifest:

```powershell
C:\Users\86180\AppData\Local\Programs\Python\Python312\python.exe -m ai_diagram_factory.cli render ABSOLUTE_MANIFEST_PATH --out-dir ABSOLUTE_OUTPUT_DIR
```

Use `catalog` to see supported diagram kinds and detected backends.
