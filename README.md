# Real Estate Lead Finder

Automatically find real estate leads from Google search results and export to Excel spreadsheets.

This tool uses the **Google Custom Search API** to search for:
- **Service Providers**: Realtors, contractors, home improvement professionals
- **Potential Clients**: Home buyers, sellers, people needing renovations, relocating families, and more

Extract contact details (names, emails, phone numbers, company info) into structured spreadsheets.

## Features

- 🎯 **11 Pre-built Search Templates** - Find different types of leads instantly
- 🔍 Search Instagram, Facebook, LinkedIn, Twitter, and more
- 📧 Extract emails, phone numbers, names, and company information
- 📊 Export results to Excel (.xlsx) or CSV format
- 🌍 Filter by specific locations (cities, states)
- ⚙️ Fully customizable search parameters
- 🔒 Uses official Google API (legal and reliable)

## Available Search Templates

### Service Providers
- **realtors** - Find real estate agents and realtors
- **contractors** - Find contractors and home improvement professionals

### Home Buyers (Potential Clients)
- **home_buyers** - People who recently bought homes
- **first_time_buyers** - First-time home buyers actively looking

### Home Sellers (Potential Clients)
- **home_sellers** - People looking to sell their homes
- **downsizing** - People downsizing/selling family homes
- **urgent_sellers** - People who need to sell quickly (divorce, foreclosure, etc.)

### Home Improvement (Potential Clients)
- **renovation_needed** - People needing home renovations or remodels
- **home_repair** - People needing home repairs or handyman services

### Other Potential Clients
- **relocating** - People relocating to new areas
- **investors** - Real estate investors looking for properties

## Quick Start

### Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google Custom Search API** (see detailed setup below)

3. **Configure your credentials:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API key and CSE ID
   ```

### Basic Usage Examples

**List all available templates:**
```bash
python main.py --list-templates
```

**Find realtors (default):**
```bash
python main.py
```

**Find people who recently bought homes:**
```bash
python main.py --template home_buyers --locations "Miami FL" "Fort Lauderdale FL"
```

**Find people looking to sell:**
```bash
python main.py --template home_sellers --locations "Los Angeles CA"
```

**Find people needing renovations:**
```bash
python main.py --template renovation_needed --locations "Austin TX"
```

**Find first-time home buyers:**
```bash
python main.py --template first_time_buyers --locations "Boston MA"
```

## Detailed Setup Instructions

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Google Custom Search API

#### 2.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name your project (e.g., "Lead Finder")
4. Click "Create"

#### 2.2 Enable Custom Search API

1. In the Google Cloud Console, go to [APIs & Services](https://console.cloud.google.com/apis/library)
2. Search for "Custom Search API"
3. Click on it and press "Enable"

#### 2.3 Create API Key

1. Go to [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "API Key"
3. Copy your API key (it looks like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
4. (Optional) Click "Restrict Key" to limit it to Custom Search API only

#### 2.4 Create Custom Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" or "Get Started"
3. Fill in the form:
   - **Sites to search**: Enter `www.google.com` (we'll configure it to search the whole web)
   - **Name**: "Lead Search" (or any name)
4. Click "Create"
5. On the next page, click "Control Panel"
6. Under "Basics":
   - Turn ON "Search the entire web"
   - Turn OFF "Search only included sites"
7. Copy your **Search Engine ID** (looks like: `0123456789abcdefg:hijklmnop`)

### Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   GOOGLE_API_KEY=YOUR_API_KEY_HERE
   GOOGLE_CSE_ID=YOUR_SEARCH_ENGINE_ID_HERE
   ```

## Usage Guide

### Command Line Options

```bash
python main.py [OPTIONS]
```

**Key Options:**
- `--template <name>` - Which type of leads to find (default: realtors)
- `--list-templates` - Show all available templates
- `--locations <loc1> <loc2>` - Cities/states to search
- `--results <num>` - Max results to fetch (default: 100)
- `--sites <site1> <site2>` - Override which sites to search
- `--format <excel|csv|both>` - Output format (default: excel)
- `--output <filename>` - Custom output filename
- `--no-emails` - Don't include email domains in search
- `--query <query>` - Use custom search query

### More Examples

**Search different cities:**
```bash
python main.py --template home_buyers --locations "Seattle WA" "Portland OR"
```

**Search LinkedIn instead of Instagram/Facebook:**
```bash
python main.py --template home_sellers --sites linkedin.com --locations "Denver CO"
```

**Get only 50 results (saves API quota):**
```bash
python main.py --template renovation_needed --results 50 --locations "Phoenix AZ"
```

**Export to CSV:**
```bash
python main.py --template relocating --locations "Nashville TN" --format csv
```

