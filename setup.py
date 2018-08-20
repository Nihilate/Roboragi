from setuptools import setup, find_packages

install_requires = [
    'praw==3.1.0',
    'psycopg2',  # TODO: If possible, this should be updated beyond 2.6.1.
    'pyquery',  # TODO: What version should this be?
    'requests==2.7.0',
    'six==1.9.0',
]

dev_requires = [
    'flake8',
    'pytest',
]

setup(
    name='roboragi',
    author='Nihilate',
    url='https://github.com/Nihilate/Roboragi',
    install_requires=install_requires,
    packages=find_packages(),
    extras_require={
        'dev': dev_requires,
    }
)
