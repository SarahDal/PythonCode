import requests
import csv
import time

# Enter your user details
username = "sarahdal"
instance = "https://crispsandwi.ch"

# Preparations
print("Getting account ID from the given username...")
lookup_url = f"{instance}/api/v1/accounts/lookup?acct={username}"
lookup_response = requests.get(lookup_url)
lookup_response.raise_for_status()

userid = lookup_response.json().get("id")
if not userid:
    raise ValueError("Failed to fetch user ID. Check your username and instance.")
print(f"Found account ID: {userid}")

# Initial URL for fetching followers
initial_url = f"{instance}/api/v1/accounts/{userid}/followers"

# Function to get the 'next' URL from headers
def get_next_link(headers):
    link_header = headers.get("Link")
    if link_header:
        for link in link_header.split(","):
            if 'rel="next"' in link:
                return link[link.find("<")+1:link.find(">")]
    return None

# Fetch followers
print(f"Fetching followers from {initial_url}...")
followers = []
next_url = initial_url

while next_url:
    response = requests.get(next_url)
    response.raise_for_status()
    
    # Add current page of followers
    followers.extend(response.json())
    
    # Get the next URL
    next_url = get_next_link(response.headers)
    print(f"Next URL: {next_url}" if next_url else "No more pages.")

# Fetch the last post's timestamp for each follower
def get_last_post_date(follower_id):
    url = f"{instance}/api/v1/accounts/{follower_id}/statuses?limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        statuses = response.json()
        if statuses:
            return statuses[0].get("created_at", "No date available")
    return "No posts found"

print("Fetching last post date for each follower...")
follower_data = []
for follower in followers:
    follower_id = follower["id"]
    acct = follower["acct"]
    last_post_date = get_last_post_date(follower_id)
    follower_data.append([acct, "true", "false", last_post_date])
    print(f"Processed: {acct} - Last post date: {last_post_date}")

    # Introduce a delay to prevent rate limiting
    time.sleep(1)  # Adjust delay as needed (e.g., 1 second between requests)

# Save output to CSV
timestamp = int(time.time())
output_filename = f"{username}_follower_accounts_{timestamp}.csv"
print(f"Writing to CSV file: {output_filename}...")

with open(output_filename, mode="w", newline="", encoding="utf-8") as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["Account address", "Show boosts", "Notify on new posts", "Last post date"])
    csvwriter.writerows(follower_data)

print("Done!")