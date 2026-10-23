"""Datos del problema: el planeta Veguitto, sus regiones y las restricciones.

Las coordenadas, prioridades y radios son los del enunciado; solo cambian el
planeta y los nombres (ver docs/01-definicion-del-problema.md).
"""

from dataclasses import dataclass, field, replace

PESOS_PRIORIDAD = {"alta": 3.0, "media": 2.0, "normal": 1.0}


@dataclass(frozen=True)
class Planeta:
    nombre: str = "Veguitto"
    radio_km: float = 5200.0


@dataclass(frozen=True)
class Region:
    nombre: str
    equivale_a: str
    lat: float
    lon: float
    prioridad: str  # "alta", "media" o "normal"

    @property
    def centro(self):
        return (self.lat, self.lon)


@dataclass(frozen=True)
class Zona:
    """Casquete esférico donde no se permite colocar satélites."""
    nombre: str
    lat: float
    lon: float
    radio_grados: float
    tipo: str  # "escombros" u "ocupada"
    equivale_a: str = ""

    @property
    def centro(self):
        return (self.lat, self.lon)


@dataclass(frozen=True)
class Escenario:
    nombre: str
    planeta: Planeta = field(default_factory=Planeta)
    regiones: tuple = ()
    zonas: tuple = ()
    num_satelites: int = 8
    altitud_km: float = 600.0
    semiangulo_sensor: float = 35.0
    radio_observacion_km: float = 300.0
    pesos: dict = field(default_factory=lambda: dict(PESOS_PRIORIDAD))
    peso_redundancia: float = 0.10
    umbral_cubierta: float = 0.95
    separacion_minima: float = 1.0
    anillos_muestra: tuple = (6, 12, 18)

    # --- Variantes: cada una devuelve un escenario nuevo, no modifica este ---

    def con_zona(self, zona, nombre=None):
        return replace(self, zonas=self.zonas + (zona,), nombre=nombre or self.nombre + " + " + zona.nombre)

    def sin_zonas(self, nombre=None):
        return replace(self, zonas=(), nombre=nombre or self.nombre + " (sin zonas)")

    def con_prioridad(self, nombre_region, prioridad, nombre=None):
        regiones = tuple(replace(r, prioridad=prioridad) if r.nombre == nombre_region else r for r in self.regiones)
        if regiones == self.regiones and not any(r.nombre == nombre_region for r in self.regiones):
            raise ValueError(f"No existe la región {nombre_region!r}")
        return replace(self, regiones=regiones,
                       nombre=nombre or f"{self.nombre} ({nombre_region} → {prioridad})")

    def con(self, **cambios):
        return replace(self, **cambios)


REGIONES = (
    Region("Meseta Saiyan", "Península de Yucatán, México", 20.5, -89.0, "alta"),
    Region("Selva Namek", "Amazonía brasileña", -3.5, -62.0, "alta"),
    Region("Valle Capsule", "California, EE. UU.", 36.8, -119.4, "media"),
    Region("Llanura Kaio", "Región del Sahel, África", 15.0, 0.0, "media"),
    Region("Archipiélago Zenkai", "Japón", 36.0, 138.0, "media"),
    Region("Desierto Kami", "Interior de Australia", -25.0, 133.0, "normal"),
)

ZONAS_ESCOMBROS = (
    Zona("Cinturón de escombros Norte", 45.0, -35.0, 12.0, "escombros", "Atlántico Norte"),
    Zona("Cinturón de escombros Sur", -30.0, -120.0, 10.0, "escombros", "Pacífico Sur"),
    Zona("Casquete de escombros polar", 78.0, 30.0, 8.0, "escombros", "Región polar norte"),
)

OBJETOS_OCUPADOS = (
    Zona("Objeto A", 10.0, 45.0, 5.0, "ocupada", "Objeto A"),
    Zona("Objeto B", -15.0, 110.0, 5.0, "ocupada", "Objeto B"),
)


def escenario_etapa1():
    """Primera etapa: solo las regiones, sin restricciones espaciales."""
    return Escenario(nombre="Etapa 1 — sin restricciones", regiones=REGIONES)


def escenario_etapa2():
    """Segunda etapa: regiones + zonas de escombros + objetos ocupados."""
    return Escenario(nombre="Etapa 2 — con restricciones", regiones=REGIONES,
                     zonas=ZONAS_ESCOMBROS + OBJETOS_OCUPADOS)
