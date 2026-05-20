# Windows Python PATH Troubleshooting

**Problema:** En Windows, cuando Python se instala desde Microsoft Store (la forma mas comun hoy), `pip install` guarda los ejecutables CLI en una ruta profunda que NO se agrega automaticamente al PATH del sistema. Resultado: el comando no se encuentra.

**Ejemplo:**
```powershell
PS> pip install notebooklm-py
PS> notebooklm login
notebooklm: el termino 'notebooklm' no se reconoce como nombre de cmdlet...
```

**Causa:** El ejecutable queda en:
```
C:\Users\<Usuario>\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_<hash>\LocalCache\local-packages\Python312\Scripts\notebooklm.exe
```

**Soluciones en orden de preferencia:**

### 1. Usar `python -m` (mas rapido, siempre funciona)
```powershell
python -m notebooklm login
```

### 2. Usar pipx en vez de pip (recomendado para herramientas CLI)
```powershell
python -m pip install pipx
python -m pipx ensurepath
pipx install notebooklm-py
# Ahora funciona directo:
notebooklm login
```

### 3. Agregar al PATH permanentemente
```powershell
$path = "C:\Users\$env:USERNAME\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$path", "User")
# Cerrar y reabrir terminal
```

### 4. Usar ruta completa al ejecutable
```powershell
# Buscar donde quedo instalado
pip show notebooklm-py
# Luego ejecutar con ruta completa:
C:\Users\...\Scripts\notebooklm.exe login
```

**Regla general para el equipo:** En Windows, siempre probar `python -m <paquete>` primero antes de debuggear el PATH.
