from __future__ import annotations


def deep_learning_gallery_manifest() -> dict:
    return {
        "project": "deep_learning_gallery",
        "description": "Starter manifest covering the visual families in the reference collage.",
        "figures": [
            {
                "id": "vgg_style_cnn",
                "kind": "plotneuralnet_cnn",
                "title": "VGG / AlexNet Style 3D CNN",
                "layers": [
                    {"type": "input", "name": "Input", "shape": "224x224x3"},
                    {"type": "conv", "name": "Conv1", "shape": "224x224x64"},
                    {"type": "pool", "name": "MaxPool1", "shape": "112x112x64"},
                    {"type": "conv", "name": "Conv2", "shape": "112x112x128"},
                    {"type": "pool", "name": "MaxPool2", "shape": "56x56x128"},
                    {"type": "dense", "name": "FC", "shape": "4096"},
                    {"type": "softmax", "name": "Softmax", "shape": "1000"},
                ],
            },
            {
                "id": "multi_branch_architecture",
                "kind": "drawio_architecture",
                "title": "Multi-Branch Feature Fusion Architecture",
                "lanes": [
                    {"name": "Image Stream", "nodes": ["Input image", "CNN backbone", "Visual embedding"]},
                    {"name": "Text Stream", "nodes": ["Text tokens", "Transformer", "Semantic embedding"]},
                    {"name": "Fusion Head", "nodes": ["Concat", "Attention fusion", "Classifier"]},
                ],
                "edges": [
                    ["Input image", "CNN backbone"],
                    ["CNN backbone", "Visual embedding"],
                    ["Text tokens", "Transformer"],
                    ["Transformer", "Semantic embedding"],
                    ["Visual embedding", "Concat"],
                    ["Semantic embedding", "Concat"],
                    ["Concat", "Attention fusion"],
                    ["Attention fusion", "Classifier"],
                ],
            },
            {
                "id": "training_flow",
                "kind": "drawio_flow",
                "title": "Training Pipeline Flowchart",
                "nodes": [
                    {"id": "data", "label": "Dataset"},
                    {"id": "augment", "label": "Augmentation"},
                    {"id": "model", "label": "Model forward"},
                    {"id": "loss", "label": "Loss"},
                    {"id": "update", "label": "Backprop update"},
                    {"id": "eval", "label": "Validation"},
                ],
                "edges": [["data", "augment"], ["augment", "model"], ["model", "loss"], ["loss", "update"], ["update", "eval"]],
            },
            {
                "id": "lstm_cell",
                "kind": "tikz_lstm",
                "title": "LSTM Cell",
                "inputs": ["x_t", "h_{t-1}", "c_{t-1}"],
                "gates": ["f_t", "i_t", "o_t", "\\tilde{c}_t"],
                "outputs": ["h_t", "c_t"],
            },
            {
                "id": "probabilistic_graph",
                "kind": "graphviz_graph",
                "title": "Probabilistic Graph Model",
                "layout": "layered",
                "nodes": [
                    {"id": "x1", "label": "X1", "rank": 0},
                    {"id": "x2", "label": "X2", "rank": 0},
                    {"id": "h1", "label": "H1", "rank": 1},
                    {"id": "h2", "label": "H2", "rank": 1},
                    {"id": "z", "label": "Z", "rank": 2},
                    {"id": "y", "label": "Y", "rank": 3},
                ],
                "edges": [["x1", "h1"], ["x1", "h2"], ["x2", "h1"], ["x2", "h2"], ["h1", "z"], ["h2", "z"], ["z", "y"]],
            },
        ],
    }


def blank_manifest(project: str = "diagram_batch") -> dict:
    payload = deep_learning_gallery_manifest()
    payload["project"] = project
    payload["figures"] = []
    return payload


def reference_workflow_manifest(reference_1: str | None = None, reference_2: str | None = None) -> dict:
    return {
        "project": "reference_multisoftware_replica_workflow",
        "description": "Staged workflow: specialist tools create assets, then Draw.io master assembly controls layout, routing, labels, and final export.",
        "workflows": [
            _reference_1_workflow(reference_1),
            _reference_2_workflow(reference_2),
        ],
    }


