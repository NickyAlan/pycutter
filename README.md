# Pycutter
Using Python: audio2numpy, NumPy, and MoviePy for Removing or Preserving Silent Parts in .mp4 or .mp3 Files
- The idea behind this project is to find the threshold for the cut point in order to remove parts of the audio that are quieter. 
- By determining the shortest duration for cutting the silent parts, such as removing parts longer than 0.5 seconds of silence, we can extract the speech segments. 
- In addition, this idea can make creating .srt files for pre-timed subtitles make your life easier when making subtitles
- This Python script can be used to process both MP4 and MP3 files. 
- You can either clone the repository or use it on [Google Colab](https://colab.research.google.com/github/NickygenN1/pycutter/blob/main/pycutter_colab.ipynb)
- For a demonstration of the functionality, please watch the demo video on [YouTube](https://youtu.be/6LRnvP1Ab90)

### Removing or Preserving Silent Parts
```Python
cut = CutterIt(filepath='video.mp4')
array = cut.array
undercuts = cut.get_under_cuts(array)
keeps_sec = cut.get_keeps_sec(undercuts)
cut.cutter('keep_cutter.mp4', keeps_sec, file_type='mp4') # or .mp3

# if want only silent part
cut.cutter('silent_part.mp4', undercuts, file_type='mp4')
```

### Pre-timed subtitles
```Python
tsub = Timesub(filepath='video.mp4')
keeps_sec_subtitle = tsub.get_timesub()
tsub.get_srtfile('timesub.srt', keeps_sec_subtitle)
```
