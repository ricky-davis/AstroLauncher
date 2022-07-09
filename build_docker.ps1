Write-Host "Removing old AstroLauncher EXE"
Remove-Item .\AstroLauncher.exe -Force -ErrorAction SilentlyContinue
Write-Host "Starting AstroLauncher Docker Image build..."
docker build --pull --rm  -f "Dockerfile" -t astrolauncher-build:latest "."
Write-Host "Running Build Container"
$container_id=(docker run -it --detach astrolauncher-build:latest)
while (-not (docker ps -a | select-string ($container_id[0..11] -join "") | select-string "Exited")){
    sleep 1
}
Write-Host "Downloading Built EXE"
docker cp "$($container_id):C:/Build/dist/AstroLauncher.exe" AstroLauncher.exe
docker rm $container_id