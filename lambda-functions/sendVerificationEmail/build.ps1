Remove-Item -Recurse -Force package -ErrorAction SilentlyContinue
Remove-Item sendVerificationEmail.zip -ErrorAction SilentlyContinue

docker run --rm -v ${PWD}:/var/task python:3.14-slim pip install -r /var/task/requirements.txt -t /var/task/package/

Copy-Item lambda_function.py package/ -Force

cd package
Compress-Archive -Path * -DestinationPath ../sendVerificationEmail.zip -Force
cd ..

Write-Host "✅ Package built: sendVerificationEmail.zip"