from setuptools import setup, find_packages

setup(
    name="mazegen",
    version="0.1.0",
    description=(
        "Génération (parfaite/imparfaite) et résolution de labyrinthes"
    ),
    packages=find_packages(include=["mazegen", "mazegen.*"]),
    python_requires=">=3.10",
)
