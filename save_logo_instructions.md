# Logo Setup Instructions

The Streamlit UI has been configured to use your logo image.

## Quick Setup

1. **Save your logo image** as:
   ```
   ui/assets/logo.png
   ```

2. The image will automatically appear:
   - As the browser tab icon (favicon)
   - In the main header (100px width)
   - In the sidebar (150px width)

## Current Status

- ✅ UI code updated to support logo
- ✅ Assets directory created at `ui/assets/`
- ⏳ Waiting for logo image file

## To add your logo:

**Option 1: Drag and Drop**
- Drag the logo image file into the `ui/assets/` folder
- Rename it to `logo.png`

**Option 2: Command Line**
```bash
# Copy your logo to the project
cp /path/to/your/logo.png "ui/assets/logo.png"
```

**Option 3: macOS Finder**
1. Open Finder
2. Navigate to: Documents/AI Knowledge Continuity System/ui/assets/
3. Copy your logo image there
4. Rename to: logo.png

## Supported Formats

The app expects PNG format, but you can also use:
- JPG/JPEG
- SVG
- GIF

Just update the file extension in `ui/app.py` if using a different format.

## Test the UI

After saving the logo, run:
```bash
python main.py --ui
```

The logo should appear in:
1. Browser tab icon
2. Top of the main page (left side)
3. Top of the sidebar
