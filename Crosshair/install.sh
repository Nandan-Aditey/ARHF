# Set the location where you want Crosshair to be installed

location="$HOME/Downloads/UI-For-AI/Crosshair"

# Install the python venv package for python 3.10 (you can probably change it to your version, I haven't tried)
sudo apt install python3.10-venv

# Create the virtual environment for Crosshair
python3 -m venv $location

# Switch to that directory and activate the virtual environment
cd $location
source ./bin/activate

# Install crosshair fr
pip install crosshair-tool
