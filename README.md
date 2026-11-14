# Mi Agenda Digital

Agenda docente para el profesorado de MEDAC: horario, tareas, calendario escolar
de Aragón, evaluaciones, notas, sincronización con el Aula Virtual (Canvas) y
fichaje en Factorial.

Funciona **en tu ordenador**: los datos se guardan solo en tu equipo y no se
envían a ningún servidor propio.

## Instalarla

1. Descarga `MiAgendaDigital.exe` de la última versión en
   [Releases](../../releases/latest).
2. Guárdalo en una carpeta tuya (por ejemplo, `Documentos`) y ábrelo con doble clic.
   - La primera vez Windows puede avisar («Windows protegió su PC»): pulsa
     **Más información → Ejecutar de todas formas**.
3. Entra con tu usuario y contraseña del Aula Virtual de MEDAC.
4. Pulsa **Sincronizar** para traer tus cursos o añade tus asignaturas en
   **Mi horario → Mis asignaturas**, y rellena tu horario.

Cuando haya una versión nueva, la agenda te avisará y se actualizará sola si lo
aceptas. Tus datos se conservan.

Requisitos: Windows 10 u 11 con Microsoft Edge (viene instalado).

Los datos están en `%LOCALAPPDATA%\MiAgendaDigital`. Para hacer copias usa
**Copias y datos** dentro de la agenda.

## Desarrollo

```bat
cd AgendaDigitalApp
iniciar_agenda.bat          :: ejecuta desde el código (crea .venv e instala Flask)
build_exe.bat               :: genera dist\MiAgendaDigital.exe en local
```

- Backend: Python 3.12 + Flask, SQLite. Frontend: HTML/CSS/JS sin dependencias.
- Desde el código, los datos van a `AgendaDigitalApp/data/` (ignorado por git).

### Publicar una versión

1. Sube `APP_VERSION` en `AgendaDigitalApp/app/version.py` (por ejemplo `1.2.0`) y haz commit.
2. Crea y sube la etiqueta con las novedades (las verá el profesorado al actualizar):

   ```bash
   git tag -a v1.2.0 -m "Novedades:
   - Lo que ha cambiado"
   git push origin main v1.2.0
   ```

3. GitHub Actions (`.github/workflows/release.yml`) compila el `.exe`, comprueba
   que arranca y crea la Release. Las agendas instaladas lo detectan en su
   siguiente arranque.

Solo el `.exe` compilado por GitHub Actions busca actualizaciones (sabe de qué
repositorio sale); el compilado en local, no. El repositorio debe ser público
para que las agendas puedan descargar las versiones sin iniciar sesión en GitHub.
