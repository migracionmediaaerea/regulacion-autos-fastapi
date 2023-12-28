# This works with python 3.10

# Make a virtual enviroment
py | python | python3 -m venv venv

# Activate virtual enviroment
.\venv\Scripts\activate

# Install requirements
py -m pip install -r .\requirements.txt

# To run the app
uvicorn main:app 1 --reload 


# Actualizar requirements después de agregar librerías:
.\venv\Scripts\activate
pip freeze > requirements.txt

# To run this, wkhtmltopdf must be installed
Docs:"https://wkhtmltopdf.org/downloads.html


### Deployment:
# Instalar python 3.10
https://computingforgeeks.com/how-to-install-python-on-ubuntu-linux-system/
sudo apt-get install python3.10-dev

# Instalar pip
sudo apt install python3-pip
sudo apt install python3.10-distutils
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
python3.10 -m pip --version

# Instalar venv
sudo apt-get install python3.10-venv
python3.10 -m pip install virtualenv
python3.10 -m venv venv

# Instalar mysql
sudo apt install mysql-server
sudo apt-get install libmysqlclient-dev

# Correr venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Abrir puerto 3000 (Oracle Cloud)
sudo firewall-cmd --permanent --zone=public --add-port=3000/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
https://docs.oracle.com/en-us/iaas/developer-tutorials/tutorials/apache-on-ubuntu/01oci-ubuntu-apache-summary.htm

# Correrlo tras todo el setup
source venv/bin/activate
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 3000