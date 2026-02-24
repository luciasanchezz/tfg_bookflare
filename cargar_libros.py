from books.models import Libro, Biblioteca, Inventario
import random

biblio, _ = Biblioteca.objects.get_or_create(
    nombre="Biblioteca Central",
    defaults={"slug": "biblioteca-central"},
)

datos = [
    ("9780000000001", "El nombre del viento", "Patrick Rothfuss", "Fantasía", 2007),
    ("9780000000002", "El temor de un hombre sabio", "Patrick Rothfuss", "Fantasía", 2011),
    ("9780000000003", "1984", "George Orwell", "Distopía", 1949),
    ("9780000000004", "Rebelión en la granja", "George Orwell", "Sátira", 1945),
    ("9780000000005", "Dune", "Frank Herbert", "Ciencia ficción", 1965),
    ("9780000000006", "Fundación", "Isaac Asimov", "Ciencia ficción", 1951),
    ("9780000000007", "Yo, robot", "Isaac Asimov", "Ciencia ficción", 1950),
    ("9780000000008", "El Hobbit", "J. R. R. Tolkien", "Fantasía", 1937),
    ("9780000000009", "El señor de los anillos", "J. R. R. Tolkien", "Fantasía", 1954),
    ("9780000000010", "Fahrenheit 451", "Ray Bradbury", "Distopía", 1953),
    ("9780000000011", "Crónica de una muerte anunciada", "Gabriel García Márquez", "Novela", 1981),
    ("9780000000012", "Cien años de soledad", "Gabriel García Márquez", "Novela", 1967),
    ("9780000000013", "La sombra del viento", "Carlos Ruiz Zafón", "Misterio", 2001),
    ("9780000000014", "El juego del ángel", "Carlos Ruiz Zafón", "Misterio", 2008),
    ("9780000000015", "Los pilares de la tierra", "Ken Follett", "Histórica", 1989),
    ("9780000000016", "El psicoanalista", "John Katzenbach", "Thriller", 2002),
    ("9780000000017", "El código Da Vinci", "Dan Brown", "Thriller", 2003),
    ("9780000000018", "La carretera", "Cormac McCarthy", "Distopía", 2006),
    ("9780000000019", "Neuromante", "William Gibson", "Ciencia ficción", 1984),
    ("9780000000020", "El extranjero", "Albert Camus", "Novela", 1942),
]

creados = 0
for isbn, titulo, autor, genero, anio in datos:
    libro, was_created = Libro.objects.get_or_create(
        isbn=isbn,
        defaults={
            "titulo": titulo,
            "autor": autor,
            "genero": genero,
            "anio": anio,
            "descripcion": f"Libro de ejemplo: {titulo}.",
        },
    )

    Inventario.objects.get_or_create(
        biblioteca=biblio,
        libro=libro,
        defaults={"licencias_totales": random.randint(1, 8)},
    )

    if was_created:
        creados += 1

print("listo:", creados, "libros nuevos creados")
