import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os

st.set_page_config(page_title="ChainSink Forensic Dashboard", layout="wide")

st.title("ChainSink: Automated Blockchain Forensics")
st.subheader("Interactive Multi-Hop Risk & Topology Explorer")

# Load Results CSV
@st.cache_data
def load_data():
    if os.path.exists("chainsink_results.csv"):
        return pd.read_csv("chainsink_results.csv")
    return None

df = load_data()

if df is None:
    st.warning("`chainsink_results.csv` not found in the root directory. Please upload or commit your results file.")
    uploaded_file = st.file_uploader("Upload chainsink_results.csv", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

if df is not None:
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Flagged Entities", len(df))
    col2.metric("Seed Entities (Hop 0)", len(df[df['hops_to_seed'] == 0]))
    col3.metric("Multi-Hop Targets", len(df[df['hops_to_seed'] > 0]))
    col4.metric("Pattern Hits", len(df[df['pattern_count'] > 0]))

    st.markdown("---")

    # Layout Split: Data Table & Interactive Graph
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("Flagged Risk Entities")
        search = st.text_input("Filter by Wallet Address / Seed:")
        
        filtered_df = df
        if search:
            filtered_df = df[df['entity'].astype(str).str.contains(search, case=False)]
            
        st.dataframe(filtered_df[['entity', 'hops_to_seed', 'proximity_risk', 'patterns']], height=450, use_container_width=True)

  with right_col:
        st.subheader("🕸️ Interactive Graph Visualization")
        
        G = nx.DiGraph()
        
        # Select seeds (Hop 0) and multi-hop targets (Hop > 0)
        seeds_sample = df[df[hops_col] == 0].head(5)
        targets_sample = df[df[hops_col] > 0].head(25)
        sample_df = pd.concat([seeds_sample, targets_sample])
        
        for _, row in sample_df.iterrows():
            entity = str(row['entity']).split(' ')[0]  # Clean off any (+count) suffix
            seed = str(row.get('nearest_seed', '')).split(' ')[0]
            risk = row.get(risk_col, 0)
            hops = row.get(hops_col, 0)
            
            node_id = entity[:10] + "..."
            
            # Color palette
            if hops == 0:
                node_color = "#FF4B4B"  # Red for seeds
            elif hops == 1:
                node_color = "#FFA500"  # Orange for 1-hop
            else:
                node_color = "#999999"  # Light grey for multi-hop
                
            G.add_node(node_id, title=f"Address: {entity}\nHops: {hops}\nRisk: {risk}%", color=node_color)
            
            # Draw explicit, visible connecting edge to seed
            if seed and seed != 'nan' and seed != entity:
                seed_id = seed[:10] + "..."
                G.add_node(seed_id, title=f"Seed: {seed}", color="#FF4B4B")
                G.add_edge(seed_id, node_id, color="#888888", weight=2)  # Bright visible edge

        net = Network(height="450px", width="100%", directed=True, bgcolor="#111111", font_color="white")
        net.from_nx(G)
        
        # Force physics layout so nodes pull together along edges
        net.toggle_physics(True)
        net.save_graph("network.html")
        
        with open("network.html", 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        components.html(html_content, height=470)
