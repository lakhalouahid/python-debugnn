from setuptools import setup
setup (
  name='debugnn',
  version='0.0.2',
  description='collecting of function to better debug neural networks',
  py_modules=['debugnn'],
  package_dir={'': 'src'},
  requires=['pyfzf']
)
