==================================================
MAULI TRAVEL - PROJECT RUN INSTRUCTIONS
==================================================

1. Open project folder in VS Code.
2. Open Windows Terminal (PowerShell or Command Prompt).

3. Create virtual environment:
   python -m venv venv

4. Activate virtual environment:
   .\venv\Scripts\Activate.ps1

5. Install dependencies:
   python -m pip install -r requirements.txt

6. Run application:
   python app.py

7. Access the application in browser:
   Main Site: http://127.0.0.1:5000
   Admin Panel: http://127.0.0.1:5000/admin/login

==================================================
ADMIN LOGIN CREDENTIALS
==================================================
Username: admin
Password: admin123

==================================================
ASSET REPLACEMENT LOCATIONS
==================================================
Replace assets anytime with identical filenames:
- Forest Background (4K JPEG): static/img/forest-background.jpg
- Hyundai Aura Image: static/img/aura-car.jpg
- Logo Image: static/img/logo.png


# in the below 1 one project overview


# Mauli Travel V3 — Notebook Travel Website

A Flask + SQLite website for Mauli Travel, Buldana.

## Included in V3
- Shree Sant Gajanan Maharaj logo from the supplied image.
- Moving ticker: `संत श्री गजानन महाराज !! गण गण गणात बोते !!`
- Notebook / handwritten visual style across customer pages.
- Slow smooth page transitions and reveal animations.
- Aura car scroll animation on the home page.
- Large circular 360-style interactive viewer area with mouse/touch drag behavior.
- Customer booking calendar + green available / red booked time slots.
- Admin login and simple admin control desk.
- Admin can add/delete upcoming tours; published tours appear on Home and Tours pages.
- Existing customer registration/login/dashboard and booking workflow retained.
- Direct WhatsApp link to +91 70201 38677.

## 360 interior image
The supplied Hyundai HTML confirms that the reference page uses a dedicated `Hyundai Aura 360° Interior View Experience` / panorama viewer, but the saved HTML does not contain the actual panorama image file. This project therefore includes the interactive circular viewer shell without copying Hyundai's protected panorama asset.

For a true interior panorama, place your own equirectangular 360 image at:

`static/img/360/aura-360.jpg`

The current viewer remains usable as a visual fallback until that asset is added.

## Run in VS Code PowerShell
```powershell
cd path\to\mauli_travel_v3
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

Admin:
- URL: `http://127.0.0.1:5000/admin/login`
- Username: `admin`
- Password: `admin123`

Change the admin password before production deployment.
