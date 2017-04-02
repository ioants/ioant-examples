# Virtual environment set up
sudo pip install virtualenv
sudo pip install virtualenvwrapper
echo 'export WORKON_HOME=~/Envs' >> ~/.bashrc
echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bashrc
source  ~/.bashrc
mkvirtualenv ioant
