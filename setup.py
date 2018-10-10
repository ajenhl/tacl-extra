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
            'lifetime=bin.lifetime:main',
        ],
    },
    test_suite='tests',
    install_required=['tacl'],
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Linguistic',
    ],
)
