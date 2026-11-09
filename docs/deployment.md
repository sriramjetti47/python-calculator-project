# AWS EC2 Deployment Guide

This guide explains how to deploy the Python Calculator Flask application on an Ubuntu EC2 instance using Gunicorn and Nginx.

> This project was previously deployed using Ubuntu, Gunicorn, Nginx, and a systemd service. Commands below use the directory layout from that deployment. Replace the public IP and SSH key filename with your own values.

## 1. Architecture

Requests follow this path:

```text
Browser
  |
  | HTTP - port 80
  v
Nginx
  |
  | proxy to 127.0.0.1:8000
  v
Gunicorn (2 workers)
  |
  v
Flask application (app.py)
```

Nginx accepts public HTTP requests and forwards them to Gunicorn. Gunicorn runs the Flask application. Gunicorn is bound to localhost, so port 8000 does not need to be publicly accessible.

## 2. Create and configure the EC2 instance

1. Launch an Ubuntu Server EC2 instance.
2. Create or select an SSH key pair. Keep the private `.pem` file secure; never upload it to GitHub.
3. Configure the instance security group:
   - **SSH (TCP 22):** allow access from your own IP address.
   - **HTTP (TCP 80):** allow access from anywhere only if you want the website to be publicly reachable.
   - Do **not** add a public inbound rule for port 8000.
4. Note the instance's current public IPv4 address.

## 3. Connect to Ubuntu

From a terminal on your computer, connect using your key:

```bash
ssh -i "YOUR_KEY_FILE.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

Use the correct path to your key file. Do not share the private key.

## 4. Install system packages

On the EC2 terminal:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv nginx
```

## 5. Clone the application and install Python dependencies

The directory below matches the layout used in the original deployment:

```bash
mkdir -p ~/calculator-project
cd ~/calculator-project
git clone --branch feature/calculator-v2 https://github.com/sriramjetti47/python-calculator-project.git
cd python-calculator-project

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The virtual environment keeps this application's Python packages separate from system Python packages.

## 6. Test Gunicorn locally on the instance

While the virtual environment is active, run:

```bash
gunicorn --bind 127.0.0.1:8000 app:app
```

Open a second SSH terminal and test the local endpoint:

```bash
curl http://127.0.0.1:8000
```

If HTML is returned, stop the foreground Gunicorn process with `Ctrl+C` in the first terminal before creating the systemd service.

## 7. Configure Gunicorn as a systemd service

Create the service file:

```bash
sudo nano /etc/systemd/system/calculator.service
```

Add:

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

Save the file, then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable calculator
sudo systemctl start calculator
sudo systemctl status calculator --no-pager
```

The `enable` command configures the service to start automatically when the instance boots.

If you clone the project into a different directory, update both `WorkingDirectory` and `ExecStart` to the matching absolute paths.

## 8. Configure Nginx as a reverse proxy

Create the Nginx site file:

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

Enable the site and validate the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/calculator /etc/nginx/sites-enabled/calculator
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

If the symbolic link already exists, do not create it again; continue with the Nginx test.

## 9. Open the website

In your browser, visit:

```text
http://YOUR_EC2_PUBLIC_IP
```

Use the current public IP shown in the EC2 console. A stopped and restarted instance may receive a different public IP unless an Elastic IP is configured.

This setup uses HTTP, not HTTPS. For a real production service, configure a domain name and TLS certificate before handling sensitive information.

## 10. Deploy later code updates

After pushing your tested changes to the GitHub branch, connect to the instance and run:

```bash
cd ~/calculator-project/python-calculator-project
git pull origin feature/calculator-v2
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart calculator
sudo systemctl status calculator --no-pager
```

## 11. Useful troubleshooting commands

Check the Flask/Gunicorn service:

```bash
sudo systemctl status calculator --no-pager
sudo journalctl -u calculator -n 50 --no-pager
sudo systemctl restart calculator
```

Check Nginx:

```bash
sudo nginx -t
sudo systemctl status nginx --no-pager
sudo journalctl -u nginx -n 50 --no-pager
sudo systemctl restart nginx
```

Test each layer from inside the EC2 instance:

```bash
curl http://127.0.0.1:8000
curl http://127.0.0.1
```

- If port 8000 does not respond, check the Gunicorn service and its paths.
- If port 8000 responds but port 80 does not, check Nginx configuration and service status.
- If both local tests work but the public website does not, check the EC2 security group's inbound HTTP rule and the instance's public IP.

## 12. Avoid unexpected AWS charges

Stopping an instance stops its compute usage, but attached EBS storage and certain public IPv4 resources may still incur charges. Terminating an instance is permanent. Before terminating, check the EBS volume's delete-on-termination setting and review any retained volumes, snapshots, and allocated Elastic IPs.

The source code remains available in GitHub. To host it again, launch a new instance and repeat this guide.
