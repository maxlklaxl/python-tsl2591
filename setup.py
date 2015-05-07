from setuptools import setup

setup(name='tsl2591',
      version='0.0.1',
      url='http://github.com/maxlklaxl/tsl2591',
      author='Max Hofbauer',
      author_email='maxhofb@gmail.com',
      description='Community-coded Python module for tsl2591. Use it at your own risk.',
      packages=['tsl2591'],
      long_description=open('README.md').read(),
      requires=['python (>= 2.7)', 'smbus (>=0.4.1)'],
      install_requires=[' smbus-cffi'],
      zip_safe=False)
