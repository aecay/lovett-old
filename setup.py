from distutils.core import setup

setup(
    name = "Lovett",
    author = "Aaron Ecay",
    author_email = "aaronecay@gmail.com",
    version = "0.1dev",
    packages = ["lovett","lovett.cs"],
    license = "GNU General Public License v.3 or higher",
    # long_description = open("README").read()
    # scripts = []
    install_requires = ["nltk",]
)
