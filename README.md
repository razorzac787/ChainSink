# ChainSink: Automated Multi-Hop Blockchain Forensics & On-Chain Compliance Pipeline

**ChainSink** is a modular, high-throughput blockchain forensics system designed to trace illicit crypto fund flows from victim-reported scam addresses, uncover hidden peel chains, calculate proximity risk metrics, and settle verified compliance states on-chain via smart contracts.

By combining standard Python graph processing with a high-performance parallel engine, a defensive Universal Dataset Ingestion Wizard, and an Optimistic STM Smart Contract Registry, ChainSink eliminates analysis bottlenecks and enables programmatic, low-gas compliance verification.

## Problem Statement

Social engineering attacks, phishing, and advance fee fraud schemes present ongoing threats to crypto asset holders. Fraudsters leverage blockchain pseudo-anonymity to rapidly move stolen funds through complex peel chains, mixers, and decentralized liquidity pools before withdrawing through Centralized Exchanges (CEXs). Traditional blocklists operate reactively and fail to track dynamic multi-hop flows. Furthermore, off-chain forensic tools lack an immutable, gas-efficient mechanism to publish and verify risk scores directly on-chain for smart contracts and protocols to act upon automatically.

## Project Objectives

1. **Defensive Dataset Ingestion Wizard:** Provide an interactive schema-mapping ingestion wizard that accepts open datasets (e.g., Elliptic2, raw UTXO dumps, custom CSV/Parquet files) with built-in sanitization to protect against file corruption, invalid binary uploads, and null identifiers

2. **Deterministic Clustering & Heuristics:** Implement rule-based on-chain clustering logic—including multi-input co-spending aggregation and change address reuse detection—to group connected wallet addresses into unified entity clusters (Pillar 1).

3. **High-Throughput Pattern Mining:** Adapt the BlazingAML architecture into a native C++ parallel compute module using multi-threading (OpenMP / native thread pools) to scan large transaction graphs for structural money laundering patterns (Scatter-Gather, Cycles, Fan-In/Fan-Out) across Placement, Layering, and Integration stages without performance bottlenecks (Pillar 2).

4. **Proximity-Based Path Scoring:** Compute shortest-path distance decay scores $D(v, E) = \max\left(0, 100 \times 0.5^{\text{hops}}\right)$ from target nodes $v$ to known illicit seed entities $E$ to quantify compliance risk (Pillar 3).

