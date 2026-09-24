# ChainSink: Automated Multi-Hop Blockchain Forensics and Exchange Attribution Pipeline

**ChainSink** is an automated, deterministic blockchain forensics pipeline designed to track fund flows from victim-reported scam addresses, trace multi-hop transactions across peel chains, and attribute terminal deposit nodes to Centralized Exchanges (CEXs) without machine learning overhead.

## Problem Statement

Social engineering attacks, phishing, and advance fee fraud schemes are key challenges faced by crypto asset holders. Fraudsters utilize ledger anonymity to quickly move hacked money through peel chains of wallets and decentralized liquidity pools into liquidation through centralized cryptocurrency exchanges (CEXs). Current blocklists are reactionary measures and fail to capture rapid movement of stolen crypto until it reaches CEXs where the money is withdrawn.

## Project Objectives

1. **Automate Scam Ingestion:** Build a data pipeline to continuously ingest victim-reported suspect wallet addresses from public OSINT repositories (e.g., Chainabuse, CryptoScamDB).

2. **Multi-Hop Graph Traversal:** Develop a directed transaction graph engine using Python `NetworkX` querying public APIs (e.g., Etherscan) to trace outgoing fund flows up to $N$-hops deep.

3. **Deterministic Clustering:** Apply on-chain clustering heuristics (co-spending logic, deposit reuse) to aggregate intermediate addresses into unified entity clusters.

4. **Exchange Attribution:** Map destination sink nodes against public exchange wallet labels (e.g., Binance, Coinbase) to measure proximity distance and pinpoint cash-out endpoints.

5. **Interactive Dashboard:** Build a lightweight web UI using Streamlit and PyVis to render visual fund-flow trees for real-time inspection.

6. **Validate Performance:** Backtest the engine against historical ground-truth scam datasets to measure attribution recall and runtime.

## System Architecture

```
[ OSINT Repository ] (Chainabuse / CryptoScamDB)
         │
         ▼
[ Ingestion Pipeline ] Continuous Ingestion of Victim-Reported Addresses
         │
         ▼
[ Directed Graph Engine ] Multi-Hop BFS Traversal (NetworkX + Web3 APIs)
         │
         ├───> [ Deterministic Clustering ] Co-spending & Deposit Reuse Logic
         │
         ▼
[ Sink Attribution ] Map Terminal Destination Nodes to Exchange Deposit Labels
         │
         ▼
[ Visual Analytics Dashboard ] Streamlit + PyVis Real-Time Fund-Flow Inspection
```

## Project Roadmap

### Phase 1: Mid-Sem Milestones (Immediate Scope)

* **Automate Scam Ingestion:** OSINT data ingestion pipeline setup for victim-reported seed addresses.
* **Multi-Hop Graph Traversal Engine:** Directed graph generation (`NetworkX`) querying block explorer APIs up to $N$-hops.
* **Visual Analytics Prototype:** Initial PyVis interactive rendering for immediate demo/slides export.

### Phase 2: Post Mid-Sem Development

* **Deterministic Clustering:**
  * Multi-input co-spending aggregation.
  * Intermediate deposit address reuse detection.
* **Exchange Attribution Engine:**
  * Terminal sink node mapping against exchange wallet labels.
  * Distance proximity calculations (D(v, E)).

### Phase 3: End-Sem Final Deliverables

* **Interactive Dashboard:** Unifying graph generation, depth controls, and node analytics into Streamlit.
* **Performance Validation & Backtesting:** Evaluating recall and processing runtime across ground-truth scam datasets.

## Tech Stack

* **Language:** Python 3.10+
* **Graph Engine:** NetworkX
* **Visualization:** PyVis, Streamlit
* **APIs & Sources:** Etherscan REST API, Public OSINT Repositories (Chainabuse, CryptoScamDB)
* **Data Processing:** Pandas, JSON

## References

1. **Chen, Y., et al. (2025).** *A Graph-Based Approach to Blockchain Fraud Prevention.* arXiv preprint arXiv:2505.24284. [https://arxiv.org/pdf/2505.24284](https://arxiv.org/pdf/2505.24284)
2. **Wu, J., et al. (2023).** *Towards Understanding Crypto Money Laundering in Web3: Heuristic Transaction Tracing and Empirical Analysis.* arXiv preprint arXiv:2305.14748. [https://arxiv.org/pdf/2305.14748](https://arxiv.org/pdf/2305.14748)
3. **Lin, H., et al. (2026).** *BlazingAML: High-Throughput Anti-Money Laundering System via Graph Pattern Mining.* arXiv preprint arXiv:2604.12241. [https://arxiv.org/pdf/2604.12241](https://arxiv.org/pdf/2604.12241)
