# StudyPet — Attention / Face demos

Main Idea
“Focus Buddy: A Distraction-Aware Study Companion”

A system that:

- tracks eyes, face, and posture through webcam
- detects distraction, drowsiness, looking away, slouching, or phone usage
- when distraction occurs:
    pops up a playful 3D pet (dog/cat/alien etc.)
    pet makes noise, barks, waves, asks to play, gives reminders
    user interacts briefly → returns to study

What has been done? 

Used face_recognition + OpenCV + Pillow to create -

- `main.py` — detect facial landmarks in a static image and draw features.
- `webcam.py` — webcam demo that blurs detected faces in real time.

## Prerequisites (macOS)
- Python 3.9.6
- Xcode Command Line Tools: `xcode-select --install`
- Homebrew (optional, for native deps)

## Quick install
Open Terminal and run:
```bash
cd /Users/arya/code/studypet
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
# install native build deps if needed
brew install cmake boost libomp pkg-config
# python packages
pip install pillow face_recognition opencv-python