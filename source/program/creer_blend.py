import sys
import os

def creation(fichier):
    """
    Crée un nouveau fichier .blend vide.
    Cette fonction est conçue pour être appelée depuis Blender.
    """
    try:
        import bpy
        # (Optionnel) Supprimer tous les objets de la scène par défaut
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        # Créer le répertoire parent s'il n'existe pas
        os.makedirs(os.path.dirname(os.path.abspath(fichier)), exist_ok=True)
        # Sauvegarder le fichier .blend à l'emplacement souhaité
        bpy.ops.wm.save_as_mainfile(filepath=fichier)
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