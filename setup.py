from setuptools import setup

__version_info__ = ('0', '0', '1')
__version__ = '.'.join(__version_info__)

setup(
    name="grash",
    version=__version__,
    description="jinja based static site generator",
    author="Sasha Illarionov",
    author_email="sasha.delly@gmail.com",
    url="https://github.com/sdll/grash",
    keywords=["jinja", "static", "website"],
    packages=["grash"],
    entry_points={
        'console_scripts': [
            'grash = grash.cli:main',
        ],
    },
    install_requires=[
        "docopt",
        "pypandoc",
        "jinja2",
        "pathlib",
        "watchdog"
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 2  - Pre-Alpha",
    ]
)
