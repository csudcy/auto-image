# auto-image
Automatically choose the top N interesting images from a set of images

# Setup

- Install node
- Install [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods) - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Install [rust](https://rustup.rs/) - `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Install [tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html) for OCR - `brew install tesseract`
- Restart terminal
- Install dependencies (takes a while cause of numpy, torch, etc.) - `npm run deps:install`

# Notes

`brew info tesseract`
path => `/usr/local/Cellar/tesseract/5.5.0/share/tesserdata`
