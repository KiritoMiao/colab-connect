from setuptools import setup, find_packages

setup(
    name="colabconnect",
    version="0.0.9",
    license="MIT",
    description="Connect to Google Colab VM locally from VSCode or Cursor",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    author="Amit Chaudhary",
    author_email="meamitkc@gmail.com",
    url="https://github.com/amitness/colab-connect",
    packages=find_packages(),
)
