# Project Launcher Server

A simple web server for hosting and distributing Project Launcher that works with the Project Launcher client.

## Features

- RESTful API for modpack management
- Web interface for browsing and downloading modpacks
- Admin panel for uploading and managing modpacks
- Compatible with Project Launcher client

## Installation

### Requirements

- Python 3.9 or higher
- Flask and other dependencies

### Setup

1. Install dependencies:
   ```bash
   pip install flask flask-cors flask-httpauth werkzeug
   ```

2. Set admin credentials (optional):
   ```bash
   export ADMIN_USERNAME=your_username
   export ADMIN_PASSWORD=your_secure_password
   ```

3. Run the server:
   ```bash
   python app.py
   ```

The server will run on http://localhost:5000 by default.

## Usage

### Accessing the Web Interface

- **Main Page**: http://localhost:5000/
  - Displays all available modpacks
  - Users can download modpacks directly from this page

- **Admin Panel**: http://localhost:5000/admin
  - Requires authentication (default: admin/admin)
  - Upload new modpacks
  - Manage existing modpacks

### API Endpoints

- **GET /api/modpacks**
  - Get a list of all modpacks

- **GET /api/modpacks/{modpack_id}**
  - Get information about a specific modpack

- **GET /api/modpacks/{modpack_id}/download**
  - Download a modpack

- **GET /api/modpacks/{modpack_id}/icon**
  - Get the modpack's icon

- **POST /api/modpacks**
  - Upload a new modpack (requires authentication)

- **DELETE /api/modpacks/{modpack_id}**
  - Delete a modpack (requires authentication)

## Modpack Format

Modpacks should be provided as ZIP files with the following structure:

```
modpack.zip
├── manifest.json         # Required: Contains modpack metadata
├── mods/                 # Optional: Mod files
├── config/               # Optional: Configuration files
├── resourcepacks/        # Optional: Resource packs
└── icon.png              # Optional: Modpack icon
```

The `manifest.json` file must contain the following fields:
- `id`: Unique identifier for the modpack
- `name`: Display name
- `version`: Version string
- `mc_versions`: Array of compatible Minecraft versions
- `author`: Author name
- `description`: Modpack description
- `icon_path`: Optional path to the icon file within the ZIP

## Deployment

For production use, we recommend:

1. Using a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 app:app
   ```

2. Setting up a reverse proxy with Nginx or Apache

3. Using HTTPS with Let's Encrypt

4. Changing the default admin credentials

## License

This project is licensed under the MIT License - see the LICENSE file for details.