def _reference_1_workflow(reference_image: str | None = None) -> dict:
    assembly = {
        "id": "reference_1_unet_3d_master",
        "title": "",
        "canvas": {"width": 1600, "height": 900},
        "notes": "Draw.io master owns the final composition; PlotNeuralNet and Graphviz assets remain in stages for traceability and refinement.",
        "placements": [
        ],
        "shapes": _reference_1_shapes(),
        "connectors": _reference_1_connectors(),
        "labels": _reference_1_labels(),
    }
    if reference_image:
        assembly["reference"] = {"path": reference_image, "x": 0, "y": 0, "width": 1600, "height": 900, "opacity": 0.35}
    return {
        "id": "reference_1_unet_3d_multisoftware",
        "title": "Reference 1 U-Net 3D Replica Workflow",
        "objective": "Use PlotNeuralNet for 3D convolutional feature-map language, Graphviz for dependency skeleton, and Draw.io master assembly for skip routes and final paper-style layout.",
        "planning": _reference_1_planning(),
        "workflow": [
            "Stage 1: PlotNeuralNet creates a controlled 3D CNN backbone asset.",
            "Stage 2: Graphviz records the encoder-decoder dependency skeleton.",
            "Stage 3: Draw.io master assembly imports assets, then owns long skip routes, labels, and final composition.",
        ],
        "stages": [
            {
                "id": "ref1_plotneuralnet_backbone",
                "tool": "PlotNeuralNet",
                "role": "3D encoder/decoder block style source",
                "figure": {
                    "id": "ref1_plotneuralnet_backbone",
                    "kind": "plotneuralnet_cnn",
                    "title": "3D U-Net block language",
                    "layers": [
                        {"type": "input", "name": "Input", "shape": "K"},
                        {"type": "conv", "name": "64", "shape": "64x64x64"},
                        {"type": "pool", "name": "Pool", "shape": "1/2"},
                        {"type": "conv", "name": "128", "shape": "32x32x128"},
                        {"type": "pool", "name": "Pool", "shape": "1/4"},
                        {"type": "conv", "name": "256", "shape": "16x16x256"},
                        {"type": "pool", "name": "Pool", "shape": "1/8"},
                        {"type": "conv", "name": "512", "shape": "8x8x512"},
                        {"type": "conv", "name": "Concat", "shape": "K"},
                    ],
                },
            },
            {
                "id": "ref1_dependency_graph",
                "tool": "Graphviz",
                "role": "layout skeleton for skip-connection dependencies",
                "figure": {
                    "id": "ref1_dependency_graph",
                    "kind": "graphviz_graph",
                    "title": "U-Net skip dependency skeleton",
                    "nodes": [
                        {"id": "in", "label": "K", "rank": 0},
                        {"id": "e1", "label": "64", "rank": 1},
                        {"id": "e2", "label": "128", "rank": 2},
                        {"id": "e3", "label": "256", "rank": 3},
                        {"id": "b", "label": "512", "rank": 4},
                        {"id": "d3", "label": "1/8", "rank": 3},
                        {"id": "d2", "label": "1/4", "rank": 2},
                        {"id": "d1", "label": "1/2", "rank": 1},
                        {"id": "out", "label": "K", "rank": 0},
                    ],
                    "edges": [["in", "e1"], ["e1", "e2"], ["e2", "e3"], ["e3", "b"], ["b", "d3"], ["d3", "d2"], ["d2", "d1"], ["d1", "out"], ["e1", "d1"], ["e2", "d2"], ["e3", "d3"]],
                },
            },
        ],
        "assembly": assembly,
    }


