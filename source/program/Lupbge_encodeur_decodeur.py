# doit servir à l'encodage
# complresser les donné avec zlib
# le décodage doit être un fichier créer à l'export pour utilisez les donné encoder
import base64
import pathlib
import zlib

dos_test = pathlib.Path(__file__).parent.parent.parent / "test"
decodeElem = dos_test / "sortie_decoder"

jsonEncode = decodeElem / "cofiguration.json"
fichier_encode_json = {}

if not decodeElem.exists(): decodeElem.mkdir(exist_ok=True)

def encodage(element, sortie):
    if not sortie.exists(): sortie.touch(exist_ok=True)
    # lire puis encoder le fichier
    with open(element, 'rb') as f:
        data = f.read()
        encode = base64.b64encode(data)
        print(encode)
    
    enregistrement_encodage(encode, sortie)
    compresser_encode(encode, sortie)
        

def compresser_encode(element, sortie):
    print("ZLIB en action")
    niv_compression = zlib.compressobj(level=9)
    data = niv_compression.compress(element) + niv_compression.flush()
    export = sortie.with_suffix('.zlib')

    with open(export, 'wb') as f:
        f.write(data)

def enregistrement_encodage(element, sortie):
    with open(sortie, "wb") as f:
        f.write(element)

def decodeur(element=None):
    print("Decodeur 64")

if __name__ == "__main__":
    print(dos_test)
    print(decodeElem)
    encodage((dos_test / "dépendence utils.txt"), (decodeElem / "dépendence utils.txt"))