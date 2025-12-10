Remove-Item -Recurse -Force package -ErrorAction SilentlyContinue
Remove-Item updateUserProfile.zip -ErrorAction SilentlyContinue

docker run --rm -v ${PWD}:/var/task python:3.14-slim pip install -r /var/task/requirements.txt -t /var/task/package/

Copy-Item lambda_function.py, models.py package/ -Force

cd package
Compress-Archive -Path * -DestinationPath ../updateUserProfile.zip -Force
cd ..

Write-Host "✅ Package built: updateUserProfile.zip"