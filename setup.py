from setuptools import setup, find_packages

setup(
    name='back-trader-demo',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'backtrader',
        'pandas',
        'matplotlib'
    ],
    description='A 股交易策略回测项目',
    author='Howard',
    author_email='hyh_29@163.com',
    url='https://github.com/SuchAFool123/back-trader-demo'
)