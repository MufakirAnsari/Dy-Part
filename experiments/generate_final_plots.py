# experiments/generate_final_plots.py
# VERSION 2: Plots mean values with standard deviation error bands.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_ar_vs_noise_averaged(data: pd.DataFrame, num_nodes: int, ax: plt.Axes):
    """
    Plots MEAN Approximation Ratio vs. Noise Level with shaded error bands
    representing one standard deviation.
    """
    sns.set_theme(style="whitegrid")
    
    # Filter data for the specific number of nodes
    df_nodes = data[data['num_nodes'] == num_nodes]
    
    # --- Group by method and noise level to calculate mean and std ---
    grouped = df_nodes.groupby(['method', 'noise_level'])['approximation_ratio']
    mean_ar = grouped.mean().reset_index()
    std_ar = grouped.std().reset_index()
    
    # Merge mean and std dataframes for easy plotting
    plot_data = pd.merge(mean_ar, std_ar, on=['method', 'noise_level'], suffixes=('_mean', '_std'))

    methods = plot_data['method'].unique()
    colors = sns.color_palette("viridis", len(methods))
    markers = ['o', 's']
    linestyles = ['-', '--']

    for i, method in enumerate(methods):
        method_data = plot_data[plot_data['method'] == method]
        
        # Plot the mean line
        ax.plot(method_data['noise_level'], method_data['approximation_ratio_mean'], 
                marker=markers[i], linestyle=linestyles[i],
                label=f'Dy-Part' if method == 'dypart' else f'Static (n_sub=4)', 
                linewidth=2, markersize=7)
        
        # --- NEW: Add the shaded error band (std dev) ---
        ax.fill_between(method_data['noise_level'], 
                        method_data['approximation_ratio_mean'] - method_data['approximation_ratio_std'],
                        method_data['approximation_ratio_mean'] + method_data['approximation_ratio_std'],
                        alpha=0.2)

    ax.set_xscale('log')
    ax.set_title(f'{num_nodes}-Node Graph', fontsize=16)
    ax.set_xlabel('2-Qubit Gate Error Rate (ε_gate)', fontsize=12)
    ax.set_ylabel('Mean Approximation Ratio', fontsize=12)
    ax.axhline(y=1.0, color='red', linestyle=':', label='Ideal Solution (AR=1.0)')
    ax.tick_params(axis='both', which='major', labelsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(bottom=0) # Ensure y-axis starts at 0

def plot_scheduler_decisions_averaged(data: pd.DataFrame, ax: plt.Axes):
    """
    Plots the chosen partition size by the Dy-Part scheduler vs. noise,
    showing the distribution of choices.
    """
    dypart_data = data[data['method'] == 'dypart'].copy()
    
    # Use seaborn's lineplot which can automatically show mean and confidence interval (95% CI)
    sns.lineplot(data=dypart_data, x='noise_level', y='chosen_n_sub', hue='num_nodes',
                 palette='plasma', marker='o', ax=ax, errorbar='sd') # errorbar='sd' shows std dev

    ax.set_xscale('log')
    ax.set_title('Mean Scheduler Decision vs. Noise', fontsize=16)
    ax.set_xlabel('2-Qubit Gate Error Rate (ε_gate)', fontsize=12)
    ax.set_ylabel('Mean Chosen Partition Size (n_sub)', fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=11)
    ax.legend(title='Graph Size', fontsize=11)

if __name__ == "__main__":
    data_path = "results/final_benchmark_data_averaged.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Averaged data file not found at {data_path}. Please run the updated benchmark first.")
        
    df = pd.read_csv(data_path)
    
    # --- Create Figure 1: Performance Comparison (Multi-panel plot) ---
    fig1, axes = plt.subplots(1, 3, figsize=(24, 7), sharey=True)
    fig1.suptitle('Performance Comparison with Statistical Averaging (30 Seeds)', fontsize=22)
    
    node_sizes = sorted(df['num_nodes'].unique())
    for i, size in enumerate(node_sizes):
        plot_ar_vs_noise_averaged(df, size, axes[i])

    fig1.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    output_path1 = "results/Figure_Performance_Comparison_Averaged.png"
    fig1.savefig(output_path1, dpi=300)
    print(f"Averaged performance plot saved to: {output_path1}")
    
    # --- Create Figure 2: Scheduler Decisions ---
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    plot_scheduler_decisions_averaged(df, ax2)

    output_path2 = "results/Figure_Scheduler_Decisions_Averaged.png"
    fig2.savefig(output_path2, dpi=300)
    print(f"Averaged scheduler decisions plot saved to: {output_path2}")
    
    plt.show()