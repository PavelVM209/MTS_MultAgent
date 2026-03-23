from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mts-multagent",
    version="0.1.0",
    author="MTS Development Team",
    author_email="dev@mts.ru",
    description="Multi-agent system for automated corporate data analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mts/MTS_MultAgent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
            "flake8>=5.0.0",
        ],
        "nlp": [
            "spacy>=3.4.0",
            "nltk>=3.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mts-agent=src.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yaml", "*.yml"],
    },
    zip_safe=False,
)
