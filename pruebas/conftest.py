import sys
from pathlib import Path

# Permite importar el paquete `astroshield` al correr pytest desde la raíz.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
