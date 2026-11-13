# El Quiosco — app web instalable

Titulares de las portadas de El Mundo, El Confidencial, El País, ABC, La Razón, El Español y elDiario.es.
Al pinchar un titular se abre su copia en archive.ph (o se crea en ese momento).

## Qué hay en esta carpeta

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La app |
| `manifest.webmanifest`, `icons/` | Hacen que se pueda instalar en el móvil con tu logo |
| `sw.js` | Permite abrirla sin conexión con el último barrido |
| `barrido.py`, `requirements.txt` | El programa que lee las portadas |
| `portadas.json` | Las noticias del último barrido (lo actualiza GitHub solo) |
| `.github/workflows/barrido.yml` | Programa los barridos: cada 30 minutos de 5:48 a 23:48 (hora de Madrid) |

## Puesta en marcha (una sola vez, ~10 minutos)

1. **Crea una cuenta gratuita** en https://github.com
2. **Crea un repositorio nuevo**: botón **+** (arriba a la derecha) → *New repository*.
   - Nombre: `elquiosco`
   - Visibilidad: **Public** (GitHub Pages gratis solo funciona con repositorios públicos)
   - Pulsa *Create repository*.
3. **Sube los archivos**: en el repositorio vacío pulsa *uploading an existing file*, arrastra **todo el contenido** de esta carpeta descomprimida (incluida la carpeta `.github`; si tu ordenador la oculta, mira la nota de abajo) y pulsa *Commit changes*.
4. **Activa la web**: *Settings* → *Pages* → en *Branch* elige `main` y carpeta `/ (root)` → *Save*.
   En 1–2 minutos aparecerá arriba la dirección: `https://TU-USUARIO.github.io/elquiosco/`
5. **Permite que los barridos guarden las noticias**: *Settings* → *Actions* → *General* → en *Workflow permissions* marca **Read and write permissions** → *Save*.
6. **Primer barrido de prueba**: pestaña *Actions* → *Barrido de portadas* → *Run workflow*. Cuando salga en verde, recarga la app.

### Nota sobre la carpeta `.github`
En Windows la carpeta `.github` se ve normal en el Explorador. Aun así, la web de GitHub a veces no la sube al
arrastrarla. Después de subir, comprueba que aparece en la lista del repositorio. Si no está, créala a mano:
*Add file* → *Create new file*, escribe como nombre `.github/workflows/barrido.yml` y pega dentro el contenido
de ese archivo (ábrelo con el Bloc de notas, Ctrl+A, Ctrl+C).

## Instalarla en el móvil

- **iPhone (Safari):** abre la dirección → botón compartir → *Añadir a pantalla de inicio*.
- **Android (Chrome):** abre la dirección → menú ⋮ → *Instalar app* (o *Añadir a pantalla de inicio*).

Se instala con tu logo y se abre a pantalla completa, sin barra del navegador. No hace falta cuenta de nada.

## Uso diario

- Los barridos se hacen solos. GitHub a veces los retrasa entre 5 y 30 minutos en horas punta.
- **Barrido a mano:** pestaña *Actions* → *Barrido de portadas* → *Run workflow*.
- **Cambiar horario:** edita `INICIO` y `FIN` (y la línea `cron`) en `.github/workflows/barrido.yml`.
- **Ver último barrido** (botón de la app) carga las noticias del último barrido guardado.

## Cosas a tener en cuenta

- Al ser un repositorio público, cualquiera que tenga la dirección puede abrir la app. No aparece en buscadores
  salvo que alguien la enlace, pero no es privada. Para uso personal o de un círculo pequeño no hay problema;
  difundirla abiertamente puede chocar con los derechos de los periódicos.
- Si un periódico cambia el diseño de su web, puede que su pestaña se quede con pocas o ninguna noticia hasta
  ajustar `barrido.py`.
- GitHub desactiva los barridos programados de un repositorio público si pasan 60 días sin actividad. Si te pasa,
  verás un aviso en la pestaña *Actions* y basta con pulsar *Enable workflow*.
