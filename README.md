# CROX - Computer Science Project

## Overview
This is a full-stack web application built with **Python (Flask)** and **HTML/CSS/JS**. 
It allows users to dynamically design a house blueprint, calculate budgets, and manipulate a 3D CSS-based Isometric architectural model in real-time.

## Features
- **Python Backend**: Manages dynamic floor levels, room objects, furniture inventory, and budget calculations.
- **Persistent Storage**: Saves all user progress to a local `house_data.json` file.
- **3D Isometric Engine**: A custom CSS engine that renders the 2D blueprint into a scrollable, draggable 3D view.
- **Magnetic Snapping**: JavaScript physics bounds-checking that perfectly snaps rooms together and draws doorway connections on adjoining walls.

## How to Run (Windows)
1. Double-click the `run_project.bat` file.
2. It will automatically check for Python, install `Flask`, and start the server.
3. Open your web browser and go to: `http://127.0.0.1:5000`

## How to Run (Mac / Linux / Manual)
1. Ensure Python 3 is installed.
2. Open a terminal in this folder and install Flask:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your web browser and go to: `http://127.0.0.1:5000`
