# Echo Local Start

## Start Echo

From the project root, run:

```powershell
.\start_echo.ps1
```

This opens two separate PowerShell windows:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

The launcher opens the frontend in your browser and prints `Echo ready`.

## Stop Echo

From the project root, run:

```powershell
.\stop_echo.ps1
```

This stops processes listening on ports `8000` and `5173` and prints what was stopped.

## Troubleshooting

If a port is already in use, run:

```powershell
.\stop_echo.ps1
```

Then start Echo again:

```powershell
.\start_echo.ps1
```

If PowerShell blocks the scripts, run this once from the project root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

The launcher uses `.env` for the backend, but it does not print `.env` contents or API keys.
