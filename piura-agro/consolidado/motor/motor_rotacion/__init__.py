"""Motor de rotación de cultivos v1 para Piura (NASA Space Apps 2026, Field Shift)."""
from .catalogo import Catalogo
from .cifra import Cifra
from .entradas import Consulta
from .estado_suelo import EstadoSuelo, actualizar_tras_cosecha
from .motor import Resultado, comparar_secuencias, evaluar

__all__ = ["Catalogo", "Cifra", "Consulta", "EstadoSuelo", "Resultado", "actualizar_tras_cosecha",
           "comparar_secuencias", "evaluar"]
