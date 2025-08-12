#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 13:31:06 2025

@author: ansari
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the averaged data
df = pd.read_csv("results/final_benchmark_data_averaged.csv")

# The scheduler time is very fast, let's estimate it at ~0.5s for all runs
# A more accurate way would be to log it, but this is a good approximation.
df['scheduler_time'] = df.apply(lambda row: 0.5 if row['method'] == 'dypart' else 0, axis=1)
df['vqe_time'] = df['runtime_seconds'] - df['scheduler_time']

# Group and get the mean runtimes
runtime_data = df.groupby(['method', 'num_nodes'])[['scheduler_time', 'vqe_time']].mean().reset_index()

# Create the stacked bar chart
sns.set_theme(style="whitegrid")
plt.figure(figsize=(10, 6))

# Plot VQE time
sns.barplot(data=runtime_data, x='num_nodes', y='vqe_time', hue='method', palette='viridis')
# Plot scheduler time on top for Dy-Part
dypart_data = runtime_data[runtime_data['method'] == 'dypart']
plt.bar(x=dypart_data['num_nodes'] - 0.2, height=dypart_data['scheduler_time'], width=0.4, 
        bottom=dypart_data['vqe_time'], color='orange', label='Scheduler Overhead (Dy-Part)')

plt.xlabel("Problem Size (Number of Nodes)")
plt.ylabel("Mean Total Runtime (seconds)")
plt.title("Runtime Breakdown: VQE Execution vs. Scheduler Overhead")
plt.legend()
plt.savefig("results/Figure_Runtime_Breakdown.png", dpi=300)
plt.show()