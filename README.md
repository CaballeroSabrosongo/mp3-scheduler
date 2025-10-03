# Programador de Música

![License](https://img.shields.io/badge/license-MIT-green)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20|%20Linux%20|%20Windows-lightgrey)

## Descripción
`mp3-scheduler` permite **programar la reproducción de archivos MP3** en horarios específicos. Ideal para automatizar música, alarmas o notificaciones sonoras en tu sistema. Compatible con **macOS, Linux y Windows**.

---

## Características
- Reproducción de MP3 en horarios programados.
- Soporte para múltiples archivos y horarios.
- Control de Volumen por pista
- Fácil de configurar y usar desde la terminal.
- Funciona en **macOS, Linux y Windows**.

---

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/CaballeroSabrosongo/mp3-scheduler.git
cd mp3-scheduler
```

Instala dependencias (Python ejemplo):

```bash
pip install -r requirements.txt
```

> ⚠️ Asegúrate de tener Python 3.8 o superior instalado.

---

## Uso

Ejemplo básico para programar una reproducción:

```bash
python Programador de musica.py --file "cancion.mp3" --time "14:30"
```

Opciones:
- `--file`: Ruta del archivo MP3.
- `--time`: Hora de reproducción (formato HH:MM).

---

## Contribución

Si quieres contribuir:

```bash
git checkout -b nueva-funcionalidad
git commit -am "Agrega nueva funcionalidad"
git push origin nueva-funcionalidad
```

Luego abre un pull request en GitHub.

---

## Licencia
Este proyecto está bajo la **Licencia MIT**. Ver [LICENSE](LICENSE) para más detalles.
