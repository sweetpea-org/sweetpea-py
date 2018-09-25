import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sweetpea",
    version="0.0.9",
    author="Annie Cherkaev, Ben Draut",
    author_email="annie.cherk@gmail.com, drautb@cs.utah.edu",
    description="A language for synthesizing randomized experimental designs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anniecherk/sweetpea-py",
    packages=setuptools.find_packages(),
    install_requires=[
      'docker',
      'requests'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    test_suite='nose.collector',
    tests_require=['nose']
)
