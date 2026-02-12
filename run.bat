@echo off
REM Activate conda environment and run the app (run from project root)
echo Activating conda environment 'py311'...
call conda activate py311
echo Running main.py...
python main.py
echo Program exited. Press any key to close.
pause >nul
