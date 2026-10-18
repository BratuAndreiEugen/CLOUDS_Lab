import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def plot_latency(json_filepath):
    with open(json_filepath, 'r') as file:
        data = json.load(file)
    
    platforms = data.get('platforms', {})
    vm_ms = platforms['vm']['warm_ms']
    cr_ms = platforms['cloudrun']['warm_ms']
    cf_ms = platforms['function']['warm_ms']

    df = pd.DataFrame({
        'Compute Engine (VM)': vm_ms,
        'Cloud Run': cr_ms,
        'Cloud Functions': cf_ms
    })
    
    plt.figure(figsize=(9, 6))
    
    sns.boxplot(data=df, palette="pastel", width=0.5)
    
    sns.stripplot(data=df, color="black", alpha=0.6, jitter=True, size=6)
    
    plt.title('Warm Request Latency by Platform', fontsize=14, pad=15)
    plt.ylabel('Latency (ms)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('latency_plot.png', dpi=300)
    print("Graph saved successfully as 'latency_plot.png'.")
    
    plt.show()

if __name__ == "__main__":
    plot_latency('../submission/phase1_report.json')