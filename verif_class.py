import os
import ast

def find_duplicate_classes(root_dir):
    class_names = set()
    duplicates = {}

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                if node.name in class_names:
                                    if node.name not in duplicates:
                                        duplicates[node.name] = []
                                    duplicates[node.name].append(filepath)
                                class_names.add(node.name)
                    except Exception as e:
                        print(f"Erreur lors de l'analyse de {filepath}: {e}")

    return duplicates

if __name__ == "__main__":
    duplicate_classes = find_duplicate_classes(".")
    if duplicate_classes:
        print("Classes en double trouvées :")
        for class_name, files in duplicate_classes.items():
            print(f"  - Classe '{class_name}' dans les fichiers suivants :")
            for file in files:
                print(f"    -> {file}")
    else:
        print("Aucune classe en double trouvée.")
