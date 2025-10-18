import networkx as nx
from collections import Counter
import statistics 
import random
#Replace this string with the file location of the dataset
filename="C:\\Users\\somen\\Desktop\\Project\\power_grid_uci.txt"

# Settings for Multi-Point Failure Simulation
multi_point_trials = 100 # How many random sets of APs to test
num_ap_removal = 3  # How many APs to remove simultaneously in each trial


# FUnction to classify articulation points
def classify_impact(increase):
    if increase >= 50:         
        return "Critical Hub / Link"
    elif increase >= 10:       
        return "High-Impact"
    elif increase >= 2:        
        return "Moderate-Impact"
    elif increase == 1:        
        return "Low-Impact"
    else: # increase <= 0      
        return "Minor (Non-critical)"


#Function to carry out AP impact analysis
def analyze_single_ap_impact(G, all_articulation_points, initial_components):
    print(f"  Running {len(all_articulation_points)} independent AP removal experiments...")
    results = []
    total_nodes = G.number_of_nodes()
    
    for i, ap in enumerate(all_articulation_points):
    #    print("hello")
        G_copy = G.copy()
        G_copy.remove_node(ap)
        
        fragments = nx.number_connected_components(G_copy)
        
        # Component Size Analysis
        if fragments > 0:
            component_nodes = list(nx.connected_components(G_copy))
            largest_component = max(component_nodes, key=len) if component_nodes else set()
            lcc_size = len(largest_component)
            lcc_relative_size = lcc_size / (total_nodes - 1) if total_nodes > 1 else 0 # -1 because we removed a node
        else:
            lcc_size = 0
            lcc_relative_size = 0
            largest_component = set()

        results.append({
            "element_id": ap,
            "element_type": "Node (AP)",
            "fragments": fragments,
            "increase": fragments - initial_components,
            "lcc_size": lcc_size,
            "lcc_relative_size": lcc_relative_size
        })
        
        # Progress indicator
        if (i + 1) % 50 == 0 or i == len(all_articulation_points) - 1:
            # FIX: Added flush=True to ensure the counter updates visibly
            print(f"    ...tested AP {i + 1}/{len(all_articulation_points)}", end='\r', flush=True)

    print("\n  AP Analysis completed.")
    return results


#function to carry out bridge impact analysis
def analyze_single_bridge_impact(G, all_bridges, initial_components):
    print(f"  Running {len(all_bridges)} independent bridge removal experiments...")
    results = []
    total_nodes = G.number_of_nodes()

    for i, bridge in enumerate(all_bridges):
        G_copy = G.copy()
        G_copy.remove_edge(*bridge) # Remove the specific edge
        
        fragments = nx.number_connected_components(G_copy)
        
        # Component Size Analysis
        if fragments > 0:
            component_nodes = list(nx.connected_components(G_copy))
            largest_component = max(component_nodes, key=len) if component_nodes else set()
            lcc_size = len(largest_component)
            lcc_relative_size = lcc_size / total_nodes if total_nodes > 0 else 0
        else:
            lcc_size = 0
            lcc_relative_size = 0
            
        results.append({
            "element_id": bridge,
            "element_type": "Edge (Bridge)",
            "fragments": fragments,
            "increase": fragments - initial_components,
            "lcc_size": lcc_size,
            "lcc_relative_size": lcc_relative_size
        })
        
        # Progress indicator
        if (i + 1) % 200 == 0 or i == len(all_bridges) - 1:
            # FIX: Added flush=True to ensure the counter updates visibly
            print(f"    ...tested Bridge {i + 1}/{len(all_bridges)}", end='\r', flush=True)

    print("\n  Bridge Analysis completed.")
    return results

#Function to carry out Multi point AP impact analysis
def analyze_multi_ap_failure(G, all_articulation_points, num_trials, num_aps_per_trial):
    print(f"  Running {num_trials} multi-point failure simulations ({num_aps_per_trial} APs each)...")
    multi_results = []
    
    for i in range(num_trials):
        # Select unique APs for this trial
        aps_to_remove = random.sample(all_articulation_points, num_aps_per_trial)
        
        G_copy = G.copy()
        G_copy.remove_nodes_from(aps_to_remove)
        fragments = nx.number_connected_components(G_copy)
        multi_results.append(fragments)

        if (i + 1) % 20 == 0 or i == num_trials - 1:
            print(f"    ...completed trial {i + 1}/{num_trials}", end='\r', flush=True)

    print("\n  Multi-AP Analysis completed.")

    if not multi_results:
        return None

    return {
        "avg_fragments": statistics.mean(multi_results),
        "max_fragments": max(multi_results),
        "min_fragments": min(multi_results)
    }



