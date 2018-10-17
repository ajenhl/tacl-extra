from setuptools import setup


with open('README.rst') as fh:
    long_description = fh.read()

setup(
    name='tacl-extra',
    long_description=long_description,
    author='Jamie Norrish',
    author_email='jamie@artefact.org.nz',
    license='GPLv3+',
    packages=['taclextra'],
    entry_points={
        'console_scripts': [
            'int-all=bin.int_all:main',
            'lifetime=bin.lifetime:main',
            'paternity=bin.paternity:main',
        ],
    },
    test_suite='tests',
    install_requires=['tacl'],
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Linguistic',
    ],
)
