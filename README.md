# Python Calculator Web App

A responsive calculator web application built with **Python, Flask, HTML, CSS, and JavaScript**. It supports basic arithmetic, percentage input, keyboard controls, and a recent-calculation history.

This project was also deployed on an **AWS EC2 Ubuntu instance** using **Gunicorn** and **Nginx**.

## Features

- Addition, subtraction, multiplication, and division
- Percentage button
- Clear and delete controls
- Keyboard input (numbers and operators, Enter to calculate, Backspace to delete, Escape to clear)
- Recent calculation history (latest 8 calculations, stored in the browser session)
- Responsive dark-themed interface
- Server-side expression validation using Python's `ast` module; does not use Python `eval()`

> Calculation history is held in browser memory and is cleared when the page is refreshed.

## Technology stack

| Technology | Purpose |
| --- | --- |
| Python | Backend language |
| Flask | Web framework and calculation API |
| HTML, CSS, JavaScript | Calculator interface and browser interactions |
| Gunicorn | Production WSGI application server |
| Nginx | Reverse proxy / public web server |
| AWS EC2 (Ubuntu) | Cloud hosting |
| Git and GitHub | Version control and source hosting |
| pytest | Automated backend tests |

## Project structure

```text
python-calculator-project/
├── app.py                 # Flask application and calculation API
├── requirements.txt       # Python dependencies
├── .gitignore             # Files excluded from Git
├── README.md              # Project overview and setup
├── docs/
│   └── deployment.md      # Step-by-step AWS EC2 deployment
├── .github/
│   └── workflows/
│       └── tests.yml      # Automated tests with GitHub Actions
├── templates/
│   └── index.html         # Calculator page and browser-side logic
├── static/
│   └── style.css          # Responsive calculator styling
└── tests/
    └── test_app.py        # Flask API tests
```

## Run locally

### 1. Requirements

- Python 3.10 or newer
- Git

### 2. Clone the repository

```bash
git clone https://github.com/sriramjetti47/python-calculator-project.git
cd python-calculator-project
```

To use the version developed in this project:

```bash
git checkout feature/calculator-v2
```

### 3. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

**Ubuntu / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Start the development server

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. Stop the local server with `Ctrl+C`.

## Run tests

With the virtual environment activated:

```bash
python -m pytest -q
```

## AWS EC2 deployment (Ubuntu)

For the complete step-by-step deployment procedure, see the [detailed AWS EC2 deployment guide](docs/deployment.md).

The application was deployed on an Ubuntu EC2 instance with this request flow:

```text
Browser
  |
  | HTTP :80
  v
Nginx (reverse proxy)
  |
  | http://127.0.0.1:8000
  v
Gunicorn (2 workers)
  |
  v
Flask application (app.py)
```

### 1. Create the EC2 instance

- Choose an Ubuntu Server image.
- Create or select an SSH key pair and keep the private key safe.
- In the instance security group, allow **SSH (TCP 22) from your own IP** and **HTTP (TCP 80) from the internet** if the site should be public.
- Do not open Gunicorn's port 8000 to the internet; it listens on localhost.

### 2. Connect and install packages

Connect using the instance's current public IP:

```bash
ssh -i "your-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

Then install the system packages:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx
```

### 3. Download and prepare the application

```bash
mkdir -p ~/calculator-project
cd ~/calculator-project
git clone --branch feature/calculator-v2 https://github.com/sriramjetti47/python-calculator-project.git
cd python-calculator-project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Create a Gunicorn systemd service

Create the service file:

```bash
sudo nano /etc/systemd/system/calculator.service
```

Use the following content. If you clone the project into a different directory, update both paths:

```ini
[Unit]
Description=Python Calculator Flask Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/calculator-project/python-calculator-project
ExecStart=/home/ubuntu/calculator-project/python-calculator-project/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now calculator
sudo systemctl status calculator --no-pager
```

### 5. Configure Nginx

Create the site configuration:

```bash
sudo nano /etc/nginx/sites-available/calculator
```

Add:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site and validate Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/calculator /etc/nginx/sites-enabled/calculator
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

Open `http://YOUR_EC2_PUBLIC_IP` in a browser. This setup uses HTTP; configure a domain and TLS certificate before using it for a production service.

### Useful service commands

```bash
sudo systemctl status calculator
sudo systemctl restart calculator
sudo journalctl -u calculator -n 50 --no-pager

sudo systemctl status nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Deploying a code update

After pushing tested changes to the same Git branch:

```bash
cd ~/calculator-project/python-calculator-project
git pull origin feature/calculator-v2
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart calculator
sudo systemctl status calculator --no-pager
```

### AWS cost reminder

Stopping an EC2 instance stops its compute usage, but attached EBS storage and some public IPv4 address resources may still incur charges. Terminating an instance is permanent; check the EBS volume's delete-on-termination setting and review any remaining snapshots or allocated IP addresses.

## API

### `POST /calculate`

Request JSON:

```json
{
  "expression": "12 * (3 + 2)"
}
```

Successful response:

```json
{
  "result": 60
}
```

Invalid expressions and division by zero return HTTP 400 with an error message.

## Security notes

- The backend parses expressions with Python's abstract syntax tree and permits only numeric constants, selected arithmetic operators, and unary plus/minus.
- Arbitrary Python expressions and function calls are not evaluated.
- The app limits expression length, exponent size, and result magnitude.
- For a public production service, add HTTPS, monitoring, rate limiting, and further operational hardening.

## Future improvements

- Persist calculation history in a database.
- Add automated CI tests on every push.
- Add HTTPS with a domain name.
- Add structured application logging and monitoring.

## Author

**Sriram Jetti** — [GitHub](https://github.com/sriramjetti47)
