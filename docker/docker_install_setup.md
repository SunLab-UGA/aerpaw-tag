# install docker repo to apt (the default package manager for ubuntu)
```
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
# update again and install docker
```
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io
```

# check if docker is running
```
sudo systemctl status docker
```

# check version
```
docker --version
```

# check docker compose version
```
docker compose version
```
# add your user to the docker group to avoid using sudo, redo 
```
sudo usermod -aG docker $USER
newgrp docker
```

# add an external network (this is used to put both inpulsedb and graphana on the same bridged network)
```
docker network create external_network
```