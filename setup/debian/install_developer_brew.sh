# Install homebrew
sudo apt-get install build-essential curl git python-setuptools ruby
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install)"
echo 'export PATH="$HOME/.linuxbrew/bin:$PATH"' >>~/.bash_profile
source ~/.bash_profile
echo 'export PATH="$HOME/.linuxbrew/bin:$PATH"' >>~/.bashrc
source ~/.bashrc

brew update
brew doctor
brew upgrade

# Install everything else using homebrew

# protocol buffers
brew install protobuf

# NodeJS and npm package manager
brew install npm
# PM2 for process management
npm install pm2@latest -g

# MongoDB
brew install mongodb
