# ytconverter

Applicazione desktop per Windows che scarica una singola traccia audio e la converte in MP3 tramite `yt-dlp` e FFmpeg. Supporta anche l'importazione di una playlist Spotify: legge le tracce dalla playlist e le cerca una a una su YouTube per scaricarle come MP3.

## Funzionalità

- interfaccia grafica Tkinter;
- download di singoli video o playlist complete;
- **importazione di playlist, album e tracce Spotify** (link `open.spotify.com` o URI `spotify:`): le tracce vengono cercate su YouTube con «artista - titolo» e scaricate una a una, con riepilogo finale delle eventuali non trovate;
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
python -m pip install -U yt-dlp
```

> Con versioni datate di `yt-dlp` la ricerca su YouTube può fallire con l'errore «The page needs to be reloaded»: in quel caso aggiornala con `python -m pip install -U yt-dlp`.

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

La configurazione genera un singolo `ytconverter.exe` senza finestra del terminale e include il file `dependencies/ffmpeg.exe` nell'eseguibile.

## Importazione da Spotify

Incolla un link Spotify (`https://open.spotify.com/playlist/...`, `.../album/...`, `.../track/...` o `spotify:playlist:...`) al posto di un URL YouTube: l'app recupera automaticamente l'elenco delle tracce e le cerca su YouTube.

L'accesso ai metadati funziona normalmente senza login tramite il token anonimo del player web; se Spotify lo blocca (accade su alcune reti), crea gratuitamente una app su [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard), abilita le Web API, e aggiungi al file `%LOCALAPPDATA%\ytconverter\config.json`:

```json
{
  "spotify_client_id": "IL_TUO_CLIENT_ID",
  "spotify_client_secret": "IL_TUO_CLIENT_SECRET"
}
```

## Utilizzo responsabile

Scarica soltanto contenuti che sei autorizzato a utilizzare e rispetta i diritti d'autore e i termini del servizio di origine.

## Licenza

Questo progetto è distribuito con licenza MIT.
