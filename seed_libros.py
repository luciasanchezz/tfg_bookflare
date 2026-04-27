import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookflare.settings")
django.setup()

from books.models import Libro, Biblioteca, Inventario


def crear_libros():

    Libro.objects.all().delete()

    biblioteca, _ = Biblioteca.objects.get_or_create(
        nombre="Biblioteca Central",
        defaults={"slug": "biblioteca-central"}
    )

    libros_data = [
        ("9780000000101", "Don Quijote de la Mancha", "Miguel de Cervantes", "Clásico", 1605),
        ("9780000000102", "La Celestina", "Fernando de Rojas", "Clásico", 1499),
        ("9780000000103", "Fortunata y Jacinta", "Benito Pérez Galdós", "Clásico", 1887),
        ("9780000000104", "La Regenta", "Leopoldo Alas Clarín", "Clásico", 1884),
        ("9780000000105", "El Lazarillo de Tormes", "Anónimo", "Clásico", 1554),

        ("9780000000201", "Moby Dick", "Herman Melville", "Aventura", 1851),
        ("9780000000202", "Orgullo y prejuicio", "Jane Austen", "Romance", 1813),
        ("9780000000203", "Crimen y castigo", "Fiódor Dostoyevski", "Drama", 1866),
        ("9780000000204", "Guerra y paz", "León Tolstói", "Histórico", 1869),
        ("9780000000205", "Drácula", "Bram Stoker", "Terror", 1897),
        ("9780000000206", "Frankenstein", "Mary Shelley", "Ciencia ficción", 1818),
        ("9780000000207", "El retrato de Dorian Gray", "Oscar Wilde", "Filosófico", 1890),
        ("9780000000208", "Alicia en el país de las maravillas", "Lewis Carroll", "Fantástico", 1865),
        ("9780000000209", "Sherlock Holmes", "Arthur Conan Doyle", "Misterio", 1887),
        ("9780000000210", "La isla del tesoro", "Robert Louis Stevenson", "Aventura", 1883),

        ("9780000000301", "Meditaciones", "Marco Aurelio", "Filosofía", 180),
        ("9780000000302", "Así habló Zaratustra", "Friedrich Nietzsche", "Filosofía", 1883),
        ("9780000000303", "Discurso del método", "René Descartes", "Filosofía", 1637),
        ("9780000000304", "Ética", "Baruch Spinoza", "Filosofía", 1677),

        ("9780000000401", "El origen de las especies", "Charles Darwin", "Ciencia", 1859),
        ("9780000000402", "Principia Mathematica", "Isaac Newton", "Ciencia", 1687),
        ("9780000000403", "Viaje al centro de la Tierra", "Julio Verne", "Ciencia ficción", 1864),
        ("9780000000404", "Veinte mil leguas de viaje submarino", "Julio Verne", "Ciencia ficción", 1870),

        ("9780000000501", "Hamlet", "William Shakespeare", "Teatro", 1603),
        ("9780000000502", "Romeo y Julieta", "William Shakespeare", "Teatro", 1597),
        ("9780000000503", "Macbeth", "William Shakespeare", "Teatro", 1606),
        ("9780000000504", "Fuenteovejuna", "Lope de Vega", "Teatro", 1619),
        ("9780000000505", "La vida es sueño", "Calderón de la Barca", "Teatro", 1635),

        ("9780000000601", "Los miserables", "Victor Hugo", "Drama", 1862),
        ("9780000000602", "Anna Karenina", "León Tolstói", "Drama", 1877),
        ("9780000000603", "El conde de Montecristo", "Alexandre Dumas", "Aventura", 1844),
        ("9780000000604", "Madame Bovary", "Gustave Flaubert", "Drama", 1856),
        ("9780000000605", "La metamorfosis", "Franz Kafka", "Existencialismo", 1915),

        ("9780000000701", "Las flores del mal", "Charles Baudelaire", "Poesía", 1857),
        ("9780000000702", "La divina comedia", "Dante Alighieri", "Poesía", 1320),
        ("9780000000703", "El paraíso perdido", "John Milton", "Poesía", 1667),
        ("9780000000704", "Cumbres borrascosas", "Emily Brontë", "Romance", 1847),

        ("9780000000801", "El corazón de las tinieblas", "Joseph Conrad", "Drama", 1899),
        ("9780000000802", "La llamada de la selva", "Jack London", "Aventura", 1903),
        ("9780000000803", "Dr. Jekyll y Mr. Hyde", "Robert L. Stevenson", "Terror", 1886),
        ("9780000000804", "El príncipe", "Nicolás Maquiavelo", "Política", 1532),
        ("9780000000805", "Walden", "Henry David Thoreau", "Filosofía", 1854),
    ]

    for isbn, titulo, autor, genero, anio in libros_data:

        libro = Libro.objects.create(
            isbn=isbn,
            titulo=titulo,
            autor=autor,
            genero=genero,
            descripcion=f"Edición digital de {titulo}. Dominio público.",
            anio=anio
        )

        Inventario.objects.create(
            biblioteca=biblioteca,
            libro=libro,
            licencias_totales=5,
            licencias_ocupadas=0
        )

    print("Libros creados correctamente 🚀")


if __name__ == "__main__":
    crear_libros()