**Custom output filename:**
```bash
python main.py --template realtors --locations "Tampa FL" --output tampa_realtors.xlsx
```

**Use a custom search query:**
```bash
python main.py --query 'site:facebook.com "just bought" "house" "Miami" "@gmail.com"'
```

### Understanding Search Templates

Each template is optimized for finding specific types of leads:

**Service Provider Templates** find professionals offering services (contact info more likely to be public)

**Client Templates** find people who need services. These searches look for:
- Social media posts about home purchases/sales
- People asking for recommendations
- Life events (moving, downsizing, etc.)
- Home improvement needs

## Output Format

The tool creates a spreadsheet with these columns:

| Column | Description |
|--------|-------------|
| `first_name` | First name (extracted from title) |
| `last_name` | Last name (extracted from title) |
| `company_name` | Real estate company name |
| `website_url` | URL of the search result |
| `email` | Email address (if found) |
| `phone` | Phone number (if found) |

Results are saved in the `output/` folder with timestamps.

## API Limits & Costs

### Free Tier
- **100 queries per day** for free
- Each search result page = 1 query
- Default setting fetches 100 results = 10 queries

### Paid Tier
- $5 per 1,000 queries after free tier
- Max 10,000 queries per day

### Tips to Stay Within Free Tier
- Use `--results 50` to fetch only 50 results (5 queries)
- Run targeted searches for specific locations
- Test with smaller result sets first
- One search template per day uses only 10 queries

## How It Works

1. **Search**: Uses Google Custom Search API to find pages matching your criteria
2. **Extract**: Parses search result titles and snippets for contact information using regex
3. **Filter**: Identifies relevant leads based on keywords and patterns
4. **Export**: Creates a spreadsheet with structured contact data

## Use Cases

### For Real Estate Agents
- Find potential home buyers in your area
- Identify people looking to sell
- Connect with people relocating to your city
- Find investors looking for properties

### For Contractors
- Find homeowners needing renovations
- Identify fixer-upper buyers who'll need work done
- Target new homeowners (often need repairs/updates)

### For Service Businesses
- Find motivated sellers who need help
- Target specific neighborhoods or cities
- Build targeted lead lists by client type

## Limitations

- Contact information must appear in search result titles/snippets (Google API doesn't provide full page content)
- Name extraction is best-effort and may not always be accurate
- Not all results will contain emails or phone numbers
- Requires manual verification of extracted data
- Social media posts may be outdated

## Troubleshooting

### "Error: API key and CSE ID are required"
- Make sure your `.env` file exists with valid credentials
- Check that you copied the API key and CSE ID correctly

### "No results found"
- Try broader locations or different templates
- Check if your search query is too restrictive
- Verify your Custom Search Engine is set to "Search the entire web"

### "Template not found"
- Run `python main.py --list-templates` to see available templates
- Check spelling of template name

### "API quota exceeded"
- You've hit the 100 queries/day limit
- Wait until the next day or upgrade to paid tier
- Reduce `--results` to use fewer queries

### Poor quality contact extraction
- The API only provides titles and snippets, not full page content
- Try different templates or search parameters
- Some manual verification will always be necessary
- Client searches may have less direct contact info than service provider searches

## Project Structure

```
quickhandleads/
├── main.py                    # Main script to run
├── google_search.py           # Google Custom Search API client
├── search_templates.py        # Pre-built search templates for different lead types
├── contact_extractor.py       # Contact information extraction logic
├── spreadsheet_exporter.py    # Excel/CSV export functionality
├── examples.sh                # Example commands
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Your credentials (create this)
├── .gitignore                # Git ignore file
├── README.md                 # This file
└── output/                   # Generated spreadsheets (created automatically)
```

## Privacy & Legal Considerations

- This tool only searches publicly available information
- Respect privacy laws (GDPR, CAN-SPAM, TCPA, etc.) when using collected data
- Use extracted contacts ethically and in compliance with anti-spam regulations
- Always verify information before using it for outreach
- Get proper consent before adding contacts to marketing lists
- Consider that contact information may be outdated or incorrect
- Review your local regulations regarding lead generation and data collection

## Tips for Best Results

1. **Start with specific locations** - Narrower geographic targeting = better results
2. **Test different templates** - Some may work better in different markets
3. **Verify leads manually** - Always check that extracted info is accurate
4. **Combine templates** - Run multiple searches for comprehensive coverage
5. **Export small batches first** - Test with `--results 20` before large exports
6. **Use social context** - Posts from clients show intent and timing
7. **Follow up quickly** - Social media posts about home buying/selling are time-sensitive

## Contributing

Feel free to submit issues or pull requests if you have improvements!

## License

MIT License - feel free to use and modify as needed.
