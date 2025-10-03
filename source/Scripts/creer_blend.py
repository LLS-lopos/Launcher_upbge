import sys
import os
from pathlib import Path

def creation(fichier):
    """
    Crée un nouveau fichier .blend vide.
    Cette fonction est conçue pour être appelée depuis Blender.
    """
    try:
        import bpy
        # Démarrer avec une scène vide propre
        bpy.ops.wm.read_factory_settings(use_empty=True)
        # Préparer le chemin de sortie de manière portable
        p = Path(fichier).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        # Sauvegarder le fichier .blend à l'emplacement souhaité
        bpy.ops.wm.save_as_mainfile(filepath=str(p))
        return True
    except Exception as e:
        print(f"Erreur lors de la création du fichier .blend: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    # Vérifier si on est exécuté par Blender
    if '--python-exit-code' in sys.argv:
        # Ce bloc est exécuté par Blender
        if '--' in sys.argv:
            args = sys.argv[sys.argv.index('--') + 1:]
            if args:
                fichier = args[0]
                if creation(fichier):
                    sys.exit(0)
                else:
                    sys.exit(1)
    
    # Si on arrive ici, c'est qu'il y a eu une erreur
    print("Utilisation:")
    print(f"blender -b -P {os.path.basename(__file__)} -- [fichier_sortie.blend]")
    sys.exit(1)