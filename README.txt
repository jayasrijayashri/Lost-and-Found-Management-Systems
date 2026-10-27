FINDLY — LOST & FOUND MANAGEMENT SYSTEM (UPDATED COLOURFUL COMMUNITY THEME)

FIXES
1. No sample lost/found reports: database starts empty.
2. Uploaded images are stored in static/uploads and shown to every browser connecting to the SAME running server.
3. QR Handover removed from the navigation and app.
4. Smart matching requires same category AND matching item-name type. A backpack cannot match a wallet.

RUN (Windows / VS Code)
1. Install Python 3.10 or newer from python.org (check Add Python to PATH).
2. Extract the ZIP and open the Findly_Fixed_Light_Theme folder in VS Code.
3. Open Terminal > New Terminal.
4. Run: python -m pip install -r requirements.txt
5. Run: python app.py
6. Open http://127.0.0.1:5000 in Chrome / Edge.

DO NOT double-click templates/index.html and DO NOT use Live Server.
The Python Flask server is needed to store images and share data across visitors.

SHARE WITH OTHER DEVICES ON THE SAME WI-FI
- Keep python app.py running on your computer.
- Find your computer's local IPv4 address using ipconfig.
- On another device, open http://YOUR_COMPUTER_IP:5000
- Allow port 5000 through your firewall if prompted.
- Both devices now see the same reports and photos.

DATA
- findly.db is created automatically when the server starts; it starts EMPTY.
- Photos are stored in static/uploads.
- Data remains after restarting the server.
- If you want to reset YOUR reports, stop the server, delete findly.db and the uploaded photos, then restart.

IMPORTANT
- This is a local college project prototype, not a secure public service.
- No login or access control. Claim review buttons are a demonstration.
- Smart matching is rule-based, not an AI image classifier.
- Photos are shared with anyone who can reach your running server; do not upload sensitive documents.
