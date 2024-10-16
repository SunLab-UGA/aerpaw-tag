# this is a project to collect williot tag data using a aerpaw small drone

## ensure docker is installed and setup
* use docker_install_setup.md
    * if docker is already installed ensure the external_network is created
    ```
    docker network create external_network
    ```

## bring the containers up
```
docker compose up
```

kill it with fire
```
docker system prune -a
```