def _reference_2_workflow(reference_image: str | None = None) -> dict:
    assembly = {
        "id": "reference_2_cswf_attention_unet_master",
        "title": "",
        "canvas": {"width": 1400, "height": 980},
        "notes": "Draw.io master owns the dense topology and routed links. TikZ attention inset is imported as a staged asset.",
        "placements": [
            {"asset": "ref2_attention_gate_tikz", "x": 660, "y": 48, "width": 600, "height": 230, "opacity": 0.98},
        ],
        "shapes": _reference_2_shapes(),
        "connectors": _reference_2_connectors(),
        "labels": _reference_2_labels(),
    }
    if reference_image:
        assembly["reference"] = {"path": reference_image, "x": 0, "y": 0, "width": 1400, "height": 980, "opacity": 0.35}
    return {
        "id": "reference_2_cswf_attention_unet_multisoftware",
        "title": "Reference 2 CSWF Attention U-Net Replica Workflow",
        "objective": "Use Draw.io for the dense block topology, TikZ for the attention-gate inset, PlotNeuralNet for small 3D feature blocks, and Draw.io master assembly for routed red/blue/black connections.",
        "planning": _reference_2_planning(),
        "workflow": [
            "Stage 1: TikZ creates the attention gate inset with math-style labels.",
            "Stage 2: PlotNeuralNet creates the 3D CSWF feature-map language used inside modules.",
            "Stage 3: Graphviz records the information-flow skeleton.",
            "Stage 4: Draw.io master assembly imports the inset/assets, then owns orthogonal routing, legend, and final layout.",
        ],
        "stages": [
            {
                "id": "ref2_attention_gate_tikz",
                "tool": "TikZ",
                "role": "attention gate local inset",
                "figure": {
                    "id": "ref2_attention_gate_tikz",
                    "kind": "tikz_attention_gate",
                    "title": "",
                },
            },
            {
                "id": "ref2_cswf_plotneuralnet_asset",
                "tool": "PlotNeuralNet",
                "role": "3D feature blocks inside CSWF modules",
                "figure": {
                    "id": "ref2_cswf_plotneuralnet_asset",
                    "kind": "plotneuralnet_cnn",
                    "title": "CSWF 3D block asset",
                    "layers": [
                        {"type": "input", "name": "N", "shape": "H x W x C"},
                        {"type": "conv", "name": "Conv", "shape": "H x W x N"},
                        {"type": "conv", "name": "Fuse", "shape": "H x W x C"},
                    ],
                },
            },
            {
                "id": "ref2_flow_graph",
                "tool": "Graphviz",
                "role": "encoder-decoder information-flow skeleton",
                "figure": {
                    "id": "ref2_flow_graph",
                    "kind": "graphviz_graph",
                    "title": "CSWF Attention U-Net flow skeleton",
                    "nodes": [
                        {"id": "input", "label": "Input", "rank": 0},
                        {"id": "enc", "label": "Encoder", "rank": 1},
                        {"id": "cswf", "label": "CSWF", "rank": 2},
                        {"id": "gate", "label": "Gate", "rank": 3},
                        {"id": "dec", "label": "Decoder", "rank": 4},
                        {"id": "out", "label": "Output", "rank": 5},
                    ],
                    "edges": [["input", "enc"], ["enc", "cswf"], ["cswf", "gate"], ["gate", "dec"], ["dec", "out"], ["enc", "gate"]],
                },
            },
        ],
        "assembly": assembly,
    }


def _reference_1_planning() -> dict:
    return {
        "strategy": "Classify the figure before rendering: 3D feature slabs are specialist assets; skip routes, labels, and final alignment stay in Draw.io.",
        "components": [
            {
                "id": "ref1_reference_trace",
                "name": "locked reference underlay",
                "description": "Original image used only as a locked Draw.io tracing underlay when provided.",
                "features": ["reference", "trace", "drawio"],
            },
            {
                "id": "ref1_encoder_decoder_3d_slabs",
                "name": "thin 3D encoder-decoder feature slabs",
                "description": "Flat perspective convolution and deconvolution feature-map stacks, including K, 64, 128, 256, and 512 labels.",
                "features": ["3d", "feature map", "stack", "conv", "plotneuralnet"],
            },
            {
                "id": "ref1_skip_connection_skeleton",
                "name": "encoder-decoder dependency skeleton",
                "kind": "graphviz_graph",
                "description": "Optional dependency skeleton for skip routes before the Draw.io connector pass.",
            },
            {
                "id": "ref1_long_skip_routes",
                "name": "long teal skip routes and arrow directions",
                "description": "Connector-heavy long routes with clear arrow direction, no broken line segments, and final line-jump cleanup.",
                "features": ["drawio", "connectors", "routing", "arrow", "line jumps"],
            },
            {
                "id": "ref1_dimension_labels",
                "name": "dimension labels and output caption",
                "description": "Small K, 1/2, 1/4, 1/8, 1/16 and concatenation labels that need final manual alignment in Draw.io.",
                "features": ["drawio", "labels", "2d"],
            },
            {
                "id": "ref1_master_canvas",
                "name": "final Draw.io assembly",
                "description": "Import generated 3D assets, then assemble, align, route, and export from Draw.io.",
                "features": ["drawio", "master", "assembly", "final export"],
            },
        ],
    }


