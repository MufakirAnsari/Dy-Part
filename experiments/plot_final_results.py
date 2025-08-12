# experiments/plot_final_results.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_results(df: pd.DataFrame):
    """
    Generates and saves the final plots for the paper from the benchmark data.
    """
    # Use a professional plot style
    sns.set_theme(style="whitegrid", palette="viridis")
    
    node_sizes = df['num_nodes'].unique()
    
    # --- Plot 1: AR vs. Noise for each problem size ---
    fig, axes = plt.subplots(1, len(node_sizes), figsize=(18, 6), sharey=True)
    fig.suptitle('Approximation Ratio vs. Hardware Noise Level', fontsize=16, y=1.02)

    for i, nodes in enumerate(node_sizes):
        ax = axes[i]
        subset = df[df['num_nodes'] == nodes]
        
        dypart_data = subset[subset['method'] == 'dypart']
        static_data = subset[subset['method'] == 'static']
        
        ax.plot(dypart_data['noise_level'], dypart_data['approximation_ratio'], 'o-', label='Dy-Part (Dynamic)')
        ax.plot(static_data['noise_level'], static_data['approximation_ratio'], 's--', label='Static (n_sub=4)')
        
        ax.set_xscale('log')
        ax.set_xlabel('2-Qubit Gate Error Rate')
        ax.set_title(f'{nodes}-Node Problem')
        ax.legend()
        ax.grid(True, which="both", ls="--")

    axes[0].set_ylabel('Approximation Ratio')
    plt.savefig("results/final_plot_AR_vs_Noise.png", dpi=300, bbox_inches='tight')
    
    # --- Plot 2: Scheduler's Choice of n_sub vs. Noise ---
    fig, ax = plt.subplots(figsize=(10, 6))
    
    dypart_df = df[df['method'] == 'dypart']
    
    for nodes in node_sizes:
        subset = dypart_df[dypart_df['num_nodes'] == nodes]
        ax.plot(subset['noise_level'], subset['chosen_n_sub'], 'o-', label=f'{nodes}-Node Problem')

    ax.set_xscale('log')
    ax.set_xlabel('2-Qubit Gate Error Rate')
    ax.set_ylabel('Optimal Subgraph Size (chosen_n_sub)')
    ax.set_title("Dy-Part Scheduler's Decision vs. Noise Level")
    ax.legend()
    ax.grid(True, which="both", ls="--")
    plt.savefig("results/final_plot_Choice_vs_Noise.png", dpi=300, bbox_inches='tight')

    print("Final plots saved to 'results/' directory.")
    plt.show()

if __name__ == '__main__':
    # Load the data from our benchmark run
    try:
        data_df = pd.read_csv("results/final_benchmark_data.csv")
        plot_results(data_df)
    except FileNotFoundError:
        print("Error: 'results/final_benchmark_data.csv' not found.")
        print("Please run 'experiments/run_final_benchmark.py' first.")