from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QFrame,
    QStatusBar,
    QMessageBox,
    QComboBox,
    QTextEdit,
    QCheckBox,
    QFileDialog,
    QLineEdit,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QPropertyAnimation
from PyQt6.QtGui import QIcon
import os
from ui.file_upload import FileUploadWidget
from ui.language_selector import LanguageSelectorWidget
from core.audio import extract_audio
import tempfile
from modules.autosave import autosave_session, restore_session
from ui.loading_overlay import LoadingOverlay
from core.tts import list_voices, synthesize_speech
from core.diarization import diarize_speakers
from core.transcription import transcribe_audio
from core.translation import batch_translate_texts
from core.video import merge_audio_with_video
from pydub import AudioSegment
from core.subtitles import generate_srt


class AudioExtractWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)

    def __init__(self, video_path, audio_out_path):
        super().__init__()
        self.video_path = video_path
        self.audio_out_path = audio_out_path

    def run(self):
        self.progress.emit(10)
        success = extract_audio(self.video_path, self.audio_out_path)
        self.progress.emit(100 if success else 0)
        self.finished.emit(success, self.audio_out_path if success else "")


class DiarizationWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path

    def run(self):
        self.progress.emit(20)
        speakers = diarize_speakers(self.audio_path)
        self.progress.emit(40)
        self.finished.emit(speakers)


class TranscriptionWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path

    def run(self):
        self.progress.emit(30)
        segments = transcribe_audio(self.audio_path)
        self.progress.emit(50)
        self.finished.emit(segments)


class TranslationWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def __init__(self, segments, target_language):
        super().__init__()
        self.segments = segments
        self.target_language = target_language

    def run(self):
        self.progress.emit(55)
        texts = [seg["text"] for seg in self.segments]
        translated = batch_translate_texts(texts, self.target_language)
        self.progress.emit(60)
        self.finished.emit(translated)


class TTSDubWorker(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, transcript, speakers, voices, emotions, audio_out_path):
        super().__init__()
        self.transcript = transcript
        self.speakers = speakers
        self.voices = voices
        self.emotions = emotions
        self.audio_out_path = audio_out_path

    def run(self):
        self.progress.emit(70)
        # Synthesize each segment and concatenate
        segments_audio = []
        for i, seg in enumerate(self.transcript):
            speaker = seg.get(
                "speaker", self.speakers[0] if self.speakers else "Speaker 1"
            )
            text = seg.get("translated_text", seg.get("text", ""))
            voice = self.voices.get(
                speaker,
                (
                    self.voices[self.speakers.index(speaker)]
                    if speaker in self.speakers
                    else list(self.voices.values())[0]
                ),
            )
            emotion = self.emotions.get(speaker, None)
            audio_path = synthesize_speech(text, voice, emotion)
            segments_audio.append(AudioSegment.from_file(audio_path))
            self.progress.emit(70 + int(20 * (i + 1) / len(self.transcript)))
        # Concatenate all segments
        if segments_audio:
            final_audio = segments_audio[0]
            for seg_audio in segments_audio[1:]:
                final_audio += seg_audio
            final_audio.export(self.audio_out_path, format="wav")
        self.progress.emit(90)
        self.finished.emit(self.audio_out_path)


class DubCraftMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DubCraft Studio")
        self.setMinimumSize(1200, 800)
        self.setWindowIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "../assets/logo.png"))
        )
        self.setStyleSheet(
            open(os.path.join(os.path.dirname(__file__), "style.qss")).read()
        )
        self.session_state = {
            "video_file": None,
            "audio_path": None,
            "language": None,
            "speakers": [],
            "voices": [],
            "transcript": [],
            "translated_transcript": [],
        }
        self.speakers = []  # List of detected speakers
        self.voices = list_voices() or ["Voice A", "Voice B", "Voice C"]
        self.transcript = []
        self.translated_transcript = []
        self.init_ui()
        self.restore_last_session()
        # Loading spinner overlay
        self.loading_overlay = LoadingOverlay(self.centralWidget())
        self.loading_overlay.resize(self.centralWidget().size())
        self.centralWidget().installEventFilter(self)
        # Scan TTS voices on startup
        self.scan_tts_voices()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        # Sidebar with icons
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setObjectName("Sidebar")
        sidebar_items = [
            ("🏠 Home"),
            ("🎬 Project"),
            ("🗣️ Voices"),
            ("📦 Export"),
            ("📝 Logs"),
        ]
        for name in sidebar_items:
            item = QListWidgetItem(name)
            self.sidebar.addItem(item)
        self.sidebar.currentRowChanged.connect(self.switch_panel)
        # Stacked panels
        self.panels = QStackedWidget()
        self.panels.addWidget(self.make_panel("Welcome to DubCraft Studio!"))
        self.panels.addWidget(self.make_project_panel())
        self.panels.addWidget(self.make_voices_panel())
        self.panels.addWidget(self.make_export_panel())
        self.panels.addWidget(self.make_logs_panel())
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.panels)
        self.setCentralWidget(main_widget)
        self.sidebar.setCurrentRow(0)
        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        # Help button
        help_btn = QPushButton("❓ Help")
        help_btn.setToolTip("Show quick tips and help")
        help_btn.clicked.connect(self.show_help)
        self.status.addPermanentWidget(help_btn)

    def make_panel(self, text):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addStretch()
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("PanelLabel")
        l.addWidget(label)
        l.addStretch()
        return w

    def make_section_header(self, text):
        frame = QFrame()
        frame.setObjectName("SectionHeader")
        layout = QHBoxLayout(frame)
        label = QLabel(text)
        layout.addWidget(label)
        layout.addStretch()
        return frame

    def make_project_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(24)
        l.setContentsMargins(80, 40, 80, 40)
        l.addWidget(self.make_section_header("1. Upload Video File"))
        self.file_upload = FileUploadWidget()
        self.file_upload.setToolTip("Upload or drag & drop your video file here.")
        l.addWidget(self.file_upload)
        l.addWidget(self.make_section_header("2. Select Target Language"))
        self.language_selector = LanguageSelectorWidget()
        self.language_selector.setToolTip("Choose the language for dubbing.")
        l.addWidget(self.language_selector)
        l.addWidget(self.make_section_header("3. Progress"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(32)
        self.progress_bar.setStyleSheet("font-size: 1.1em; border-radius: 8px;")
        l.addWidget(self.progress_bar)
        # Transcript/subtitle display
        self.transcript_toggle = QComboBox()
        self.transcript_toggle.addItems(
            ["Original Transcript", "Translated Transcript"]
        )
        self.transcript_toggle.setToolTip("Toggle transcript/subtitle display")
        self.transcript_toggle.currentIndexChanged.connect(
            self.update_transcript_display
        )
        l.addWidget(self.transcript_toggle)
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setToolTip("View transcript or subtitles here")
        l.addWidget(self.transcript_text)
        # Edit Translations button
        self.edit_trans_btn = QPushButton("Edit Translations")
        self.edit_trans_btn.setToolTip("Manually edit the translated transcript")
        self.edit_trans_btn.clicked.connect(self.open_edit_translations_dialog)
        l.addWidget(self.edit_trans_btn)
        l.addStretch()
        # Connect signals for future use
        self.file_upload.fileSelected.connect(self.on_file_selected)
        self.language_selector.languageChanged.connect(self.on_language_changed)
        return w

    def update_transcript_display(self):
        idx = self.transcript_toggle.currentIndex()
        if idx == 0:
            # Original
            text = "\n".join([seg["text"] for seg in self.transcript])
        else:
            # Translated
            text = "\n".join(
                [seg.get("translated_text", seg["text"]) for seg in self.transcript]
            )
        self.transcript_text.setPlainText(text)

    def open_edit_translations_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Translations & Timing")
        layout = QVBoxLayout(dialog)
        table = QTableWidget(len(self.transcript), 4)
        table.setHorizontalHeaderLabels(
            ["Start Time (s)", "End Time (s)", "Original", "Translated"]
        )
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        for i, seg in enumerate(self.transcript):
            table.setItem(i, 0, QTableWidgetItem(str(seg.get("start", 0))))
            table.setItem(i, 1, QTableWidgetItem(str(seg.get("end", 0))))
            table.setItem(i, 2, QTableWidgetItem(seg["text"]))
            table.setItem(
                i, 3, QTableWidgetItem(seg.get("translated_text", seg["text"]))
            )
        layout.addWidget(table)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)

        def save_edits():
            for i, seg in enumerate(self.transcript):
                try:
                    seg["start"] = float(table.item(i, 0).text())
                    seg["end"] = float(table.item(i, 1).text())
                except Exception:
                    seg["start"] = seg.get("start", 0)
                    seg["end"] = seg.get("end", 0)
                seg["translated_text"] = table.item(i, 3).text()
            self.translated_transcript = [
                seg["translated_text"] for seg in self.transcript
            ]
            self.session_state["translated_transcript"] = self.translated_transcript
            self.update_transcript_display()
            autosave_session(self.session_state)
            dialog.accept()

        buttons.accepted.connect(save_edits)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()

    def make_voices_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(18)
        l.setContentsMargins(80, 40, 80, 40)
        l.addWidget(self.make_section_header("Speaker Voice Assignment"))
        # Speaker Assignment button
        self.speaker_assign_btn = QPushButton("Edit Speaker Assignments")
        self.speaker_assign_btn.setToolTip(
            "Manually assign speakers to transcript segments"
        )
        self.speaker_assign_btn.clicked.connect(self.open_speaker_assignment_dialog)
        l.addWidget(self.speaker_assign_btn)
        # Use real speakers and voices
        speakers = self.speakers if self.speakers else ["Speaker 1", "Speaker 2"]
        voices = self.voices if self.voices else ["Voice A", "Voice B", "Voice C"]
        emotions = ["Neutral", "Happy", "Sad", "Excited"]
        self.voice_assign_widgets = []
        for i, speaker in enumerate(speakers):
            row = QHBoxLayout()
            label = QLabel(str(speaker))
            label.setToolTip(f"Assign a unique voice to {speaker}")
            row.addWidget(label)
            voice_combo = QComboBox()
            voice_combo.addItems(voices)
            voice_combo.setToolTip("Select a voice for this speaker")
            row.addWidget(voice_combo)
            emotion_combo = QComboBox()
            emotion_combo.addItems(emotions)
            emotion_combo.setToolTip("Select an emotion for this speaker's voice")
            row.addWidget(emotion_combo)
            preview_btn = QPushButton("Preview")
            preview_btn.setToolTip("Preview the selected voice and emotion")
            row.addWidget(preview_btn)
            row.addStretch()
            l.addLayout(row)
            self.voice_assign_widgets.append(
                (label, voice_combo, emotion_combo, preview_btn)
            )
        l.addStretch()
        w.setLayout(l)
        self.voices_panel_widget = w
        return w

    def open_speaker_assignment_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Speaker Assignments")
        layout = QVBoxLayout(dialog)
        table = QTableWidget(len(self.transcript), 2)
        table.setHorizontalHeaderLabels(["Text", "Speaker"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        speakers = self.speakers if self.speakers else ["Speaker 1", "Speaker 2"]
        for i, seg in enumerate(self.transcript):
            table.setItem(i, 0, QTableWidgetItem(seg["text"]))
            speaker_combo = QComboBox()
            speaker_combo.addItems(speakers)
            current = seg.get("speaker", speakers[0])
            speaker_combo.setCurrentText(str(current))
            table.setCellWidget(i, 1, speaker_combo)
        layout.addWidget(table)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(buttons)

        def save_edits():
            for i, seg in enumerate(self.transcript):
                combo = table.cellWidget(i, 1)
                seg["speaker"] = combo.currentText()
            autosave_session(self.session_state)
            dialog.accept()

        buttons.accepted.connect(save_edits)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()

    def update_voices_panel(self, speakers=None, voices=None):
        if speakers is not None:
            self.speakers = speakers
            self.session_state["speakers"] = speakers
        if voices is not None:
            self.voices = voices
            self.session_state["voices"] = voices
        # Remove old panel and insert new one
        idx = 2  # Voices panel index
        new_panel = self.make_voices_panel()
        self.panels.removeWidget(self.panels.widget(idx))
        self.panels.insertWidget(idx, new_panel)
        if self.sidebar.currentRow() == idx:
            self.panels.setCurrentIndex(idx)
        autosave_session(self.session_state)

    def on_diarization_complete(self, speakers):
        self.loading_overlay.hide()
        self.progress_bar.setValue(40)
        self.progress_bar.setFormat("Speakers detected!")
        self.speakers = speakers if speakers else ["Speaker 1"]
        self.session_state["speakers"] = self.speakers
        self.update_voices_panel(speakers=self.speakers)
        self.status.showMessage(f"Detected {len(self.speakers)} speaker(s).", 4000)
        autosave_session(self.session_state)
        # Start TTS and audio reconstruction
        self.loading_overlay.show("Synthesizing voices and reconstructing audio...")
        self.progress_bar.setValue(70)
        self.progress_bar.setFormat("Synthesizing voices...")
        # Gather voice/emotion assignments
        voices_map = {}
        emotions_map = {}
        for i, (label, voice_combo, emotion_combo, _) in enumerate(
            self.voice_assign_widgets
        ):
            speaker = label.text()
            voices_map[speaker] = voice_combo.currentText()
            emotions_map[speaker] = emotion_combo.currentText()
        self.dubbed_audio_path = tempfile.mktemp(suffix="_dubbed.wav")
        self.tts_thread = QThread()
        self.tts_worker = TTSDubWorker(
            self.transcript,
            self.speakers,
            voices_map,
            emotions_map,
            self.dubbed_audio_path,
        )
        self.tts_worker.moveToThread(self.tts_thread)
        self.tts_thread.started.connect(self.tts_worker.run)
        self.tts_worker.progress.connect(self.progress_bar.setValue)
        self.tts_worker.finished.connect(self.on_tts_complete)
        self.tts_worker.finished.connect(self.tts_thread.quit)
        self.tts_worker.finished.connect(self.tts_worker.deleteLater)
        self.tts_thread.finished.connect(self.tts_thread.deleteLater)
        self.tts_thread.start()
        # Re-enable controls for next steps
        self.file_upload.setEnabled(True)
        self.language_selector.setEnabled(True)

    def on_tts_complete(self, audio_path):
        self.progress_bar.setValue(90)
        self.progress_bar.setFormat("Merging dubbed audio with video...")
        self.status.showMessage("Merging dubbed audio with video...", 4000)
        # Merge dubbed audio with video
        output_video_path = os.path.join(
            self.export_folder_le.text(), "final_video.mp4"
        )
        success = merge_audio_with_video(
            self.session_state["video_file"],
            audio_path,
            output_video_path,
            keep_bgm=True,
        )
        self.loading_overlay.hide()
        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Dubbed video ready!")
            self.status.showMessage(
                f"Dubbed video exported to {output_video_path}", 6000
            )
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Audio/video merge failed.")
            self.status.showMessage("Audio/video merge failed.", 6000)

    def on_language_changed(self, lang):
        self.session_state["language"] = lang
        autosave_session(self.session_state)
        self.status.showMessage(f"Language set to {lang}", 3000)

    def restore_last_session(self):
        state = restore_session()
        if state:
            self.session_state.update(state)
            self.speakers = self.session_state.get("speakers", [])
            self.voices = self.session_state.get(
                "voices", list_voices() or ["Voice A", "Voice B", "Voice C"]
            )
            self.transcript = self.session_state.get("transcript", [])
            self.translated_transcript = self.session_state.get(
                "translated_transcript", []
            )
            # Optionally, update UI to reflect restored state
            if self.session_state.get("language"):
                self.language_selector.combo.setCurrentText(
                    self.session_state["language"]
                )
            # You could also show the selected file, etc.
            self.update_voices_panel(self.speakers, self.voices)
            autosave_session(self.session_state)

    def scan_tts_voices(self):
        voices = list_voices() or ["Voice A", "Voice B", "Voice C"]
        self.on_tts_voices_scanned(voices)

    def on_tts_voices_scanned(self, voices):
        # Call this after TTS voice scan
        self.update_voices_panel(voices=voices)

    def on_file_selected(self, file_path):
        self.progress_bar.setValue(10)
        self.file_upload.setEnabled(False)
        self.language_selector.setEnabled(False)
        self.progress_bar.setFormat("Extracting audio...")
        self.loading_overlay.show("Extracting audio...")
        self.temp_audio_path = tempfile.mktemp(suffix=".wav")
        self.audio_thread = QThread()
        self.audio_worker = AudioExtractWorker(file_path, self.temp_audio_path)
        self.audio_worker.moveToThread(self.audio_thread)
        self.audio_thread.started.connect(self.audio_worker.run)
        self.audio_worker.progress.connect(self.progress_bar.setValue)
        self.audio_worker.finished.connect(self.on_audio_extracted)
        self.audio_worker.finished.connect(self.audio_thread.quit)
        self.audio_worker.finished.connect(self.audio_worker.deleteLater)
        self.audio_thread.finished.connect(self.audio_thread.deleteLater)
        self.audio_thread.start()
        # Update session state
        self.session_state["video_file"] = file_path
        autosave_session(self.session_state)
        self.status.showMessage("Video file selected. Extracting audio...", 4000)

    def on_audio_extracted(self, success, audio_path):
        self.loading_overlay.hide()
        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Audio extracted!")
            self.session_state["audio_path"] = audio_path
            self.status.showMessage("Audio extracted successfully!", 4000)
            # Start transcription
            self.loading_overlay.show("Transcribing audio...")
            self.progress_bar.setValue(30)
            self.progress_bar.setFormat("Transcribing audio...")
            self.trans_thread = QThread()
            self.trans_worker = TranscriptionWorker(audio_path)
            self.trans_worker.moveToThread(self.trans_thread)
            self.trans_thread.started.connect(self.trans_worker.run)
            self.trans_worker.progress.connect(self.progress_bar.setValue)
            self.trans_worker.finished.connect(self.on_transcription_complete)
            self.trans_worker.finished.connect(self.trans_thread.quit)
            self.trans_worker.finished.connect(self.trans_worker.deleteLater)
            self.trans_thread.finished.connect(self.trans_thread.deleteLater)
            self.trans_thread.start()
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Audio extraction failed.")
            self.session_state["audio_path"] = None
            self.status.showMessage("Audio extraction failed.", 4000)
            self.file_upload.setEnabled(True)
            self.language_selector.setEnabled(True)
            autosave_session(self.session_state)

    def on_transcription_complete(self, segments):
        self.progress_bar.setValue(50)
        self.progress_bar.setFormat("Transcription complete!")
        self.transcript = segments
        self.session_state["transcript"] = segments
        autosave_session(self.session_state)
        self.status.showMessage("Transcription complete!", 4000)
        # Start translation
        self.loading_overlay.show("Translating transcript...")
        self.progress_bar.setValue(55)
        self.progress_bar.setFormat("Translating transcript...")
        target_lang = self.session_state.get("language", "English")
        self.transl_thread = QThread()
        self.transl_worker = TranslationWorker(segments, target_lang)
        self.transl_worker.moveToThread(self.transl_thread)
        self.transl_thread.started.connect(self.transl_worker.run)
        self.transl_worker.progress.connect(self.progress_bar.setValue)
        self.transl_worker.finished.connect(self.on_translation_complete)
        self.transl_worker.finished.connect(self.transl_thread.quit)
        self.transl_worker.finished.connect(self.transl_worker.deleteLater)
        self.transl_thread.finished.connect(self.transl_thread.deleteLater)
        self.transl_thread.start()

    def on_translation_complete(self, translated_texts):
        self.progress_bar.setValue(60)
        self.progress_bar.setFormat("Translation complete!")
        # Attach translated text to transcript
        for i, seg in enumerate(self.transcript):
            seg["translated_text"] = (
                translated_texts[i] if i < len(translated_texts) else seg["text"]
            )
        self.translated_transcript = [seg["translated_text"] for seg in self.transcript]
        self.session_state["translated_transcript"] = self.translated_transcript
        autosave_session(self.session_state)
        self.status.showMessage("Translation complete!", 4000)
        self.loading_overlay.hide()
        self.update_transcript_display()
        # Start diarization
        self.loading_overlay.show("Detecting speakers (diarization)...")
        self.progress_bar.setValue(20)
        self.progress_bar.setFormat("Detecting speakers...")
        self.diar_thread = QThread()
        self.diar_worker = DiarizationWorker(self.session_state["audio_path"])
        self.diar_worker.moveToThread(self.diar_thread)
        self.diar_thread.started.connect(self.diar_worker.run)
        self.diar_worker.progress.connect(self.progress_bar.setValue)
        self.diar_worker.finished.connect(self.on_diarization_complete)
        self.diar_worker.finished.connect(self.diar_thread.quit)
        self.diar_worker.finished.connect(self.diar_worker.deleteLater)
        self.diar_thread.finished.connect(self.diar_thread.deleteLater)
        self.diar_thread.start()

    def show_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("DubCraft Studio Help")
        msg.setText(
            """
<b>DubCraft Studio Quick Tips</b><br><br>
- <b>Upload Video:</b> Drag & drop or browse to select a video file.<br>
- <b>Language:</b> Choose your target dubbing language.<br>
- <b>Progress:</b> Watch the progress bar for real-time updates.<br>
- <b>Sidebar:</b> Use the sidebar to navigate between features.<br>
- <b>Export:</b> Export your dubbed video and assets.<br><br>
For more help, visit the documentation or contact the community!
"""
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def switch_panel(self, idx):
        # Micro animation: fade transition
        old = self.panels.currentWidget()
        self.panels.setCurrentIndex(idx)
        new = self.panels.currentWidget()
        anim = QPropertyAnimation(new, b"windowOpacity")
        new.setWindowOpacity(0.0)
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.resize(self.centralWidget().size())

    def browse_export_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Export Folder", self.export_folder_le.text()
        )
        if folder:
            self.export_folder_le.setText(folder)

    def make_export_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(18)
        l.setContentsMargins(80, 40, 80, 40)
        l.addWidget(self.make_section_header("Export Options"))
        self.export_video_cb = QCheckBox("Export Final Video (with Dubbed Audio)")
        self.export_video_cb.setChecked(True)
        self.export_video_cb.setToolTip(
            "Export the final video with dubbed audio track"
        )
        l.addWidget(self.export_video_cb)
        self.export_audio_cb = QCheckBox("Export Translated Audio Only")
        self.export_audio_cb.setToolTip("Export only the dubbed/translated audio track")
        l.addWidget(self.export_audio_cb)
        self.export_transcript_cb = QCheckBox("Export Transcript (.txt)")
        self.export_transcript_cb.setToolTip(
            "Export the full transcript as a text file"
        )
        l.addWidget(self.export_transcript_cb)
        self.export_subtitles_cb = QCheckBox("Export Subtitles (.srt)")
        self.export_subtitles_cb.setToolTip("Export subtitles as an SRT file")
        l.addWidget(self.export_subtitles_cb)
        # Export folder
        folder_row = QHBoxLayout()
        folder_label = QLabel("Export Folder:")
        folder_label.setToolTip("Choose where to save exported files")
        folder_row.addWidget(folder_label)
        self.export_folder_le = QLineEdit(os.path.abspath("export"))
        self.export_folder_le.setToolTip("Export destination folder")
        folder_row.addWidget(self.export_folder_le)
        folder_btn = QPushButton("Browse")
        folder_btn.setToolTip("Browse for export folder")
        folder_btn.clicked.connect(self.browse_export_folder)
        folder_row.addWidget(folder_btn)
        l.addLayout(folder_row)
        # Export button
        self.export_btn = QPushButton("Export")
        self.export_btn.setToolTip("Start export of selected assets")
        self.export_btn.clicked.connect(self.export_assets)
        l.addWidget(self.export_btn)
        l.addStretch()
        return w

    def export_assets(self):
        folder = self.export_folder_le.text()
        os.makedirs(folder, exist_ok=True)
        exported = []
        errors = []
        # Export video
        if self.export_video_cb.isChecked():
            video_path = os.path.join(folder, "final_video.mp4")
            if os.path.exists(video_path):
                exported.append("Video: final_video.mp4")
            else:
                errors.append("Video not found. Please run the full workflow first.")
        # Export dubbed audio
        if self.export_audio_cb.isChecked():
            if hasattr(self, "dubbed_audio_path") and os.path.exists(
                self.dubbed_audio_path
            ):
                audio_out = os.path.join(folder, "translated_audio.wav")
                try:
                    import shutil

                    shutil.copy(self.dubbed_audio_path, audio_out)
                    exported.append("Audio: translated_audio.wav")
                except Exception as e:
                    errors.append(f"Audio export failed: {e}")
            else:
                errors.append(
                    "Dubbed audio not found. Please run the full workflow first."
                )
        # Export transcript
        if self.export_transcript_cb.isChecked():
            transcript_out = os.path.join(folder, "transcript.txt")
            try:
                with open(transcript_out, "w", encoding="utf-8") as f:
                    for seg in self.transcript:
                        f.write(
                            f"[{seg.get('start', 0):.2f}-{seg.get('end', 0):.2f}] {seg['text']}\n"
                        )
                exported.append("Transcript: transcript.txt")
            except Exception as e:
                errors.append(f"Transcript export failed: {e}")
        # Export subtitles
        if self.export_subtitles_cb.isChecked():
            srt_out = os.path.join(folder, "subtitles.srt")
            try:
                speaker_names = {i: s for i, s in enumerate(self.speakers)}
                generate_srt(self.transcript, srt_out, speaker_names=speaker_names)
                exported.append("Subtitles: subtitles.srt")
            except Exception as e:
                errors.append(f"Subtitle export failed: {e}")
        # Show result
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Results")
        if exported:
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("Exported:\n" + "\n".join(exported))
        if errors:
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(
                (msg.text() + "\n\n" if exported else "")
                + "Errors:\n"
                + "\n".join(errors)
            )
        msg.exec()

    def make_logs_panel(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setSpacing(18)
        l.setContentsMargins(80, 40, 80, 40)
        l.addWidget(self.make_section_header("Recent Logs"))
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setToolTip("View recent log entries here")
        l.addWidget(self.logs_text)
        clear_btn = QPushButton("Clear Logs")
        clear_btn.setToolTip("Clear all log entries from this view")
        clear_btn.clicked.connect(self.clear_logs)
        l.addWidget(clear_btn)
        l.addStretch()
        self.load_logs()
        return w

    def load_logs(self):
        log_path = os.path.join("export", "dubcraft.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                self.logs_text.setPlainText(f.read())
        else:
            self.logs_text.setPlainText("No logs yet.")

    def clear_logs(self):
        self.logs_text.clear()
        log_path = os.path.join("export", "dubcraft.log")
        if os.path.exists(log_path):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