def _reference_2_planning() -> dict:
    return {
        "strategy": "Separate 2D topology from specialist assets: the dense network body and connectors are Draw.io tasks; only the inset and 3D module language are generated upstream.",
        "components": [
            {
                "id": "ref2_reference_trace",
                "name": "locked reference underlay",
                "description": "Original image used only as a locked Draw.io tracing underlay when provided.",
                "features": ["reference", "trace", "drawio"],
            },
            {
                "id": "ref2_legend",
                "name": "legend box and icons",
                "description": "Editable 2D legend, icon keys, Chinese labels, dropout squares, and connector samples.",
                "features": ["drawio", "legend", "labels", "2d"],
            },
            {
                "id": "ref2_main_unet_topology",
                "name": "main CSWF attention U-Net topology",
                "description": "Flat encoder-decoder blocks, feature stacks, dropout markers, concat bars, and U-shape topology.",
                "features": ["drawio", "2d", "topology", "architecture", "block"],
            },
            {
                "id": "ref2_routed_arrows",
                "name": "red, blue, black, and cyan routed arrows",
                "description": "Final connector routing, arrowheads, line jumps, and crossing cleanup must be done in Draw.io.",
                "features": ["drawio", "connectors", "routing", "arrow", "line jumps"],
            },
            {
                "id": "ref2_attention_gate_inset",
                "name": "attention-gate inset",
                "kind": "tikz_attention_gate",
                "description": "Math-like labels and crisp local module inset generated as a vector component.",
            },
            {
                "id": "ref2_cswf_3d_block_language",
                "name": "small 3D CSWF feature blocks",
                "description": "Perspective cube/feature-map language inside CSWF modules.",
                "features": ["3d", "feature map", "stack", "plotneuralnet"],
            },
            {
                "id": "ref2_flow_skeleton",
                "name": "information-flow skeleton",
                "kind": "graphviz_graph",
                "description": "Optional auto-layout dependency skeleton used only for planning and checking route direction.",
            },
            {
                "id": "ref2_master_canvas",
                "name": "final Draw.io assembly",
                "description": "Import specialist assets, then build editable topology, align all labels, route connectors, and export final files.",
                "features": ["drawio", "master", "assembly", "final export"],
            },
        ],
    }


def _reference_1_shapes() -> list[dict]:
    shapes = [
        {"type": "iso_block", "x": 135, "y": 455, "width": 88, "height": 280, "depth": 20, "fill": "#fee5ac", "stroke": "#8c6b35", "opacity": 0.72},
        {"type": "iso_block", "x": 340, "y": 150, "width": 82, "height": 285, "depth": 18, "fill": "#f7bf73", "stroke": "#8d6734", "stripes": 2},
        {"type": "iso_block", "x": 430, "y": 174, "width": 55, "height": 230, "depth": 15, "fill": "#e9563c", "stroke": "#9d2f29", "opacity": 0.82},
        {"type": "iso_block", "x": 510, "y": 184, "width": 68, "height": 225, "depth": 16, "fill": "#f7bf73", "stroke": "#8d6734", "stripes": 1},
        {"type": "iso_block", "x": 606, "y": 205, "width": 48, "height": 177, "depth": 14, "fill": "#e9563c", "stroke": "#9d2f29", "opacity": 0.82},
        {"type": "iso_block", "x": 660, "y": 230, "width": 70, "height": 154, "depth": 15, "fill": "#f7bf73", "stroke": "#8d6734", "stripes": 2},
        {"type": "iso_block", "x": 796, "y": 260, "width": 38, "height": 116, "depth": 12, "fill": "#e9563c", "stroke": "#9d2f29", "opacity": 0.82},
        {"type": "iso_block", "x": 890, "y": 283, "width": 76, "height": 106, "depth": 14, "fill": "#f7bf73", "stroke": "#8d6734", "stripes": 3},
        {"type": "iso_block", "x": 1084, "y": 304, "width": 34, "height": 72, "depth": 10, "fill": "#e9563c", "stroke": "#9d2f29", "opacity": 0.82},
        {"type": "iso_block", "x": 1135, "y": 316, "width": 90, "height": 62, "depth": 12, "fill": "#f7bf73", "stroke": "#8d6734", "stripes": 4},
        {"type": "iso_block", "x": 435, "y": 505, "width": 72, "height": 204, "depth": 15, "fill": "#fee5ac", "stroke": "#8c6b35", "opacity": 0.68},
        {"type": "iso_block", "x": 758, "y": 462, "width": 68, "height": 177, "depth": 14, "fill": "#fee5ac", "stroke": "#8c6b35", "opacity": 0.68},
        {"type": "iso_block", "x": 982, "y": 417, "width": 58, "height": 122, "depth": 12, "fill": "#fee5ac", "stroke": "#8c6b35", "opacity": 0.68},
        {"type": "feature_stack", "x": 1320, "y": 149, "width": 76, "height": 300, "count": 6, "step_x": 9, "step_y": -9, "fill": "#b8c2ca", "stroke": "#57606a", "opacity": 0.62},
        {"type": "feature_stack", "x": 1333, "y": 156, "width": 64, "height": 286, "count": 4, "step_x": 7, "step_y": -7, "fill": "#5d86ae", "stroke": "#1f496b", "opacity": 0.76},
        {"type": "iso_block", "x": 1492, "y": 159, "width": 76, "height": 285, "depth": 18, "fill": "#fee5ac", "stroke": "#8c6b35", "opacity": 0.68},
    ]
    return shapes


