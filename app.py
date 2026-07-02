import json
from itertools import islice

import networkx as nx
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow requests from your portfolio's domain

with open("graph_data.json") as f:
    DATA = json.load(f)

G = nx.Graph()
for nid, attrs in DATA["nodes"].items():
    G.add_node(int(nid), x=attrs["x"], y=attrs["y"])
for e in DATA["edges"]:
    G.add_edge(e["u"], e["v"], length=e["length"])

POIS = DATA["pois"]  # name -> node id


@app.route("/")
def index():
    return render_template("index.html", poi_names=sorted(POIS.keys()))


@app.route("/api/graph")
def api_graph():
    return jsonify({
        "nodes": DATA["nodes"],
        "edges": DATA["edges"],
        "pois": POIS,
    })


@app.route("/api/route")
def api_route():
    source = request.args.get("source")
    target = request.args.get("target")
    k = int(request.args.get("k", 3))

    if source not in POIS or target not in POIS:
        return jsonify({"error": "Unknown source or target POI"}), 400

    src, dst = POIS[source], POIS[target]
    if not nx.has_path(G, src, dst):
        return jsonify({"error": f"No path between {source} and {target}"}), 404

    paths_gen = nx.shortest_simple_paths(G, src, dst, weight="length")
    paths = list(islice(paths_gen, k))

    out = []
    for p in paths:
        coords = [{"x": G.nodes[n]["x"], "y": G.nodes[n]["y"]} for n in p]
        total = sum(G.edges[u, v]["length"] for u, v in zip(p, p[1:]))
        out.append({"nodes": p, "coords": coords, "length_m": round(total, 1)})

    return jsonify({"source": source, "target": target, "paths": out})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
