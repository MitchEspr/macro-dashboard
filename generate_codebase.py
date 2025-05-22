import os

# Configuration
output_filename = "full_codebase.txt"
excluded_dirs_simple = { # For top-level directory names to skip
    "node_modules", "obj", "bin", "__pycache__", ".git", ".vscode",
    "venv", ".venv", "env", ".env", "dist", "build",
    "coverage", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "site", "docs_build", # Add any other simple dir names
}
# For path segments anywhere in the path that should exclude the path
# This helps catch nested vendor/library folders if not caught by top-level name.
# Use with caution to avoid over-excluding.
excluded_path_segments = {
    os.path.join("lib", "python"), # Common pattern for venv site-packages
    os.path.join("Lib", "site-packages"), # Windows venv
    os.path.join("site-packages"),
    # Add more specific known library paths if needed, e.g., "node_modules" here too as a fallback
    "node_modules" 
}

included_extensions = {
    ".py", ".md", ".yml", ".yaml",  ".sh", ".toml",
    ".css", ".tsx", ".ts", ".html", ".bat", ".ps1",
    ".env.example" 
    # ".py.bak" # Typically excluded
}
root_dir = "."  # Current directory

def path_contains_excluded_segment(path_str: str, segments_to_exclude: set) -> bool:
    """Checks if any part of the path matches any of the excluded segments."""
    # Normalize path separators for consistent matching
    normalized_path = os.path.normpath(path_str)
    path_parts = set(normalized_path.split(os.sep))
    return not segments_to_exclude.isdisjoint(path_parts)


def create_codebase_snapshot():
    with open(output_filename, "w", encoding="utf-8", errors="ignore") as outfile:
        
        project_files_for_listing = []
        project_files_for_content = []

        for root, dirs, files in os.walk(root_dir, topdown=True):
            # 1. Prune recursion into top-level excluded directory names
            dirs[:] = [d for d in dirs if d not in excluded_dirs_simple]

            # 2. Check if the current 'root' itself is part of an excluded path segment
            # This helps skip processing files in already-entered excluded subdirectories deeper down
            # (e.g. if os.walk still yields a path like "some_dir/node_modules/some_file")
            relative_root_path = os.path.relpath(root, root_dir)
            if relative_root_path != "." and path_contains_excluded_segment(relative_root_path, excluded_path_segments):
                dirs[:] = [] # Don't recurse further into this path
                continue     # Don't process files in this root either

            # Prepare files from current directory for listing and content
            current_dir_files_listing = []
            for file_name in sorted(files):
                # Construct relative path for the file
                relative_file_path = os.path.join(relative_root_path, file_name) if relative_root_path != "." else file_name
                
                # Check again if this specific file's path is within an excluded segment
                if path_contains_excluded_segment(relative_file_path, excluded_path_segments):
                    continue

                _, file_extension = os.path.splitext(file_name.lower())
                
                # Add to directory listing
                current_dir_files_listing.append(file_name)
                
                # Decide if content should be added
                if file_extension in included_extensions:
                    absolute_file_path = os.path.join(root, file_name)
                    project_files_for_content.append((relative_file_path, absolute_file_path))
            
            if current_dir_files_listing:
                display_path = "Root Directory" if relative_root_path == "." else relative_root_path
                project_files_for_listing.append((display_path, current_dir_files_listing))

        # Write Directory Structure
        outfile.write("Directory Structure:\n")
        for display_path, files_in_dir in sorted(project_files_for_listing):
            outfile.write(f"{display_path}{os.sep}:\n")
            for file_name in files_in_dir:
                outfile.write(f"  {file_name}\n")
        
        # Write File Contents
        outfile.write("\nFile Contents:\n")
        project_files_for_content.sort() # Sort for consistent output

        for rel_path, abs_path in project_files_for_content:
            outfile.write(f"\n=== {rel_path} ===\n\n")
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as infile:
                    outfile.write(infile.read())
                outfile.write("\n") 
            except Exception as e:
                outfile.write(f"Error reading file {rel_path}: {e}\n")

        # Handle Dockerfile specifically (if it exists in the root_dir)
        dockerfile_path_root = os.path.join(root_dir, "Dockerfile")
        if os.path.exists(dockerfile_path_root):
            is_already_added = any(rel_p == "Dockerfile" for rel_p, _ in project_files_for_content)
            if not is_already_added: # Only add if not already captured by extension rules
                outfile.write(f"\n=== Dockerfile ===\n\n")
                try:
                    with open(dockerfile_path_root, "r", encoding="utf-8", errors="ignore") as infile:
                        outfile.write(infile.read())
                    outfile.write("\n")
                except Exception as e:
                    outfile.write(f"Error reading Dockerfile: {e}\n")

    print(f"Codebase snapshot created: {output_filename}")

if __name__ == "__main__":
    create_codebase_snapshot()