def _reference_1_connectors() -> list[dict]:
    teal = "#4f8f8a"
    return [
        {"points": [[18, 658], [190, 658]], "color": teal, "width": 2.1, "opacity": 0.75},
        {"points": [[190, 656], [645, 656], [1290, 438]], "color": teal, "width": 2.0, "opacity": 0.68},
        {"points": [[270, 522], [523, 522], [1065, 433]], "color": teal, "width": 2.0, "opacity": 0.68},
        {"points": [[520, 455], [760, 455], [1000, 390]], "color": teal, "width": 2.0, "opacity": 0.68},
        {"points": [[785, 380], [935, 380], [1114, 326]], "color": teal, "width": 2.0, "opacity": 0.68},
        {"points": [[276, 505], [442, 247]], "color": teal, "width": 2.0, "opacity": 0.72},
        {"points": [[455, 248], [492, 248]], "color": teal, "width": 2.0, "opacity": 0.72},
        {"points": [[578, 292], [610, 292]], "color": teal, "width": 2.0, "opacity": 0.72},
        {"points": [[728, 308], [796, 308]], "color": teal, "width": 2.0, "opacity": 0.72},
        {"points": [[1010, 334], [1086, 334]], "color": teal, "width": 2.0, "opacity": 0.72},
        {"points": [[1188, 346], [1262, 346]], "color": teal, "width": 1.8, "opacity": 0.70},
        {"points": [[508, 602], [769, 602]], "color": teal, "width": 2.0, "opacity": 0.70},
        {"points": [[826, 558], [1080, 558]], "color": teal, "width": 2.0, "opacity": 0.70},
        {"points": [[1038, 479], [1254, 479]], "color": teal, "width": 2.0, "opacity": 0.70},
        {"points": [[1120, 340], [1318, 339]], "color": teal, "width": 2.0, "opacity": 0.72},
        {"curve": "M 1260 450 C 1292 422 1299 398 1320 374", "points": [[1260, 450], [1320, 374]], "color": teal, "width": 2.0, "opacity": 0.68},
        {"curve": "M 1260 480 C 1299 447 1304 421 1324 395", "points": [[1260, 480], [1324, 395]], "color": teal, "width": 2.0, "opacity": 0.68},
        {"curve": "M 1260 510 C 1305 471 1312 450 1328 420", "points": [[1260, 510], [1328, 420]], "color": teal, "width": 2.0, "opacity": 0.68},
        {"points": [[1416, 339], [1490, 339]], "color": teal, "width": 2.0, "opacity": 0.72},
    ]


