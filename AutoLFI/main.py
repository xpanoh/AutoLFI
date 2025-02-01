import requests
import threading
import queue
import argparse

# Queue for managing words
q = queue.Queue()
lock = threading.Lock()
found_results = []  # Store found directories/files


# Function to check directories/files
def check_url(target_url, extensions, proxies, user_agent, status_codes):
    headers = {"User-Agent": user_agent} if user_agent else {}

    while not q.empty():
        word = q.get()
        urls = [f"{target_url.rstrip('/')}/{word}"]

        # Append extensions if provided
        if extensions:
            urls.extend([f"{target_url.rstrip('/')}/{word}{ext}" for ext in extensions])

        for url in urls:
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=5)

                if response.status_code in status_codes:
                    result = f"[+] Found: {url} ({response.status_code})"

                    # Print result thread-safe
                    with lock:
                        print(result)
                        found_results.append(result)  # Store result for final output
            except requests.exceptions.RequestException:
                pass  # Ignore errors

        q.task_done()


# Load wordlist into queue
def load_wordlist(wordlist_file):
    with open(wordlist_file, "r") as file:
        for line in file:
            q.put(line.strip())


# Main function
def main():
    parser = argparse.ArgumentParser(description="Python GoBuster Clone")
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g., http://example.com)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to wordlist file")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads (default: 10)")
    parser.add_argument("-x", "--extensions", help="File extensions to check (comma-separated, e.g., .php,.html,.txt)")
    parser.add_argument("--proxy", help="Proxy (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--user-agent", help="Custom User-Agent string")
    parser.add_argument("--status-codes",
                        help="Filter results by status codes (comma-separated, default: 200,301,302,403)")
    parser.add_argument("-o", "--output", help="Save results to an output file")

    args = parser.parse_args()

    # Convert extensions to list
    extensions = args.extensions.split(",") if args.extensions else []

    # Convert status codes to list
    status_codes = list(map(int, args.status_codes.split(","))) if args.status_codes else [200, 301, 302, 403]

    # Set up proxies
    proxies = {"http": args.proxy, "https": args.proxy} if args.proxy else {}

    # Load wordlist
    load_wordlist(args.wordlist)

    # Start threads
    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=check_url, args=(args.url, extensions, proxies, args.user_agent, status_codes))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Write all results to the output file at the end
    if args.output and found_results:
        with open(args.output, "w") as f:
            f.write("\n".join(found_results))
        print(f"\n[+] Results saved to: {args.output}")


if __name__ == "__main__":
    main()
