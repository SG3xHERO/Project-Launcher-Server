#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server application for Project Launcher.
A simple Flask API for hosting and distributing modpacks.
"""

import os
import json
import uuid
import shutil
import zipfile
import tempfile
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file, abort, render_template
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
import requests
from mod_sources import ModrinthClient
import flask

app = Flask(__name__,
          template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
          static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# Configure Jinja properly
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}  # Disable cache
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['DEBUG'] = True

CORS(app)
auth = HTTPBasicAuth()

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modpacks')
ALLOWED_EXTENSIONS = {'zip'}
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max upload size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure templates directory exists
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'), exist_ok=True)

# Ensure static directory exists
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), exist_ok=True)

# Admin credentials (should be stored more securely in production)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')

@auth.verify_password
def verify_password(username, password):
    """Verify admin credentials."""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return username

def allowed_file(filename):
    """Check if file is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_modpacks():
    """Load modpack metadata from modpacks.json file."""
    modpacks_file = os.path.join(UPLOAD_FOLDER, 'modpacks.json')
    if not os.path.exists(modpacks_file):
        return []
    
    try:
        with open(modpacks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading modpacks: {e}")
        return []

def save_modpacks(modpacks):
    """Save modpack metadata to modpacks.json file."""
    modpacks_file = os.path.join(UPLOAD_FOLDER, 'modpacks.json')
    try:
        with open(modpacks_file, 'w', encoding='utf-8') as f:
            json.dump(modpacks, f, indent=4)
    except Exception as e:
        print(f"Error saving modpacks: {e}")

def extract_modpack_info(modpack_path):
    """Extract modpack info from the uploaded file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract zip file
        with zipfile.ZipFile(modpack_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Look for manifest.json
        manifest_path = os.path.join(temp_dir, 'manifest.json')
        if not os.path.exists(manifest_path):
            raise ValueError("No manifest.json found in modpack")
            
        # Load manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        # Extract required fields
        required_fields = ['id', 'name', 'version', 'mc_versions', 'author', 'description']
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field: {field}")
                
        # Find icon if present
        icon_file = None
        icon_path = manifest.get('icon_path')
        if icon_path and os.path.exists(os.path.join(temp_dir, icon_path)):
            icon_file = os.path.join(temp_dir, icon_path)
            
        # Count mods
        mod_count = len(manifest.get('mods', []))
            
        return {
            'id': manifest['id'],
            'name': manifest['name'],
            'version': manifest['version'],
            'mc_versions': manifest['mc_versions'],
            'author': manifest['author'],
            'description': manifest['description'],
            'mod_count': mod_count,
            'icon_file': icon_file
        }

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Create default icon if it doesn't exist
def create_default_icon():
    """Create a simple default icon if it doesn't exist."""
    icon_path = os.path.join('static', 'default-icon.png')
    if os.path.exists(icon_path):
        return
        
    try:
        from PIL import Image, ImageDraw
        
        # Create a new image with a dark background
        img = Image.new('RGB', (128, 128), (46, 49, 66))
        draw = ImageDraw.Draw(img)
        
        # Draw a slightly lighter center area
        draw.rectangle([(10, 10), (118, 118)], fill=(43, 49, 78))
        
        # Draw a stylized "M" using simple shapes
        # Outer border of the "M"
        draw.polygon([(30, 30), (50, 30), (64, 60), (78, 30), (98, 30), (98, 98), (78, 98), 
                      (78, 60), (64, 90), (50, 60), (50, 98), (30, 98)], 
                     fill=(230, 27, 114))
        
        # Save the image
        img.save(icon_path)
        print(f"Created default icon at {icon_path}")
        
    except ImportError:
        # If PIL is not available, create a simple colored square
        with open(icon_path, 'wb') as f:
            # Basic PNG file with a pink square (minimal valid PNG)
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x80\x00\x00\x00\x80\x08\x02\x00\x00\x00L\\\xf6\x9c\x00\x00\x00\x19IDAT\x18W\xed\xc1\x01\x01\x00\x00\x00\x82 \xff\xafnH@\x01\x00\x00\x00\x00\xef\x06\x10 \x00\x01\x89Q\xc9\xb0\x00\x00\x00\x00IEND\xaeB`\x82')
            print(f"Created simple default icon at {icon_path}")

# Initialize client
modrinth_client = ModrinthClient()

@app.route('/')
def index():
    """Main page."""
    modpacks = load_modpacks()
    return render_template('index.html', modpacks=modpacks)

@app.route('/admin')
@auth.login_required
def admin_panel():
    """Admin panel."""
    modpacks = load_modpacks()
    return render_template('admin.html', modpacks=modpacks)

@app.route('/admin/create-modpack')
@auth.login_required
def create_modpack_page():
    """Modpack creation page."""
    print("Rendering create_modpack.html template")
    try:
        return render_template('create_modpack.html')
    except Exception as e:
        print(f"ERROR rendering create_modpack.html: {str(e)}")
        # Return a simple error message if template is missing
        return f"Error: {str(e)}", 500

@app.route('/api/modpacks', methods=['GET'])
def get_modpacks():
    """Get all modpacks."""
    modpacks = load_modpacks()
    return jsonify(modpacks)

@app.route('/api/modpacks/<modpack_id>', methods=['GET'])
def get_modpack(modpack_id):
    """Get a specific modpack."""
    modpacks = load_modpacks()
    for modpack in modpacks:
        if modpack['id'] == modpack_id:
            return jsonify(modpack)
    abort(404)

@app.route('/api/mods/search', methods=['GET'])
def search_mods():
    """Search for mods from Modrinth."""
    query = request.args.get('query', '')
    mc_version = request.args.get('mc_version', '')
    modloader = request.args.get('modloader', '')
    
    print(f"Search request: query='{query}', mc_version='{mc_version}', modloader='{modloader}'")
    
    if not query:
        print("Empty query, returning empty results")
        return jsonify([])
    
    try:
        results = modrinth_client.search_mods(query, mc_version, modloader)
        print(f"Found {len(results)} results")
        return jsonify(results)
    except Exception as e:
        print(f"Error in search_mods: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mods/popular', methods=['GET'])
def get_popular_mods():
    """Get popular mods from Modrinth."""
    mc_version = request.args.get('mc_version', '')
    modloader = request.args.get('modloader', '')
    limit = int(request.args.get('limit', 20))
    
    print(f"Getting popular mods (MC: {mc_version}, Modloader: {modloader})")
    
    try:
        results = modrinth_client.get_popular_mods(mc_version, modloader, limit)
        print(f"Found {len(results)} popular mods")
        return jsonify(results)
    except Exception as e:
        print(f"Error in get_popular_mods: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/search', methods=['GET'])
def debug_search_mods():
    """Debug route for mod searching."""
    try:
        result = modrinth_client.search_mods("fabric", "1.20.1", 5)
        return jsonify({
            "status": "ok",
            "count": len(result),
            "results": result
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/search', methods=['GET'])
def debug_search():
    """Debug route for testing API."""
    return jsonify({
        "status": "ok",
        "count": 5,
        "results": [
            {
                "id": "test1",
                "name": "Test Mod 1",
                "author": "Test Author",
                "description": "This is a test mod",
                "downloads": 1000,
                "page_url": "#"
            }
        ]
    })

@app.route('/api/modpacks', methods=['POST'])
@auth.login_required
def upload_modpack():
    """Upload a new modpack."""
    # Check if file is included
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
        
    # Save file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, secure_filename(file.filename))
    file.save(temp_path)
    
    try:
        # Extract modpack info
        modpack_info = extract_modpack_info(temp_path)
        modpack_id = modpack_info['id']
        
        # Check if modpack already exists
        modpacks = load_modpacks()
        for i, modpack in enumerate(modpacks):
            if modpack['id'] == modpack_id:
                # Update existing modpack
                modpack_dir = os.path.join(UPLOAD_FOLDER, modpack_id)
                if os.path.exists(modpack_dir):
                    shutil.rmtree(modpack_dir)
                    
                modpacks[i]['version'] = modpack_info['version']
                modpacks[i]['mc_versions'] = modpack_info['mc_versions']
                modpacks[i]['updated_at'] = datetime.now().isoformat()
                modpacks[i]['mod_count'] = modpack_info['mod_count']
                break
        else:
            # Add new modpack
            new_modpack = {
                'id': modpack_id,
                'name': modpack_info['name'],
                'version': modpack_info['version'],
                'mc_versions': modpack_info['mc_versions'],
                'author': modpack_info['author'],
                'description': modpack_info['description'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'download_count': 0,
                'mod_count': modpack_info['mod_count']
            }
            modpacks.append(new_modpack)
            
        # Save modpack file
        modpack_dir = os.path.join(UPLOAD_FOLDER, modpack_id)
        os.makedirs(modpack_dir, exist_ok=True)
        
        modpack_file = os.path.join(modpack_dir, f"{modpack_id}.zip")
        shutil.copy(temp_path, modpack_file)
        
        # Save icon if present
        if modpack_info.get('icon_file'):
            icon_ext = os.path.splitext(modpack_info['icon_file'])[1]
            icon_path = os.path.join(modpack_dir, f"icon{icon_ext}")
            shutil.copy(modpack_info['icon_file'], icon_path)
            
            # Update icon URL in metadata
            for modpack in modpacks:
                if modpack['id'] == modpack_id:
                    modpack['icon_url'] = f"/api/modpacks/{modpack_id}/icon"
                    break
        
        # Calculate file size and hash
        file_size = os.path.getsize(modpack_file)
        file_hash = calculate_file_hash(modpack_file)
        
        # Update metadata
        for modpack in modpacks:
            if modpack['id'] == modpack_id:
                modpack['file_size'] = file_size
                modpack['file_hash'] = file_hash
                modpack['download_url'] = f"/api/modpacks/{modpack_id}/download"
                break
        
        # Save modpack metadata
        save_modpacks(modpacks)
        
        return jsonify({'success': True, 'id': modpack_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

@app.route('/api/modpacks/create', methods=['POST'])
@auth.login_required
def create_modpack():
    """Create a modpack from the web interface."""
    temp_dir = None
    try:
        # Get JSON data from the form
        data = json.loads(request.form.get('data', '{}'))
        print(f"Received modpack creation request: {data['name']} (ID: {data.get('id', 'unknown')})")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['id', 'name', 'version', 'mc_versions', 'author', 'description', 'mods', 'modloader']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Add validation for modpack ID (no special characters)
        modpack_id = data['id']
        if not modpack_id.isalnum() and not '_' in modpack_id and not '-' in modpack_id:
            return jsonify({'error': 'Modpack ID should only contain letters, numbers, underscores or hyphens'}), 400

        # Validate mods list is not empty
        if len(data['mods']) == 0:
            return jsonify({'error': 'Modpack must contain at least one mod'}), 400
        
        # Create temporary directory for building the modpack
        temp_dir = tempfile.mkdtemp()
        print(f"Created temp directory at: {temp_dir}")
        
        # Create mods directory
        mods_dir = os.path.join(temp_dir, 'mods')
        os.makedirs(mods_dir, exist_ok=True)
        
        # Process logo if it was uploaded
        logo_path = None
        if 'logo' in request.files and request.files['logo'].filename:
            logo_file = request.files['logo']
            # Save the logo to the temp directory
            logo_ext = os.path.splitext(logo_file.filename)[1].lower()
            if logo_ext not in ['.png', '.jpg', '.jpeg', '.gif']:
                return jsonify({'error': 'Logo must be PNG, JPG or GIF format'}), 400
                
            logo_path = os.path.join(temp_dir, f"icon{logo_ext}")
            logo_file.save(logo_path)
            print(f"Saved uploaded logo to {logo_path}")
        
        # Prepare manifest
        manifest = {
            'id': data['id'],
            'name': data['name'],
            'version': data['version'],
            'mc_versions': data['mc_versions'],
            'author': data['author'],
            'description': data['description'],
            'modloader': data['modloader'],
            'mods': []
        }
        
        # Add logo path to manifest if logo was uploaded
        if logo_path:
            manifest['icon_path'] = os.path.basename(logo_path)
        
        # Download mods
        print(f"Starting download of {len(data['mods'])} mods")
        for mod in data['mods']:
            mod_id = mod['id']
            print(f"Processing mod {mod.get('name', 'unknown')} ({mod_id})")
            
            # Rest of the mod download code...
            # ...
        
        # Write manifest to file
        manifest_path = os.path.join(temp_dir, 'manifest.json')
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create ZIP file
        modpack_dir = os.path.join(UPLOAD_FOLDER, modpack_id)
        os.makedirs(modpack_dir, exist_ok=True)
        
        modpack_zip = os.path.join(modpack_dir, f"{modpack_id}.zip")
        print(f"Creating ZIP archive at {modpack_zip}")
        
        with zipfile.ZipFile(modpack_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add manifest
            zipf.write(manifest_path, os.path.basename(manifest_path))
            
            # Add logo if present
            if logo_path:
                zipf.write(logo_path, os.path.basename(logo_path))
                
                # Also save the logo directly to the modpack directory for icon API
                icon_ext = os.path.splitext(logo_path)[1]
                icon_dest = os.path.join(modpack_dir, f"icon{icon_ext}")
                shutil.copy(logo_path, icon_dest)
            
            # Add mods
            for mod_file in os.listdir(mods_dir):
                mod_path = os.path.join(mods_dir, mod_file)
                zipf.write(mod_path, os.path.join('mods', mod_file))
                
        print(f"✅ Created modpack ZIP at {modpack_zip}")
        
        # Update modpack metadata
        modpacks = load_modpacks()
        for i, modpack in enumerate(modpacks):
            if modpack['id'] == modpack_id:
                modpacks[i]['version'] = data['version']
                modpacks[i]['mc_versions'] = data['mc_versions']
                modpacks[i]['updated_at'] = datetime.now().isoformat()
                modpacks[i]['mod_count'] = len(manifest['mods'])
                if logo_path:
                    modpacks[i]['icon_url'] = f"/api/modpacks/{modpack_id}/icon"
                break
        else:
            # Add new modpack
            new_modpack = {
                'id': modpack_id,
                'name': data['name'],
                'version': data['version'],
                'mc_versions': data['mc_versions'],
                'author': data['author'],
                'description': data['description'],
                'modloader': data['modloader'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'download_count': 0,
                'mod_count': len(manifest['mods']),
                'download_url': f"/api/modpacks/{modpack_id}/download",
                'file_size': os.path.getsize(modpack_zip),
                'file_hash': calculate_file_hash(modpack_zip)
            }
            if logo_path:
                new_modpack['icon_url'] = f"/api/modpacks/{modpack_id}/icon"
            modpacks.append(new_modpack)
            
        # Save modpack metadata
        save_modpacks(modpacks)
        
        print(f"✅ Successfully created modpack '{data['name']}' (ID: {modpack_id})")
        return jsonify({'success': True, 'id': modpack_id})
        
    except Exception as e:
        import traceback
        print(f"❌ Error creating modpack: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up
        if temp_dir and os.path.exists(temp_dir):
            print(f"Cleaning up temp directory: {temp_dir}")
            shutil.rmtree(temp_dir)

@app.route('/api/modpacks/<modpack_id>/download', methods=['GET'])
def download_modpack(modpack_id):
    """Download a modpack."""
    modpack_file = os.path.join(UPLOAD_FOLDER, modpack_id, f"{modpack_id}.zip")
    if not os.path.exists(modpack_file):
        abort(404)
        
    # Update download count
    modpacks = load_modpacks()
    for modpack in modpacks:
        if modpack['id'] == modpack_id:
            modpack['download_count'] += 1
            save_modpacks(modpacks)
            break
            
    return send_file(modpack_file, as_attachment=True)

@app.route('/api/modpacks/<modpack_id>/icon', methods=['GET'])
def get_modpack_icon(modpack_id):
    """Get modpack icon."""
    modpack_dir = os.path.join(UPLOAD_FOLDER, modpack_id)
    if not os.path.exists(modpack_dir):
        # Return default icon
        default_icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'default-icon.png')
        if os.path.exists(default_icon):
            return send_file(default_icon)
        abort(404)
        
    # Find icon file
    for filename in os.listdir(modpack_dir):
        if filename.startswith('icon'):
            icon_path = os.path.join(modpack_dir, filename)
            return send_file(icon_path)
            
    # No icon found, return default
    default_icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'default-icon.png')
    if os.path.exists(default_icon):
        return send_file(default_icon)
        
    abort(404)

@app.route('/api/modpacks/<modpack_id>', methods=['DELETE'])
@auth.login_required
def delete_modpack(modpack_id):
    """Delete a modpack."""
    modpacks = load_modpacks()
    for i, modpack in enumerate(modpacks):
        if modpack['id'] == modpack_id:
            # Remove from list
            del modpacks[i]
            
            # Delete files
            modpack_dir = os.path.join(UPLOAD_FOLDER, modpack_id)
            if os.path.exists(modpack_dir):
                shutil.rmtree(modpack_dir)
                
            # Save modpack metadata
            save_modpacks(modpacks)
            
            return jsonify({'success': True})
            
    abort(404)

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_file(os.path.join('static', filename))

if __name__ == '__main__':
    # Create template files if they don't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    
    # Make sure the default icon exists
    create_default_icon()
    
    # Start the server
    app.run(host='0.0.0.0', port=5000, debug=True)