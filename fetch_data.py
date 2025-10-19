import requests 
from bs4 import BeautifulSoup
import json 
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
        fullUrl = "https://www.eventfinda.sg" + url

        response = requests.get(fullUrl, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.select_one("h1.p-name").text.strip() if soup.select_one("h1.p-name") else "Title not found"
        
        image_element = soup.select_one("img.photo")
        image_url = image_element['src'] if image_element and image_element.has_attr('src') else "Image URL not found"
        
        venue_element = soup.select_one("p.venue a.venue-name")
        venue = venue_element.text.strip() if venue_element else "Venue not found"
        
        address_element = soup.select_one("span.adr")
        address = address_element.text.strip() if address_element else venue # Default to venue if no specific address

        date_element = soup.select_one("p.session span.date")
        date_str = date_element.text.strip() if date_element else "Date not found"
        
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
            "date_string": date_str,
            "venue_name": venue,
            "address": address,
            "image_url": image_url,
            "registration_link": registration_link,
            "source": fullUrl
        }

    except Exception as e:
        print(f"Error scraping detail page {url}: {e}")
        return None
    
if __name__ == "__main__":
    
    statistics = fetch_gov_statistics()
    print("\n--- Fetched Statistics Data ---")
    print(json.dumps(statistics, indent=2))

    artsrepublic_events = scrape_artsrepublic_sg()
    print("\n--- Scraped ArtsRepublic.sg Event Data ---")
    
    print(json.dumps(artsrepublic_events, indent=2, ensure_ascii=False))
    
    eventfinda_events = scrape_eventfinda_sg()
    print("\n--- Scraped Eventfinda.sg Event Data ---")
    
    print(json.dumps(eventfinda_events, indent=2, ensure_ascii=False))