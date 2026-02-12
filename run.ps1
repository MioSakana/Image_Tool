# PowerShell script to activate conda env and run the app (run from project root)
Write-Host "Activating conda environment 'py311'..."
conda activate py311
Write-Host "Running main.py..."
python main.py
Read-Host -Prompt "Program exited. Press Enter to close"
