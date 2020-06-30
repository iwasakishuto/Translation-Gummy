# coding: utf-8
import os
import setuptools
import gummy

DESCRIPTION = "Translation Gummy is a magical gadget which enables user to be able to speak and understand other languages."

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

def setup_package():
    metadata = dict(
        name="Translation-Gummy",
        version=gummy.__version__,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        author="Shuto Iwasaki",
        author_email="cabernet.rock@gmail.com",
        license="MIT",
        project_urls={
            "Bug Reports" : "https://github.com/iwasakishuto/Translation-Gummy/issues",
            "Source Code" : "https://github.com/iwasakishuto/Translation-Gummy",
            "Say Thanks!" : "https://twitter.com/cabernet_rock",
        },
        packages=setuptools.find_packages(),
        package_data={"gummy": ["templates/*"]},
        python_requires=">=3.7",
        install_requires=[
            # "numpy>=1.15.1",
            # "seaborn>=0.10.0",
        ],
        extras_require={
          "tests": ["pytest"],
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Other Audience",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.7",
            "Topic :: Software Development :: Libraries",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )
    setuptools.setup(**metadata)

if __name__ == "__main__":
    setup_package()