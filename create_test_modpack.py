#!/usr/bin/env python3
"""
This script creates a test modpack ZIP file that can be uploaded to the server.
It generates a basic structure with a manifest.json and placeholder files.
This simplified version doesn't rely on PIL for image creation.
"""

import os
import json
import zipfile
import tempfile
import shutil

# Create a temporary directory for building the modpack
temp_dir = tempfile.mkdtemp()
print(f"Creating modpack in temporary directory: {temp_dir}")

try:
    # Create subdirectories
    os.makedirs(os.path.join(temp_dir, "mods"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "config"), exist_ok=True)

    # Create manifest.json
    manifest = {
        "id": "test_modpack",
        "name": "Test Modpack",
        "version": "1.0.0",
        "mc_versions": ["1.19.4", "1.20.1"],
        "author": "Ben Foggon",
        "description": "A simple test modpack to verify the server is working correctly.",
        "mods": [
            {
                "id": "mod1",
                "name": "Example Mod 1",
                "version": "1.2.3",
                "mc_versions": ["1.19.4", "1.20.1"],
                "file_name": "mod1-1.2.3.jar",
                "dependencies": []
            },
            {
                "id": "mod2",
                "name": "Example Mod 2",
                "version": "2.0.1",
                "mc_versions": ["1.19.4", "1.20.1"],
                "file_name": "mod2-2.0.1.jar",
                "dependencies": ["mod1"]
            }
        ],
        "config_files": ["config/example.cfg"],
        "resource_packs": []
    }

    with open(os.path.join(temp_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

    # Create a placeholder config file
    with open(os.path.join(temp_dir, "config", "example.cfg"), "w", encoding="utf-8") as f:
        f.write("# This is a sample configuration file\n")
        f.write("setting1 = true\n")
        f.write("setting2 = 42\n")
        f.write("setting3 = \"Hello, World!\"\n")

    # Create placeholder mod files (just empty files)
    with open(os.path.join(temp_dir, "mods", "mod1-1.2.3.jar"), "w") as f:
        f.write("This is a placeholder for a mod file")

    with open(os.path.join(temp_dir, "mods", "mod2-2.0.1.jar"), "w") as f:
        f.write("This is another placeholder for a mod file")

    # Create the ZIP file
    zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_modpack.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, temp_dir)
                zip_file.write(file_path, arc_name)

    print(f"Modpack created successfully: {zip_path}")
    print("You can now upload this modpack to your server using the admin panel.")

except Exception as e:
    print(f"Error creating modpack: {e}")

finally:
    # Clean up temporary directory
    shutil.rmtree(temp_dir)