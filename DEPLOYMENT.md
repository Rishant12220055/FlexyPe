# Deployment Guide for Smart Inventory System

The application is fully containerized using Docker, making deployment straightforward on any Virtual Private Server (VPS).

## Recommended Hosting Providers
- **DigitalOcean** (Basic Droplet) - Easiest for beginners.
- **AWS** (EC2 t2.micro or t3.micro) - Good for free tier usage.
- **Hetzner / Linode** - Cost-effective alternatives.

## Prerequisites
Your server must have:
1. **Docker** and **Docker Compose** installed.
2. **Git** installed.

---

## Quick Deployment Steps (Linux/Ubuntu)

### 1. Provision the Server
Launch an Ubuntu 22.04 LTS instance. SSH into your server:
```bash
ssh root@your-server-ip
```

### 2. Install Docker
Run the following commands to install Docker and Docker Compose:
```bash
# Update packages
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify installation
docker --version
docker compose version
```

### 3. Clone the Repository
Clone your code from GitHub:
```bash
git clone https://github.com/YOUR_USERNAME/flexype-hackathon.git
cd flexype-hackathon
```

### 4. Configure Environment Variables
Create the production environment file in the `backend` directory:
```bash
cd backend
cp .env.example .env
nano .env
```
**Important:**
- Change `DATABASE_URL` if you use a managed DB (or leave it to use the containerized Postgres).
- Change `JWT_SECRET` to a strong random string.
- Set `NODE_ENV=production` inside your frontend configuration if applicable.

### 5. Start the Application
Return to the root directory and launch the containers in detached mode:
```bash
cd ..
docker compose up -d --build
```

### 6. Verify Deployment
- **Frontend:** Visit `http://your-server-ip:3000`
- **Backend API:** Visit `http://your-server-ip:8000/docs`

---

## Advanced: Production Domain Setup (Optional)
To use a real domain (e.g., `flashsale.com`) with HTTPS:

1. **Point Domain DNS:** Add an `A Record` pointing to your Server IP.
2. **Setup Nginx Proxy** (Recommended):
   Run an Nginx container or install Nginx on the host to forward traffic:
   - Port 80/443 -> Port 3000 (Frontend)
   - `/api` path -> Port 8000 (Backend)

For a quick hackathon demo, accessing via `http://IP:3000` is usually sufficient.