5. **On-Chain Settlement & Merkle Verification (compliance_registry.py:** Commit computed compliance states and 32-byte global Merkle roots to an on-chain smart contract layer driven by an Optimistic Software Transactional Memory (STM) execution engine for concurrent state updates and low-gas client proof verification.

6. **Interactive Visual Dashboard:** Build a web interface using Streamlit and PyVis to render dynamic network sub-graphs, trace path proximity, inspect entity risk profiles, and export automated audit reports.

7. **Validate Performance & Backtest:** Evaluate recall and benchmark runtime performance across historical datasets (such as Elliptic2), comparing multi-threaded C++ graph processing against baseline Python execution and measuring optimistic STM state contention.

## Key Features & Architecture

ChainSink organizes its end-to-end architecture into four execution layers:

**Ingestion & Sanitization Wizard:** Handles file validation (magic byte checks, format parsing) and dynamic user schema mapping to standardize raw input files into internal entity graph structures.

**Pillar 1 — Heuristic Clustering Engine (heuristic_analyzer.py):** Executes deterministic multi-input co-spending and change-address heuristics to map raw cryptographic addresses into unified entity clusters.

**Pillar 2 — High-Throughput Topology Core (blazing_aml.cpp):** A multi-threaded python pattern-mining engine that traverses directed transaction graphs to detect cycles, peel chains, and complex mixing topographies at bare-metal speeds.

**Pillar 3 — EAI Proximity Engine (multihop_engine.py):** Calculates direct directed path hop counts and applies exponential distance-decay functions to determine compliance risk scores.

**Smart Contract Layer (compliance_registry.py):** Settles off-chain forensic results on-chain via update_eai_status, update_proximity_merkle_root, and enables low-gas client verification via verify_proximity_proof.

## System Architecture

```
[ Ingested Dataset ] (Elliptic2 / UTXO Dumps / Custom CSV)
         │
         ▼
[ Ingestion Wizard ] Pre-Parse Validation, Schema Alignment, & Defensive Sanitization
         │
         ▼
[ Pillar 1: Heuristic Engine ] Co-Spending & Address Clustering 
         │
         ▼
[ Pillar 2: BlazingAML Core ] Multi-Threaded C++ Pattern Mining 
         │
         ▼
[ Pillar 3: EAI Proximity Engine ] Shortest Path Scoring D(v, E) 
         │
         ├───► [ Visual Dashboard ] Interactive PyVis Network Visualizer & Risk Inspector
         │
         ▼
[ Smart Contract Registry ] On-Chain State Settlement via Optimistic STM Engine
  ├── update_eai_status()            ──► Updates entity risk flags
  ├── update_proximity_merkle_root() ──► Commits 32-byte Merkle root
  └── verify_proximity_proof()       ──► Low-gas client proof verification
```

---

## Technology Stack

| Layer | Component / Tool | Location in Code |
| :--- | :--- | :--- |
| **Ingestion & Wizard** | Pandas, BytesIO, Schema Mapper | `DatasetIngestionEngine` |
| **Heuristics & Clustering** | Python Entity Grouping | `ChainSinkForensicEngine.run_pillar_1_heuristics` |
| **Pattern Mining** | NetworkX Graph Engine | `ChainSinkForensicEngine.run_pillar_2_topology_mining` |
| **Proximity Scoring** | Exponential Distance Decay $D(v,E)$ | `ChainSinkForensicEngine.run_pillar_3_proximity_scoring` |
| **Smart Contract Registry** | Optimistic STM Engine & Merkle Trees | `ComplianceRegistryContract` |
| **UI & Visual Analytics** | Streamlit, PyVis | Terminal CLI / `app.py` |
---

## Project Roadmap & Deliverables

### Phase 1: Ingestion Wizard & Heuristic Foundation
- [x] Defensive Ingestion Engine: Pre-parse validation, magic byte checking, structural sanitization, and row-error coercion.
- [x] Dynamic Schema Alignment: Streamlit modal for mapping custom file headers to standard graph inputs (source, target, amount, timestamp).
- [x] Pillar 1 Address Clustering: Multi-input co-spending and address aggregation module

### Phase 2: High-Performance Parallel Processing & Heuristic Mining
- [ ] **BlazingAML (Python Core)**
   - Multi-threaded parallel graph pattern mining (Cycles, Fan-In/Fan-Out, Peel Chains).
   - OpenMP acceleration for sub-second execution over multi-million-edge graphs
- [ ] **Pillar 3 Proximity Engine (multihop_engine.py):**
  - Shortest-path calculations from target entities to illicit seed clusters E.
  - Distance-decay metric calculation $D(v, E) = 100 x 0.5^{hops}

### On-Chain Settlement, UI & Benchmarking
- [ ] **On-Chain Compliance Registry (compliance_registry.py):**
   - Optimistic STM driver integration for concurrent update_eai_status and update_proximity_merkle_root calls.
   - Merkle tree construction and verify_proximity_proof verification functions.
- [ ] **Unified Interactive Dashboard:** Streamlit UI with graph rendering, address search, and PDF audit report generation.
- [ ] **Performance Backtesting:** Benchmark execution runtime (C++ parallel core vs. Python sequential traversal) and evaluate STM conflict contention under high-throughput batch updates.

---

## References

1. **Chen, Y., et al. (2025).** *A Graph-Based Approach to Blockchain Fraud Prevention.* arXiv preprint arXiv:2505.24284. [https://arxiv.org/pdf/2505.24284](https://arxiv.org/pdf/2505.24284)
2. **Wu, J., et al. (2023).** *Towards Understanding Crypto Money Laundering in Web3: Heuristic Transaction Tracing and Empirical Analysis.* arXiv preprint arXiv:2305.14748. [https://arxiv.org/pdf/2305.14748](https://arxiv.org/pdf/2305.14748)
3. **Lin, H., et al. (2026).** *BlazingAML: High-Throughput Anti-Money Laundering System via Graph Pattern Mining.* arXiv preprint arXiv:2604.12241. [https://arxiv.org/pdf/2604.12241](https://arxiv.org/pdf/2604.12241)



