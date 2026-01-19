#!/bin/bash
# Example commands for using the Real Estate Lead Finder

# Show all available search templates
python main.py --list-templates

echo "\n========================================="
echo "EXAMPLE SEARCHES"
echo "=========================================\n"

# Example 1: Find realtors (default behavior)
echo "1. Find realtors in Boston area:"
echo "   python main.py"
echo ""

# Example 2: Find people who just bought homes
echo "2. Find people who recently bought homes in Miami:"
echo "   python main.py --template home_buyers --locations 'Miami FL' 'Fort Lauderdale FL'"
echo ""

# Example 3: Find first-time home buyers
echo "3. Find first-time home buyers in Austin:"
echo "   python main.py --template first_time_buyers --locations 'Austin TX'"
echo ""

# Example 4: Find people looking to sell
echo "4. Find people looking to sell homes in Los Angeles:"
echo "   python main.py --template home_sellers --locations 'Los Angeles CA' 'San Diego CA'"
echo ""

# Example 5: Find people downsizing
echo "5. Find people downsizing in Phoenix:"
echo "   python main.py --template downsizing --locations 'Phoenix AZ' 'Scottsdale AZ'"
echo ""

# Example 6: Find people needing renovations
echo "6. Find people needing home renovations in Denver:"
echo "   python main.py --template renovation_needed --locations 'Denver CO'"
echo ""

# Example 7: Find people needing repairs
echo "7. Find people needing home repairs in Seattle:"
echo "   python main.py --template home_repair --locations 'Seattle WA'"
echo ""

# Example 8: Find people relocating
echo "8. Find people relocating to Nashville:"
echo "   python main.py --template relocating --locations 'Nashville TN'"
echo ""

# Example 9: Find real estate investors
echo "9. Find real estate investors in Dallas:"
echo "   python main.py --template investors --locations 'Dallas TX'"
echo ""

# Example 10: Find urgent sellers
echo "10. Find people who need to sell quickly:"
echo "    python main.py --template urgent_sellers --locations 'Chicago IL'"
echo ""

# Example 11: Search different social media platforms
echo "11. Search LinkedIn and Twitter instead of Instagram/Facebook:"
echo "    python main.py --template home_buyers --sites linkedin.com twitter.com --locations 'Boston MA'"
echo ""

# Example 12: Export to CSV instead of Excel
echo "12. Export results to CSV:"
echo "    python main.py --template home_sellers --locations 'San Francisco CA' --format csv"
echo ""

# Example 13: Get fewer results to save API quota
echo "13. Get only 50 results (saves API calls):"
echo "    python main.py --template home_buyers --locations 'Portland OR' --results 50"
echo ""

# Example 14: Custom output filename
echo "14. Specify custom output filename:"
echo "    python main.py --template realtors --locations 'Tampa FL' --output tampa_realtors.xlsx"
echo ""
