# PhishOps

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Terraform](https://img.shields.io/badge/terraform-1.0%2B-purple)
![Platform](https://img.shields.io/badge/cloud-Tencent%20Cloud-blue)
![Status](https://img.shields.io/badge/status-production%20ready-success)

**Quick Deploy GophishModified Enhanced Edition to Cloud**

Based on [GophishModified](https://github.com/25smoking/GophisModified) Custom Edition

[中文](README.md) | [日本語](README_JP.md)

</div>

![Deployment Success](assets/deployment_success.png)

---

## 📖 About

**PhishOps** is a Gophish automation deployment tool that enables one-click CI/CD deployment of the enhanced GophishModified platform, solving tedious setup processes and maximizing cost efficiency.

> 💡 **About GophishModified**  
> This project deploys the [GophishModified](https://github.com/25smoking/GophisModified) custom edition, featuring:
> - QR code generation (inspired by EvilGophish)
> - More custom features...

### ✨ Key Features

- **🚀 One-Click Deployment** - Fully automated infrastructure provisioning in 3 minutes
- **☁️ Tencent Cloud Optimized** - Fully tested deployment for Tencent Cloud (Hong Kong, Guangzhou regions)
- **🔄 GitOps Workflow** - Continuous delivery from GitHub with branch switching support
- **🎨 Enhanced Features** - Custom modifications from GophishModified
- **🔒 Security-First** - Automatic firewall configuration, HTTPS support, password generation
- **💾 Smart Backup** - Automatic database backup before resource destruction
- **📊 Cost Transparency** - Real-time resource monitoring and cost estimation

### 🎯 Use Cases

- **Security Awareness Training** - Employee phishing email identification training
- **Red Team Operations** - Adversary simulation and incident response exercises
- **Penetration Testing** - Social engineering testing scenarios
- **Security Research** - Phishing technique research and defense mechanism validation

---

## 🛠️ Prerequisites

### 1. Tencent Cloud Account

Obtain Tencent Cloud API credentials:

- **Console**: [API Key Management](https://console.cloud.tencent.com/cam/capi)
- **Recommended Regions**:
  - `ap-hongkong` - Hong Kong (International)
  - `ap-guangzhou` - Guangzhou (Mainland China)
  - `ap-shanghai` - Shanghai (Mainland China)

> 💡 **Experimental Support**  
> This project has been **fully tested on Tencent Cloud**. ~~Configuration files for Alibaba Cloud and Huawei Cloud are prepared but not fully tested. Use at your own discretion.~~

### 2. Local Tools Installation

**One-Click Installation via Chocolatey (Recommended for Windows)**

1. Open PowerShell **as Administrator**
2. Install Chocolatey (if not already installed):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

3. Install all dependencies:
   ```powershell
   choco install python terraform git openssh -y
   ```

4. Verify installation:
   ```powershell
   python --version    # Should show Python 3.8+
   terraform -v        # Should show Terraform 1.0+
   git --version       # Should show Git version
   ssh -V             # Should show OpenSSH version
   ```

---

## 🚀 Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/25smoking/PhishOps.git
cd PhishOps
```

### Step 2: Configure Credentials

```powershell
# Copy configuration template
copy configs\.env.example configs\.env

# Edit configuration file
notepad configs\.env
```

**Configuration Example:**

```ini
# Tencent Cloud
TENCENT_CLOUD_SECRET_ID=your_secret_id
TENCENT_CLOUD_SECRET_KEY=your_secret_key

# Optional: Specify availability zone (if encountering resource shortages)
# TENCENT_CLOUD_AVAILABILITY_ZONE=ap-hongkong-3

# Optional: Custom SSH key path (defaults to ~/.ssh/id_rsa)
# SSH_KEY_PATH=$HOME/.ssh/id_rsa
```

> ⚠️ **Windows Users Note**  
> On Windows, `$HOME` in paths will automatically expand to your user directory (e.g., `C:\Users\YourName`)

### Step 3: Deploy to Cloud

**Deploy to Tencent Cloud (Hong Kong)**
```powershell
python scripts/deploy.py -p tencent -r ap-hongkong
```

**Deploy to Tencent Cloud (Guangzhou)**
```powershell
python scripts/deploy.py -p tencent -r ap-guangzhou
```

**Deploy Specific GitHub Branch**
```powershell
python scripts/deploy.py -p tencent -r ap-hongkong -b master
```

### Step 4: Wait for Deployment

The script automatically completes (approximately 3-5 minutes):

1. ✅ Create cloud infrastructure (VPC, security group, server instance)
2. ✅ Wait for SSH service to be ready
3. ✅ Install Docker and Go environment
4. ✅ Pull source code from GitHub and compile
5. ✅ Configure external access (listen on 0.0.0.0)
6. ✅ Start Gophish service

**Deployment Success Output:**

```text
========================================================
🎉 Gophish Deployment Successful!
========================================================

📍 Access Information:
   Admin Panel: https://1.2.3.4:3333
   Phishing Site: http://1.2.3.4

🔑 Admin Login:
   Username: admin
   Password: a1b2c3d4e5f6

🖥️  SSH Access:
   Command: ssh -i ~/.ssh/id_rsa root@1.2.3.4

💰 Estimated Cost: $0.02/hour (approx. $15/month)
========================================================
```

---

## 💻 Management & Maintenance

### Check Resource Status

```powershell
python scripts/check-resources.py
```

### SSH Remote Access

```bash
# Login with auto-generated key
ssh -i ~/.ssh/id_rsa root@<server_ip>

# View Gophish logs
journalctl -u gophish -f
```

### Restart Gophish Service

```bash
systemctl restart gophish
```

---

## 🗑️ Destroy Resources

### Standard Destruction (with Backup)

```powershell
python scripts/destroy.py -p tencent
```

**Execution Flow:**
1. Prompt for destruction confirmation
2. Automatically backup database to `backups/` directory
3. Destroy all cloud resources (server, VPC, security group)
4. Clean up local Terraform state files

### Force Destruction (Skip Confirmation)

```powershell
python scripts/destroy.py -p tencent --force
```

### ⚠️ Important Notice

> **Solution for Terraform Destroy Hang**  
> If the `terraform destroy` command becomes unresponsive or hangs:
> 
> 1. **Press `Ctrl+C` to interrupt the script**
> 2. **Manually delete resources in cloud console**:
>    - Tencent Cloud: [CVM Console](https://console.cloud.tencent.com/cvm/instance)
>    - Deletion order: Instance → Security Group → VPC
> 3. **Clean up local state**:
>    ```powershell
>    cd terraform/tencent
>    rm -rf .terraform terraform.tfstate*
>    ```

⚠️ **Warning:** Destruction is irreversible. Ensure important data is backed up!

---

## 💰 Cost Estimation

### Hourly Billing (Actual Usage Time)

| Platform | Instance Type | Hourly Cost | Monthly Cost (720hrs) |
|----------|---------------|-------------|----------------------|
| Tencent Cloud | SA2.MEDIUM4 (2C4G) | $0.021/hr | $15/month |

> 💡 **Money-Saving Tip:** Destroy resources immediately after exercises - pay only for actual usage (e.g., 2 hours = $0.042)

---

## 📚 Project Structure

```
phishops/
├── configs/              # Configuration files
│   ├── .env.example     # Configuration template
│   └── .env             # Actual config (not committed)
├── scripts/              # Automation scripts
│   ├── deploy.py        # Deployment script
│   ├── destroy.py       # Destruction script
│   └── check-resources.py # Resource check script
├── terraform/            # Terraform configurations
│   ├── alibaba/         # Alibaba Cloud config
│   ├── tencent/         # Tencent Cloud config
│   └── huawei/          # Huawei Cloud config
├── backups/              # Database backup directory
├── README.md             # Chinese Documentation (Main)
├── README_EN.md          # English Documentation
└── README_JP.md          # Japanese Documentation
```

---

This tool is intended for **authorized security testing and educational purposes only**. Users must:

- ✅ Obtain explicit written authorization from target system owners
- ✅ Comply with all applicable laws and regulations in their jurisdiction
- ✅ Not use for any illegal or malicious activities
- ✅ Take full responsibility for their actions and consequences

**Unauthorized phishing attacks are illegal. The author assumes no liability for misuse.**

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit Issues and Pull Requests.

1. Star this project
2. Fork the project
3. Create your feature branch (`git checkout -b feature/AmazingFeature`)
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

---

## 📞 Contact

- **Project Home**: [https://github.com/25smoking/PhishOps](https://github.com/25smoking/PhishOps)
- **Issue Tracker**: [GitHub Issues](https://github.com/25smoking/PhishOps/issues)

---

<div align="center">

**If you find this project helpful, please give it a ⭐ Star!**

Made with ❤️ by Security Researchers

</div>
