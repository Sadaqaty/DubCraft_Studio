# DubCraft Studio

**DubCraft Studio** is a free, open-source desktop tool for AI-powered video dubbing, translation, and voiceover. It features a beautiful PyQt6 interface, fast transcription, speaker diarization, natural TTS, and professional export options.

## Features
- 🎨 Gorgeous, modern UI (PyQt6, dark mode, smooth transitions, micro animations)
- 🧭 Sidebar with icons and animated transitions
- 🛠️ Tooltips, section headers, and a status bar for user feedback
- ❓ Built-in Help modal with quick tips
- 🔊 Extract, replace, and merge audio with video
- 🧠 Fast, accurate transcription (faster-whisper)
- 🗣️ Speaker diarization (WhisperX/pyannote-audio)
- 🌍 AI translation (deep-translator, manual override)
- 🎤 Assign unique, natural voices per speaker (Tortoise-TTS/Bark)
- 📝 Subtitle generation (.srt, burn-in, speaker names)
- 📦 Export: video, audio, transcript, subtitles
- 🧩 Drag & drop, auto-save, live preview, modular code
- ✍️ **Manual editing of translations, segment timing, and speaker assignments**
- ♿ **Accessibility:** keyboard navigation, tooltips, high-contrast mode ready
- 🧑‍💻 **Logs panel, export progress, and error feedback**

## Screenshots
![Main UI](assets/screenshot_main.png)
![Project Panel](assets/screenshot_project.png)

## Quick Start
1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the app:**
   ```bash
   python main.py
   ```

## Usage Tips
- Use the sidebar to navigate between Home, Project, Voices, Export, and Logs.
- Hover over controls for tooltips and guidance.
- Click the ❓ Help button in the status bar for quick tips.
- Watch the animated progress bar for real-time feedback.
- All your work is autosaved and restored on restart.
- Edit translations, segment timing, and speaker assignments for full control.

## Folder Structure
- `core/` — Audio, video, transcription, translation, TTS, diarization, subtitles, utils
- `modules/` — Plugins, autosave, drag & drop, logging, preview
- `ui/` — PyQt6 UI, QSS styles, resources, loading overlay
- `assets/` — Icons, images, logo, voices, spinner
- `export/` — User export output
- `tests/` — Unit/integration tests

## Accessibility
- Keyboard navigation for all major controls
- Tooltips and ARIA labels for screen readers
- High-contrast mode ready (toggle coming soon)

## Troubleshooting
**Common Issues & Solutions:**

- **Missing Models:**
  - Make sure you have downloaded all required models for faster-whisper, pyannote-audio, and Tortoise-TTS/Bark. See their documentation for model download instructions.
  - For pyannote-audio diarization, set the `PYANNOTE_AUTH_TOKEN` environment variable.
- **ffmpeg Errors:**
  - Ensure `ffmpeg` is installed and available in your system PATH. On Linux, install with `sudo apt install ffmpeg`. On Windows/Mac, download from [ffmpeg.org](https://ffmpeg.org/download.html).
- **PyQt6 Multimedia Issues:**
  - If audio/video preview does not work, ensure you have the `PyQt6.QtMultimedia` package and all system dependencies for multimedia playback.
- **TTS/Voice Issues:**
  - Make sure your Tortoise/Bark voices are in the correct directory (see `TORTOISE_VOICES_DIR` env variable).
- **GPU/CPU Issues:**
  - Some models require a GPU for fast processing. If you encounter out-of-memory or device errors, try using a smaller model or run on CPU.
- **Other Errors:**
  - Check the Logs panel for detailed error messages. If you need help, open an issue on GitHub with your log output.

## Contributing
We welcome contributions from the community!

- Please fork the repo and submit a pull request for new features, bug fixes, or improvements.
- Follow the existing code style and add docstrings/type hints where possible.
- For major features, open an issue first to discuss your proposal.
- Add or update tests for your changes if possible.
- All contributions must be free/open-source and not rely on paid APIs.

**Thank you for helping make DubCraft Studio better for everyone!**

## License
MIT — Free for everyone, forever. 