# Multi-Platform Search - Implementation Strategy

## The Core Concept

**You're building a search aggregator** - like Google Shopping, but for resale marketplaces.

**What this does:**
- Searches publicly available listings across platforms
- Shows unified results to users
- Links directly back to original platform listings
- Helps buyers find items, helps sellers get discovered

**This is platform-friendly** - you're sending them traffic and helping their ecosystem.

---

## Platform Categories (Reality Check)

### ✅ **Category 1: Official APIs Available** (~10-12 platforms)

These platforms provide official APIs **specifically designed** for your use case.

**Benefits:**
- Fast, structured data
- Official support
- Rate limits clearly defined
- Most reliable

**Platforms:**
- eBay (Finding API)
- Etsy (Open API v3)
- Shopify (Storefront API - per-store)
- WooCommerce (REST API - per-store)
- Square (Catalog API)
- TCGplayer (Catalog API)
- Reverb (Public API)
- Discogs (Database API)
- Amazon (Product Advertising API)
- Cardmarket (API v2.0)
- AbeBooks (Amazon-owned, may have API access)

**Implementation:** Use official API with credentials

**Credentials Needed:** See CREDENTIAL_SETUP.md for each platform

---

### ✅ **Category 2: Public Search Available** (~25-30 platforms)

These platforms have public-facing search that anyone can access via URL.

**Examples:**
- Mercari - `mercari.com/search/?keyword=pokemon`
- Poshmark - `poshmark.com/search?query=jordan`
- Grailed - `grailed.com/shop?query=supreme`
- Depop - `depop.com/search/?q=vintage`
- Bonanza - `bonanza.com/listings/search?q=cards`
- Ruby Lane - `rubylane.com/search/all?q=antique`
- Vinted - `vinted.com/catalog?search_text=nike`
- The RealReal - `therealreal.com/products?query=rolex`
- Vestiaire Collective - Public product pages
- Curtsy - Public listings
- Rebag - Public product catalog
- Fashionphile - Public listings
- ThredUp - Public search
- Chairish - `chairish.com/search?query=midcentury`
- ArtFire - Public marketplace
- Folksy - Public handmade listings
- Zibbet - Public listings
- COMC - `comc.com/Cards/Search`
- Sportlots - Public card search
- MySlabs - Public graded card listings
- Biblio - `biblio.com/search.php?keyisbn=`
- Shpock - Public classifieds
- Wallapop - Public listings
- Carousell - Public search

**What "public search" means:**
- You can access it in a browser without logging in
- Google indexes these pages
- The platform wants traffic to these listings

**Implementation:**
- Send HTTP requests to public search URLs
- Parse HTML or JSON responses
- Extract listing data (title, price, image, link)
- Link back to original listing

**Credentials Needed:** None (public access)

**Best Practices:**
- Identify yourself in User-Agent: `"RebelOperator/1.0 (+yoursite.com/about)"`
- Respect rate limits (1-2 requests per second max)
- Check robots.txt (most allow search)
- Cache results briefly to reduce load
- Always link back to original listing

---

### ⚠️ **Category 3: Login Wall / Closed Platform** (~4-6 platforms)

These platforms require login to search or don't expose public listings.

**Platforms:**
- StockX - Account required to search
- GOAT - Account required to browse
- Whatnot - Live auction platform, no static search
- Chrono24 - Some listings public, some require account

**Why they're different:**
- They want to control the user experience
- Data is behind authentication
- Business model depends on keeping users on platform

**Implementation:** Mark as "Not Available" for now

**Future options:**
- User-level OAuth (user connects their own account)
- Partner API access (if you can negotiate)
- Wait for public API

---

### ❌ **Category 4: Explicitly Forbidden** (~2-3 platforms)

These platforms explicitly ban automated access in their Terms of Service.

**Platforms:**
- Facebook Marketplace - TOS: "You may not access or collect data from our Products using automated means"
- Craigslist - Extremely strict, has sued scrapers, must use manually

**Why they're forbidden:**
- Explicit TOS violations
- Legal risk
- They've taken legal action against scrapers

**Implementation:** Don't implement - mark as "Cannot Automate"

---

### 🔵 **Category 5: Local/Manual Only** (~5-6 platforms)

These aren't really platforms - they're local/person-to-person.

**Platforms:**
- OfferUp - Local pickup focus
- Nextdoor - Neighborhood-only
- VarageSale - Local groups

**Why they're different:**
- Location-based, not national search
- Person-to-person transactions
- No centralized search across all listings

**Implementation:** Mark as "Manual Entry Only" or skip

---

## Summary by Numbers

| Category | Count | Action | Credentials |
|----------|-------|--------|-------------|
| Official APIs | 10-12 | **Implement first** | API keys required |
| Public Search | 25-30 | **Implement next** | None needed |
| Login Wall | 4-6 | Mark "Not Available" | Would need user OAuth |
| Explicitly Forbidden | 2-3 | **Don't implement** | N/A |
| Local/Manual | 5-6 | Mark "Manual Only" | N/A |
| **TOTAL** | **44+** | **35-40 can be implemented!** | — |

---

## Implementation Phases

### **Phase 1: APIs (Best Experience)**

Implement these first - cleanest, fastest, most reliable:

1. eBay (Finding API) - Free, 5,000 calls/day
2. Etsy (Open API) - Free, 10,000 calls/day
3. TCGplayer (Catalog API) - Free, approval required
4. Reverb (Public API) - Free
5. Discogs (Database API) - Free
6. Amazon (PA-API) - Free, requires Associate account

**Time estimate:** 1-2 hours per platform
**Result:** 6 major platforms working via official APIs

