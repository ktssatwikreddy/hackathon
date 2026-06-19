# Start the frontend on the network so phones on the same Wi-Fi can reach it
# (needed for QR check-in). App will be at http://10.0.7.160:5173
Set-Location "$PSScriptRoot\frontend"
npm run dev -- --host 0.0.0.0
