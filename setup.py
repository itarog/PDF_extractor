#!/usr/bin/env python3
"""
Setup script for PDF Chemical Analysis Extractor
"""

import os
import shutil
import subprocess
import zipfile
from io import BytesIO
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.install import install

# --- helpers ---------------------------------------------------------------
def safe_print(msg: str) -> None:
    # Avoid UnicodeEncodeError on Windows terminals (cp1255 etc.)
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))

def _dl_bytes(url, chunk=8192):
    try:
        import requests
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            bio = BytesIO()
            for c in r.iter_content(chunk_size=chunk):
                if c:
                    bio.write(c)
            bio.seek(0)
            return bio
    except Exception as e:
        raise RuntimeError(f"Failed downloading from {url}: {e}")


class CustomInstallCommand(install):
    """Download yolov5 zip, extract yolov5 folder, install Poppler."""

    def run(self):
        import zipfile
        import urllib.request
        
        project_root = Path(__file__).parent.resolve()
        repo_url = os.environ.get("YODE_REPO_URL", "https://github.com/OneChorm/YoDe-Segmentation/archive/refs/heads/master.zip")
        target_dir = project_root / "yolov5"
        temp_zip = project_root / "_temp.zip"
        temp_dir = project_root / "_temp_repo"

        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            print(f"Downloading from {repo_url} ...")
            urllib.request.urlretrieve(repo_url, temp_zip)
            
            with zipfile.ZipFile(temp_zip, 'r') as z:
                z.extractall(temp_dir)
            
            # Find yolov5 folder in extracted content
            extracted = next(temp_dir.iterdir())
            yolov5_path = extracted / "yolov5"
            
            if yolov5_path.exists():
                shutil.copytree(yolov5_path, target_dir, dirs_exist_ok=True)
                print("yolov5 folder copied.")
            else:
                print("WARNING: No yolov5 folder found.")
        except Exception as e:
            print(f"WARNING: download/extract failed: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_zip.unlink(missing_ok=True)

        # --- 2) Download model file from Google Drive into yolov5 ---
        file_id = "1tXX_-RE2sL2U7lRvFfOBUBTIIIN_MhnN"
        target_dir.mkdir(parents=True, exist_ok=True)
        weights_out = target_dir / "best.pt"
        if not weights_out.exists():
            safe_print(f"Downloading model file to {weights_out} ...")
            try:
                url = f"https://drive.google.com/uc?export=download&id={file_id}"
                bio = _dl_bytes(url)
                with open(weights_out, "wb") as f:
                    f.write(bio.read())
                safe_print("Model file downloaded successfully.")

            except Exception as e:
                safe_print(f"WARNING: could not download Drive file: {e}")
        else:
            safe_print("Model file already exists — skipping download.")

        # --- 3) Download & extract Poppler into ./poppler and delete the zip ---
        poppler_url = (
            "https://github.com/oschwartz10612/poppler-windows/releases/download/"
            "v25.07.0-0/Release-25.07.0-0.zip"
        )
        poppler_dir = project_root / "poppler"
        poppler_zip_tmp = project_root / "_poppler_tmp.zip"

        if not poppler_dir.exists():
            safe_print(f"Downloading Poppler from {poppler_url} ...")
            try:
                bio = _dl_bytes(poppler_url)
                with open(poppler_zip_tmp, "wb") as f:
                    f.write(bio.read())

                safe_print("Extracting Poppler ...")
                stage_dir = project_root / "_poppler_stage"
                if stage_dir.exists():
                    shutil.rmtree(stage_dir, ignore_errors=True)
                with zipfile.ZipFile(poppler_zip_tmp, "r") as zf:
                    zf.extractall(stage_dir)

                # find the top-level extracted folder and rename to 'poppler'
                extracted_roots = [p for p in stage_dir.iterdir() if p.is_dir()]
                if len(extracted_roots) == 1:
                    shutil.move(str(extracted_roots[0]), str(poppler_dir))
                else:
                    poppler_dir.mkdir(parents=True, exist_ok=True)
                    for p in stage_dir.iterdir():
                        shutil.move(str(p), str(poppler_dir / p.name))

                # cleanup
                if stage_dir.exists():
                    shutil.rmtree(stage_dir, ignore_errors=True)
                if poppler_zip_tmp.exists():
                    poppler_zip_tmp.unlink()

                safe_print(f"Poppler installed at: {poppler_dir}")
                safe_print(f"If using pdf2image on Windows, set poppler_path to: {poppler_dir / 'bin'}")
            except Exception as e:
                safe_print(f"WARNING: Poppler install failed: {e}")
                try:
                    if poppler_zip_tmp.exists():
                        poppler_zip_tmp.unlink()
                    stage_dir = project_root / "_poppler_stage"
                    if stage_dir.exists():
                        shutil.rmtree(stage_dir, ignore_errors=True)
                except Exception:
                    pass
        else:
            safe_print("Poppler folder already exists — skipping download.")


        # --- 4) Download & extract DECIMER locally ---
        decimer_url = (
            "https://github.com/Kohulan/DECIMER-Image_Transformer/"
            "archive/refs/tags/v2.8.0.zip"
        )

        decimer_dir = project_root / "DECIMER"
        decimer_zip = project_root / "_decimer_tmp.zip"
        decimer_stage = project_root / "_decimer_stage"

        if not decimer_dir.exists():
            safe_print("Downloading DECIMER repository...")
            try:
                bio = _dl_bytes(decimer_url)
                with open(decimer_zip, "wb") as f:
                    f.write(bio.read())

                with zipfile.ZipFile(decimer_zip, "r") as zf:
                    zf.extractall(decimer_stage)

                extracted_root = next(decimer_stage.iterdir())
                shutil.move(str(extracted_root), str(decimer_dir))

                safe_print(f"DECIMER installed locally at: {decimer_dir}")

            except Exception as e:
                safe_print(f"WARNING: DECIMER install failed: {e}")

            finally:
                shutil.rmtree(decimer_stage, ignore_errors=True)
                if decimer_zip.exists():
                    decimer_zip.unlink()
        else:
            safe_print("DECIMER folder already exists — skipping download.")
        # Continue normal installation
        install.run(self)


# --------- Setup metadata ----------
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="pdf-chemical-extractor",
    version="0.1.0",
    author="Itamar Wallwater et al.",
    description="Extract chemical analysis text and molecule images from PDF files for Label Studio annotation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/PDF_extractor",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "decimer-segmentation>=1.0.0",
        "PyMuPDF>=1.23.0",
        "pypdf>=3.0.0",
        "numpy>=1.24.0",
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "torch==2.5.0",
        "torchvision==0.20.0",
        "seaborn>=0.13.0",
        "pdf2image>=1.16.0",
        "label-studio>=1.21.0",
        "regex>=2023.0.0",
        "python-dateutil>=2.8.0",
        "gdown>=5.1.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pdf-extract=main:main",
        ],
    },
    cmdclass={"install": CustomInstallCommand},
)
