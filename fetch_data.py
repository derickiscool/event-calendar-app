import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from project import app
from project.db import get_mongo_client
from project.models import db, EventCache

# Load environment variables
load_dotenv()

# --- STATISTICS FUNCTIONS (KEPT ORIGINAL) ---

def fetch_gov_statistics():
    """Fetches arts and culture statistics from data.gov.sg API."""
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

def transform_and_load_statistics(client, stats_data):
    """Transforms and loads statistics into the 'statistics' collection."""
    if not client or not stats_data:
        print("No client or statistics data provided.")
        return
        
    db_mongo = client.get_database("event_calendar") 
    statistics_collection = db_mongo.statistics

    stats_by_year = {}
    
    # Group all raw data by year
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

    upserted_count = 0
    modified_count = 0
    for year, data in stats_by_year.items():
        statistics_document = {
            "year": year,
            "gov_contributions": data["gov_contributions"],
            "employment_items": data["employment_items"],
            "activities": data["activities"]
        }
        
        result = statistics_collection.update_one(
            {'year': year},
            {'$set': statistics_document},
            upsert=True
        )
        if result.upserted_id:
            upserted_count += 1
        elif result.modified_count > 0:
            modified_count += 1

    print(f"Statistics Load Complete. Inserted: {upserted_count} years. Updated: {modified_count} years.")


# --- SCRAPING FUNCTIONS (KEPT ORIGINAL) ---

