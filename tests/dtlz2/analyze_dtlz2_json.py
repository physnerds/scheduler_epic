import json
import pandas as pd
import numpy as np
import os,sys
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Tuple

def analyze_dtlz2_experiment(json_file_path: str):
    """
    Analyze the DTLZ2 optimization experiment results from JSON file.
    
    Args:
        json_file_path: Path to the test_dtlz2.json file
    """
    
    # Load the JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    experiment = data['experiment']
    trials_metrics = data['trials_metrics']
    
    print("=== DTLZ2 Experiment Analysis ===\n")
    
    # Basic experiment info
    print(f"Experiment Name: {experiment['name']}")
    print(f"Experiment Type: Multi-objective optimization")
    print(f"Total Trials: {len(experiment['trials'])}")
    print(f"Search Space Dimensions: {len(experiment['search_space']['parameters'])}")
    
    # Search space analysis
    print("\n=== Search Space ===")
    for param in experiment['search_space']['parameters']:
        print(f"Parameter {param['name']}: [{param['lower']}, {param['upper']}]")
    
    # Objectives analysis
    print("\n=== Objectives ===")
    objectives = experiment['optimization_config']['objective']['objectives']
    for obj in objectives:
        metric_name = obj['metric']['name']
        minimize = obj['minimize']
        print(f"Objective {metric_name}: {'Minimize' if minimize else 'Maximize'}")
    
    # Extract trial results
    trial_results = []
    for trial_id, trial_data in experiment['trials'].items():
        trial_idx = int(trial_id)
        
        # Get parameters
        arm = trial_data['generator_run']['arms'][0]
        parameters = arm['parameters']
        
        # Get metrics from data_by_trial
        trial_metrics = {}
        if trial_id in experiment['data_by_trial']:
            data_entries = experiment['data_by_trial'][trial_id]['value']
            for _, data_entry in data_entries:
                df_json = data_entry['df']['value']
                df = pd.read_json(df_json)
                for _, row in df.iterrows():
                    trial_metrics[row['metric_name']] = row['mean']
        
        # Get timing info
        timing_info = trials_metrics.get(trial_id, {})
        
        trial_results.append({
            'trial_id': trial_idx,
            'x0': parameters['x0'],
            'x1': parameters['x1'],
            'f1': trial_metrics.get('f1', None),
            'f2': trial_metrics.get('f2', None),
            'time_used': timing_info.get('time_used', None),
            'status': trial_data['status']['name']
        })
    
    # Convert to DataFrame for easier analysis
    df_results = pd.DataFrame(trial_results)
    df_results = df_results.sort_values('trial_id')
    
    print("\n=== Trial Results ===")
    print(df_results.to_string(index=False, float_format='%.6f'))
    
    # Statistical analysis
    print("\n=== Statistical Summary ===")
    completed_trials = df_results[df_results['status'] == 'COMPLETED']
    
    if len(completed_trials) > 0:
        print(f"Completed Trials: {len(completed_trials)}")
        print(f"Average execution time: {completed_trials['time_used'].mean():.2f} seconds")
        print(f"Total execution time: {completed_trials['time_used'].sum():.2f} seconds")
        
        print("\nObjective Statistics:")
        for obj_name in ['f1', 'f2']:
            if obj_name in completed_trials.columns:
                values = completed_trials[obj_name].dropna()
                if len(values) > 0:
                    print(f"{obj_name}: min={values.min():.6f}, max={values.max():.6f}, "
                          f"mean={values.mean():.6f}, std={values.std():.6f}")
    
    # Pareto front analysis
    print("\n=== Pareto Front Analysis ===")
    pareto_points = find_pareto_front(completed_trials[['f1', 'f2']].values)
    pareto_trials = completed_trials.iloc[pareto_points]
    
    print(f"Number of Pareto optimal points: {len(pareto_points)}")
    print("Pareto optimal trials:")
    print(pareto_trials[['trial_id', 'x0', 'x1', 'f1', 'f2']].to_string(index=False, float_format='%.6f'))
    
    # Visualization
    create_visualizations(completed_trials, pareto_trials)
    
    return df_results, pareto_trials

