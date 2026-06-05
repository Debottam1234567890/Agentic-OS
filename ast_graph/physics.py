import math
import random

def calculate_layout(graph, width=80, height=40, iterations=50):
    positions = {node: [random.uniform(width*0.2, width*0.8), random.uniform(height*0.2, height*0.8)] for node in graph}
    temp = 2.0 # Initial temperature
    
    for _ in range(iterations):
        forces = {node: [0.0, 0.0] for node in graph}
        for n1 in graph:
            # 1. Repulsion (Coulomb)
            for n2 in graph:
                if n1 == n2:
                    continue
                dx = positions[n1][0] - positions[n2][0]
                dy = (positions[n1][1] - positions[n2][1]) * 2.0 # Aspect ratio correction
                dist = math.hypot(dx, dy) + 0.1

                force = 40.0 / dist # Stronger repulsion to prevent overlap
                forces[n1][0] += (dx / dist) * force
                forces[n1][1] += (dy / dist) * force / 2.0

            # 2. Gravity (Pull to center)
            cx, cy = width / 2, height / 2
            dx = cx - positions[n1][0]
            dy = (cy - positions[n1][1]) * 2.0
            dist = math.hypot(dx, dy) + 0.1
            force = 0.02 * dist # Gentle pull to center
            forces[n1][0] += (dx / dist) * force
            forces[n1][1] += (dy / dist) * force / 2.0

        for node, edges in graph.items():
            # 3. Attraction (Hooke)
            for edge in edges:
                if edge in positions:
                    dx = positions[edge][0] - positions[node][0]
                    dy = (positions[edge][1] - positions[node][1]) * 2.0
                    dist = math.hypot(dx, dy) + 0.1

                    force = 0.08 * dist
                    forces[node][0] += (dx / dist) * force
                    forces[node][1] += (dy / dist) * force / 2.0

                    forces[edge][0] -= (dx / dist) * force
                    forces[edge][1] -= (dy / dist) * force / 2.0
                    
        for node in positions:
            positions[node][0] += forces[node][0] * temp
            positions[node][1] += forces[node][1] * temp
            
        temp *= 0.92 # Cooldown

    # Clamp safely inside boundaries leaving room for text labels
    return {n: (max(2, min(width - 25, int(p[0]))), max(1, min(height - 3, int(p[1])))) for n, p in positions.items()}