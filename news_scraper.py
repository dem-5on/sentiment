import feedparser
import logging
from datetime import datetime
import re
from urllib.parse import urlparse

class NewsScraper:
    def __init__(self):
        self.scraped_urls = set()
        
    def scrape_news(self, keywords, rss_feeds, max_results=5):
        """Scrape news from RSS feeds based on keywords"""
        all_news = []
        target_count = max_results * len(keywords)
        
        for feed_url in rss_feeds:
            try:
                # Stop if we have enough news
                if len(all_news) >= target_count:
                    break
                
                logging.info(f"Fetching RSS feed: {feed_url}")
                
                # Parse RSS feed
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    logging.warning(f"RSS feed may have issues: {feed_url}")
                
                # Process feed entries
                feed_news = []
                for entry in feed.entries[:max_results * 3]:  # Limit entries to check
                    
                    news_item = self._process_entry(entry, keywords, feed_url)
                    if news_item and news_item['url'] not in self.scraped_urls:
                        feed_news.append(news_item)
                        self.scraped_urls.add(news_item['url'])
                        
                        # Stop if we have enough from this feed
                        if len(feed_news) >= max_results:
                            break
                
                # Sort by published date (most recent first)
                feed_news.sort(key=lambda x: x['published_date'], reverse=True)
                all_news.extend(feed_news[:max_results])
                
                logging.info(f"Found {len(feed_news)} relevant news items from {self._get_domain(feed_url)}")
                
            except Exception as e:
                logging.error(f"Error fetching RSS feed {feed_url}: {str(e)}")
                continue
        
        # Sort all news by published date (most recent first)
        all_news.sort(key=lambda x: x['published_date'], reverse=True)
        final_results = all_news[:target_count]
        
        logging.info(f"Total news items found: {len(final_results)}")
        return final_results
    
    def _process_entry(self, entry, keywords, feed_url):
        """Process RSS entry and check if it matches keywords"""
        try:
            title = entry.get('title', '').strip()
            summary = entry.get('summary', '') or entry.get('description', '')
            link = entry.get('link', '').strip()
            
            if not title or not link:
                return None
            
            # Clean up summary
            summary = re.sub(r'<[^>]+>', '', summary)  # Remove HTML tags
            summary = ' '.join(summary.split())  # Clean whitespace
            
            # Skip if title is too short
            if len(title) < 10:
                return None
                
            # Check if any keyword is in title or summary
            combined_text = f"{title} {summary}".lower()
            
            matched_keyword = None
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    matched_keyword = keyword
                    break
            
            if not matched_keyword:
                return None
            
            # Get published date
            published_date = self._parse_date(entry)
            
            # Create summary (limit to 200 chars)
            if summary:
                clean_summary = summary[:200] + "..." if len(summary) > 200 else summary
            else:
                clean_summary = "Click to read more..."
            
            return {
                'title': title,
                'summary': clean_summary,
                'url': link,
                'keyword': matched_keyword,
                'published_date': published_date,
                'source': self._get_domain(feed_url),
                'scraped_at': datetime.now()
            }
                    
        except Exception as e:
            logging.error(f"Error processing RSS entry: {str(e)}")
            return None
    
    def _parse_date(self, entry):
        """Parse published date from RSS entry"""
        try:
            # Try different date fields
            date_str = entry.get('published') or entry.get('updated') or entry.get('pubDate')
            
            if date_str:
                # feedparser usually parses dates automatically
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    return datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    return datetime(*entry.updated_parsed[:6])
            
            # Fallback to current time if no date found
            return datetime.now()
            
        except Exception as e:
            logging.error(f"Error parsing date: {str(e)}")
            return datetime.now()
    
    def _get_domain(self, url):
        """Extract domain name from URL"""
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return "Unknown"
    
    def clear_cache(self):
        """Clear old scraped URLs"""
        self.scraped_urls.clear()