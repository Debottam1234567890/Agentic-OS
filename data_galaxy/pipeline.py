import os
import re
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import MinMaxScaler

def get_comment_rules(file_extension):
    ext = file_extension.lower()
    if ext in ['.js', '.ts', '.java', '.c', '.cpp', '.cs', '.php', '.go', '.rs']:
        return {'single_line': r'//.*', 'multi_line': r'/\*.*?\*/'}
    elif ext in ['.py', '.rb', '.pl', '.sh', '.r', '.ps1']:
        return {'single_line': r'#.*', 'multi_line': r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'' if ext == '.py' else None}
    elif ext in ['.sql']:
        return {'single_line': r'--.*', 'multi_line': r'/\*.*?\*/'}
    elif ext in ['.html', '.xml']:
        return {'single_line': None, 'multi_line': r'<!--[\s\S]*?-->'}
    elif ext in ['.css']:
        return {'single_line': None, 'multi_line': r'/\*.*?\*/'}
    return {'single_line': r'#.*', 'multi_line': None}

def extract_clean_text(input_path):
    """Reads a file, strips comments and trims spaces in-memory."""
    _, ext = os.path.splitext(input_path)
    rules = get_comment_rules(ext)
    
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return ""

    if rules['multi_line']:
        content = re.sub(rules['multi_line'], '', content, flags=re.DOTALL if r'[\s\S]' not in rules['multi_line'] else 0)

    cleaned_lines = []
    for line in content.splitlines():
        if rules['single_line']:
            line = re.sub(rules['single_line'], '', line)
        trimmed_line = line.strip()
        if trimmed_line:
            cleaned_lines.append(trimmed_line)

    return "\n".join(cleaned_lines)

def build_galaxy(workspace_root=None):
    """
    Crawls the workspace, computes TF-IDF and SVD, 
    and saves normalized 2D coordinates to coordinates.json.
    """
    if workspace_root is None:
        workspace_root = os.getcwd()

    ignore_dirs = {'.git', 'venv', '__pycache__', '.chronos_vault', 'sandbox', 'node_modules'}
    
    all_file_contents = []
    all_file_paths = []

    # 1. Crawl Workspace
    for root, dirs, files in os.walk(workspace_root):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.startswith('.') or file.endswith('.json') or file.endswith('.wav') or file.endswith('.log') or file.endswith('.bak'):
                continue
                
            file_path = os.path.join(root, file)
            text = extract_clean_text(file_path)
            if len(text.strip()) > 10:  # Skip effectively empty files
                all_file_contents.append(text)
                # Keep path relative to workspace for cleaner UI
                all_file_paths.append(os.path.relpath(file_path, workspace_root))

    if not all_file_contents:
        print("No valid files found to map.")
        return False

    # 2. Vectorize
    print(f"Mapping {len(all_file_contents)} files in the Data Galaxy...")
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(all_file_contents)

    # 3. Dimensionality Reduction (TruncatedSVD is designed for sparse matrices)
    # If we have less than 2 files, SVD will fail. Fallback gracefully.
    n_components = min(2, len(all_file_contents) - 1)
    if n_components < 1:
        print("Not enough files for 2D mapping.")
        return False
        
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    reduced_coords = svd.fit_transform(tfidf_matrix)

    # If we only got 1 component (because only 2 files existed), pad with 0
    if reduced_coords.shape[1] == 1:
        reduced_coords = np.hstack((reduced_coords, np.zeros((reduced_coords.shape[0], 1))))

    # 4. Normalize coordinates to 0.0 - 1.0 so UI can scale them
    scaler = MinMaxScaler()
    normalized_coords = scaler.fit_transform(reduced_coords)

    # 5. Export JSON Manifest
    manifest = []
    for i, path in enumerate(all_file_paths):
        manifest.append({
            "path": path,
            "x": float(normalized_coords[i, 0]),
            "y": float(normalized_coords[i, 1])
        })

    out_dir = os.path.join(workspace_root, "data_galaxy")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "coordinates.json")
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Galaxy built successfully! Exported to {out_file}")
    return True

if __name__ == "__main__":
    build_galaxy()
