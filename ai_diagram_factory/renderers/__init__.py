from .drawio import render_drawio_architecture, render_drawio_flow
from .graphviz import render_graphviz_graph
from .plotneuralnet import render_plotneuralnet_cnn
from .tikz import render_tikz_attention_gate, render_tikz_lstm


RENDERERS = {
    "plotneuralnet_cnn": render_plotneuralnet_cnn,
    "drawio_flow": render_drawio_flow,
    "drawio_architecture": render_drawio_architecture,
    "graphviz_graph": render_graphviz_graph,
    "tikz_lstm": render_tikz_lstm,
    "tikz_attention_gate": render_tikz_attention_gate,
}
