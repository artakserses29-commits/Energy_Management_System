@echo off
echo ============================================
echo   Diagnostic Serveur Gestion Energie
echo ============================================
echo.

echo 1. Test du port 5000...
netstat -ano | findstr :5000
echo.

echo 2. Test connexion locale...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/' -UseBasicParsing -TimeoutSec 5; Write-Host 'OK: ' $r.StatusCode } catch { Write-Host 'ECHEC: ' $_ }"
echo.

echo 3. Test localhost...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:5000/' -UseBasicParsing -TimeoutSec 5; Write-Host 'OK: ' $r.StatusCode } catch { Write-Host 'ECHEC: ' $_ }"
echo.

echo 4. Test API...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/api/status' -UseBasicParsing -TimeoutSec 5; Write-Host 'OK: ' $r.Content.Substring(0,100) } catch { Write-Host 'ECHEC: ' $_ }"
echo.

echo 5. Verifications Firefox...
echo    - Verifiez que Firefox n'utilise pas de proxy :
echo      Menu ^> Parametres ^> Parametres du reseau ^> Parametres proxy
echo    - Desactiver "Utiliser un proxy" si actif
echo    - Essayez http://localhost:5000 au lieu de 127.0.0.1:5000
echo.

echo ============================================
echo Si les tests 1-4 echouent alors que le serveur
echo tourne: desactivez le pare-feu Windows.
echo ============================================
pause
