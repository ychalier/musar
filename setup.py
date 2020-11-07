import os
from setuptools import setup
import musar

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='musar',
    version=musar.__version__,
    packages=["musar"],
    include_package_data=True,
    license=musar.__license__,
    description=musar.__doc__,
    long_description=README,
    url='https://github.com/ychalier/musar',
    author=musar.__author__,
    author_email=musar.__email__,
    install_requires=[
        "eyed3",
        "Pillow",
        "python-slugify"
    ],
    data_files=[('data', ["data/config.txt", "data/genres.json"])],
)
