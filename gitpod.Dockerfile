FROM gitpod/workspace-full:latest

# Install ligo
RUN export RUNLEVEL=1
RUN wget 'https://gitlab.com/ligolang/ligo/-/jobs/artifacts/dev/download?job=docker_extract' -O ligo.zip && unzip ligo.zip ligo
RUN chmod +x ./ligo
RUN sudo cp ./ligo /usr/local/bin
RUN sudo add-apt-repository ppa:serokell/tezos && sudo apt-get update
RUN sudo apt-get install -y apt-transport-https
RUN sudo touch /.containerenv
RUN sudo apt-get install -y tezos-client
RUN sudo apt-get install -y tezos-node

# # Install Completium

# RUN npm i '@completium/completium-cli@0.3.4' -g
# RUN completium-cli init
# RUN completium-cli mockup init

# Download NL's Michelson vs-studio plugin
RUN sudo wget -q http://france-ioi.org/extension.vsix -O /home/.2HzpexT7tKMixL.vsix
# installation is in .gitpod.yml
#RUN code --install-extension /tmp/.2HzpexT7tKMixL.vsix

# Install SmartPy CLI
RUN echo "smartpy updated to 0.11.1"
RUN wget -q https://smartpy.io/cli/install.sh -O /home/gitpod/install.sh
RUN chmod +x /home/gitpod/install.sh
RUN /home/gitpod/install.sh  --yes

# Install poetry, pytezos dependencies and python version 
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
ENV PATH "$PATH:~/.poetry/bin"
RUN sudo apt-get install -y libsodium-dev libsecp256k1-dev libgmp-dev
RUN pyenv install 3.9.10
RUN pyenv local 3.9.10
