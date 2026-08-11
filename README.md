# ytconverter

Applicazione desktop per Windows che scarica una singola traccia audio e la converte in MP3 tramite `yt-dlp` e FFmpeg.

## Funzionalità

- interfaccia grafica Tkinter;
- qualità MP3 selezionabile da 96 a 320 kbps;
- avanzamento, velocità e tempo stimato;
- annullamento del download;
- scelta della cartella di destinazione;
- tentativo alternativo opzionale;
- archivio ZIP opzionale dei file creati nella sessione;
- preferenze salvate in `%LOCALAPPDATA%\ytconverter`.

## Installazione

```powershell
git clone https://github.com/smokytek/ytconverter.git
cd ytconverter
python -m pip install -r requirements.txt
```

Installa FFmpeg nel `PATH`, oppure copia `ffmpeg.exe` in `dependencies/ffmpeg.exe`.

## Avvio

```powershell
python app.py
```

Per compatibilità è possibile utilizzare anche:

```powershell
python bot.py
```

## Creazione dell'eseguibile

```powershell
pyinstaller --clean ytconverter.spec
```

Copia quindi `dependencies/ffmpeg.exe` accanto all'eseguibile generato, conservando la stessa struttura di cartelle.

## Utilizzo responsabile

Scarica soltanto contenuti che sei autorizzato a utilizzare e rispetta i diritti d'autore e i termini del servizio di origine.

## Licenza

Questo progetto è distribuito con licenza MIT.