### **Phase 2: Public Search (Wider Coverage)**

Add these next - good coverage, no credentials needed:

7. Mercari (huge resale platform)
8. Poshmark (fashion/apparel)
9. Grailed (menswear)
10. Depop (vintage/streetwear)
11. Bonanza (general marketplace)
12. Ruby Lane (antiques/collectibles)
13. Vinted (secondhand fashion)
14. COMC (sports cards)
15. Chairish (furniture/decor)

**Time estimate:** 2-3 hours per platform (need to reverse engineer search)
**Result:** 15 total platforms, covering most major resale categories

### **Phase 3: Niche Platforms (Specialty Items)**

Add category-specific platforms:

16. Fashionphile (luxury handbags)
17. The RealReal (luxury consignment)
18. Rebag (luxury bags)
19. Cardmarket (European TCG)
20. Sportlots (vintage sports cards)
21. AbeBooks (rare books)
22. Biblio (books)

**Time estimate:** 2-3 hours per platform
**Result:** 22+ platforms, comprehensive coverage

### **Phase 4: International & Regional**

23. Shpock (classifieds, EU)
24. Wallapop (classifieds, Spain/Europe)
25. Carousell (Southeast Asia)
26. Vinted (Europe/US fashion)

**Result:** 25+ platforms, global coverage

---

## Technical Implementation

### **For Official APIs:**

```python
class PlatformSearcher(BasePlatformSearcher):
    def search(self, query: SearchQuery) -> List[SearchResult]:
        # Get credentials
        api_key = self.credentials.get('api_key')

        # Call official API
        response = requests.get(
            'https://api.platform.com/search',
            params={'q': query.keywords},
            headers={'Authorization': f'Bearer {api_key}'}
        )

        # Parse structured JSON response
        return [self._parse_item(item) for item in response.json()['results']]
```

### **For Public Search:**

```python
class PlatformSearcher(BasePlatformSearcher):
    def search(self, query: SearchQuery) -> List[SearchResult]:
        # Build public search URL
        search_url = f'https://platform.com/search?q={query.keywords}'

        # Make respectful HTTP request
        response = requests.get(
            search_url,
            headers={
                'User-Agent': 'RebelOperator/1.0 (+https://yoursite.com/about)'
            },
            timeout=10
        )

        # Parse HTML or JSON response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract listing data
        results = []
        for item in soup.select('.listing-card'):  # Platform-specific selector
            results.append(SearchResult(
                platform=self.get_platform_name(),
                listing_id=item['data-id'],
                url=item.find('a')['href'],
                title=item.find('.title').text,
                price=float(item.find('.price').text.replace('$', '')),
                thumbnail_url=item.find('img')['src']
            ))

        return results
```

---

## Legal & Ethical Considerations

### ✅ **What's Allowed:**

1. **Reading public data** - If it's viewable without login, it's public
2. **Linking back to source** - You're sending them traffic
3. **Aggregating for user benefit** - Helping users find items
4. **Respectful requests** - Rate limiting, clear identification
5. **No data storage** - Just showing current search results

### ❌ **What to Avoid:**

1. **Bypassing authentication** - Don't try to access logged-in areas
2. **Pretending to be a user** - Don't use headless browsers to fake clicks
3. **Stealing listings** - Always link back, don't copy and republish
4. **High-volume scraping** - Keep requests reasonable (1-2/sec max)
5. **Ignoring robots.txt** - Respect their crawling preferences
6. **Removing attribution** - Always show platform name and link

### 📋 **Best Practices:**

1. **User-Agent Identification:**
   ```
   User-Agent: RebelOperator/1.0 (+https://rebeloperator.com/about)
   ```

2. **Rate Limiting:**
   - Official APIs: Follow their documented limits
   - Public search: 1-2 requests/second max per platform
   - Add random delays (0.5-2 seconds between requests)

3. **Robots.txt Compliance:**
   - Check each platform's robots.txt
   - Most allow search: `User-agent: * / Allow: /search`
   - Respect any disallows

4. **Caching:**
   - Cache results for 5-15 minutes
   - Reduces load on platforms
   - Faster for users
   - Don't store long-term

5. **Attribution:**
   - Always show platform name
   - Always link to original listing
   - Consider adding "Powered by [Platform] API" for API-based searches

---

## Platform-Specific Notes

### **Mercari** (Public Search)
- URL: `https://www.mercari.com/search/?keyword={query}`
- Returns JSON in HTML (easy to parse)
- Very scraper-friendly
- No authentication needed

### **Poshmark** (Public Search)
- URL: `https://poshmark.com/search?query={query}`
- HTML parsing required
- Pagination available
- Public listings

### **Grailed** (Public Search)
- URL: `https://www.grailed.com/shop?query={query}`
- GraphQL API (inspect network tab)
- JSON responses
- Very clean data structure

### **StockX** (Closed - Skip for Now)
- Requires account to search
- API is partner-only
- Mark as "Not Available"

### **Facebook Marketplace** (Forbidden - Don't Touch)
- Explicit TOS ban on automation
- Legal risk
- Mark as "Cannot Automate"

---

## Conclusion

**You can implement search for 35-40 of the 44 platforms** using:
- 10-12 official APIs (best quality)
- 25-30 public search endpoints (good coverage)

**This is legitimate, legal, and platform-friendly** because:
- ✅ You're searching public data
- ✅ You're linking back to original listings
- ✅ You're sending them traffic
- ✅ You're helping their sellers get found

**Start with 6-10 platforms using official APIs**, then expand to public search platforms over time.

No scary TOS warnings needed - you're doing exactly what Google Shopping does, just focused on resale marketplaces. 🚀
