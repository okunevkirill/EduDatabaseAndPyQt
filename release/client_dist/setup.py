from setuptools import setup, find_packages

setup(name="messenger-trial-client",
      version="0.0.1",
      description="The client part of the messenger",
      author="Ivan Ivanov",
      author_email="iv.iv@gmail.com",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy'],
      entry_points={
          "console_scripts": [
              "client_run = messenger_trial_client.run_client:main",
          ]
      })
