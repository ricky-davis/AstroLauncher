docker build --pull --rm -f "Dockerfile" -t astrolauncher-build:latest "."
$container_id=(docker run -it --detach astrolauncher-build:latest)
while (-not (docker ps -a | select-string ($container_id[0..11] -join "") | select-string "Exited")){
    sleep 1
}
docker cp "$($container_id):C:/Build/dist/AstroLauncher.exe" AstroLauncher.exe
docker rm $container_id