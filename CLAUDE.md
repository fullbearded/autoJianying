# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pyJianYingDraft is a Python library for generating and exporting 剪映 (JianYing) video editing drafts programmatically. It enables automated video editing pipelines by creating draft files that can be opened in the JianYing video editor.

## Core Architecture

### Main Components

- **DraftFolder**: Manages draft files within a folder structure, mimicking JianYing's draft organization
- **ScriptFile**: Core class representing a video editing project/draft with tracks, segments, and materials
- **Segments**: Video, Audio, Text, Sticker, Effect, and Filter segments representing timeline elements
- **Materials**: VideoMaterial, AudioMaterial handling media file references and metadata
- **Tracks**: Container system for organizing segments by type (video, audio, text, effect, filter)
- **Metadata**: Extensive enums for effects, filters, fonts, animations, transitions

### Template Mode System
The library supports loading existing JianYing drafts as templates:
- Load encrypted draft files (JianYing 5.9 and below only)
- Replace materials by name or segment
- Import tracks between drafts
- Extract material metadata (resource_ids for stickers, effects, etc.)

### Time System
Uses microseconds internally but supports string format for convenience:
- Microsecond integers: `1000000` (1 second)
- String format: `"1.5s"`, `"1h3m12s"`, etc.
- Helper functions: `tim()` for conversion, `trange()` for time ranges

## Development Commands

### Installation
```bash
pip install pyJianYingDraft
```

### Running Demo
```bash
python demo.py
```
Note: Requires setting `<你的草稿文件夹>` to your actual JianYing drafts folder path.

### Project Structure
- `pyJianYingDraft/` - Main package
- `pyJianYingDraft/metadata/` - Effect, filter, font, and animation definitions
- `pyJianYingDraft/assets/` - Template JSON files for draft structure
- `readme_assets/tutorial/` - Sample media files for demo

## Key Development Patterns

### Creating a Basic Draft
```python
import pyJianYingDraft as draft

# Initialize draft folder manager
draft_folder = draft.DraftFolder("path/to/jianying/drafts")

# Create new draft
script = draft_folder.create_draft("project_name", 1920, 1080)

# Add tracks
script.add_track(draft.TrackType.video)
script.add_track(draft.TrackType.audio)

# Add segments with time ranges
video_seg = draft.VideoSegment("video.mp4", draft.trange("0s", "10s"))
script.add_segment(video_seg)

# Save draft
script.save()
```

### Template Mode Usage
```python
# Load existing draft as template
script = draft_folder.duplicate_as_template("template_name", "new_draft")

# Replace materials
new_material = draft.AudioMaterial("new_audio.mp3")
script.replace_material_by_name("old_audio.mp3", new_material)

# Import tracks from other drafts
source_script = draft_folder.load_template("source_draft")
target_script.import_track(source_script, text_track, offset="10s")
```

### Working with Effects and Animations
```python
# Add video effects
from pyJianYingDraft import VideoSceneEffectType
video_seg.add_effect(VideoSceneEffectType.全息扫描, [None, None, 100.0])

# Add animations
from pyJianYingDraft import IntroType, TextIntro
video_seg.add_animation(IntroType.斜切)
text_seg.add_animation(TextIntro.复古打字机)

# Add filters
from pyJianYingDraft import FilterType
video_seg.add_filter(FilterType.原生肤, intensity=10)
```

## Platform Support

- **Windows**: Full functionality including automated export via JianyingController
- **Linux/macOS**: Draft generation and template mode only (no automated export)
- **JianYing Version Support**: 
  - Template mode: 5.9 and below (due to encryption in 6+)
  - Export automation: 6 and below (UI changes in 7+)
  - Draft generation: All versions 5+

## Dependencies

- `pymediainfo`: Media file metadata extraction
- `imageio`: Image processing for video materials
- `uiautomation>=2`: Windows-only UI automation for export (conditional import)

## Backward Compatibility

The library maintains backward compatibility through deprecated snake_case class names (e.g., `Script_file` → `ScriptFile`) with deprecation warnings.