import pandas as pd
import networkx as nx
import json
import io
from typing import Dict, List, Tuple, Optional, Any

# =============================================================================
# 1. DEFENSIVE DATASET INGESTION & FAILURE HANDLING
# =============================================================================
class DatasetIngestionEngine:
    """Handles dataset loading, magic-byte checks, structural validation,
    row sanitization, and schema mapping to prevent engine crashes."""
    
    REQUIRED_FIELDS = ["source", "target", "amount", "timestamp"]

    @staticmethod
    def validate_and_load(file_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """Pre-parse validation to catch empty, corrupt, or invalid binary uploads."""
        if len(file_bytes) == 0:
            return False, "Uploaded file is empty (0 Bytes).", None

        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes))
            elif filename.endswith(".parquet"):
                df = pd.read_parquet(io.BytesIO(file_bytes))
            else:
                return False, "Unsupported file extension. Please upload a .csv or .parquet file.", None
        except pd.errors.EmptyDataError:
            return False, "File contains no readable data rows.", None
        except pd.errors.ParserError:
            return False, "Malformed CSV structure (e.g., inconsistent delimiters or broken quotes).", None
        except Exception as e:
            return False, f"Corrupted or unreadable file structure: {str(e)}", None

        if len(df) == 0:
            return False, "Dataset loaded, but contains 0 rows.", None

        return True, f"File successfully pre-parsed ({len(df)} raw rows).", df

    @classmethod
    def normalize_schema(cls, df: pd.DataFrame, mapping: Dict[str, str]) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Standardizes user-mapped columns into internal schema with robust error coercion."""
        stats = {"total_rows": len(df), "cleaned_rows": 0, "dropped_rows": 0}
        
        normalized = pd.DataFrame()
        
        # Coerce address/entity strings and drop nulls
        normalized['source_entity'] = df[mapping['source']].astype(str).str.strip()
        normalized['target_entity'] = df[mapping['target']].astype(str).str.strip()
        
        # Coerce numeric values safely
        normalized['amount'] = pd.to_numeric(df[mapping['amount']], errors='coerce').fillna(0.0)
        normalized['timestamp'] = pd.to_numeric(df[mapping['timestamp']], errors='coerce').fillna(0)
        
        if mapping.get('tx_hash') and mapping['tx_hash'] in df.columns:
            normalized['tx_hash'] = df[mapping['tx_hash']].astype(str)
        else:
            normalized['tx_hash'] = [f"tx_{i}" for i in range(len(df))]

        # Defensive Sanitization Rules: Drop invalid addresses, nulls, and self-loops
        valid_mask = (
            (normalized['source_entity'] != "") & 
            (normalized['source_entity'] != "nan") & 
            (normalized['source_entity'] != "None") &
            (normalized['target_entity'] != "") & 
            (normalized['target_entity'] != "nan") & 
            (normalized['target_entity'] != "None") &
            (normalized['source_entity'] != normalized['target_entity']) # Filter self-loops
        )
        
        clean_df = normalized[valid_mask].copy()
        stats["cleaned_rows"] = len(clean_df)
        stats["dropped_rows"] = stats["total_rows"] - stats["cleaned_rows"]
        
        return clean_df, stats


# =============================================================================
# 2. CORE CHAINSINK FORENSIC ENGINE (PILLARS 1, 2, & 3)
# =============================================================================
class ChainSinkForensicEngine:
    def __init__(self):
        self.address_clusters: Dict[str, str] = {}
        self.graph = nx.DiGraph()
        self.scam_seeds: Set[str] = set()

    def set_scam_seeds(self, seeds: List[str]):
        """Register known illicit/scam addresses (Seed Set E)."""
        self.scam_seeds = {str(s).strip() for s in seeds}

    def run_pillar_1_heuristics(self, df: pd.DataFrame):
        """Pillar 1: Address Clustering (Multi-Input Co-Spending Heuristic)."""
        cluster_id = 0
        for _, row in df.iterrows():
            src = row['source_entity']
            # If input represents a JSON list of co-spending addresses
            if src.startswith('[') and src.endswith(']'):
                try:
                    addrs = json.loads(src.replace("'", '"'))
                    if len(addrs) > 1:
                        existing = {self.address_clusters[a] for a in addrs if a in self.address_clusters}
                        target_cluster = list(existing)[0] if existing else f"Cluster_{cluster_id}"
                        if not existing: cluster_id += 1
                        for a in addrs:
                            self.address_clusters[a] = target_cluster
                        continue
                except json.JSONDecodeError:
                    pass
            
            # Default single address mapping
            if src not in self.address_clusters:
                self.address_clusters[src] = src

    def run_pillar_2_topology_mining(self, df: pd.DataFrame):
        """Pillar 2: BlazingAML Graph Construction & Topology Mining."""
        self.graph.clear()
        for _, row in df.iterrows():
            src = self.address_clusters.get(row['source_entity'], row['source_entity'])
            dst = self.address_clusters.get(row['target_entity'], row['target_entity'])
            
            self.graph.add_edge(
                src, dst,
                amount=row['amount'],
                timestamp=row['timestamp'],
                tx_hash=row['tx_hash']
            )

    def run_pillar_3_proximity_scoring(self, max_hop_depth: int = 5) -> Dict[str, Dict[str, Any]]:
        """Pillar 3: EAI Shortest-Path Proximity Risk Scoring D(v, E)."""
        results = {}
        for node in self.graph.nodes():
            shortest_dist = float('inf')
            closest_seed = None
            
            for seed in self.scam_seeds:
                if seed in self.graph and nx.has_path(self.graph, seed, node):
                    try:
                        # Compute shortest directed path length
                        dist = nx.shortest_path_length(self.graph, seed, node)
                        if dist < shortest_dist:
                            shortest_dist = dist
                            closest_seed = seed
                    except nx.NetworkXNoPath:
                        continue
            
            # Compute distance-decay risk score
            if shortest_dist == float('inf') or shortest_dist > max_hop_depth:
                hop_count = -1
                risk_score = 0.0
            else:
                hop_count = int(shortest_dist)
                risk_score = round(max(0.0, 100.0 * (0.5 ** hop_count)), 2)

            results[node] = {
                "entity": node,
                "shortest_hop_distance": hop_count,
                "nearest_scam_seed": closest_seed,
                "proximity_risk_score": risk_score,
                "in_degree": self.graph.in_degree(node),
                "out_degree": self.graph.out_degree(node)
            }
        return results


# =============================================================================
# 3. VERIFICATION & TEST DRIVE
# =============================================================================
if __name__ == "__main__":
    import os

    print("=================================================================")
    print("    CHAINSINK FORENSIC PIPELINE - INTERACTIVE DATASET RUN        ")
    print("=================================================================\n")

    # 1. Prompt User for File Path
   # 1. Prompt User for File Path
    file_path = input("Enter path to your dataset file (.csv or .parquet): ").strip()
    
    # Strip quotes if dragged & dropped into terminal
    file_path = file_path.strip("'\"")
    
    # Expand ~ to /home/username automatically
    file_path = os.path.expanduser(file_path)

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found at absolute path: {os.path.abspath(file_path)}")
        exit(1)
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        exit(1)

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # 2. Ingest and Validate
    valid, msg, raw_df = DatasetIngestionEngine.validate_and_load(file_bytes, file_path)
    if not valid:
        print(f"Ingestion Error: {msg}")
        exit(1)

    print(f"\nDataset loaded successfully! Total rows: {len(raw_df)}")
    print("Available columns in your file:", list(raw_df.columns))
    print("-" * 65)

    # 3. Interactive Column Mapping
    print("Please map your dataset columns to ChainSink standard fields:")
    src_col = input(f"Source Entity column name (e.g. {raw_df.columns[0]}): ").strip()
    dst_col = input(f"Target Entity column name (e.g. {raw_df.columns[1]}): ").strip()
    amt_col = input("Amount column name: ").strip()
    ts_col  = input("Timestamp/Block column name: ").strip()
    tx_col  = input("Tx Hash column name (Press Enter to skip): ").strip() or None

    column_mapping = {
        "source": src_col,
        "target": dst_col,
        "amount": amt_col,
        "timestamp": ts_col,
        "tx_hash": tx_col
    }

    # 4. Prompt for Seed Addresses
    seed_input = input("\nEnter known scam seed addresses (comma-separated): ").strip()
    scam_seeds = [s.strip() for s in seed_input.split(",") if s.strip()]

    # 5. Execute Pipeline
    clean_df, stats = DatasetIngestionEngine.normalize_schema(raw_df, column_mapping)
    print(f"\nSanitization Complete: Cleaned {stats['cleaned_rows']} rows, dropped {stats['dropped_rows']} invalid rows.")

    engine = ChainSinkForensicEngine()
    engine.set_scam_seeds(scam_seeds)
    engine.run_pillar_1_heuristics(clean_df)
    engine.run_pillar_2_topology_mining(clean_df)
    results = engine.run_pillar_3_proximity_scoring()

    # 6. Display Results
    print("\nCalculated Entity Proximity & Compliance Risk Scores:")
    print("-" * 65)
    print(f"{'Entity':<20} | {'Hop Distance':<12} | {'Nearest Seed':<15} | {'Risk Score':<10}")
    print("-" * 65)
    for entity, metrics in list(results.items())[:20]: # Show first 20
        print(f"{str(entity):<20} | {metrics['shortest_hop_distance']:<12} | {str(metrics['nearest_scam_seed']):<15} | {metrics['proximity_risk_score']:<10}")
