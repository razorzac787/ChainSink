import os
import json
import asyncio
import aiohttp
import networkx as nx
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
    "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": ("Tornado.Cash 0.1 ETH", "Mixer"),
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": ("Tornado.Cash 1 ETH", "Mixer"),
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": ("Tornado.Cash 10 ETH", "Mixer"),
    "0xa160cd31f2977d856956c0a233ba68367881f2a2": ("Tornado.Cash 100 ETH", "Mixer"),
}

# --- STAGE 1: ASYNC MULTI-HOP DATA EXTRACTION ---

async def fetch_endpoint(session, url):
    """Fetch a single Etherscan endpoint asynchronously."""
    try:
        async with session.get(url, timeout=10) as response:
            res = await response.json()
            if res.get("status") == "1" and isinstance(res.get("result"), list):
                return res.get("result", [])
    except Exception as e:
        print(f"[!] Async Request Exception: {e}")
    return []

async def fetch_address_transfers_async(session, address):
    """Parallel fetching of normal, internal, and token transfers for multi-hop tracing."""
    address = address.lower()
    base_url = "https://api.etherscan.io/api"
    
    urls = [
        f"{base_url}?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}",
        f"{base_url}?module=account&action=txlistinternal&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}",
        f"{base_url}?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    ]

    results = await asyncio.gather(*(fetch_endpoint(session, url) for url in urls))
    
    transfers = []
    for raw_list in results:
        for tx in raw_list:
            f_addr = tx.get("from", "").lower()
            t_addr = tx.get("to", "").lower()
            
            # Bidirectional multi-hop tracking
            if (f_addr == address or t_addr == address) and f_addr != t_addr:
                decimals = int(tx.get("tokenDecimal", 18) or 18)
                val = float(tx.get("value", 0)) / (10 ** decimals)
                
                if val > 0:
                    transfers.append({
                        "from": f_addr,
                        "to": t_addr,
                        "value": val,
                        "hash": tx.get("hash", "")
                    })
    return transfers

# --- STAGE 2: MULTI-HOP GRAPH TRAVERSAL ---

async def build_multihop_graph(seed_address, max_depth=2, min_value=0.01):
    G = nx.DiGraph()
    seed_address = seed_address.lower()
    
    # Queue structure: (address, depth, incoming_value)
    queue = [(seed_address, 0, 1000.0)]
    visited = set()

    # Seed Node (Hop 0)
    G.add_node(
        seed_address, 
        depth=0, 
        label="Seed Scam Node", 
        category="Seed"
    )

    async with aiohttp.ClientSession() as session:
        while queue:
            current_batch = []
            while queue and len(current_batch) < 5:  # Batch rate control
                node_data = queue.pop(0)
                if node_data[0] not in visited and node_data[1] < max_depth:
                    current_batch.append(node_data)

            if not current_batch:
                break

            tasks = [fetch_address_transfers_async(session, addr) for addr, d, v in current_batch]
            batch_results = await asyncio.gather(*tasks)

            for (curr_addr, depth, in_val), transfers in zip(current_batch, batch_results):
                visited.add(curr_addr)
                transfers.sort(key=lambda x: x["value"], reverse=True)

                for tx in transfers:
                    src, dst, val = tx["from"], tx["to"], tx["value"]
                    
                    if val < min_value:
                        continue

                    # Check Terminal Integrations
                    if dst in KNOWN_TERMINALS:
                        term_label, term_cat = KNOWN_TERMINALS[dst]
                        G.add_node(dst, depth=depth+1, label=term_label, category=term_cat)
                        G.add_edge(src, dst, weight=val, hash=tx["hash"])
                        continue

                    # Multi-Hop Depth Labeling
                    dst_depth = depth + 1
                    hop_label = f"Hop {dst_depth} Node"
                    
                    if dst not in G:
                        G.add_node(
                            dst, 
                            depth=dst_depth, 
                            label=f"{hop_label} ({dst[:6]}...)", 
                            category=f"Hop{dst_depth}"
                        )
                    
                    G.add_edge(src, dst, weight=val, hash=tx["hash"])

                    if dst not in visited and dst_depth < max_depth:
                        queue.append((dst, dst_depth, val))

            await asyncio.sleep(0.35)

    return G

# --- STAGE 3: VISUALIZATION RENDERER ---

def render_html_graph(G, filename="fund_flow_graph.html"):
    nodes = []
    for node, data in G.nodes(data=True):
        depth = data.get("depth", 0)
        label = data.get("label", f"{node[:6]}...{node[-4:]}")
        
        # Color coding matching original UI layout
        if depth == 0:
            color = "#FF4B4B"  # Seed Scam Node (Red)
        elif depth == 1:
            color = "#FFC107"  # Hop 1 Node (Amber/Yellow)
        elif depth == 2:
            color = "#00C0F2"  # Hop 2 Node (Blue)
        else:
            color = "#00E676"  # Hop 3+ / Terminal Node (Green)

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
    print(f"[✓] Generated graph at '{filename}'")

if __name__ == "__main__":
    print("[+] Executing ChainSink Multi-Hop Tracer Engine...")
    graph = asyncio.run(build_multihop_graph(SEED_SCAM_ADDRESS, max_depth=2, min_value=0.01))
    render_html_graph(graph)
