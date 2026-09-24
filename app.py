import os
import json
import requests
import networkx as nx
from collections import deque
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
SEED_SCAM_ADDRESS = "0x5026f006b85729a8b14553fae312930261e1b2f8"

# Terminal Nodes (Hop Sinks / CEXs / Mixers)
KNOWN_TERMINALS = {
    "0x28c6c06298d514db089934071355e5743bf21d60": ("Binance 14", "CEX"),
    "0x0d0707963952f2a572d1264c7676757b85040f7b": ("Kraken Hot Wallet", "CEX"),
    "0x47ac0fb3f2d84898e4d9e7b4dab3c24507a6d503": ("Binance 8", "CEX"),
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": ("Tornado.Cash Router", "Mixer"),
}

def fetch_address_transfers(address):
    """Synchronous fetching of transfers via Etherscan API."""
    address = address.lower()
    base_url = "https://api.etherscan.io/api"
    transfers = []
    
    endpoints = [
        f"{base_url}?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}",
        f"{base_url}?module=account&action=txlistinternal&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}",
        f"{base_url}?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    ]

    for url in endpoints:
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("status") == "1" and isinstance(res.get("result"), list):
                for tx in res["result"]:
                    f_addr = tx.get("from", "").lower()
                    t_addr = tx.get("to", "").lower()
                    
                    if (f_addr == address or t_addr == address) and f_addr != t_addr:
                        decimals = int(tx.get("tokenDecimal", 18) or 18)
                        raw_val = float(tx.get("value", 0))
                        val = raw_val / (10 ** decimals) if raw_val > 0 else 0.0
                        
                        transfers.append({
                            "from": f_addr,
                            "to": t_addr,
                            "value": val,
                            "hash": tx.get("hash", "")
                        })
        except Exception as e:
            print(f"[!] Request Exception for {address[:8]}: {e}")

    return transfers

def build_bfs_graph(seed_address, max_depth=2, min_value=0.0):
    """Standard Breadth-First Search (BFS) Traversal using Queue."""
    G = nx.DiGraph()
    seed_address = seed_address.lower()
    
    # BFS Queue storing tuple: (current_address, current_depth)
    queue = deque([(seed_address, 0)])
    visited = set()

    G.add_node(
        seed_address, 
        depth=0, 
        label="Seed Scam Node", 
        category="Seed"
    )

    while queue:
        curr_addr, depth = queue.popleft()

        if curr_addr in visited or depth >= max_depth:
            continue

        visited.add(curr_addr)
        print(f"[+] BFS Processing: {curr_addr[:8]}... at Depth {depth}")

        transfers = fetch_address_transfers(curr_addr)

        for tx in transfers[:10]:  # Cap to prevent excessive fan-out
            src, dst, val = tx["from"], tx["to"], tx["value"]
            
            if val < min_value:
                continue

            target_node = dst if src == curr_addr else src
            dst_depth = depth + 1

            if target_node in KNOWN_TERMINALS:
                term_label, term_cat = KNOWN_TERMINALS[target_node]
                G.add_node(target_node, depth=dst_depth, label=term_label, category=term_cat)
            elif target_node not in G:
                G.add_node(
                    target_node, 
                    depth=dst_depth, 
                    label=f"Hop {dst_depth} ({target_node[:6]}...)", 
                    category=f"Hop{dst_depth}"
                )
            
            G.add_edge(src, dst, weight=val, hash=tx["hash"])

            if target_node not in visited and dst_depth < max_depth:
                queue.append((target_node, dst_depth))

    return G

def render_html_graph(G, filename="fund_flow_graph.html"):
    nodes = []
    for node, data in G.nodes(data=True):
        depth = data.get("depth", 0)
        label = data.get("label", f"{node[:6]}...{node[-4:]}")
        
        if depth == 0:
            color = "#FF4B4B"
        elif depth == 1:
            color = "#FFC107"
        elif depth == 2:
            color = "#00C0F2"
        else:
            color = "#00E676"

        nodes.append({
            "id": node,
            "label": f"{label}\n({node[:6]}...{node[-4:]})",
            "title": f"Address: {node}<br>Hop Depth: {depth}",
            "color": color,
            "size": 26 if depth == 0 else 16
        })

    edges = []
    for src, dst, data in G.edges(data=True):
        edges.append({
            "from": src,
            "to": dst,
            "title": f"Value: {data.get('weight', 0):.4f} ETH",
            "arrows": "to",
            "color": {"color": "#848484"}
        })

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ChainSink Multi-Hop Tracer</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ margin: 0; background: #111111; color: #ffffff; font-family: sans-serif; }}
        #network {{ width: 100vw; height: 100vh; }}
        #legend {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.85); padding: 12px; border-radius: 8px; border: 1px solid #333; z-index: 10; }}
    </style>
</head>
<body>
    <div id="legend">
        <h3 style="margin:0 0 5px 0; color:#FF4B4B;">ChainSink Multi-Hop Tracer</h3>
        <p style="margin:0; font-size:12px;">
            🔴 Seed Scam Node | 🟡 Hop 1 Node | 🔵 Hop 2 Node
        </p>
    </div>
    <div id="network"></div>
    <script>
        var container = document.getElementById('network');
        var data = {{
            nodes: new vis.DataSet({json.dumps(nodes)}),
            edges: new vis.DataSet({json.dumps(edges)})
        }};
        var options = {{
            physics: {{ enabled: true, solver: 'forceAtlas2Based' }},
            nodes: {{ shape: 'dot', font: {{ color: '#ffffff', size: 11 }} }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>"""

    with open(filename, "w") as f:
        f.write(html)
    print(f"[✓] Generated graph at '{filename}' with {len(G.nodes())} nodes and {len(G.edges())} edges.")

if __name__ == "__main__":
    print("[+] Running ChainSink BFS Traversal...")
    graph = build_bfs_graph(SEED_SCAM_ADDRESS, max_depth=2, min_value=0.0)
    render_html_graph(graph)