def find_pareto_front(objectives: np.ndarray) -> List[int]:
    """
    Find Pareto optimal points (assuming minimization for both objectives).
    
    Args:
        objectives: Array of shape (n_points, n_objectives)
    
    Returns:
        List of indices of Pareto optimal points
    """
    n_points = objectives.shape[0]
    pareto_indices = []
    
    for i in range(n_points):
        is_pareto = True
        for j in range(n_points):
            if i != j:
                # Check if point j dominates point i
                if np.all(objectives[j] <= objectives[i]) and np.any(objectives[j] < objectives[i]):
                    is_pareto = False
                    break
        if is_pareto:
            pareto_indices.append(i)
    
    return pareto_indices

def create_visualizations(df_results: pd.DataFrame, pareto_trials: pd.DataFrame):
    """
    Create visualizations for the DTLZ2 experiment results.
    
    Args:
        df_results: DataFrame with all trial results
        pareto_trials: DataFrame with Pareto optimal trials
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Objective space plot
    ax1 = axes[0, 0]
    ax1.scatter(df_results['f1'], df_results['f2'], alpha=0.6, label='All trials')
    ax1.scatter(pareto_trials['f1'], pareto_trials['f2'], color='red', s=100, label='Pareto front')
    ax1.set_xlabel('f1')
    ax1.set_ylabel('f2')
    ax1.set_title('Objective Space')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Parameter space plot
    ax2 = axes[0, 1]
    ax2.scatter(df_results['x0'], df_results['x1'], alpha=0.6, label='All trials')
    ax2.scatter(pareto_trials['x0'], pareto_trials['x1'], color='red', s=100, label='Pareto optimal')
    ax2.set_xlabel('x0')
    ax2.set_ylabel('x1')
    ax2.set_title('Parameter Space')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Convergence plot (objectives over trials)
    ax3 = axes[1, 0]
    ax3.plot(df_results['trial_id'], df_results['f1'], 'o-', alpha=0.7, label='f1')
    ax3.plot(df_results['trial_id'], df_results['f2'], 's-', alpha=0.7, label='f2')
    ax3.set_xlabel('Trial ID')
    ax3.set_ylabel('Objective Value')
    ax3.set_title('Objectives vs Trial ID')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Execution time plot
    ax4 = axes[1, 1]
    ax4.bar(df_results['trial_id'], df_results['time_used'], alpha=0.7)
    ax4.set_xlabel('Trial ID')
    ax4.set_ylabel('Execution Time (seconds)')
    ax4.set_title('Execution Time per Trial')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def calculate_hypervolume(pareto_front: np.ndarray, reference_point: np.ndarray) -> float:
    """
    Calculate hypervolume indicator for the Pareto front.
    
    Args:
        pareto_front: Array of Pareto optimal points
        reference_point: Reference point for hypervolume calculation
    
    Returns:
        Hypervolume value
    """
    # Simple 2D hypervolume calculation
    if pareto_front.shape[1] != 2:
        raise ValueError("This implementation only supports 2D objectives")
    
    # Sort points by first objective
    sorted_front = pareto_front[np.argsort(pareto_front[:, 0])]
    
    hypervolume = 0.0
    prev_f1 = reference_point[0]
    
    for point in sorted_front:
        f1, f2 = point
        if f1 < reference_point[0] and f2 < reference_point[1]:
            width = prev_f1 - f1
            height = reference_point[1] - f2
            hypervolume += width * height
            prev_f1 = f1
    
    return hypervolume

# Main analysis function
if __name__ == "__main__":
    # Run the analysis
    json_file_path = str(sys.argv[1]) if len(sys.argv) > 1 else sys.exit()

    try:
        df_results, pareto_trials = analyze_dtlz2_experiment(json_file_path)
        
        # Additional analysis
        print("\n=== Additional Analysis ===")
        
        # Calculate hypervolume if we have Pareto points
        if len(pareto_trials) > 0:
            pareto_objectives = pareto_trials[['f1', 'f2']].values
            reference_point = np.array([1.1, 1.1])  # Based on objective thresholds
            hv = calculate_hypervolume(pareto_objectives, reference_point)
            print(f"Hypervolume: {hv:.6f}")
        
        # Performance metrics
        completed_trials = df_results[df_results['status'] == 'COMPLETED']
        if len(completed_trials) > 0:
            print(f"Success rate: {len(completed_trials) / len(df_results) * 100:.1f}%")
            print(f"Average time per trial: {completed_trials['time_used'].mean():.2f}s")
            print(f"Fastest trial: {completed_trials['time_used'].min():.2f}s")
            print(f"Slowest trial: {completed_trials['time_used'].max():.2f}s")
        
    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
        print("Please ensure the file path is correct.")
    except Exception as e:
        print(f"Error analyzing experiment: {e}")