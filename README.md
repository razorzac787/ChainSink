# ChainSink: Automated Multi-Hop Blockchain Forensics & Exchange Attribution Pipeline

**ChainSink** is a modular, high-throughput blockchain forensics system designed to trace illicit crypto fund flows from victim-reported scam addresses, uncover hidden peel chains, and attribute terminal deposit nodes to Centralized Exchanges (CEXs). 

By combining standard Python graph traversal with a high-performance **parallel C++ engine (`blazing_aml.cpp`)**, ChainSink eliminates execution bottlenecks and achieves real-time topology detection without machine learning overhead.

## Problem Statement

Social engineering attacks, phishing, and advance fee fraud schemes are key challenges faced by crypto asset holders. Fraudsters utilize ledger anonymity to quickly move hacked money through peel chains of wallets and decentralized liquidity pools into liquidation through centralized cryptocurrency exchanges (CEXs). Current blocklists are reactionary measures and fail to capture rapid movement of stolen crypto until it reaches CEXs where the money is withdrawn.

## Project Objectives

1. **Automate Scam Ingestion:** Build an OSINT ingestion pipeline to continuously ingest victim-reported suspect wallet addresses from public repositories (e.g., Chainabuse, CryptoScamDB).

2. **Multi-Hop Graph Traversal (`multihop_engine.py`):** Develop a directed graph engine using Python `NetworkX` querying Web3 APIs (e.g., Etherscan) to build dynamic transaction trees and trace outgoing fund flows up to $N$-hops deep.

3. **Deterministic Clustering & Heuristics (`heuristic_analyzer.py`):** Implement rule-based on-chain clustering logic—including multi-input co-spending aggregation and intermediate deposit address reuse detection—to group connected wallet addresses into unified entity clusters.

4. **High-Throughput Pattern Mining (`blazing_aml.cpp`):** Adapt the BlazingAML architecture into a native C++ parallel compute module using multi-threading (OpenMP / native threads) to scan large transaction graphs for complex typologies (Scatter-Gather, Cycles, Fan-In/Fan-Out) across Placement, Layering, and Integration stages without performance bottlenecks.

5. **Exchange Attribution:** Map destination sink nodes against labeled centralized exchange (CEX) deposit wallets (e.g., Binance, Coinbase) to calculate proximity distance $D(v, E)$ and pinpoint cash-out endpoints.

6. **Interactive Dashboard:** Build a real-time web UI using Streamlit and PyVis to visualize fund-flow paths, render network sub-graphs, and provide interactive node analytics for forensic investigation.

7. **Validate Performance & Backtest:** Evaluate system recall and benchmark performance runtime (comparing C++ parallel graph processing against standard Python sequential traversal) across historical ground-truth scam datasets.

## Key Features & Architecture

ChainSink isolates its detection pipeline into three specialized, decoupled execution modules:

* **`multihop_engine.py` (Graph Traversal Engine):** Handles API queries (e.g., Etherscan) to construct dynamic $N$-hop directed transaction graphs representing outgoing fund flows.
* **`heuristic_analyzer.py` (On-Chain Heuristic Engine):** Applies deterministic clustering logic, including co-spending aggregation and intermediate deposit address reuse detection.
* **`blazing_aml.cpp` (High-Throughput C++ Core):** A parallelized C++ pattern-mining engine (powered by OpenMP / native threads) that processes high-volume graph structures (Placement, Layering, Integration) at bare-metal performance speeds.

## System Architecture

```
[ OSINT Repository ] (Chainabuse / CryptoScamDB)
         │
         ▼
[ Ingestion Pipeline ] Automated Ingestion of Victim-Reported Seed Addresses
         │
         ▼
[ Directed Graph Traversal ] NetworkX + Web3 APIs (multihop_engine.py)
         │
         ├────► [ Heuristic Engine ] Co-Spending & Deposit Reuse Logic (heuristic_analyzer.py)
         │
         ├────► [ Parallel Pattern Mining ] Multi-Threaded C++ Core (blazing_aml.cpp)
         │
         ▼
[ Sink Attribution Engine ] Terminal Node Mapping to Exchange Deposit Labels
         │
         ▼
[ Visual Analytics Dashboard ] Streamlit + PyVis Real-Time Interactive UI
```

---

## Technology Stack

| Layer | Component / Tool |
| :--- | :--- |
| **Languages** | C++17 / C++20, Python 3.10+ |
| **Parallel Compute Engine** | C++ (`blazing_aml.cpp`), OpenMP / Thread Pools |
| **Graph Traversal & Analysis** | NetworkX (`multihop_engine.py`), Pandas, NumPy |
| **Heuristics & Clustering** | Python (`heuristic_analyzer.py`) |
| **UI & Visual Analytics** | Streamlit, PyVis |
| **Data Sources & APIs** | Etherscan REST API, Web3.py, Chainabuse, CryptoScamDB |

---

## Project Roadmap & Deliverables

### Phase 1: Ingestion & Core Traversal Engine
- [x] **Automated Scam Ingestion Pipeline:** Continuous ingest of victim-reported addresses from OSINT repos.
- [x] **Multi-Hop Traversal Engine (`multihop_engine.py`):** Directed $N$-hop graph traversal using NetworkX and Web3 block explorer APIs.
- [x] **Visual Analytics Prototype:** Initial interactive HTML/JS graph generation via PyVis.

### Phase 2: High-Performance Parallel Processing & Heuristic Mining
- [ ] **Heuristic Analysis Engine (`heuristic_analyzer.py`):**
  - Deterministic co-spending input aggregation.
  - Intermediate deposit address reuse detection across transactions.
- [ ] **BlazingAML C++ Core (`blazing_aml.cpp`):**
  - High-throughput parallel graph pattern mining (Scatter-Gather, Cycles, Fan-In/Fan-Out).
  - OpenMP-accelerated multi-threading for fast evaluation across Placement, Layering, and Integration stages.
- [ ] **Exchange Attribution Engine:**
  - Sink node mapping against known exchange wallet labels (Binance, Coinbase, etc.).
  - Distance-to-Exchange proximity calculation $D(v, E)$.

### Phase 3: Integration, Dashboard & Benchmarking
- [ ] **Unified Interactive Dashboard:** Streamlit UI integrating real-time depth controls, graph rendering, and address analytics.
- [ ] **Performance Backtesting:** Benchmark execution speeds (C++ parallel core vs. Python baseline traversal) and calculate recall against labeled ground-truth scam datasets.

---

## References

1. **Chen, Y., et al. (2025).** *A Graph-Based Approach to Blockchain Fraud Prevention.* arXiv preprint arXiv:2505.24284. [https://arxiv.org/pdf/2505.24284](https://arxiv.org/pdf/2505.24284)
2. **Wu, J., et al. (2023).** *Towards Understanding Crypto Money Laundering in Web3: Heuristic Transaction Tracing and Empirical Analysis.* arXiv preprint arXiv:2305.14748. [https://arxiv.org/pdf/2305.14748](https://arxiv.org/pdf/2305.14748)
3. **Lin, H., et al. (2026).** *BlazingAML: High-Throughput Anti-Money Laundering System via Graph Pattern Mining.* arXiv preprint arXiv:2604.12241. [https://arxiv.org/pdf/2604.12241](https://arxiv.org/pdf/2604.12241)
## References


