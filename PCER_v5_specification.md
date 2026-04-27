# PCER-v5 Protocol Specification

This document provides a formal, mathematically rigorous specification for the Priority-Coupled Elastic Routing (PCER) Protocol v5. It is designed to address the unique challenges of constrained AIoT environments by coupling application-layer QoS tags with network-layer routing metrics.

## 1. Core Architecture

PCER-v5 operates as a cross-layer protocol. Applications tag traffic with a 2-bit QoS class (Critical, Standard, Bulk). The network layer translates these tags into fractional weight vectors that dynamically shift the routing objective function.

### 1.1 Bi-Directional Backpressure
Unlike traditional open-loop routing, PCER-v5 implements a closed-loop backpressure mechanism. The network layer (L3) continuously monitors the average queue load across the mesh. 
If the global average queue occupancy exceeds the backpressure threshold ($> 60\%$), L3 signals the application layer (L7), which dynamically throttles its packet injection rate to prevent network collapse.

## 2. Objective Function

The routing decision is governed by a dynamic, 5-component cost function. For a given destination $D$, node $u$ evaluates neighbor $v$ based on:

$$P(u, v)_{PCER} = w_d \cdot D(u, v) + w_e \cdot \sigma(R(v)) + w_t \cdot (1 - T(v)) + w_{etx} \cdot E(u, v) + w_l \cdot L(v)$$

Where:
*   $w_d, w_e, w_t, w_{etx}, w_l$: Fractional weights mapped from the QoS tag.
*   $D(u, v)$: Delay (latency + distance to destination).
*   $R(v)$: Remaining resource (battery) of node $v$.
*   $\sigma(x)$: Sigmoid-transformed penalty function.
*   $T(v)$: Trust/Reputation score of node $v$.
*   $E(u, v)$: Link quality (ETX) penalty between $u$ and $v$.
*   $L(v)$: Load factor (queue occupancy) at node $v$.

### 2.1 Weight Vectors
The weights adapt based on the traffic class:
*   **Critical (00)**: $w_d = 0.70, w_e = 0.08, w_t = 0.14, w_{etx} = 0.06, w_l = 0.02$
*   **Standard (01)**: $w_d = 0.38, w_e = 0.30, w_t = 0.18, w_{etx} = 0.08, w_l = 0.06$
*   **Bulk (10)**: $w_d = 0.04, w_e = 0.60, w_t = 0.20, w_{etx} = 0.10, w_l = 0.06$

## 3. Sub-Component Definitions

### 3.1 Energy & Sigmoid Smoothing
Instead of a binary "dead/alive" threshold, PCER-v5 uses a continuous penalty.

$$\sigma(R) = \begin{cases} 
      \infty & R \leq 0.03 \\
      \left(\frac{0.08}{R}\right)^3 \cdot 100 & 0.03 < R < 0.08 \\
      \frac{2.0}{R} & R \geq 0.08
   \end{cases}
$$

### 3.2 Dual Trust Compound & Exploration
Trust $T(v)$ tracks the reputation of node $v$, calculated via a Proof-of-Routing ledger using Packet Delivery Ratio (PDR).
To solve the "Cold-Start" problem where new nodes ($T \approx 0.5$) are ignored, **Bulk Data** performs "Trust Exploration". If a node has neutral trust ($0.45 \leq T(v) \leq 0.55$), the trust penalty is reduced by $90\%$ *only* for Bulk packets, encouraging safe exploration without risking Critical traffic.

### 3.3 Link Quality (MRHOF-ETX)
Borrowed from RFC 6552, ETX measures the expected number of transmissions.
$$E(u, v) = \max(0, (ETX(u, v) - 1.0) \cdot 12.0) \cdot (1 - T(v))$$
Note the "Dual Compound": Poor link quality is amplified if the node also has a low trust score.

### 3.4 Queue & Congestion
Queue occupancy ($q \in [0, 1]$) is strictly penalized:
$$L(v) = \begin{cases} 
      \left(\frac{q - 0.8}{0.2}\right)^2 \cdot 200 & q > 0.8 \\
      (q - 0.5) \cdot 20 & 0.5 < q \leq 0.8 \\
      0 & q \leq 0.5
   \end{cases}
$$

## 4. Stability & Hysteresis

To prevent "Routing Oscillations" (ping-ponging between routes due to load fluctuations), PCER-v5 implements adaptive hysteresis.
Let $C_{old}$ be the cost of the previously preferred parent. A new parent $v'$ with cost $C_{new}$ is only selected if:
$$ \frac{C_{old} - C_{new}}{C_{old}} > m_{stabilityThreshold} $$
Where $m_{stabilityThreshold} = 0.15$ ($15\%$ improvement).

## 5. Loop Prevention & Mid-Flight Rerouting
Packets carry a Time-to-Live (TTL) field. If a packet encounters a dead link or a sudden topological hole mid-flight, it triggers a local recalculation based on the new 5-component cost. The TTL prevents infinite reroute loops if the mesh partitions.
