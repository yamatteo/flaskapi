from setuptools import setup, find_packages

setup(
    name='engine',
    version='0.1',
    packages=find_packages(),
    package_dir={
        'engine': 'engine',
    },
    setup_requires=['wheel'],
    install_requires=[
        'attr',
        'cattrs'
    ]
)