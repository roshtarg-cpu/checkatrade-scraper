# 🔍 Checkatrade Scraper - AI-Powered UK Tradespeople Data Extraction

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-00D4FF?style=flat-square)](https://apify.com/fervent_bus/checkatrade-scraper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![AI Agent Compatible](https://img.shields.io/badge/AI-Claude%20%7C%20ChatGPT%20%7C%20MCP-blueviolet?style=flat-square)](https://apify.com)

Extract structured data from **Checkatrade** with this powerful scraper. Built for developers, AI agents (Claude, ChatGPT), and automation workflows via **Apify MCP integration**. Get verified UK tradespeople listings including electricians, plumbers, builders, and more.

---

## ✨ Features

- 🤖 **AI Agent Ready** - Works seamlessly with Claude, ChatGPT, and other AI agents via Apify MCP
- 🔄 **Full Pagination** - Automatically scrapes all pages
- 🌍 **Proxy Support** - Residential proxies included for Cloudflare bypass
- 📊 **Multiple Export Formats** - JSON, CSV, Excel, HTML
- ⚡ **Fast & Reliable** - Optimized for speed and accuracy with Camoufox stealth browser
- 🛡️ **Anti-Bot Protection** - Handles Cloudflare protection automatically
- 🔍 **Advanced Filtering** - Trade category, location, minimum rating
- ✅ **Verified Data** - Extract verification status and review counts

---

## 🚀 Quick Start

### Via Apify Console
1. Go to [Apify Console](https://console.apify.com/actors/fervent_bus~checkatrade-scraper)
2. Configure input fields:
   - **Trade**: Select category (electricians, plumbers, builders, etc.)
   - **Location**: Enter city, town, or postcode
   - **Max Results**: Set limit (default: 3)
3. Click **Run** and download results

### Via API (Python)
```python
from apify_client import ApifyClient

client = ApifyClient('YOUR_APIFY_TOKEN')

run = client.actor('fervent_bus/checkatrade-scraper').call(run_input={
    'trade': 'electricians',
    'location': 'Manchester',
    'minRating': 4.5,
    'maxResults': 50
})

# Fetch results
items = client.dataset(run['defaultDatasetId']).list_items().items
for item in items:
    print(f"{item['name']} - {item['rating']} stars - {item['location']}")
```

### Via API (JavaScript)
```javascript
const ApifyClient = require('apify-client');

const client = new ApifyClient({ token: 'YOUR_APIFY_TOKEN' });

const run = await client.actor('fervent_bus/checkatrade-scraper').call({
    trade: 'plumbers',
    location: 'London',
    minRating: 4.0,
    maxResults: 50
});

const { items } = await client.dataset(run.defaultDatasetId).listItems();
items.forEach(item => console.log(`${item.name} - ${item.rating} ⭐`));
```

### Via cURL
```bash
curl -X POST https://api.apify.com/v2/acts/fervent_bus~checkatrade-scraper/runs \
  -H "Authorization: Bearer YOUR_APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trade": "builders",
    "location": "Birmingham",
    "maxResults": 100
  }'
```

---

## 📥 Input Configuration

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `trade` | String | Trade category (electricians, plumbers, builders, carpenters, painters-decorators, roofers, gardeners, heating-engineers, bathroom-fitters, kitchen-fitters, plasterers, tilers, locksmiths, window-fitters, flooring-specialists) | ✅ |
| `location` | String | City, town, or postcode to search near (default: London) | ✅ |
| `minRating` | Number | Filter by minimum star rating (0-5, default: 0 for no filter) | ❌ |
| `maxResults` | Integer | Maximum results to scrape (default: 3, range: 1-10000) | ❌ |
| `proxyConfiguration` | Object | Proxy settings (RESIDENTIAL group required for Cloudflare) | ❌ |

---

## 📤 Output Structure

```json
[
  {
    "url": "https://www.checkatrade.com/tradespeople/john-smith-electrical",
    "name": "John Smith Electrical Services",
    "trade": "electricians",
    "rating": "4.9",
    "reviewCount": 127,
    "location": "Manchester, Greater Manchester",
    "description": "Fully qualified electrician with 15+ years experience. NICEIC approved contractor.",
    "verified": true,
    "scrapedAt": "2026-10-08T05:15:00.000Z"
  }
]
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `url` | String | Direct link to tradesperson's Checkatrade profile |
| `name` | String | Business or tradesperson name |
| `trade` | String | Trade category (electrician, plumber, builder, etc.) |
| `rating` | String | Average star rating (0-5 scale) |
| `reviewCount` | Integer | Total number of customer reviews |
| `location` | String | Operating location (city, region, or postcode) |
| `description` | String | Business description and services offered |
| `verified` | Boolean | Whether tradesperson is verified by Checkatrade |
| `scrapedAt` | String | ISO 8601 timestamp when data was collected |

---

## 💡 Use Cases

### 🎯 Lead Generation
Build targeted lists of verified UK tradespeople for B2B sales outreach, supplier partnerships, or franchise recruitment.

### 📊 Market Research
Analyze competitor density, pricing trends, and service offerings across different UK regions and trade categories.

### 🏠 Property Development
Find reliable contractors for construction, renovation, and maintenance projects with verified reviews and ratings.

### 💰 Business Intelligence
Track tradesperson availability, specialization trends, and market gaps for strategic planning and investment decisions.

### 🤖 AI Agent Workflows
Integrate with Claude Code, ChatGPT plugins, or custom AI agents via Apify MCP for automated contractor sourcing, comparison reports, and recommendation systems.

### 📈 CRM Enrichment
Enrich customer databases with verified tradesperson profiles, contact information, and service areas for automated marketing campaigns.

---

## ❓ FAQ

### Does it handle pagination?
Yes! The scraper automatically follows pagination to collect all available results up to your `maxResults` limit.

### Can I use proxies?
Absolutely. **RESIDENTIAL** proxy group is required and pre-configured for bypassing Cloudflare protection. Configure via `proxyConfiguration` input.

### What export formats are supported?
JSON, CSV, Excel (XLSX), HTML, RSS, and XML. Download from Apify Console or fetch via API.

### Is it compatible with AI agents?
✅ **Yes!** This actor works with Claude Code, ChatGPT, and other AI agents through **Apify MCP integration**. Use it directly from your AI assistant for automated contractor sourcing and research.

### How often can I run it?
As often as you need! Runs are limited only by your Apify subscription plan.

### Does it bypass Cloudflare protection?
Yes, we use **Camoufox stealth browser** with residential proxies, humanized browsing patterns, and GeoIP targeting to reliably bypass Cloudflare and other anti-bot systems.

### Can I filter by rating?
Yes! Use the `minRating` parameter to filter results by minimum star rating (0-5 scale).

### What trade categories are supported?
All major Checkatrade categories: electricians, plumbers, builders, carpenters, painters-decorators, roofers, gardeners, heating-engineers, bathroom-fitters, kitchen-fitters, plasterers, tilers, locksmiths, window-fitters, and flooring-specialists.

---

## 💰 Pricing

| Event Type | Price | Description |
|------------|-------|-------------|
| 💵 **Per Result** | $0.005 | Each tradesperson profile scraped |
| 🚀 **Actor Start** | $0.05 | One-time fee per run |

**Example:** Scraping 100 tradespeople = $0.05 (start) + $0.50 (100 × $0.005) = **$0.55 total**

[View detailed pricing](https://apify.com/fervent_bus/checkatrade-scraper/pricing)

---

## 🔗 Links

- 🏠 [Actor Page](https://apify.com/fervent_bus/checkatrade-scraper)
- 📚 [Apify Documentation](https://docs.apify.com)
- 💬 [Support](https://console.apify.com/actors/fervent_bus~checkatrade-scraper/issues)
- 🐙 [GitHub Repository](https://github.com/roshtarg-cpu/checkatrade-scraper)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for developers and AI agents. Compatible with Claude, ChatGPT & AI automation via Apify MCP.**
