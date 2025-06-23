"""Video processing: merging audio, burning subtitles."""
from typing import Optional
import moviepy.editor as mp
import ffmpeg
import subprocess
import os


def merge_audio_with_video(video_path: str, audio_path: str, output_path: str, keep_bgm: bool = True) -> bool:
    """
    Merge dubbed audio with video, optionally keeping background music.
    If keep_bgm is True, mixes original video audio (music) with dubbed audio.
    """
    try:
        if keep_bgm:
            # Extract original audio
            orig_audio_path = output_path + ".orig.wav"
            (
                ffmpeg.input(video_path)
                .output(orig_audio_path, acodec="pcm_s16le", ac=2, ar="44100")
                .overwrite_output()
                .run(quiet=True)
            )
            # Mix original and dubbed audio
            mixed_audio_path = output_path + ".mixed.wav"
            (
                ffmpeg.input(orig_audio_path)
                .filter('volume', 0.5)
                .output('vol1.wav', acodec="pcm_s16le", ac=2, ar="44100")
                .overwrite_output()
                .run(quiet=True)
            )
            (
                ffmpeg.input(audio_path)
                .filter('volume', 1.0)
                .output('vol2.wav', acodec="pcm_s16le", ac=2, ar="44100")
                .overwrite_output()
                .run(quiet=True)
            )
            (
                ffmpeg.input(['vol1.wav', 'vol2.wav'])
                .filter('amix', inputs=2, duration='longest')
                .output(mixed_audio_path, acodec="pcm_s16le", ac=2, ar="44100")
                .overwrite_output()
                .run(quiet=True)
            )
            # Merge mixed audio with video
            (
                ffmpeg.input(video_path)
                .output(output_path, audio=mixed_audio_path, vcodec='copy', acodec='aac', strict='experimental')
                .overwrite_output()
                .run(quiet=True)
            )
            # Cleanup temp files
            for f in [orig_audio_path, 'vol1.wav', 'vol2.wav', mixed_audio_path]:
                if os.path.exists(f):
                    os.remove(f)
        else:
            # Replace audio track with dubbed audio
            (
                ffmpeg.input(video_path)
                .output(output_path, audio=audio_path, vcodec='copy', acodec='aac', strict='experimental')
                .overwrite_output()
                .run(quiet=True)
            )
        return True
    except Exception as e:
        print(f"merge_audio_with_video error: {e}")
        return False


def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> bool:
    """
    Burn subtitles into video using ffmpeg.
    """
    try:
        # ffmpeg must be compiled with libass for subtitles
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vf', f"subtitles={srt_path}",
            '-c:a', 'copy', output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception as e:
        print(f"burn_subtitles error: {e}")
        return False


def get_video_info(video_path: str) -> Optional[dict]:
    """
    Return video info: duration (s), fps, size (w, h), audio channels, etc.
    """
    try:
        clip = mp.VideoFileClip(video_path)
        info = {
            'duration': clip.duration,
            'fps': clip.fps,
            'size': clip.size,
            'audio_fps': clip.audio.fps if clip.audio else None,
            'audio_channels': clip.audio.nchannels if clip.audio else None,
        }
        clip.close()
        return info
    except Exception as e:
        print(f"get_video_info error: {e}")
        return None


def extract_preview_frame(video_path: str, time: float, out_path: str) -> bool:
    """
    Extract a frame at a given time for preview using moviepy.
    """
    try:
        clip = mp.VideoFileClip(video_path)
        frame = clip.get_frame(time)
        from PIL import Image
        img = Image.fromarray(frame)
        img.save(out_path)
        clip.close()
        return True
    except Exception as e:
        print(f"extract_preview_frame error: {e}")
        return False 