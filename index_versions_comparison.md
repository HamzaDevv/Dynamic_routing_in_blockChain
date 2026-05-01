# PCER IoT Routing Simulation: Version Comparison

This document outlines the differences and evolutionary changes across the three main versions of the PCER IoT Routing Simulation.

## 1. `index.html` (PCER Mesh Overhaul)
**Overview**: The foundational version of the simulation featuring a clean light-themed UI and introducing the core Proposed PCER concept against traditional baselines.

* **Design & Theme**: Light mode (`#f0f4f8` background) using Inter and JetBrains Mono fonts.
* **Protocols Supported**:
  * Baseline (OSPF)
  * Traditional PCER
  * Proposed PCER
  * Industry RPL
* **Routing Logic & Features**:
  * **Hard Energy Floor**: Nodes are hard-blocked at a 5% battery threshold.
  * **Binary Tag-Weights**: Basic all-or-nothing QoS tag handling.
  * **Core Metrics**: Simple delay-based routing without complex trust metrics or link degradation handling.

## 2. `index_v2.html` (PCER-T v3 — Final Optimised)
**Overview**: A major overhaul introducing a dark theme and the synthesized **PCER-T (Priority-Conscious Energy-Resilient with Trust)** protocol, which fuses features from multiple advanced routing algorithms.

* **Design & Theme**: Sleek dark mode (`#080c14` background) utilizing Space Grotesk, IBM Plex Mono, and Syne fonts.
* **Protocols Supported**:
  * OSPF Baseline
  * RPL-MRHOF+Trust
  * PCER-T (Final v3)
* **Routing Logic & Features**:
  * **Fractional QoS Tag-Weights**: Replaced binary tag-weights with blended fractional weights (Critical = speed-first, Bulk = energy-first, Standard = balanced).
  * **Trust Guard & NFR Blacklisting**: Tracks forwarding PDR (Packet Delivery Ratio) per node and penalizes chronic droppers.
  * **Soft Energy Floor**: Replaced the hard 5% cliff with an 8% "demotion zone" (gradual penalty) before a hard block at 3%.
  * **Load Balancer**: Ties in route costs are broken by forwarding history to spread network wear.
  * **Deep Dive Tab**: Added an educational dashboard explaining the math behind the cost functions.

## 3. `index_v3.html` (PCER-T v4 — Adaptive Hybrid)
**Overview**: The most advanced "cyber" version, integrating explicit RPL-MRHOF link metrics into the PCER-T v3 framework to create a highly robust Hybrid routing protocol.

* **Design & Theme**: Deep cyber/sci-fi dark theme (`#060910` background) with animated scan lines. Uses Rajdhani, Share Tech Mono, and Exo 2 fonts.
* **Protocols Supported**:
  * OSPF Baseline
  * RPL-MRHOF+Trust
  * PCER-T v3
  * PCER-T v4 Hybrid
* **Routing Logic & Features**:
  * **MRHOF ETX Link Metric**: Moves beyond static delay by incorporating Expected Transmission Count (ETX). Edges now have probabilistic link quality that affects routing.
  * **Adaptive Hysteresis**: Imports RPL's `MIN_IMPROVEMENT` (15% threshold) to prevent route flapping and oscillations under network noise.
  * **Dual Trust Compound**: Amplifies ETX penalties using a node's trust score, doubling the punishment for chronic droppers.
  * **New Controls**: Added a "Degrade Link ETX" button for testing probabilistic link failures.

## Summary of Evolution
* **Aesthetics**: Progressed from a basic light theme (`index.html`) to a polished dark mode (`index_v2.html`) and finally to a complex cyber-styled UI with scanlines and advanced telemetry (`index_v3.html`).
* **Routing Intelligence**: Evolved from static delay-based routing with hard battery limits to a sophisticated, fractional-weighted hybrid model incorporating Trust, Load Balancing, Hysteresis, and probabilistic ETX link metrics.
