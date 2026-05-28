# cogs/music_core.py
import os

# Global variables framework shared across independent music split cogs files
GLOBAL_QUEUES = {}
CURRENT_TRACK = {} # Tracks what song is currently playing in each server

# FFMPEG structural playback matrix configuration configurations
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

def get_bin_path():
    return './ffmpeg/ffmpeg' if os.path.exists('./ffmpeg/ffmpeg') else 'ffmpeg'