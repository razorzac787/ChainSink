import os
import json
import time
import requests
import networkx as nx
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
SEED_SCAM_ADDRESS = "0x5026F006B85729a8b14553FAe312930261E1b2F8"  # Kyber Exploit Address

KNOWN_TERMINAL_NODES = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14",
    "0x0d0707963952f2a572d1264c7676757b85040f7b": "Kraken Hot Wallet",
    "0x47ac0fb3f2d84898e4d9e7b4dab3c24507a6d503": "Binance 8",
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": "Tornado.Cash Router"
}

def fetch_outgoing_transactions(address):
    """Fetch direct ETH, internal contract calls, and ERC-20 token transfers via Etherscan API v2."""
    if not ETHERSCAN_API_KEY or ETHERSCAN_API_KEY == "your_actual_etherscan_api_key_here":
        print("[!] Warning: Missing valid ETHERSCAN_API_KEY in .env file!")
        return []

    address = address.lower()
    outgoing = []

    # Etherscan V2 base endpoint with chainid=1 for Ethereum Mainnet
    base_url = "https://api.etherscan.io/v2/api"
    
    actions = [
        ("Normal Tx", f"{base_url}?chainid=1&module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"),
        ("Internal Tx", f"{base_url}?chainid=1&module=account&action=txlistinternal&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"),
        ("Token Tx", f"{base_url}?chainid=1&module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}")
    ]

    for tx_type, url in actions:
        try:
            res = requests.get(url, timeout=10).json()
            # Respect Etherscan free tier rate limits (3 requests/sec)
            time.sleep(0.35)

            if res.get("status") == "1" and isinstance(res.get("result"), list):
                for tx in res.get("result", []):
                    from_addr = tx.get("from", "").lower()
                    to_addr = tx.get("to", "").lower()
                    
                    if from_addr == address and to_addr:
                        decimals = int(tx.get("tokenDecimal", 18) or 18)
                        raw_val = float(tx.get("value", 0))
                        val = raw_val / (10 ** decimals)
                        
                        if val > 0:
                            outgoing.append({
                                "from": from_addr,
                                "to": to_addr,
                                "value": val,
                                "hash": tx.get("hash", ""),
                                "type": tx_type
                            })
            else:
                msg = res.get("message", "No transactions found")
                if "NOTOK" in res.get("message", ""):
                    print(f" [!] API Notice ({tx_type}): {res.get('result', msg)}")
        except Exception as e:
            print(f"[!] API Request Error ({tx_type}): {e}")

    print(f" [✓] Found {len(outgoing)} total outgoing transfers for {address[:10]}...")
    return outgoing

def build_multihop_graph(seed_address, max_depth=2, min_decay_ratio=0.01, min_eth_threshold=0.01):
    G = nx.DiGraph()
    seed_address = seed_address.lower()
    
    queue = [(seed_address, 0, 1000.0)]  # Pass initial tracking baseline
    visited = set()

    print(f"[+] Starting Heuristic Value-Decay Traversal for Seed: {seed_address}")

    while queue:
        curr_addr, depth, in_val = queue.pop(0)
        
        if depth >= max_depth or curr_addr in visited:
            continue
            
        visited.add(curr_addr)
        
        is_terminal = curr_addr in KNOWN_TERMINAL_NODES
        label_name = KNOWN_TERMINAL_NODES.get(curr_addr, "Laundering Node")
        G.add_node(curr_addr, depth=depth, is_terminal=is_terminal, label=label_name)
        
        if is_terminal and curr_addr != seed_address:
            print(f" [★] Terminal CEX/Mixer Reached: {label_name}")
            continue

        print(f" -> Tracing Hop {depth}: {curr_addr[:10]}...")
        txs = fetch_outgoing_transactions(curr_addr)
        
        if not txs:
            continue

        txs.sort(key=lambda x: x["value"], reverse=True)
        
        for tx in txs:
            src, dst, val = tx["from"], tx["to"], tx["value"]
            
            # 1. Minimum Dust Threshold
            if val < min_eth_threshold:
                continue
                
            # 2. Decay Ratio Check
            decay_ratio = val / in_val
            if decay_ratio < min_decay_ratio and val < 1.0:
                continue

            is_dst_terminal = dst in KNOWN_TERMINAL_NODES
            dst_label = KNOWN_TERMINAL_NODES.get(dst, f"Hop {depth + 1}")
            
            G.add_node(dst, depth=depth + 1, is_terminal=is_dst_terminal, label=dst_label)
            G.add_edge(src, dst, weight=val, tx_hash=tx["hash"])

            if dst not in visited and (depth + 1) < max_depth:
                queue.append((dst, depth + 1, val))

    return G

def render_standalone_html(nx_graph, output_file="fund_flow_graph.html"):
    nodes = []
    for node, attrs in nx_graph.nodes(data=True):
        depth = attrs.get("depth", 0)
        is_seed = (depth == 0)
        is_terminal = attrs.get("is_terminal", False)
        label_text = attrs.get("label", f"{node[:6]}...{node[-4:]}")
        
        color = "#FF4B4B" if is_seed else ("#00E676" if is_terminal else ("#FFC107" if depth == 1 else "#00C0F2"))

        nodes.append({
            "id": node,
            "label": f"{label_text}\n({node[:6]}...{node[-4:]})",
            "title": f"Address: {node}<br>Hop Depth: {depth}",
            "color": color,
            "size": 28 if (is_seed or is_terminal) else 16
        })

    edges = []
    for src, dst, attrs in nx_graph.edges(data=True):
        val = attrs.get("weight", 0)
        edges.append({
            "from": src,
            "to": dst,
            "title": f"Amount: {val:.4f}",
            "arrows": "to",
            "color": {"color": "#848484"}
        })

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>ChainSink Multi-Hop Tracer</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        body {{ margin: 0; padding: 0; background-color: #111111; color: white; font-family: sans-serif; }}
        #network {{ width: 100vw; height: 100vh; }}
        #info {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.85); padding: 12px; border-radius: 8px; border: 1px solid #333; z-index:100; }}
    </style>
</head>
<body>
    <div id="info">
        <h4 style="margin:0 0 6px 0; color:#FF4B4B;">ChainSink Multi-Hop Tracer</h4>
        <p style="margin:0; font-size:11px;">🔴 Seed Scam Node | 🟡 Hop 1 Node | 🔵 Hop 2+ Node | 🟢 Terminal CEX</p>
    </div>
    <div id="network"></div>
    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});
        var container = document.getElementById('network');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            physics: {{ enabled: true, solver: 'forceAtlas2Based' }},
            nodes: {{ shape: 'dot', font: {{ color: '#ffffff', size: 11 }} }},
            edges: {{ smooth: {{ type: 'continuous' }} }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>"""

    with open(output_file, "w") as f:
        f.write(html_content)
    print(f"[✓] Saved visualization to {output_file}")

if __name__ == "__main__":
    graph = build_multihop_graph(SEED_SCAM_ADDRESS, max_depth=2, min_decay_ratio=0.01, min_eth_threshold=0.01)
    render_standalone_html(graph, "fund_flow_graph.html")