####################################################
#Main###############################################
####################################################

if __name__ == "__main__":
    print(f"\n{'-'*80}")
    print(f"Starting Full Analysis for: {filename}")
    print(f"{'-'*80}")
    
    G = nx.read_edgelist(filename, comments='#', nodetype=int, data=False)
    
    print("\n--- Initial State ---")
    print(f"  Graph: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
    initial_components = nx.number_connected_components(G)
    print(f"  Initial Components: {initial_components}")
    
    print("\n--- Articulation Point (AP) Analysis ---")
    all_aps = list(nx.articulation_points(G))
    if not all_aps:
        print("  No Articulation Points found.")
        ap_results = []
    else:
        print(f"  Found {len(all_aps):,} APs.")
        ap_results = analyze_single_ap_impact(G, all_aps, initial_components)


    ####################################################
    ###ResultProcessing#################################
    ####################################################
    if ap_results!=[]:
        ap_results.sort(key=lambda x: x['fragments'], reverse=True)
        print("\n  Top 10 Most Critical APs (by Fragments Created):")
        print(f"  {'AP Node':<12} | {'Fragments':<10} | {'Increase':<10} | {'LCC Size':<12} | {'LCC %':<8} | {'Classification'}")
        print("  " + "-" * 100)
        for res in ap_results[:10]:
            classification = classify_impact(res['increase'])
            
            print(f"  {str(res['element_id']):<12} | {res['fragments']:<10} | {res['increase']:<10} | {res['lcc_size']:<12,} | {res['lcc_relative_size'] * 100:<7.2f}%  | {classification}")
    
        # Summary Stats for APs
        ap_classifications = [classify_impact(res['increase']) for res in ap_results]
        ap_counts = Counter(ap_classifications)
        avg_lcc_size = statistics.mean(res['lcc_relative_size'] for res in ap_results)
        
        print("\n  AP Summary:")
        print(f"    - Critical Hubs (>49):      {ap_counts['Critical Hub / Link']:,}")
        print(f"    - High-Impact (10-49):      {ap_counts['High-Impact']:,}")
        print(f"    - Moderate-Impact (2-9):    {ap_counts['Moderate-Impact']:,}")
        print(f"    - Low-Impact (1):           {ap_counts['Low-Impact']:,}")
        print(f"    - Minor (0):                {ap_counts['Minor (Non-critical)']:,}")
        print(f"    - Avg. LCC Size after AP removal: {avg_lcc_size * 100:.2f}% of remaining nodes")
        

    print("\n--- Bridge Analysis ---")
    all_bridges = list(nx.bridges(G)) if nx.is_connected(G) else []
    if not nx.is_connected(G):
         print("  Graph is disconnected, finding bridges within components...")
         for component in nx.connected_components(G):
             if len(component) > 1:
                 subgraph = G.subgraph(component)
                 all_bridges.extend(list(nx.bridges(subgraph)))
    
    if not all_bridges:
        print("  No Bridges found.")
        bridge_results = []
    else:
        print(f"  Found {len(all_bridges):,} Bridges.")
        bridge_results = analyze_single_bridge_impact(G, all_bridges, initial_components)
    
    # Process Bridge results
    if bridge_results:
        bridge_results.sort(key=lambda x: x['fragments'], reverse=True)
        print("\n  Top 10 Most Critical Bridges (by Fragments Created):")
        print(f"  {'Bridge':<25} | {'Fragments':<10} | {'Increase':<10} | {'LCC Size':<12} | {'LCC %':<8}")
        print("  " + "-" * 85)
        for res in bridge_results[:10]:
            classification = classify_impact(res['increase'])
            print(f"  {str(res['element_id']):<25} | {res['fragments']:<10} | {res['increase']:<10} | {res['lcc_size']:<12,} | {res['lcc_relative_size'] * 100:<7.2f}%")
    
        # Summary Stats for Bridges
        bridge_classifications = [classify_impact(res['increase']) for res in bridge_results]
        bridge_counts = Counter(bridge_classifications)
        avg_lcc_size_bridge = statistics.mean(res['lcc_relative_size'] for res in bridge_results)
    
        print("\n  Bridge Summary:")
        print(f"    - Critical Link (>49):      {bridge_counts['Critical Hub / Link']:,}")
        print(f"    - High-Impact (10-49):      {bridge_counts['High-Impact']:,}")
        print(f"    - Moderate-Impact (2-9):    {bridge_counts['Moderate-Impact']:,}")
        print(f"    - Low-Impact (1):           {bridge_counts['Low-Impact']:,}")
        print(f"    - Minor (0):                {bridge_counts['Minor (Non-critical)']:,} (Should always be 0 for bridges)")
        print(f"    - Avg. LCC Size after Bridge removal: {avg_lcc_size_bridge * 100:.2f}% of original nodes")
    
    
    # --- Multi-Point Failure Simulation (APs) ---
    print("\n--- Multi-Point AP Failure Simulation ---")
    multi_ap_stats = analyze_multi_ap_failure(G, all_aps, multi_point_trials, num_ap_removal)
    if multi_ap_stats:
        print(f"  Simultaneously removing {num_ap_removal} random APs ({multi_point_trials} trials):")
        print(f"    - Average Fragments Created: {multi_ap_stats['avg_fragments']:.2f}")
        print(f"    - Maximum Fragments Created: {multi_ap_stats['max_fragments']}")
        print(f"    - Minimum Fragments Created: {multi_ap_stats['min_fragments']}")
    
    
    ####################################################
    ###Conclusion#######################################
    ####################################################
    print("\n--- Overall Conclusion ---")
    if ap_results:
        ap_counts = Counter([classify_impact(res['increase']) for res in ap_results])
        if ap_counts['Critical Hub / Link'] > 0:
             print("  PRIMARY VULNERABILITY: Critical Hubs (Nodes).")
             print("  The network contains central nodes whose individual failure causes catastrophic fragmentation.")
             print("  While other vulnerabilities exist, securing these hubs is paramount.")
        elif ap_counts['High-Impact'] > 0:
             print("  PRIMARY VULNERABILITY: High-Impact Nodes.")
             print("  Several nodes exist whose failure significantly fragments the network.")
             print("  Targeted hardening of these specific nodes is recommended.")
        elif bridge_results and Counter([classify_impact(res['increase']) for res in bridge_results])['High-Impact'] > 0 :
             print("  PRIMARY VULNERABILITY: High-Impact Bridges (Links).")
             print("  The network's main weakness lies in specific critical links, rather than nodes.")
             print("  Adding redundancy around these key bridges is crucial.")
        elif ap_counts['Moderate-Impact'] > 0 or (bridge_results and Counter([classify_impact(res['increase']) for res in bridge_results])['Moderate-Impact'] > 0):
             print("  PRIMARY VULNERABILITY: Distributed Moderate Fragility.")
             print("  The network lacks catastrophic single points of failure but has widespread")
             print("  moderate or low-impact vulnerabilities (nodes and/or links).")
             print("  Resilience requires broad improvements or tolerance for localized failures.")
        else:
             print("  PRIMARY VULNERABILITY: Low / Minor.")
             print("  The network appears structurally resilient to single point failures (nodes or links).")
    elif bridge_results:
         bridge_counts = Counter([classify_impact(res['increase']) for res in bridge_results])
         if bridge_counts['Critical Hub / Link'] > 0:
              print("  PRIMARY VULNERABILITY: Critical Links (Bridges).")
              print("  The network contains central links whose individual failure causes catastrophic fragmentation.")
         else:
              print("  Network contains bridges, but none cause major fragmentation alone.")
    
    else:
        print("  The network is highly resilient (no APs or Bridges found).")
    
    if multi_ap_stats:
        if multi_ap_stats['max_fragments'] > 50: 
            print("\n  Multi-Point Failures are a SIGNIFICANT CONCERN.")
            print(f"  Simultaneous failure of just {num_ap_removal} APs can lead to catastrophic fragmentation")
            print(f"  (up to {multi_ap_stats['max_fragments']} components observed). Defending against coordinated")
            print("  or cascading failures is critical.")
        elif multi_ap_stats['max_fragments'] > 10:
            print("\n  Multi-Point Failures are a MODERATE CONCERN.")
            print(f"  Simultaneous failure of {num_ap_removal} APs leads to significant fragmentation")
            print(f"  (up to {multi_ap_stats['max_fragments']} components observed).")
    
    print(f"\nAnalysis complete for {filename}.")
    print("\n" + "-"*80)