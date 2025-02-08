# MP3 DL

MP3 DL è uno script Python che permette di scaricare video da YouTube e convertirli in MP3. Supporta sia il download di singoli video che di intere playlist.

## 📥 Installazione

1. **Clona il repository**
   ```sh
   git clone https://github.com/tuo-username/smokytek-mp3-downloader.git
   cd smokytek-mp3-downloader
   ```

2. **Installa le dipendenze**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configura le impostazioni**
   Il file `config.json` viene generato automaticamente al primo avvio. Puoi modificarlo per attivare o disattivare alcune funzionalità:
   ```json
   {
       "create_zip": true,          // Se true, comprime i file scaricati in un archivio zip
       "allow_single_video": true,  // Se true, consente il download di singoli video
       "allow_playlist": true       // Se true, consente il download di intere playlist
   }
   ```

## 🚀 Utilizzo

1. **Esegui lo script**
   ```sh
   python main.py
   ```
2. **Inserisci l'URL** quando richiesto.
3. Attendi il completamento del download e della conversione in MP3.
4. Se abilitata, verrà creata un'archivio ZIP con tutti i file scaricati.

## ⚠ Disclaimer

Questo progetto è stato sviluppato solo a scopo educativo. L'autore non si assume alcuna responsabilità per l'uso improprio di questo script. Scaricare contenuti protetti da copyright senza autorizzazione è illegale. Assicurati di rispettare i termini di servizio di YouTube.

## 📜 Licenza
Questo progetto è distribuito sotto licenza MIT.