def _reference_1_labels() -> list[dict]:
    return [
        {"x": 137, "y": 754, "text": "K", "size": 16, "anchor": "start"},
        {"x": 354, "y": 455, "text": "64", "size": 14},
        {"x": 377, "y": 455, "text": "64", "size": 14},
        {"x": 522, "y": 428, "text": "128", "size": 14},
        {"x": 552, "y": 428, "text": "128", "size": 14},
        {"x": 669, "y": 405, "text": "256", "size": 14},
        {"x": 699, "y": 405, "text": "256", "size": 14},
        {"x": 729, "y": 405, "text": "256", "size": 14},
        {"x": 900, "y": 412, "text": "512", "size": 14},
        {"x": 969, "y": 412, "text": "512", "size": 14},
        {"x": 1038, "y": 412, "text": "512", "size": 14},
        {"x": 1118, "y": 394, "text": "1/8", "size": 13, "rotate": -55},
        {"x": 1148, "y": 399, "text": "512", "size": 13},
        {"x": 1210, "y": 399, "text": "512", "size": 13},
        {"x": 1270, "y": 399, "text": "512", "size": 13},
        {"x": 1328, "y": 399, "text": "K", "size": 13},
        {"x": 1346, "y": 388, "text": "1/16", "size": 13, "rotate": -50},
        {"x": 432, "y": 726, "text": "K", "size": 15},
        {"x": 461, "y": 706, "text": "1/2", "size": 13, "rotate": -55},
        {"x": 758, "y": 659, "text": "K", "size": 15},
        {"x": 785, "y": 637, "text": "1/4", "size": 13, "rotate": -55},
        {"x": 982, "y": 556, "text": "K", "size": 15},
        {"x": 1005, "y": 536, "text": "1/8", "size": 13, "rotate": -55},
        {"x": 1352, "y": 500, "text": "concatenation of de-", "size": 15},
        {"x": 1352, "y": 520, "text": "convolved feature maps", "size": 15},
        {"x": 1495, "y": 463, "text": "K", "size": 14},
        {"x": 1519, "y": 452, "text": "1", "size": 13, "rotate": -55},
    ]


