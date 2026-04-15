import subprocess

print("Pushing to GitHub...")
subprocess.run(["git", "add", "Website.py", "deploy.py", "README.md"])
subprocess.run(["git", "commit", "-m", "auto deploy"])
subprocess.run(["git", "push"])

print("Done! Render will automatically deploy in ~1 minute.")
print("Your site: https://companytrace-uk.onrender.com")