Remove-Item loginUser.zip -ErrorAction SilentlyContinue

Compress-Archive -Path * -DestinationPath loginUser.zip -Force

Write-Host "✅ Package built: loginUser.zip"