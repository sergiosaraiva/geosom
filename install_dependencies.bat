@echo off

REM Update pip
echo Updating pip...
python -m pip install --upgrade pip

REM List of dependencies to install or update
echo Installing/updating required Python packages...
pip install --upgrade geopandas
pip install --upgrade numpy
pip install --upgrade rasterio
pip install --upgrade scipy
pip install --upgrade minisom
pip install --upgrade scikit-learn
pip install --upgrade matplotlib

echo All dependencies are installed/updated successfully.
pause
