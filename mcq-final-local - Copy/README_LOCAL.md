# Run the NSCT examination on a local network

The computer running the exam is the host. Student devices must be connected
to the same trusted Wi-Fi or wired LAN; the host must remain on and connected
with Docker, FastAPI, and Vite running for the full exam.

## Start the host

From PowerShell in the project folder, run:

```powershell
.\START_EXAM_LOCAL.ps1
```

The script starts PostgreSQL, applies migrations, imports
`NSCT_Prep_All_Subjects_MCQs.xlsx`, ensures the administrator account exists,
and starts the API and student website. It prints local network URLs in this
format:

```text
http://<host-LAN-IP>:5173/
```

On first launch, the script prompts for a new administrator password
(minimum 12 characters). Later launches preserve the existing administrator
credentials. Students must use accounts imported by an administrator; public
self-registration is disabled.

During an exam, each selected answer is saved to the host as it is chosen.
Answers saved before the server-side deadline are used if the browser submits
late or loses connection at timeout. Tab changes do not cause score deductions,
because the server cannot independently verify browser focus.

Give students the URL using the host's LAN IP, not `localhost` or `127.0.0.1`.
The frontend listens on all network interfaces and proxies API requests back
to the host's FastAPI service.

## Allow network connections

On the host computer, allow inbound TCP port **5173** through Windows
Defender Firewall for the **Private** network profile. Do not expose ports
8000 (API) or 5433 (database) to student devices; they only need the Vite
website on port 5173.

If the host is connected to a public/untrusted Wi-Fi network, do not share the
exam there. Avoid port forwarding on the router; this setup is intended only
for devices on the same trusted LAN.

## Check before sharing

- Open `http://localhost:5173/` on the host and confirm the student sign-in appears.
- Open `http://localhost:8000/health` on the host and confirm it reports `healthy`.
- From one student device, open the printed LAN URL and sign in.
- Keep the host's IP stable during the exam; a DHCP address change will break
  the link.

To stop the local services, use `STOP_EXAM_LOCAL.ps1`.
