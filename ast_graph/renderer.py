def get_line(x1, y1, x2, y2):
    points = []
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx, sy = 1 if x1 < x2 else -1, 1 if y1 < y2 else -1
    err = dx - dy
    while True:
        points.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
        
    return points

def render_graph(graph, positions, width=80, height=40):
    canvas = [[" " for _ in range(width)] for _ in range(height)]
    for node, edges in graph.items():
        for edge in edges:
            if edge in positions:
                for px, py in get_line(*positions[node], *positions[edge]):
                    if 0 <= py < height and 0 <= px < width:
                        canvas[py][px] = "·"
    for node, (nx, ny) in positions.items():
        label = f"[{node}]"
        for i, char in enumerate(label):
            if 0 <= ny < height and 0 <= nx + i < width:
                canvas[ny][nx + i] = char
    return "\n".join("".join(row) for row in canvas)