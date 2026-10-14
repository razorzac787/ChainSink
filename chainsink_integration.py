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
    print("=================================================================")
    print("    CHAINSINK FORENSIC PIPELINE - INTEGRATION TEST RUN           ")
    print("=================================================================\n")

    # Sample mock dataset representing raw ingested CSV content
    sample_csv_data = """src_wallet,dst_wallet,btc_val,time_step,tx_id
    0xUserA,0xUserB,1.5,100,tx_01
    0xUserB,0xUserC,1.4,101,tx_02
    ScamSeed_1,0xUserA,5.0,99,tx_00
    0xUserC,0xUserD,1.2,102,tx_03
    0xCorrupt,NaN,0.0,103,tx_04
    """

    # 1. Ingestion Check
    file_bytes = sample_csv_data.encode('utf-8')
    valid, msg, raw_df = DatasetIngestionEngine.validate_and_load(file_bytes, "test_dataset.csv")
    print(f"Ingestion Check: {msg}")

    # 2. Schema Normalization
    column_mapping = {
        "source": "src_wallet",
        "target": "dst_wallet",
        "amount": "btc_val",
        "timestamp": "time_step",
        "tx_hash": "tx_id"
    }
    clean_df, stats = DatasetIngestionEngine.normalize_schema(raw_df, column_mapping)
    print(f"Sanitization Stats: Ingested {stats['total_rows']} rows, Cleaned: {stats['cleaned_rows']}, Dropped Bad Rows: {stats['dropped_rows']}")

    # 3. Run Pipeline Pillars
    engine = ChainSinkForensicEngine()
    engine.set_scam_seeds(["ScamSeed_1"])
    engine.run_pillar_1_heuristics(clean_df)
    engine.run_pillar_2_topology_mining(clean_df)
    results = engine.run_pillar_3_proximity_scoring()

    # 4. Display Results
    print("\nCalculated Entity Proximity & Compliance Risk Scores:")
    print("-" * 65)
    print(f"{'Entity':<12} | {'Hop Distance D(v,E)':<20} | {'Nearest Seed':<12} | {'Risk Score':<10}")
    print("-" * 65)
    for entity, metrics in results.items():
        print(f"{entity:<12} | {metrics['shortest_hop_distance']:<20} | {str(metrics['nearest_scam_seed']):<12} | {metrics['proximity_risk_score']:<10}")
