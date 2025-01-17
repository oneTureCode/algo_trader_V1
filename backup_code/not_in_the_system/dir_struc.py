import os

def print_dir_structure(start_path, indent=0):
    for item in os.listdir(start_path):
        item_path = os.path.join(start_path, item)
        print("    " * indent + "|-- " + item)
        if os.path.isdir(item_path):
            print_dir_structure(item_path, indent + 1)

# Replace '.' with the path to your project directory
project_dir = '.'  # Current directory
print(f"Directory structure of: {os.path.abspath(project_dir)}\n")
print_dir_structure(project_dir)
