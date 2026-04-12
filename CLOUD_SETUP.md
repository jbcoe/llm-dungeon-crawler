# Hosting Ollama on Google Cloud

This guide explains how to set up a hosted Ollama instance on Google Cloud Compute Engine so that players can connect to it over the internet, without needing to run a local LLM.

> **Cost note:** A single `n1-standard-4` VM with an NVIDIA T4 GPU runs roughly **$0.40–$0.60 per hour** when active. If you stop the VM when nobody is playing you can keep costs low. Expect a few dollars per month for light personal use.

---

## Prerequisites

- A [Google Cloud](https://cloud.google.com/) account with billing enabled
- The [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and authenticated on your local machine
- A GCP project to deploy into (replace `MY_PROJECT` throughout with your project ID)

---

## 1 — Choose a region and enable required APIs

```bash
gcloud config set project MY_PROJECT

gcloud services enable compute.googleapis.com
```

Pick a region close to your players. GPU availability varies — `us-central1` and `us-east1` are reliable choices.

---

## 2 — Request GPU quota (if needed)

By default, new GCP projects have zero GPU quota. Request it at:

**IAM & Admin → Quotas & System Limits → filter by "NVIDIA T4 GPUs"** for your chosen region, then click **Edit Quotas** and request at least **1**.

Approval is usually automatic and near-instant for T4s.

---

## 3 — Create the VM

```bash
gcloud compute instances create ollama-server \
  --project=MY_PROJECT \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --maintenance-policy=TERMINATE \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-balanced \
  --scopes=cloud-platform \
  --tags=ollama-server
```

Key flags explained:
- `--machine-type=n1-standard-4` — 4 vCPUs / 15 GB RAM, enough for Gemma 4 inference
- `--accelerator=type=nvidia-tesla-t4,count=1` — GPU acceleration for fast inference
- `--maintenance-policy=TERMINATE` — required when using GPUs
- `--boot-disk-size=50GB` — leaves room for model weights (~10–20 GB for `gemma4:e4b`)

---

## 4 — Open the Ollama port in the firewall

```bash
gcloud compute firewall-rules create allow-ollama \
  --project=MY_PROJECT \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:11434 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=ollama-server
```

> **Security tip:** Replace `0.0.0.0/0` with your own IP address (e.g., `203.0.113.42/32`) so the port is not open to the entire internet.

---

## 5 — Install NVIDIA drivers and Ollama

SSH into the VM:

```bash
gcloud compute ssh ollama-server --zone=us-central1-a
```

Inside the VM, run the following:

```bash
# Install NVIDIA drivers
sudo apt-get update
sudo apt-get install -y linux-headers-$(uname -r)
curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output install_gpu_driver.py
sudo python3 install_gpu_driver.py

# Reboot to activate the driver
sudo reboot
```

After the reboot, SSH back in and install Ollama:

```bash
gcloud compute ssh ollama-server --zone=us-central1-a
```

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure Ollama to listen on all interfaces (so external clients can reach it)
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
EOF

sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull the default model (takes a few minutes)
ollama pull gemma4:e4b
```

Verify Ollama is running and the model is loaded:

```bash
curl http://localhost:11434/api/tags
```

---

## 6 — Get the VM's external IP address

```bash
gcloud compute instances describe ollama-server \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Note the IP — for example `34.1.2.3`. You'll use it to connect from your local machine.

> **Tip:** Assign a [static IP](https://cloud.google.com/compute/docs/ip-addresses/reserve-static-external-ip-address) to avoid the address changing every time you stop/start the VM.

---

## 7 — Connect the game to your hosted Ollama instance

On your local machine, use the `--ollama-url` flag to point the dungeon crawler at your hosted server:

```bash
uv run dungeon-crawler --ollama-url http://34.1.2.3:11434
```

You can also set the `OLLAMA_HOST` environment variable instead, which is useful for CI or shell profiles:

```bash
export OLLAMA_HOST=http://34.1.2.3:11434
uv run dungeon-crawler
```

The game will skip starting a local Ollama server and connect directly to the cloud instance.

---

## 8 — Using a different model

If you want to use a model other than the default `gemma4:e4b`, pull it on the VM first:

```bash
# On the cloud VM
ollama pull llama3
```

Then pass the model name when starting the game:

```bash
# On your local machine
uv run dungeon-crawler --ollama-url http://34.1.2.3:11434 --model llama3
```

---

## 9 — Stop the VM when not in use

You are billed for the VM while it is running. Stop it to pause charges:

```bash
gcloud compute instances stop ollama-server --zone=us-central1-a
```

Start it again when you want to play:

```bash
gcloud compute instances start ollama-server --zone=us-central1-a
```

---

## 10 — Delete the VM when done

To avoid any ongoing charges, delete the VM and firewall rule when you no longer need them:

```bash
gcloud compute instances delete ollama-server --zone=us-central1-a
gcloud compute firewall-rules delete allow-ollama
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Connection refused` or timeout | Firewall not open / Ollama not listening on `0.0.0.0` | Check step 4 and the `override.conf` in step 5 |
| `Model not found` error on startup | Model not yet pulled on the VM | Run `ollama pull gemma4:e4b` on the VM |
| Slow inference | GPU driver not loaded | Run `nvidia-smi` on the VM; if it fails, re-run the driver install from step 5 |
| VM won't start | GPU quota not granted | Check IAM & Admin → Quotas for the T4 quota in your region |