def _reference_2_shapes() -> list[dict]:
    green = "#c7f0d7"
    pale_green = "#d7e5bd"
    concat = "#fff3c9"
    d01 = "#7442a4"
    d02 = "#18aee0"
    d03 = "#12bd5e"
    shapes: list[dict] = [
        {"type": "path", "d": "M 140 0 L 140 980", "stroke": "#bfbfbf", "stroke_width": 1.5, "dash": "10 6", "opacity": 0.85},
        {
            "type": "legend_box",
            "x": 78,
            "y": 90,
            "width": 520,
            "height": 206,
            "fill": "#ffffff",
            "stroke": "#222222",
            "stroke_width": 2,
            "items": [
                {"icon": "conv_marker", "x": 110, "y": 112, "color": "#ff2020", "label": "卷积层3×3"},
                {"icon": "conv_marker", "x": 292, "y": 112, "color": "#009b63", "label": "卷积层1×1"},
                {"icon": "square", "x": 462, "y": 112, "color": d01, "label": "Dropout 0.1"},
                {"icon": "up_marker", "x": 110, "y": 158, "label": "上采样2×2"},
                {"icon": "arrow", "x": 292, "y": 164, "color": "#ff2020", "marker": "arrow-red", "label": "跳跃连接"},
                {"icon": "square", "x": 462, "y": 158, "color": d02, "label": "Dropout 0.2"},
                {"icon": "pool_marker", "x": 110, "y": 216, "label": "池化层2×2"},
                {"icon": "square", "x": 292, "y": 216, "color": concat, "label": "拼接"},
                {"icon": "square", "x": 462, "y": 204, "color": d03, "label": "Dropout 0.3"},
                {"icon": "attention_input", "x": 110, "y": 252, "label": "注意力门输入"},
                {"icon": "attention_circle", "x": 292, "y": 252, "label": "注意力门"},
                {"icon": "square", "x": 462, "y": 244, "color": "#ffd9c2", "label": "CSWF模块"},
            ],
        },
        {"type": "feature_stack", "x": 55, "y": 426, "width": 115, "height": 118, "count": 7, "step_x": 12, "step_y": -8, "fill": pale_green, "stroke": "#222222", "opacity": 0.86},
        {"type": "feature_stack", "x": 1110, "y": 456, "width": 112, "height": 118, "count": 7, "step_x": 12, "step_y": -8, "fill": pale_green, "stroke": "#222222", "opacity": 0.86},
        {"type": "cswf_module", "x": 490, "y": 392, "width": 230, "height": 82, "scale": 1.05},
        {"type": "cswf_module", "x": 490, "y": 575, "width": 214, "height": 80, "scale": 1.0},
        {"type": "rect", "x": 552, "y": 662, "width": 54, "height": 54, "fill": "#ffd8bf", "stroke": "#222222"},
        {"type": "rect", "x": 635, "y": 762, "width": 48, "height": 38, "fill": concat, "stroke": "#222222"},
        {"type": "rect", "x": 792, "y": 762, "width": 42, "height": 38, "fill": green, "stroke": "#222222"},
        {"type": "attention_circle", "cx": 925, "cy": 447, "r": 28, "stroke": "#585858", "stroke_width": 2.2},
        {"type": "attention_circle", "cx": 810, "cy": 615, "r": 28, "stroke": "#585858", "stroke_width": 2.2},
        {"type": "attention_circle", "cx": 744, "cy": 690, "r": 28, "stroke": "#585858", "stroke_width": 2.2},
    ]

    for x, label, tag in [(226, "3", ""), (255, "16", ""), (290, "16", "")]:
        shapes.append({"type": "rect", "x": x, "y": 382, "width": 11, "height": 180, "fill": concat if x == 290 else green, "stroke": "#222222", "label": ""})
    shapes.extend(
        [
            {"type": "conv_marker", "x": 245, "y": 430, "fill": "#ff2020"},
            {"type": "conv_marker", "x": 274, "y": 430, "fill": "#ff2020"},
            {"type": "rect", "x": 274, "y": 555, "width": 13, "height": 13, "fill": d01, "stroke": "#222222"},
            {"type": "pool_marker", "x": 292, "y": 568},
        ]
    )
    for x, y, h, fill in [
        (290, 566, 94, green),
        (322, 566, 94, green),
        (372, 650, 70, green),
        (410, 650, 70, green),
        (445, 650, 70, concat),
        (500, 754, 34, green),
        (548, 754, 34, green),
        (712, 764, 36, green),
        (860, 575, 94, concat),
        (890, 566, 104, green),
        (925, 566, 104, green),
        (976, 382, 180, concat),
        (1000, 382, 180, green),
        (1040, 382, 180, green),
        (1080, 382, 180, green),
    ]:
        shapes.append({"type": "rect", "x": x, "y": y, "width": 11 if h > 40 else 13, "height": h, "fill": fill, "stroke": "#222222"})
    shapes.extend(
        [
            {"type": "conv_marker", "x": 309, "y": 606, "fill": "#ff2020"},
            {"type": "conv_marker", "x": 341, "y": 606, "fill": "#ff2020"},
            {"type": "rect", "x": 339, "y": 650, "width": 13, "height": 13, "fill": d01, "stroke": "#222222"},
            {"type": "conv_marker", "x": 391, "y": 681, "fill": "#ff2020"},
            {"type": "conv_marker", "x": 429, "y": 681, "fill": "#ff2020"},
            {"type": "rect", "x": 427, "y": 713, "width": 13, "height": 13, "fill": d02, "stroke": "#222222"},
            {"type": "pool_marker", "x": 449, "y": 735},
            {"type": "conv_marker", "x": 519, "y": 770, "fill": "#ff2020"},
            {"type": "rect", "x": 568, "y": 795, "width": 13, "height": 13, "fill": d02, "stroke": "#222222"},
            {"type": "pool_marker", "x": 565, "y": 750},
            {"type": "conv_marker", "x": 686, "y": 780, "fill": "#ff2020"},
            {"type": "rect", "x": 774, "y": 805, "width": 13, "height": 13, "fill": d03, "stroke": "#222222"},
            {"type": "pool_marker", "x": 828, "y": 748},
            {"type": "conv_marker", "x": 908, "y": 615, "fill": "#ff2020"},
            {"type": "rect", "x": 930, "y": 660, "width": 13, "height": 13, "fill": d01, "stroke": "#222222"},
            {"type": "conv_marker", "x": 1018, "y": 430, "fill": "#ff2020"},
            {"type": "conv_marker", "x": 1058, "y": 430, "fill": "#009b63"},
            {"type": "rect", "x": 1046, "y": 555, "width": 13, "height": 13, "fill": d01, "stroke": "#222222"},
        ]
    )
    return shapes


