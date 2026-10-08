"""
Checkatrade Scraper - Extract UK tradespeople listings
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, quote_plus

from apify import Actor
from camoufox.async_api import AsyncCamoufox
from bs4 import BeautifulSoup


async def main() -> None:
    async with Actor:
        # Get input (synchronous in SDK 4.x)
        actor_input = Actor.get_env()['input'] if Actor.get_env().get('input') else {}
        
        trade = actor_input.get('trade', 'electricians')
        location = actor_input.get('location', 'London')
        max_results = actor_input.get('maxResults', 3)
        proxy_config = actor_input.get('proxyConfiguration', {
            'useApifyProxy': True,
            'apifyProxyGroups': ['RESIDENTIAL']
        })
        
        Actor.log.info(f'Starting Checkatrade scraper')
        Actor.log.info(f'Trade: {trade}, Location: {location}, Max: {max_results}')
        
        # Get proxy URL
        proxy_url = None
        if proxy_config.get('useApifyProxy'):
            proxy_url = Actor.create_proxy_url(
                groups=proxy_config.get('apifyProxyGroups', ['RESIDENTIAL'])
            )
            Actor.log.info(f'Using Apify proxy: {proxy_config.get("apifyProxyGroups")}')
        
        # Build search URL
        search_url = f'https://www.checkatrade.com/trades/{trade.lower()}'
        if location:
            search_url = f'https://www.checkatrade.com/trades/{trade.lower()}/near/{quote_plus(location)}'
        
        Actor.log.info(f'Search URL: {search_url}')
        
        results_count = 0
        
        # Launch Camoufox with stealth
        async with AsyncCamoufox(
            headless=True,
            humanize=True,
            geoip=True,
            proxy=proxy_url
        ) as browser:
            
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
                        
                        # Description
                        desc_elem = container.find('p')
                        description = desc_elem.get_text(strip=True) if desc_elem else None
                        
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
                            'description': description,
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
        env = Actor.get_env()
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
