import requests 
from bs4 import BeautifulSoup
import json 
from dotenv import load_dotenv
from project.db import get_mongo_client

load_dotenv()
def transform_and_load_statistics(client, stats_data):
    """
    Transforms and loads statistics into the 'statistics' collection,
    with one document per year.
    """
    if not client or not stats_data:
        print("No client or statistics data provided.")
        return
        
    db = client.get_database("event_calendar") 
    statistics_collection = db.statistics

    stats_by_year = {}
    
    for item in stats_data.get("government_contribution", []):
        year = int(item.get("year"))
        if year not in stats_by_year:
            stats_by_year[year] = {"gov_contributions": [], "employment_items": [], "activities": []}
        stats_by_year[year]["gov_contributions"].append({
            "type": item.get("contributiontype"),
            "amount_mil": float(item.get("amount"))
        })

    for item in stats_data.get("employment_item", []):
        year = int(item.get("year"))
        if year not in stats_by_year:
            stats_by_year[year] = {"gov_contributions": [], "employment_items": [], "activities": []}
        stats_by_year[year]["employment_items"].append({
            "artform": item.get("artform"),
            "employment": int(item.get("employment"))
        })

    for item in stats_data.get("activities", []):
        year = int(item.get("year"))
        if year not in stats_by_year:
            stats_by_year[year] = {"gov_contributions": [], "employment_items": [], "activities": []}
        stats_by_year[year]["activities"].append({
            "type": item.get("type"),
            "number": int(item.get("number"))
        })

    if not stats_by_year:
        print("No statistics data found to load.")
        return

    for year, data in stats_by_year.items():
        statistics_document = {
            "year": year,
            "gov_contributions": data["gov_contributions"],
            "employment_items": data["employment_items"],
            "activities": data["activities"]
        }
        
        statistics_collection.update_one(
            {'year': year},
            {'$set': statistics_document},
            upsert=True
        )

    print(f"Successfully loaded or updated statistics for {len(stats_by_year)} years.")


def transform_and_load_statistics(client, stats_data):
    """
    Transforms and loads statistics into the 'statistics' collection,
    with one document per year.
    """
    if not client or not stats_data:
        return
        
    db = client.get_database("event_calendar") # Using the correct DB name
    statistics_collection = db.statistics

    # 1. Group all raw statistics by year
    stats_by_year = {}
    
    for item in stats_data.get("government_contribution", []):
        year = int(item.get("year"))
        if year not in stats_by_year:
            stats_by_year[year] = {"gov_contributions": [], "employment_items": [], "activities": []}
        stats_by_year[year]["gov_contributions"].append({
            "type": item.get("contributiontype"),
            "amount_mil": float(item.get("amount"))
        })

    for item in stats_data.get("employment_item", []):
        year = int(item.get("year"))
        if year not in stats_by_year:
            stats_by_year[year] = {"gov_contributions": [], "employment_items": [], "activities": []}
        stats_by_year[year]["employment_items"].append({
            "artform": item.get("artform"),
            "employment": int(item.get("employment"))
        })

    for item in stats_data.get("activities", []):
        year = int(item.get("year"))
        if year not in stats_by_year:
            stats_by_year[year] = {"gov_contributions": [], "employment_items": [], "activities": []}
        stats_by_year[year]["activities"].append({
            "type": item.get("type"),
            "number": int(item.get("number"))
        })

    # 2. Iterate through each year and upsert a document
    if not stats_by_year:
        print("No statistics data found to load.")
        return

    for year, data in stats_by_year.items():
        # Create the document for the current year
        statistics_document = {
            "year": year,
            "gov_contributions": data["gov_contributions"],
            "employment_items": data["employment_items"],
            "activities": data["activities"]
        }
        
        # Use year as the unique key to update or insert
        statistics_collection.update_one(
            {'year': year},
            {'$set': statistics_document},
            upsert=True
        )

    print(f"Successfully loaded/updated statistics for {len(stats_by_year)} years.")


