from setuptools import setup, find_packages

setup(
    name='nci-tools',
    version='0.0.1',
    packages=find_packages(),
    license='MIT',
    author='Kirill Kouzoubov',
    author_email='kirill.kouzoubov@ga.gov.au',
    description='Tools for working with NCI',
    install_requires=['click', 'paramiko', 'sshtunnel'],
    setup_requires=[],
    tests_require=[],
    entry_points={
        'console_scripts': [
            'nbconnect = ncitools.nbconnect:main',
        ],
    }
)
