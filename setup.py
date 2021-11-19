import setuptools

setuptools.setup(
    name="torpedo",
    version="1.0.1",
    author="Michał Pogoda",
    author_email="michal.pogoda@bards.ai",
    description="A simple library for using tor as proxy for requests",
    long_description="A simple library for using tor as proxy for requests",
    long_description_content_type="text/markdown",
    url="https://github.com/mipo57/torpedo",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "requests",
    ],
)
