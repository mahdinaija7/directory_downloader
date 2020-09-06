import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="directory-listing-download",
    version="0.0.1",
    author="Super Vegetoo",
    author_email="vegetoo255@gmail.com",
    description="A python Package to download files from any directory listing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["bs4","aiohttp"],
    python_requires='>=3.7',
)