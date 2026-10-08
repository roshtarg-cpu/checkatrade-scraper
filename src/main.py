"""
Checkatrade Scraper - Extract UK tradespeople listings
"""
import asyncio
import re
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, quote_plus

print("Starting checkatrade-scraper...", file=sys.stderr, flush=True)

try:
    from apify import Actor
    from camoufox.async_api import AsyncCamoufox
    from bs4 import BeautifulSoup
    print("Imports successful", file=sys.stderr, flush=True)
except Exception as e:
    print(f"Import error: {e}", file=sys.stderr, flush=True)
    raise


async def main() -> None:
    print("Entering main()", file=sys.stderr, flush=True)
    
    try:
        async with Actor:
            print("Actor context started", file=sys.stderr, flush=True)
            
            # Get input (SDK 4.x uses get_input())
            try:
                actor_input = await Actor.get_input() or {}
                print(f"Got input: {actor_input}", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Error getting input: {e}", file=sys.stderr, flush=True)
                raise
            trade = actor_input.get('trade', 'electricians')
            location = actor_input.get('location', 'London')
            max_results = actor_input.get('maxResults', 3)
            proxy_config_input = actor_input.get('proxyConfiguration', {
                'useApifyProxy': True,
                'apifyProxyGroups': ['RESIDENTIAL']
            })
            
            Actor.log.info(f'Starting Checkatrade scraper')
            Actor.log.info(f'Trade: {trade}, Location: {location}, Max: {max_results}')
            
            # Get environment (synchronous in SDK 4.x - returns dict)
            env = Actor.get_env()
            
            # Use proxy from input proxyConfiguration  
            proxy_config = None
            if proxy_config_input.get('useApifyProxy'):
                # Get Apify proxy password from environment
                proxy_password = env.get('proxy_password') or env.get('token')
                if proxy_password:
                    groups = proxy_config_input.get('apifyProxyGroups', ['RESIDENTIAL'])
                    group_str = ','.join([g.upper() for g in groups])
                    # Camoufox proxy dict format
                    proxy_config = {
                        'server': 'http://proxy.apify.com:8000',
                        'username': f'groups-{group_str}',
                        'password': proxy_password
                    }
                    Actor.log.info(f'Using Apify proxy: {group_str}')
            
            # Build search URL
            # Format: /Search/Electrician/in/London
            # Capitalize first letter of trade
            trade_capitalized = trade.replace('-', ' ').title().replace(' ', '-')
            search_url = f'https://www.checkatrade.com/Search/{trade_capitalized}/in/{location}'
            
            Actor.log.info(f'Search URL: {search_url}')
            
            results_count = 0
            
            # Launch Camoufox with stealth and proxy
            browser_kwargs = {
                'headless': True,
                'humanize': True
            }
            if proxy_config:
                browser_kwargs['proxy'] = proxy_config
            
            async with AsyncCamoufox(**browser_kwargs) as browser:
                
                page = await browser.new_page()
                
                try:
                    # Navigate to search page
                    Actor.log.info('Loading search page...')
                    await page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
                    await asyncio.sleep(3)  # Wait for JS rendering
                    
                    # Get page content
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Multiple selector strategies for tradesperson cards
                    containers = set()
                    
                    # Strategy 1: data attributes
                    for elem in soup.find_all(attrs={'data-testid': re.compile(r'tradesperson|card|listing', re.I)}):
                        containers.add(elem)
                    
                    # Strategy 2: article elements with links
                    for elem in soup.find_all('article'):
                        if elem.find('a'):
                            containers.add(elem)
                    
                    # Strategy 3: divs with tradesperson/card/listing classes
                    if not containers:
                        for elem in soup.find_all('div', class_=re.compile(r'tradesperson|card|listing|result', re.I)):
                            if elem.find('a'):
                                containers.add(elem)
                    
                    # Strategy 4: links with /tradespeople/ in href
                    if not containers:
                        for link in soup.find_all('a', href=re.compile(r'/tradespeople/')):
                            parent = link.find_parent(['div', 'article', 'li'])
                            if parent:
                                containers.add(parent)
                    
                    containers = list(containers)
                    Actor.log.info(f'Found {len(containers)} listing containers')
                    
                    # Extract data from each container
                    for container in containers[:max_results]:
                        try:
                            # URL
                            link_elem = container.find('a', href=re.compile(r'/tradespeople/'))
                            if not link_elem:
                                link_elem = container.find('a')
                            url = urljoin('https://www.checkatrade.com', link_elem['href']) if link_elem and link_elem.get('href') else None
                            
                            # Name
                            name_elem = container.find(['h2', 'h3', 'h4'])
                            if not name_elem:
                                name_elem = link_elem
                            name = name_elem.get_text(strip=True) if name_elem else None
                            
                            # Rating
                            rating_elem = container.find(string=re.compile(r'\d+\.\d+|★|stars?', re.I))
                            rating = None
                            if rating_elem:
                                rating_match = re.search(r'(\d+\.\d+)', str(rating_elem))
                                if rating_match:
                                    rating = rating_match.group(1)
                            
                            # Review count
                            review_elem = container.find(string=re.compile(r'\d+\s*(review|rating)', re.I))
                            review_count = None
                            if review_elem:
                                review_match = re.search(r'(\d+)', str(review_elem))
                                if review_match:
                                    review_count = int(review_match.group(1))
                            
                            # Location
                            location_elem = container.find(string=re.compile(r'based in|location|area', re.I))
                            if not location_elem:
                                # Try to find any text that looks like a UK city/postcode
                                location_elem = container.find(string=re.compile(r'[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}|London|Manchester|Birmingham', re.I))
                            location_text = location_elem.strip() if location_elem else None
                            
                            # Business Description
                            desc_elem = container.find('p')
                            business_description = desc_elem.get_text(strip=True) if desc_elem else None
                            
                            # Trade (from input or extract from page)
                            trade_text = trade
                            
                            # Verified status
                            verified = bool(container.find(string=re.compile(r'verified|endorsed|approved', re.I)))
                            
                            result = {
                                'url': url,
                                'name': name,
                                'trade': trade_text,
                                'rating': rating,
                                'reviewCount': review_count,
                                'location': location_text,
                                'businessDescription': business_description,
                                'verified': verified,
                                'scrapedAt': datetime.now(timezone.utc).isoformat()
                            }
                            
                            # Push immediately
                            await Actor.push_data(result)
                            results_count += 1
                            Actor.log.info(f'Scraped: {name or "Unknown"} ({results_count}/{max_results})')
                            
                            if results_count >= max_results:
                                break
                        
                        except Exception as e:
                            Actor.log.warning(f'Error extracting item: {e}')
                            continue
                    
                except Exception as e:
                    Actor.log.error(f'Navigation error: {e}')
                    # Take screenshot for debugging
                    try:
                        await page.screenshot(path='error.png')
                        Actor.log.info('Screenshot saved to error.png')
                    except:
                        pass
                
                finally:
                    await page.close()
            
            # Save metadata
            await Actor.set_value('SAVED-TASK', {
                'actorId': env.get('actor_id'),
                'actorRunId': env.get('actor_run_id'),
                'defaultDatasetId': env.get('default_dataset_id'),
                'startedAt': env.get('started_at'),
                'input': actor_input,
                'stats': {
                    'resultsScraped': results_count
                }
            })
        
        Actor.log.info(f'Scraping complete. Total results: {results_count}')
    
    except Exception as e:
        print(f"ERROR in main: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        raise
