"""Poe ferramentas/ no sys.path para os testes importarem dados e analise
sem precisar transformar a pasta em pacote instalavel."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