def _reference_2_connectors() -> list[dict]:
    return [
        {"points": [[168, 480], [220, 480]], "color": "#0b86d1", "width": 2.6, "marker": "arrow-blue"},
        {"points": [[300, 445], [490, 445]], "color": "#0b86d1", "width": 2.8, "marker": "arrow-blue"},
        {"points": [[720, 448], [905, 448]], "color": "#ff2020", "width": 2.8, "marker": "arrow-red"},
        {"points": [[356, 614], [490, 614]], "color": "#0b86d1", "width": 2.8, "marker": "arrow-blue"},
        {"points": [[704, 617], [810, 617]], "color": "#ff2020", "width": 2.8, "marker": "arrow-red"},
        {"points": [[460, 687], [545, 687]], "color": "#0b86d1", "width": 2.8, "marker": "arrow-blue"},
        {"points": [[606, 690], [710, 690]], "color": "#ff2020", "width": 2.4, "marker": "arrow-red"},
        {"points": [[770, 690], [812, 690]], "color": "#ff2020", "width": 2.4, "marker": "arrow-red"},
        {"points": [[565, 780], [630, 780]], "color": "#0b86d1", "width": 2.5, "marker": "arrow-blue"},
        {"points": [[735, 780], [785, 780]], "color": "#ff2020", "width": 2.3, "marker": "arrow-red"},
        {"points": [[953, 447], [985, 447]], "color": "#ff2020", "width": 2.4, "marker": "arrow-red"},
        {"points": [[985, 447], [1000, 447]], "color": "#ff2020", "width": 2.4, "marker": "arrow-red"},
        {"points": [[1094, 445], [1114, 445]], "color": "#0b86d1", "width": 2.6, "marker": "arrow-blue"},
        {"points": [[838, 615], [875, 615]], "color": "#ff2020", "width": 2.4, "marker": "arrow-red"},
        {"points": [[944, 615], [975, 615]], "color": "#ff2020", "width": 2.4, "marker": "arrow-red"},
        {"curve": "M 666 358 C 666 235 650 168 686 118", "points": [[666, 358], [686, 118]], "color": "#23aee9", "width": 2.5, "marker": "arrow-blue", "dash": "10 8"},
        {"curve": "M 300 562 C 300 600 304 640 370 650", "points": [[300, 562], [370, 650]], "color": "#6eb7cf", "width": 1.6, "marker": "arrow-blue", "opacity": 0.45},
        {"curve": "M 328 660 C 328 710 410 734 500 754", "points": [[328, 660], [500, 754]], "color": "#6eb7cf", "width": 1.6, "marker": "arrow-blue", "opacity": 0.45},
        {"curve": "M 850 690 C 850 654 858 625 872 615", "points": [[850, 690], [872, 615]], "color": "#6eb7cf", "width": 4, "marker": "arrow-blue", "opacity": 0.75},
        {"curve": "M 960 615 C 960 552 940 498 930 475", "points": [[960, 615], [930, 475]], "color": "#6eb7cf", "width": 4, "marker": "arrow-blue", "opacity": 0.75},
    ]


def _reference_2_labels() -> list[dict]:
    return [
        {"x": 230, "y": 366, "text": "3", "size": 14},
        {"x": 260, "y": 366, "text": "16", "size": 14},
        {"x": 293, "y": 366, "text": "16", "size": 14},
        {"x": 253, "y": 552, "text": "32", "size": 13},
        {"x": 325, "y": 552, "text": "32", "size": 13},
        {"x": 386, "y": 636, "text": "64", "size": 13},
        {"x": 424, "y": 636, "text": "64", "size": 13},
        {"x": 520, "y": 738, "text": "128", "size": 13},
        {"x": 560, "y": 738, "text": "128", "size": 13},
        {"x": 660, "y": 822, "text": "128+256", "size": 13},
        {"x": 646, "y": 842, "text": "256", "size": 13},
        {"x": 735, "y": 842, "text": "256", "size": 13},
        {"x": 867, "y": 558, "text": "32+64", "size": 13},
        {"x": 895, "y": 548, "text": "32", "size": 13},
        {"x": 982, "y": 366, "text": "16+32", "size": 13},
        {"x": 1006, "y": 366, "text": "16", "size": 14},
        {"x": 1046, "y": 366, "text": "16", "size": 14},
        {"x": 1086, "y": 366, "text": "1", "size": 14},
        {"x": 718, "y": 325, "text": "CSWF 3D block asset", "size": 8, "fill": "#d0d0d0"},
        {"x": 718, "y": 463, "text": "", "size": 1},
    ]
