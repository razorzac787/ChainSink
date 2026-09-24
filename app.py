import os
import json
import requests
import networkx as nx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
SEED_SCAM_ADDRESS = "0x5026F006B85729a8b14553FAe312930261E1b2F8"  # Real Kyber Exploit Address

def fetch_outgoing_transactions(address):
    """Fetch recent outgoing ETH transactions from Etherscan API."""
    if not ETHERSCAN_API_KEY or ETHERSCAN_API_KEY == "your_actual_etherscan_api_key_here":
        print("[!] Warning: Missing valid ETHERSCAN_API_KEY in .env file!")
        return []

    url = (
        f"https://api.etherscan.io/api"
        f"?module=account&action=txlist&address={address}"
        f"&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    )
    
    try:
        res = requests.get(url, timeout=10).json()
        status = res.get("status")
        message = res.get("message")
        
        if status != "1":
            print(f"[!] Etherscan API Response for {address[:10]}... -> Status: {status}, Message: {message}")
            return []
        
        outgoing = []
        for tx in res.get("result", []):
            if tx["from"].lower() == address.lower() and tx["to"]:
                val_eth = float(tx["value"]) / 1e18
                outgoing.append({
                    "from": tx["from"],
                    "to": tx["to"],
                    "value": val_eth,
                    "hash": tx["hash"]
                })
            if len(outgoing) >= limit:
                break
        return outgoing
    except Exception as e:
        print(f"[!] API Request Error: {e}")
        return []

def calculate_dynamic_limits(tx_value, current_graph_size):
    """
    Dynamically adjusts branch limits and depth allocations upon each insertion.
    - Higher value transactions earn higher max depth limits.
    - As graph size grows, branch limit tightens to prevent combinatorial explosion.
    """
    # 1. Dynamic Depth Allocation based on Transaction Value
    if tx_value >= 10.0:
        allocated_max_depth = 4   # High-value path: explore deep
    elif tx_value >= 1.0:
        allocated_max_depth = 3   # Medium-value path
    else:
        allocated_max_depth = 2   # Low-value path: cap early

    # 2. Dynamic Branch Limit based on current Graph Node insertions
    if current_graph_size < 10:
        dynamic_branch_limit = 5  # Wide search during early graph discovery
    elif current_graph_size < 30:
        dynamic_branch_limit = 3  # Moderate branching
    else:
        dynamic_branch_limit = 2  # Strict branching when graph gets dense

    return allocated_max_depth, dynamic_branch_limit


def build_multihop_graph(seed_address, initial_max_depth=3):
    """BFS Traversal Engine with Dynamic Depth and Branch Scaling on Insertions."""
    G = nx.DiGraph()
    # Queue stores: (address, current_depth, path_value, dynamic_max_depth_limit)
    queue = [(seed_address, 0, 1000.0, initial_max_depth)]
    visited = set()

    print(f"[+] Starting Dynamic Multi-Hop Traversal for Seed: {seed_address}")

    while queue:
        curr_addr, depth, incoming_val, current_max_depth = queue.pop(0)
        
        if depth >= current_max_depth or curr_addr in visited:
            continue
            
        visited.add(curr_addr)
        print(f" -> Tracing Hop {depth}/{current_max_depth} for {curr_addr[:10]}... (Incoming Val: {incoming_val:.2f} ETH)")
        
        # Fetch outgoing transactions
        all_txs = fetch_outgoing_transactions(curr_addr)
        
        # Sort transactions by value descending so top flows get processed first
        all_txs.sort(key=lambda x: x["value"], reverse=True)

        # Get dynamic branch limit based on current total inserted nodes in graph
        _, dynamic_branch_limit = calculate_dynamic_limits(incoming_val, len(G.nodes))
        
        # Filter down to top N dynamic branches
        selected_txs = all_txs[:dynamic_branch_limit]

        for tx in selected_txs:
            src, dst, val = tx["from"], tx["to"], tx["value"]
            
            # Calculate dynamic max depth for this specific outgoing edge
            edge_max_depth, _ = calculate_dynamic_limits(val, len(G.nodes))

            G.add_node(src, depth=depth)
            G.add_node(dst, depth=depth + 1)
            G.add_edge(src, dst, weight=val)

            # Insert into queue with its dynamically assigned depth limit
            if dst not in visited and (depth + 1) < edge_max_depth:
                queue.append((dst, depth + 1, val, edge_max_depth))

    # Fallback protection if API returns no nodes
    if len(G.nodes) == 0:
        print("[!] Live API returned 0 transfers. Injecting sample multi-hop nodes for demo preview...")
        G.add_node(seed_address, depth=0)
        mock_hop1 = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
        mock_hop2 = "0x28C6c06298d514Db089934071355E5743bf21d60"
        G.add_node(mock_hop1, depth=1)
        G.add_node(mock_hop2, depth=2)
        G.add_edge(seed_address, mock_hop1, weight=12.5)
        G.add_edge(mock_hop1, mock_hop2, weight=12.0)

    return G

def render_standalone_html(nx_graph, output_file="fund_flow_graph.html"):
    """Export a clean, self-contained HTML graph using Vis.js directly."""
    nodes = []
    for node, attrs in nx_graph.nodes(data=True):
        is_seed = attrs.get("depth") == 0
        depth = attrs.get("depth", 1)
        nodes.append({
            "id": node,
            "label": f"{node[:6]}...{node[-4:]}",
            "title": f"Address: {node}<br>Hop Depth: {depth}",
            "color": "#FF4B4B" if is_seed else ("#FFC107" if depth == 1 else "#00C0F2"),
            "size": 28 if is_seed else 18
        })

    edges = []
    for src, dst, attrs in nx_graph.edges(data=True):
        val = attrs.get("weight", 0)
        edges.append({
            "from": src,
            "to": dst,
            "title": f"Transfer: {val:.4f} ETH",
            "arrows": "to",
            "color": {"color": "#848484"}
        })

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>ChainSink - Multi-Hop Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{ margin: 0; padding: 0; background-color: #111111; color: white; font-family: sans-serif; }}
        #network {{ width: 100vw; height: 100vh; }}
        #info {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); padding: 12px; border-radius: 8px; border: 1px solid #333; }}
    </style>
</head>
<body>
    <div id="info">
        <h3 style="margin:0 0 8px 0; color:#FF4B4B;">ChainSink Multi-Hop Tracer</h3>
        <p style="margin:0; font-size:12px;">🔴 Seed Scam Node | 🟡 Hop 1 Node | 🔵 Hop 2 Node</p>
    </div>
    <div id="network"></div>
    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            physics: {{ enabled: true, solver: 'forceAtlas2Based' }},
            nodes: {{ shape: 'dot', font: {{ color: '#ffffff' }} }},
            edges: {{ smooth: {{ type: 'continuous' }} }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>"""

    with open(output_file, "w") as f:
        f.write(html_content)
    print(f"[✓] Successfully exported interactive graph with {len(nx_graph.nodes)} nodes to: {output_file}")

if __name__ == "__main__":
    graph = build_multihop_graph(SEED_SCAM_ADDRESS)
    render_standalone_html(graph, "fund_flow_graph.html")
