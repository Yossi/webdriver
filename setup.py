import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as f:
    install_requires = f.read().strip().split('\n')

setuptools.setup(
    name="webdriver",
    version="0.0.7",
    author="Yossi",
    description="webdriver factory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Yossi/webdriver",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    license='Unlicense',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
)
