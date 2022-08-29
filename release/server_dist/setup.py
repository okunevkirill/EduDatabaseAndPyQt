from setuptools import setup, find_packages

setup(name="messenger-trial-server",
      version="0.0.1",
      description="The server part of the messenger",
      author="Ivan Ivanov",
      author_email="iv.iv@gmail.com",
      packages=find_packages(),
      include_package_data=True,
      install_requires=['PyQt5', 'sqlalchemy'],
      entry_points={
          "console_scripts": [
              "server_run = messenger_trial_server.run_server:main",
          ]
      })
