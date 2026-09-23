import os
import requests
import networkx as nx
from pyvis.network import Network
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

if not ETHERSCAN_API_KEY:
    raise ValueError("Missing ETHERSCAN_API_KEY. Please set it in your .env file.")


SEED_SCAM_ADDRESS = "0xe85ca9f88558ca4c5796bea5a04f66b8f8162ae8" # Example seed address (vitalik.eth for testing)

def fetch_outgoing_transactions(address, limit=5):
    """Fetch recent outgoing ETH transactions from Etherscan API."""
    url = (
        f"https://api.etherscan.io/api"
        f"?module=account&action=txlist&address={address}"
        f"&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    )
    try:
        response = requests.get(url, timeout=10).json()
        if response.get("status") != "1":
            return []
        
        outgoing = []
        for tx in response.get("result", []):
            # Track outgoing transactions only
            if tx["from"].lower() == address.lower() and tx["to"]:
                val_eth = float(tx["value"]) / 1e18
                if val_eth > 0:  # Filter out 0 ETH transactions
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
        print(f"API Error for {address}: {e}")
        return []

def build_multihop_graph(seed_address, max_depth=2, branch_limit=3):
    """BFS Traversal Engine using NetworkX."""
    G = nx.DiGraph()
    queue = [(seed_address, 0)]  # Tuple: (current_address, depth)
    visited = set()

    print(f"[+] Starting Multi-Hop Traversal for Seed: {seed_address}")

    while queue:
        curr_addr, depth = queue.pop(0)
        
        if depth >= max_depth or curr_addr in visited:
            continue
            
        visited.add(curr_addr)
        print(f" -> Tracing Hop {depth}: {curr_addr[:10]}...")
        
        txs = fetch_outgoing_transactions(curr_addr, limit=branch_limit)
        
        for tx in txs:
            src = tx["from"]
            dst = tx["to"]
            val = tx["value"]

            #Add Nodes
            G.add_node(src, depth=depth)
            G.add_node(dst, depth=depth + 1)

            #Add Directed Edge
            G.add_edge(src, dst, weight=val, title=f"Transfer: {val:.4f} ETH")

            if dst not in visited and (depth + 1) < max_depth:
                queue.append((dst, depth + 1))

    return G

def render_pyvis_graph(nx_graph, output_file="fund_flow_graph.html"):
    """Convert NetworkX graph to interactive HTML visualization using PyVis."""
    
    # 1. Check if graph contains nodes
    if len(nx_graph.nodes) == 0:
        print("[!] Warning: The graph is empty! Check your API key or seed address outgoing transactions.")
        return

    # 2. Set cdn_resources='remote' to load vis.js directly from the official CDN
    net = Network(
        height="600px", 
        width="100%", 
        directed=True, 
        bgcolor="#111111", 
        font_color="white",
        cdn_resources="remote"
    )
    
    # Import NetworkX graph structure
    net.from_nx(nx_graph)
    
    # Customize visual appearance based on node role
    for node in net.nodes:
        node_id = node["id"]
        # Add tooltips and truncated labels
        node["label"] = f"{node_id[:6]}...{node_id[-4:]}"
        node["title"] = f"Full Address: {node_id}"
        
        # Color coding strategy
        if nx_graph.nodes[node_id].get("depth") == 0:
            node["color"] = "#FF4B4B"  # Red for Seed Victim/Scam
            node["size"] = 25
        else:
            node["color"] = "#00C0F2"  # Blue for Intermediate Hop Nodes
            node["size"] = 15

    # Enable physics engine for drag-and-drop layout
    net.toggle_physics(True)
    net.write_html(output_file)
    print(f"[✓] Successfully exported interactive graph with {len(nx_graph.nodes)} nodes to: {output_file}")


if __name__ == "__main__":
    graph = build_multihop_graph(SEED_SCAM_ADDRESS, max_depth=2, branch_limit=3)
    render_pyvis_graph(graph, "fund_flow_graph.html")
