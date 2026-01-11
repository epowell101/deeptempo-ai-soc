# Timesketch Troubleshooting Summary

## Issue Found

The Timesketch display tab shows nothing because **the Timesketch server is not running**.

### Diagnostic Results

Running the diagnostic script (`scripts/test_timesketch.py`) shows:
- ✅ Timesketch is **configured** (config file exists at `~/.deeptempo/timesketch_config.json`)
- ✅ Server URL is set to: `http://localhost:5000`
- ✅ Authentication method: Username/Password
- ❌ **Server is NOT running** - Connection refused on localhost:5000

## Solution: Start Timesketch Server

Timesketch is an **external service** that must be running separately. The DeepTempo application only connects to it.

### Option 1: Docker (Recommended for Quick Testing)

```bash
# Run Timesketch in Docker
docker run -d -p 5000:5000 --name timesketch timesketch/timesketch

# Or use Docker Compose if you have a docker-compose.yml
docker-compose up -d
```

### Option 2: Local Installation

If you have Timesketch installed locally, start it with:
```bash
# Navigate to your Timesketch installation
cd /path/to/timesketch
# Start the server (method depends on your installation)
python3 timesketch.py runserver
```

### Option 3: Use Production Server

If you have a Timesketch server running elsewhere:
1. Open Settings → Timesketch Configuration
2. Update the Server URL to your production server
3. Update authentication credentials
4. Test connection

## Verify Server is Running

### Method 1: Use the Diagnostic Script

```bash
cd /Users/mando222/Github/deeptempo-ai-soc
./venv/bin/python3 scripts/test_timesketch.py
```

You should see:
- ✅ Server is reachable
- ✅ API endpoint is accessible
- ✅ Authentication successful

### Method 2: Check in Browser

Open `http://localhost:5000` in your browser. You should see the Timesketch login page.

### Method 3: Check in Application

1. Open the DeepTempo application
2. Go to the Timesketch tab (from menu: View → Timesketch Manager)
3. The connection status should now show "✅ Connected to Timesketch"

## Improvements Made

### 1. Enhanced Sketch Manager Widget

The `SketchManagerWidget` now includes:
- **Connection Status Display**: Shows current connection status at the top
- **Test Connection Button**: Allows you to test the connection without leaving the widget
- **Configure Button**: Quick access to Timesketch configuration
- **Empty State Message**: Shows a helpful message when no mappings exist
- **Better Error Messages**: More descriptive error messages for troubleshooting

### 2. Diagnostic Script

Created `scripts/test_timesketch.py` to:
- Check if Timesketch is configured
- Test server connectivity
- Test API endpoint accessibility
- Test authentication
- List available sketches

## Next Steps

1. **Start Timesketch Server** (see options above)
2. **Verify Connection** using the diagnostic script or the application
3. **Create Sketch Mappings** by syncing cases to Timesketch
4. **View Timeline** - Once mappings exist, you can view timelines

## Common Issues

### Connection Refused
- **Cause**: Timesketch server is not running
- **Solution**: Start the Timesketch server (see above)

### Authentication Failed
- **Cause**: Wrong credentials or user doesn't exist
- **Solution**: 
  - Verify username/password in Timesketch
  - Or generate a new API token in Timesketch web UI

### SSL Certificate Errors
- **Cause**: Self-signed certificate or certificate issues
- **Solution**: 
  - For local development: Disable SSL verification in settings
  - For production: Fix the SSL certificate

### No Sketches Showing
- **Cause**: No case-to-sketch mappings exist yet
- **Solution**: 
  - Sync a case to Timesketch using "Sync All Cases" or "Sync" button
  - This will create a sketch and mapping

## Testing the Fix

After starting Timesketch server:

1. Run diagnostic: `./venv/bin/python3 scripts/test_timesketch.py`
2. Open application and go to Timesketch tab
3. You should see:
   - Connection status: "✅ Connected to Timesketch"
   - Table with any existing mappings (or empty state message if none)
   - Buttons are functional

