Remove-Item -Recurse -Force package -ErrorAction SilentlyContinue
Remove-Item processImage.zip -ErrorAction SilentlyContinue

# use full python image for Pillow dependencies
docker run --rm -v ${PWD}:/var/task python:3.14 sh -c "apt-get update && apt-get install -y zlib1g-dev libjpeg-dev && pip install -r /var/task/requirements.txt -t /var/task/package/"

Copy-Item lambda_function.py package/ -Force

New-Item -ItemType Directory -Force -Path package/shared/python | Out-Null
Copy-Item ../shared/python/*.py package/shared/python/ -Force

cd package
Compress-Archive -Path * -DestinationPath ../processImage.zip -Force
cd ..

Write-Host "✅ Package built: processImage.zip"