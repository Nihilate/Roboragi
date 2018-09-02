from setuptools import setup, find_packages

install_requires = [
    'praw==5.4.0',
    'psycopg2-binary==2.7.5',
    'pyquery==1.4.0',
    'requests==2.19.1',
    'six==1.10.0',
]

dev_requires = [
    'flake8',
    'pytest',
    'pytest-cov',
]

setup(
    name='roboragi',
    author='Nihilate',
    url='https://github.com/Nihilate/Roboragi',
    license='AGPLv3+',
    install_requires=install_requires,
    packages=find_packages(),
    extras_require={
        'dev': dev_requires,
    },
    classifiers=[
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
    ]
)
