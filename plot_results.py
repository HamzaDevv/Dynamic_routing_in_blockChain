#!/usr/bin/env python3
"""
PCER-T Simulation Results — Publication-Quality Plots
Reads: battery_log_ALL.csv, packet_log_ALL.csv, simulation_summary_ALL.csv
Outputs: 8 PNG charts into Visual_artifacts/

Label mapping:  pcertv3 → PCER-T V1,  pcertv4 → PCER-T V2
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────
OUT = Path('Visual_artifacts')
OUT.mkdir(exist_ok=True)

# Label mapping: internal name → display label
LABELS = {
    'baseline': 'OSPF Baseline',
    'rpl':      'RPL-MRHOF+Trust',
    'pcertv3':  'PCER-T V1',
    'pcertv4':  'PCER-T V2',
}
PROTO_ORDER = ['baseline', 'rpl', 'pcertv3', 'pcertv4']
COLORS = {
    'baseline': '#ef4444',
    'rpl':      '#8b5cf6',
    'pcertv3':  '#f59e0b',
    'pcertv4':  '#06b6d4',
}

# ── Shared style ──────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 12,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.facecolor': '#fafbfc',
    'axes.facecolor': '#fafbfc',
    'figure.dpi': 180,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.2,
})

# ── Load Data ─────────────────────────────────────────────────────────
print("Loading CSVs...")
bat = pd.read_csv('battery_log_ALL.csv')
pkt = pd.read_csv('packet_log_ALL.csv')
summary = pd.read_csv('simulation_summary_ALL.csv')

# Clean numeric columns
bat['time'] = pd.to_numeric(bat['time'], errors='coerce')
bat['battery'] = pd.to_numeric(bat['battery'], errors='coerce')
bat['nodeId'] = pd.to_numeric(bat['nodeId'], errors='coerce')
pkt['time'] = pd.to_numeric(pkt['time'], errors='coerce')
pkt['latency'] = pd.to_numeric(pkt['latency'], errors='coerce')
pkt['simLatency'] = pd.to_numeric(pkt['simLatency'], errors='coerce')
pkt['success'] = pd.to_numeric(pkt['success'], errors='coerce')
pkt['hops'] = pd.to_numeric(pkt['hops'], errors='coerce')
pkt['tag'] = pd.to_numeric(pkt['tag'], errors='coerce')

summary['packets_delivered'] = pd.to_numeric(summary['packets_delivered'], errors='coerce')
summary['packets_dropped'] = pd.to_numeric(summary['packets_dropped'], errors='coerce')
summary['total_packets'] = pd.to_numeric(summary['total_packets'], errors='coerce')
summary['loss_rate_pct'] = pd.to_numeric(summary['loss_rate_pct'], errors='coerce')
summary['avg_latency'] = pd.to_numeric(summary['avg_latency'], errors='coerce')
summary['jitter'] = pd.to_numeric(summary['jitter'], errors='coerce')

def lbl(proto):
    return LABELS.get(proto, proto)

# ═══════════════════════════════════════════════════════════════════════
# CHART 1: Packet Delivery Ratio (PDR) Bar Chart
# ═══════════════════════════════════════════════════════════════════════
print("1/8  Packet Delivery Ratio...")
fig, ax = plt.subplots(figsize=(8, 5))
protos = [p for p in PROTO_ORDER if p in summary['protocol'].values]
pdr_vals = []
for p in protos:
    row = summary[summary['protocol'] == p].iloc[0]
    total = row['total_packets']
    pdr = (row['packets_delivered'] / total * 100) if total > 0 else 0
    pdr_vals.append(pdr)

bars = ax.bar([lbl(p) for p in protos], pdr_vals,
              color=[COLORS[p] for p in protos], edgecolor='white', linewidth=1.5,
              width=0.55, zorder=3)
for bar, val in zip(bars, pdr_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
            f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

ax.set_ylabel('Packet Delivery Ratio (%)')
ax.set_title('Packet Delivery Ratio — All Protocols')
ax.set_ylim(0, 110)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(100))
ax.grid(axis='y', alpha=0.3, linestyle='--')
fig.savefig(OUT / '01_packet_delivery_ratio.png')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# CHART 2: Packet Loss Comparison (Stacked by Tag)
# ═══════════════════════════════════════════════════════════════════════
print("2/8  Packet Loss by Traffic Class...")
fig, ax = plt.subplots(figsize=(8, 5))
tag_names = {0: 'Critical', 1: 'Standard', 2: 'Bulk'}
tag_colors = {'Critical': '#ef4444', 'Standard': '#f59e0b', 'Bulk': '#3b82f6'}

x = np.arange(len(protos))
width = 0.55
bottoms = np.zeros(len(protos))

for tag_id in [0, 1, 2]:
    vals = []
    for p in protos:
        row = summary[summary['protocol'] == p].iloc[0]
        dropped_col = f'{tag_names[tag_id].lower()}_dropped'
        vals.append(row.get(dropped_col, 0))
    vals = [float(v) for v in vals]
    ax.bar(x, vals, width, bottom=bottoms, label=tag_names[tag_id],
           color=tag_colors[tag_names[tag_id]], edgecolor='white', linewidth=0.8, zorder=3)
    bottoms += np.array(vals)

for i, total in enumerate(bottoms):
    if total > 0:
        ax.text(i, total + 0.5, f'{int(total)}', ha='center', va='bottom',
                fontweight='bold', fontsize=11)

ax.set_xticks(x)
ax.set_xticklabels([lbl(p) for p in protos])
ax.set_ylabel('Packets Dropped')
ax.set_title('Packet Loss by Traffic Class')
ax.legend(loc='upper left', framealpha=0.9)
ax.grid(axis='y', alpha=0.3, linestyle='--')
fig.savefig(OUT / '02_packet_loss_comparison.png')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# CHART 3: Average Latency Comparison
# ═══════════════════════════════════════════════════════════════════════
print("3/8  Average Latency...")
fig, ax = plt.subplots(figsize=(8, 5))
lat_vals = [float(summary[summary['protocol'] == p].iloc[0]['avg_latency']) for p in protos]

bars = ax.bar([lbl(p) for p in protos], lat_vals,
              color=[COLORS[p] for p in protos], edgecolor='white', linewidth=1.5,
              width=0.55, zorder=3)
for bar, val in zip(bars, lat_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.1f}ms', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.set_ylabel('Average Latency (ms)')
ax.set_title('Average End-to-End Latency — All Protocols')
ax.grid(axis='y', alpha=0.3, linestyle='--')
fig.savefig(OUT / '03_avg_latency_comparison.png')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# CHART 4: Latency CDF (Cumulative Distribution)
# ═══════════════════════════════════════════════════════════════════════
print("4/8  Latency CDF...")
fig, ax = plt.subplots(figsize=(8, 5))
for p in protos:
    subset = pkt[(pkt['proto'] == p) & (pkt['success'] == 1)]
    if len(subset) == 0:
        continue
    lats = np.sort(subset['latency'].values)
    cdf = np.arange(1, len(lats) + 1) / len(lats)
    ax.plot(lats, cdf, label=lbl(p), color=COLORS[p], linewidth=2.2)

ax.set_xlabel('Latency (ms)')
ax.set_ylabel('Cumulative Probability')
ax.set_title('Latency CDF — All Protocols')
ax.legend(loc='lower right', framealpha=0.9)
ax.grid(alpha=0.3, linestyle='--')
ax.set_ylim(0, 1.05)
fig.savefig(OUT / '04_latency_cdf.png')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# CHART 5: Battery Depletion Over Time (battery-powered nodes only)
# ═══════════════════════════════════════════════════════════════════════
print("5/8  Battery Depletion...")
fig, ax = plt.subplots(figsize=(10, 5.5))
bat_nodes = bat[bat['type'].isin(['fast', 'med'])]

for p in protos:
    subset = bat_nodes[bat_nodes['proto'] == p]
    if len(subset) == 0:
        continue
    avg_bat = subset.groupby('time')['battery'].mean().reset_index()
    avg_bat = avg_bat.sort_values('time')
    ax.plot(avg_bat['time'], avg_bat['battery'], label=lbl(p),
            color=COLORS[p], linewidth=2.2)

ax.axhline(y=8, color='#f97316', linestyle='--', alpha=0.6, linewidth=1, label='Soft Floor (8%)')
ax.axhline(y=3, color='#ef4444', linestyle='--', alpha=0.6, linewidth=1, label='Hard Floor (3%)')
ax.set_xlabel('Simulation Time (s)')
ax.set_ylabel('Average Battery (%)')
ax.set_title('Battery Depletion — Battery-Powered Nodes')
ax.legend(loc='upper right', framealpha=0.9, fontsize=9)
ax.grid(alpha=0.3, linestyle='--')
ax.set_ylim(0, 100)
fig.savefig(OUT / '05_battery_depletion.png')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# CHART 6: Jitter Comparison
# ═══════════════════════════════════════════════════════════════════════
print("6/8  Jitter Comparison...")
fig, ax = plt.subplots(figsize=(8, 5))
jit_vals = [float(summary[summary['protocol'] == p].iloc[0]['jitter']) for p in protos]

bars = ax.bar([lbl(p) for p in protos], jit_vals,
              color=[COLORS[p] for p in protos], edgecolor='white', linewidth=1.5,
              width=0.55, zorder=3)
for bar, val in zip(bars, jit_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val:.1f}ms', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.set_ylabel('Jitter (ms)')
ax.set_title('Jitter (Latency Variation) — All Protocols')
ax.grid(axis='y', alpha=0.3, linestyle='--')
fig.savefig(OUT / '06_jitter_comparison.png')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# CHART 7: Protocol Radar Chart (Multi-Metric)
# ═══════════════════════════════════════════════════════════════════════
print("7/8  Protocol Radar...")
fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

categories = ['PDR', 'Low Latency', 'Low Jitter', 'Low Loss', 'Throughput']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

for p in protos:
    row = summary[summary['protocol'] == p].iloc[0]
    total = float(row['total_packets'])
    dlv = float(row['packets_delivered'])
    pdr = (dlv / total * 100) if total > 0 else 0
    lat = float(row['avg_latency'])
    jit = float(row['jitter'])
    loss = float(row['loss_rate_pct'])

    # Normalize to 0-1 scale (higher is better)
    pdr_n = pdr / 100
    lat_n = max(0, 1 - lat / 120)      # lower latency = better
    jit_n = max(0, 1 - jit / 50)       # lower jitter = better
    loss_n = max(0, 1 - loss / 25)     # lower loss = better
    tput_n = min(1, dlv / 220)         # higher throughput = better

    values = [pdr_n, lat_n, jit_n, loss_n, tput_n]
    values += values[:1]

    ax.plot(angles, values, 'o-', linewidth=2, label=lbl(p), color=COLORS[p], markersize=5)
    ax.fill(angles, values, alpha=0.1, color=COLORS[p])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 1.1)
ax.set_title('Protocol Performance Radar', pad=25, fontsize=14, fontweight='bold')
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), framealpha=0.9, fontsize=9)
fig.savefig(OUT / '07_protocol_radar.png')
plt.close()

# ═══════════════════════════════════════════════════════════════════════
# CHART 8: Hop Count Distribution (Box Plot)
# ═══════════════════════════════════════════════════════════════════════
print("8/8  Hop Count Distribution...")
fig, ax = plt.subplots(figsize=(8, 5))
hop_data = []
hop_labels = []
for p in protos:
    subset = pkt[(pkt['proto'] == p) & (pkt['success'] == 1)]
    if len(subset) > 0:
        hop_data.append(subset['hops'].values)
        hop_labels.append(lbl(p))

bp = ax.boxplot(hop_data, labels=hop_labels, patch_artist=True,
                boxprops=dict(linewidth=1.5),
                medianprops=dict(color='#1e293b', linewidth=2),
                whiskerprops=dict(linewidth=1.2),
                capprops=dict(linewidth=1.2))
for patch, p in zip(bp['boxes'], protos):
    patch.set_facecolor(COLORS[p])
    patch.set_alpha(0.6)

ax.set_ylabel('Hop Count')
ax.set_title('Hop Count Distribution — Successful Packets')
ax.grid(axis='y', alpha=0.3, linestyle='--')
fig.savefig(OUT / '08_hop_count_distribution.png')
plt.close()

# ── Summary Table ─────────────────────────────────────────────────────
print("\n" + "═"*70)
print("  SIMULATION RESULTS SUMMARY")
print("═"*70)
print(f"{'Protocol':<20} {'Delivered':>10} {'Dropped':>10} {'PDR':>8} {'Latency':>10} {'Jitter':>8}")
print("─"*70)
for p in protos:
    row = summary[summary['protocol'] == p].iloc[0]
    total = float(row['total_packets'])
    dlv = int(row['packets_delivered'])
    drp = int(row['packets_dropped'])
    pdr = (dlv / total * 100) if total > 0 else 0
    lat = float(row['avg_latency'])
    jit = float(row['jitter'])
    print(f"{lbl(p):<20} {dlv:>10} {drp:>10} {pdr:>7.1f}% {lat:>9.1f}ms {jit:>7.1f}ms")
print("═"*70)
print(f"\n✅ All 8 charts saved to {OUT}/")
print("   01_packet_delivery_ratio.png")
print("   02_packet_loss_comparison.png")
print("   03_avg_latency_comparison.png")
print("   04_latency_cdf.png")
print("   05_battery_depletion.png")
print("   06_jitter_comparison.png")
print("   07_protocol_radar.png")
print("   08_hop_count_distribution.png")