def transform_and_load_events(client, events_data):
    """Transforms scraped event data and upserts it into the 'events' collection."""
    if not client or not events_data:
        return
    
    db = client.get_database("event_calendar") 
    events_collection = db.events

    for event in events_data:
        if not event.get("title") or "not found" in event.get("title").lower() or not event.get("source"):
            print(f"Skipping invalid event data: {event.get('title')}")
            continue

        mongo_event = {
            "title": event.get("title"),
            "description": event.get("description", ""),
            "start_date": event.get("start_date"),
            "end_date": event.get("end_date"),
            "venue_name": event.get("venue_name"),
            "address": event.get("address", ""),
            "image_url": event.get("image_url"),
            "registration_link": event.get("registration_link"),
            "source": event.get("source") 
        }

        events_collection.update_one(
            {'source': mongo_event['source']},
            {'$set': mongo_event},
            upsert=True
        )
    
    site = "N/A"
    if events_data:
        if "artsrepublic" in events_data[0].get("source", ""):
            site = "artsrepublic.sg"
        elif "eventfinda" in events_data[0].get("source", ""):
            site = "eventfinda.sg"

    print(f"Successfully loaded/updated {len(events_data)} events for site: {site}.")


def fetch_gov_statistics():

    urls = {
        "government_contribution": "https://data.gov.sg/api/action/datastore_search?resource_id=d_50c329c8a3d698b1b5607896163fa38f",
        "employment_item": "https://data.gov.sg/api/action/datastore_search?resource_id=d_1b3bb94dab437ad56d0a6cc26282a289",
        "activities": "https://data.gov.sg/api/action/datastore_search?resource_id=d_fe963befd0a503e6de3883d50e3f4597"
    }

    all_stats = {}

    for name, url in urls.items():
        try:
            print(f"Fetching {name} data from data.gov.sg...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()  
            all_stats[name] = response.json()["result"]["records"]
            print(f"Successfully fetched {len(all_stats[name])} records for {name}.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {name} data: {e}")
            all_stats[name] = []
            
    return all_stats


def scrape_artsrepublic_sg():
    """Scrapes event data from ArtsRepublic.sg."""
    list_page_url = "https://artsrepublic.sg/events"
    scraped_events = []

    print("Scraping artsrepublic.sg event list page...")
    try:
        response = requests.get(list_page_url, timeout=10)
        response.raise_for_status() # Will raise an error for bad status codes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all event links based on the CSS Selector from your plan
        event_links = soup.select('li a.event_thumbnail')
        
        if not event_links:
            print("No event links found on artsrepublic.sg. The page structure might have changed.")
            return []
            
        print(f"Found {len(event_links)} event links. Now scraping detail pages...")

        # Loop through each link found on the list page
        for link_tag in event_links:
            detail_url = link_tag.get('href')
            if detail_url:
                print(detail_url)
                # Scrape the detail page for each event
                event_data = scrape_artsrepublic_detail_page(detail_url)
                if event_data: # Only append if data was successfully scraped
                    scraped_events.append(event_data)

    except requests.exceptions.RequestException as e:
        print(f"Error scraping artsrepublic.sg list page: {e}")

    return scraped_events

def scrape_artsrepublic_detail_page(url):
    """Scrapes the details from a single event page on ArtsRepublic.sg."""
    try:
        fullUrl = "https://artsrepublic.sg/" + url
        response = requests.get(fullUrl, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.select_one('h1[itemprop="name"]').text.strip() if soup.select_one('h1[itemprop="name"]') else "Title not found"

        start_date = soup.select_one('meta[itemprop="startDate"]')['content'] if soup.select_one('meta[itemprop="startDate"]') else "Start date not found"
        end_date = soup.select_one('meta[itemprop="endDate"]')['content'] if soup.select_one('meta[itemprop="endDate"]') else "End date not found"
        image_url = soup.select_one('meta[itemprop="image"]')['content'] if soup.select_one('meta[itemprop="image"]') else "Image URL not found"
        
        location_div = soup.select_one('div[itemprop="location"]')
        full_location_string = ""
        if location_div and location_div.select_one('span[itemprop="name"]'):
            full_location_string = location_div.select_one('span[itemprop="name"]').text.strip()

        if ',' in full_location_string:
            parts = full_location_string.split(',', 1)
            venue = parts[0].strip()
            address = parts[1].strip()
        elif full_location_string:
            venue = full_location_string
            address = full_location_string
        else: 
            venue = "Venue not found"
            address = ""

        synopsis_div = soup.select_one('div.synopsis')
        short_description = ""
        if synopsis_div:
            # Get all paragraphs within the synopsis div and join their text
            full_synopsis = ' '.join(p.text for p in synopsis_div.find_all('p'))
            # Clean up the "Synopsis:" label and excessive whitespace
            clean_synopsis = full_synopsis.replace("Synopsis:", "").strip()
            # Split into words, take the first 50, and join back
            words = clean_synopsis.split()
            if len(words) > 50:
                short_description = ' '.join(words[:50]) + '...'
            else:
                short_description = ' '.join(words)
        
        # Find the registration link in the website data field
        website_link_tag = soup.select_one('div.data a[target="_blank"]')
        registration_link = website_link_tag['href'] if website_link_tag else "Registration link not found"
        
        return {
            "title": title,
            "description" : short_description,
            "start_date": start_date,
            "end_date": end_date,
            "venue_name": venue,
            "address": address,
            "image_url": image_url,
            "registration_link": registration_link,
            "source" : fullUrl
        }

    except requests.exceptions.RequestException as e:
        print(f"Error scraping detail page {url}: {e}")
        return None # Return None if a single page fails
    



def scrape_eventfinda_sg():
    """Scrapes event data from Eventfinda.sg."""
    list_page_url = "https://www.eventfinda.sg/whatson/events/singapore"
    scraped_events = []

    print("Scraping eventfinda.sg event list page...")
    try:
        
        response = requests.get(list_page_url, timeout=15)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all event cards, which are divs with class 'card'
        event_cards = soup.select('div.card.h-event')
        
        if not event_cards:
            print("No event links found on eventfinda.sg. The page structure might have changed.")
            return []
            
        print(f"Found {len(event_cards)} event links. Now scraping detail pages...")

        for card in event_cards:
            # The link to the detail page is on the title
            link_tag = card.select_one('h2.card-title a')
            if link_tag and link_tag.has_attr('href'):
                detail_url = link_tag['href']
                event_data = scrape_eventfinda_detail_page(detail_url)
                if event_data:
                    scraped_events.append(event_data)

    except requests.exceptions.RequestException as e:
        print(f"Error scraping eventfinda.sg list page: {e}")

    return scraped_events

def scrape_eventfinda_detail_page(url):
    """Scrapes the details from a single event page on Eventfinda."""
    print(f"Scraping detail page: {url}")
    try:
        full_url = "https://www.eventfinda.sg" + url
        response = requests.get(full_url, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.select_one("h1.p-name").text.strip() if soup.select_one("h1.p-name") else "Title not found"
        
        image_element = soup.select_one("img.photo")
        image_url = image_element['src'] if image_element and image_element.has_attr('src') else "Image URL not found"
        
        venue_element = soup.select_one("p.venue a.venue-name")
        venue = venue_element.text.strip() if venue_element else "Venue not found"
        
        address_element = soup.select_one("span.adr")
        address = address_element.text.strip() if address_element else venue

        start_date_iso = soup.select_one("span.dtstart span.value-title")
        end_date_iso = soup.select_one("span.dtend span.value-title")

        start_date = "Start date not found"
        if start_date_iso and start_date_iso.has_attr('title'):
            start_date = start_date_iso['title'].split('T')[0]

        end_date = start_date 
        if end_date_iso and end_date_iso.has_attr('title'):
            end_date = end_date_iso['title'].split('T')[0]

        description_div = soup.select_one("div.module.description")
        short_description = ""
        if description_div:
            full_description = description_div.get_text(separator=' ', strip=True)
            words = full_description.split()
            short_description = ' '.join(words[:50]) + '...' if len(words) > 50 else full_description
        
        website_link_element = soup.select_one("li.list-item-icon a.external-link")
        registration_link = website_link_element['href'] if website_link_element else url

        return {
            "title": title,
            "description": short_description,
            "start_date": start_date,
            "end_date": end_date,
            "venue_name": venue,
            "address": address,
            "image_url": image_url,
            "registration_link": registration_link,
            "source": full_url
        }

    except Exception as e:
        print(f"Error scraping detail page {url}: {e}")
        return None
if __name__ == "__main__":
    mongo_client = get_mongo_client()
    if mongo_client:
        statistics_data = fetch_gov_statistics()
        transform_and_load_statistics(mongo_client, statistics_data)

        artsrepublic_events = scrape_artsrepublic_sg()
        if artsrepublic_events: 
            transform_and_load_events(mongo_client, artsrepublic_events)
        
        eventfinda_events = scrape_eventfinda_sg()
        if eventfinda_events: 
            transform_and_load_events(mongo_client, eventfinda_events)
        
        mongo_client.close()
        print("\nMongoDB connection closed.")
    else:
        print("Could not connect to MongoDB. Aborting script.")