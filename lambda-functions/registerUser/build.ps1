Remove-Item registerUser.zip -ErrorAction SilentlyContinue

Compress-Archive -Path * -DestinationPath registerUser.zip -Force

Write-Host "✅ Package built: registerUser.zip"