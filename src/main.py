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
                    
                    Actor.log.info('Parsing page for tradesperson listings...')
                    
                    # Find all links to /trades/ profiles
                    trade_links = soup.find_all('a', href=re.compile(r'/trades/[^#]+'))
                    
                    Actor.log.info(f'Found {len(trade_links)} tradesperson links')
                    
                    seen_urls = set()
                    
                    # Extract data from each link
                    for link in trade_links:
                        if results_count >= max_results:
                            break
                            
                        try:
                            # Get URL
                            href = link.get('href', '')
                            if not href or '#' not in href:
                                continue
                            
                            # Clean URL (remove query params)
                            url = urljoin('https://www.checkatrade.com', href.split('#')[0])
                            
                            # Skip duplicates
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)
                            
                            # Get name from link text
                            name = link.get_text(strip=True)
                            if not name or len(name) < 3:
                                continue
                            
                            # Find parent container for rating/reviews
                            container = link.find_parent(['div', 'article', 'li'])
                            if not container:
                                container = link
                            
                            # Extract rating - look for decimal numbers
                            rating = None
                            rating_text = container.find(string=re.compile(r'\d+\.\d+'))
                            if rating_text:
                                rating_match = re.search(r'(\d+\.\d+)', str(rating_text))
                                if rating_match:
                                    rating = rating_match.group(1)
                            
                            # Extract review count - look for (N reviews)
                            review_count = None
                            review_text = container.find(string=re.compile(r'\(\d+\s*review', re.I))
                            if review_text:
                                review_match = re.search(r'\((\d+)', str(review_text))
                                if review_match:
                                    review_count = int(review_match.group(1))
                            
                            # Extract location - look for "Operates in"
                            location_text = None
                            loc_elem = container.find(string=re.compile(r'Operates in', re.I))
                            if loc_elem:
                                location_text = re.sub(r'Operates in\s*', '', str(loc_elem), flags=re.I).strip()
                            
                            # Extract services - look for "Services & skills"
                            services = []
                            services_section = container.find(string=re.compile(r'Services & skills', re.I))
                            if services_section:
                                services_container = services_section.find_parent()
                                if services_container:
                                    service_texts = services_container.find_all(string=True)
                                    services = [s.strip() for s in service_texts if s.strip() and s.strip() != 'Services & skills'][:5]
                            
                            result = {
                                'url': url,
                                'name': name,
                                'trade': trade,
                                'rating': rating,
                                'reviewCount': review_count,
                                'location': location_text,
                                'services': ', '.join(services) if services else None,
                                'verified': bool(container.find(string=re.compile(r'verified|sponsored', re.I))),
                                'scrapedAt': datetime.now(timezone.utc).isoformat()
                            }
                            
                            # Push immediately
                            await Actor.push_data(result)
                            results_count += 1
                            Actor.log.info(f'Scraped {results_count}/{max_results}: {name}')
                        
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