def scrape_artsrepublic_sg():
    """Scrapes event data from ArtsRepublic.sg."""
    list_page_url = "https://artsrepublic.sg/events"
    scraped_events = []

    print("\nScraping artsrepublic.sg...")
    try:
        response = requests.get(list_page_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        event_links = soup.select('li a.event_thumbnail')
        
        if not event_links:
            print("No event links found on artsrepublic.sg.")
            return []
            
        print(f"Found {len(event_links)} event links. Scraping detail pages...")
        for link_tag in event_links:
            detail_url = link_tag.get('href')
            if detail_url:
                event_data = scrape_artsrepublic_detail_page(detail_url)
                if event_data:
                    scraped_events.append(event_data)
    except requests.exceptions.RequestException as e:
        print(f"Error scraping artsrepublic.sg list page: {e}")
    return scraped_events

def scrape_artsrepublic_detail_page(url):
    """Scrapes details from ArtsRepublic."""
    try:
        base_url = "https://artsrepublic.sg"
        fullUrl = f"{base_url}/{url.lstrip('/')}"
        
        response = requests.get(fullUrl, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.select_one('h1[itemprop="name"]').text.strip() if soup.select_one('h1[itemprop="name"]') else "Title not found"
        start_date = soup.select_one('meta[itemprop="startDate"]')['content'] if soup.select_one('meta[itemprop="startDate"]') else None
        end_date = soup.select_one('meta[itemprop="endDate"]')['content'] if soup.select_one('meta[itemprop="endDate"]') else None
        image_url = soup.select_one('meta[itemprop="image"]')['content'] if soup.select_one('meta[itemprop="image"]') else None
        
        location_div = soup.select_one('div[itemprop="location"]')
        venue, address = "Venue not found", ""
        if location_div and location_div.select_one('span[itemprop="name"]'):
            full_location_string = location_div.select_one('span[itemprop="name"]').text.strip()
            if ',' in full_location_string:
                parts = full_location_string.split(',', 1)
                venue, address = parts[0].strip(), parts[1].strip()
            else:
                venue, address = full_location_string, full_location_string

        synopsis_div = soup.select_one('div.synopsis')
        short_description = ""
        if synopsis_div:
            full_synopsis = ' '.join(p.text.replace("Synopsis:", "").strip() for p in synopsis_div.find_all('p'))
            words = full_synopsis.split()
            short_description = ' '.join(words[:50]) + '...' if len(words) > 50 else ' '.join(words)
        
        website_link_tag = soup.select_one('div.data a[target="_blank"]')
        registration_link = website_link_tag['href'] if website_link_tag else None
        
        return {
            "title": title, "description": short_description, "start_date": start_date,
            "end_date": end_date, "venue_name": venue, "address": address,
            "image_url": image_url, "registration_link": registration_link, "source": fullUrl
        }
    except requests.exceptions.RequestException as e:
        print(f"Error scraping detail page {url}: {e}")
        return None

def scrape_eventfinda_sg():
    """Scrapes event data from Eventfinda.sg."""
    list_page_url = "https://www.eventfinda.sg/whatson/events/singapore"
    scraped_events = []

    print("\nScraping eventfinda.sg...")
    try:
        response = requests.get(list_page_url, timeout=15)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        event_cards = soup.select('div.card.h-event')
        
        if not event_cards:
            print("No event links found on eventfinda.sg.")
            return []
            
        print(f"Found {len(event_cards)} event links. Scraping detail pages...")
        for card in event_cards:
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
    """Scrapes details from Eventfinda."""
    try:
        full_url = "https://www.eventfinda.sg" + url
        response = requests.get(full_url, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.select_one("h1.p-name").text.strip() if soup.select_one("h1.p-name") else "Title not found"
        image_url = soup.select_one("img.photo")['src'] if soup.select_one("img.photo") else None
        venue = soup.select_one("p.venue a.venue-name").text.strip() if soup.select_one("p.venue a.venue-name") else "Venue not found"
        address = soup.select_one("span.adr").text.strip() if soup.select_one("span.adr") else venue

        start_date = soup.select_one("span.dtstart span.value-title")['title'].split('T')[0] if soup.select_one("span.dtstart span.value-title") else None
        end_date = soup.select_one("span.dtend span.value-title")['title'].split('T')[0] if start_date and soup.select_one("span.dtend span.value-title") else start_date

        description_div = soup.select_one("div.module.description")
        short_description = ""
        if description_div:
            full_description = description_div.get_text(separator=' ', strip=True)
            words = full_description.split()
            short_description = ' '.join(words[:50]) + '...' if len(words) > 50 else full_description
        
        registration_link = soup.select_one("li.list-item-icon a.external-link")['href'] if soup.select_one("li.list-item-icon a.external-link") else full_url

        return {
            "title": title, "description": short_description, "start_date": start_date,
            "end_date": end_date, "venue_name": venue, "address": address,
            "image_url": image_url, "registration_link": registration_link, "source": full_url
        }
    except Exception as e:
        print(f"Error scraping detail page {url}: {e}")
        return None


# --- UPDATED LOAD FUNCTION (SYNC MONGODB + MYSQL CACHE) ---

def transform_and_load_events(client, events_data, site_name):
    """
    1. Upserts events into MongoDB 'events' collection.
    2. Upserts same events into MySQL 'event_cache' table (The Universal Adapter).
    """
    if not client or not events_data:
        return
    
    db_mongo = client.get_database("event_calendar") 
    events_collection = db_mongo.events

    upserted_count = 0
    modified_count = 0
    skipped_count = 0
    cached_count = 0

    for event in events_data:
        # Basic validation
        if not event.get("title") or "not found" in event.get("title").lower() or not event.get("source"):
            print(f"Skipping invalid event data: {event.get('title')}")
            skipped_count += 1
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

        # --- A. MongoDB Upsert ---
        result = events_collection.update_one(
            {'source': mongo_event['source']},
            {'$set': mongo_event},
            upsert=True
        )
        
        mongo_id = None
        if result.upserted_id:
            upserted_count += 1
            mongo_id = str(result.upserted_id)
        elif result.modified_count > 0:
            modified_count += 1
            # Retrieve existing ID
            doc = events_collection.find_one({'source': mongo_event['source']})
            mongo_id = str(doc['_id'])
        else:
            # No change, but we still need ID for cache check
            doc = events_collection.find_one({'source': mongo_event['source']})
            if doc:
                mongo_id = str(doc['_id'])

        # --- B. MySQL Cache Upsert ---
        if mongo_id:
            try:
                event_identifier = f"official_{mongo_id}"
                
                # Check if exists in cache
                existing_cache = EventCache.query.get(event_identifier)
                
                if not existing_cache:
                    new_cache = EventCache(
                        event_identifier=event_identifier,
                        source='official',
                        original_id=mongo_id,
                        title=mongo_event['title'][:255] # Truncate for SQL safety
                    )
                    db.session.add(new_cache)
                    cached_count += 1
                else:
                    # Sync title if changed
                    if existing_cache.title != mongo_event['title'][:255]:
                        existing_cache.title = mongo_event['title'][:255]
                
                # Commit frequently to keep connection fresh
                db.session.commit()
                
            except Exception as e:
                print(f"MySQL Cache Error for {mongo_event['title']}: {e}")
                db.session.rollback()

    print(f"'{site_name}' Load Complete. Mongo: +{upserted_count}/~{modified_count}. MySQL Cache Updated.")


# --- MAIN EXECUTION BLOCK ---

if __name__ == "__main__":
    print("--- Starting Full Data Synchronization ---")

    
    with app.app_context():
        mongo_client = get_mongo_client()
        if mongo_client:
            # 1. Load Statistics
            statistics_data = fetch_gov_statistics()
            transform_and_load_statistics(mongo_client, statistics_data)

            # 2. Load Events from ArtsRepublic
            artsrepublic_events = scrape_artsrepublic_sg()
            if artsrepublic_events: 
                transform_and_load_events(mongo_client, artsrepublic_events, "artsrepublic.sg")
            
            # 3. Load Events from Eventfinda
            eventfinda_events = scrape_eventfinda_sg()
            if eventfinda_events: 
                transform_and_load_events(mongo_client, eventfinda_events, "eventfinda.sg")
            
            mongo_client.close()
            print("\nMongoDB connection closed. Sync finished.")
        else:
            print("Could not connect to MongoDB. Aborting script.")