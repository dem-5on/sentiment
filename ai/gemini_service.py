import google.generativeai as genai
import logging
import config
from typing import List, Dict, Any

class GeminiService:
    def __init__(self):
        """Initialize Gemini AI service"""
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("Gemini AI service initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Gemini AI: {str(e)}")
            raise
    
    def summarize_individual_articles(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Summarize each article individually
        Returns: List of news items with AI summaries added
        """
        summarized_articles = []
        
        for i, article in enumerate(news_items, 1):
            try:
                logging.info(f"Summarizing article {i}/{len(news_items)}: {article['title'][:50]}...")
                
                # Create prompt for individual article
                prompt = self._create_individual_prompt(article)
                
                # Generate summary
                response = self.model.generate_content(prompt)
                ai_summary = response.text
                
                # Add AI summary to article
                article_copy = article.copy()
                article_copy['ai_summary'] = ai_summary
                summarized_articles.append(article_copy)
                
                logging.info(f"Successfully summarized article {i}")
                
            except Exception as e:
                logging.error(f"Error summarizing article {i}: {str(e)}")
                # Add original article without AI summary
                article_copy = article.copy()
                article_copy['ai_summary'] = "⚠️ AI summary unavailable for this article."
                summarized_articles.append(article_copy)
        
        return summarized_articles
    
    def summarize_combined_articles(self, news_items: List[Dict[str, Any]]) -> str:
        """
        Create a combined summary of all articles
        Returns: Single combined AI summary string
        """
        try:
            logging.info(f"Creating combined summary for {len(news_items)} articles...")
            
            # Create prompt for combined summary
            prompt = self._create_combined_prompt(news_items)
            
            # Generate combined summary
            response = self.model.generate_content(prompt)
            combined_summary = response.text
            
            logging.info("Successfully created combined summary")
            return combined_summary
            
        except Exception as e:
            logging.error(f"Error creating combined summary: {str(e)}")
            return "⚠️ Unable to generate combined AI summary at this time."
    
    def _create_individual_prompt(self, article: Dict[str, Any]) -> str:
        """Create prompt for individual article summarization"""
        prompt = f"""
Please analyze the following news article and provide a comprehensive summary organized into exactly 3 sections:

**ARTICLE TO ANALYZE:**
Title: {article['title']}
Content: {article['summary']}
Source: {article['source']}
Keyword: {article['keyword']}

**LINKS**
Articles with urls, if any, open the urls fetch the content of the page for more context.

**INSTRUCTIONS:**
Create a summary with these 3 clearly separated sections:

1. **🔍 KEY FACTS:** List the main factual points, events, and important details from the article.

2. **📈 MARKET IMPACTS:** Analyze potential effects on markets, economy, industries, or financial implications. Indicate if positive impact or negative impact.

3. **🏢 BUSINESS INSIGHTS:** Provide business-focused analysis, strategic implications, and what this means for companies/sectors.

**FORMAT REQUIREMENTS:**
- Use the exact section headers shown above with emojis
- Keep each section concise but informative (2-4 bullet points each)
- Use bullet points (•) for clarity
- Be factual and avoid speculation
- If a section doesn't apply, briefly state "No significant impacts identified"

**RESPONSE FORMAT**
Please provide the summary in the following format:
1. 🔍 KEY FACTS:
• [Fact 1]
• [Fact 2]
...
2. 📈 MARKET IMPACTS:
• [Impact 1]
• [Impact 2]
...
3. 🏢 BUSINESS INSIGHTS:
• [Insight 1]
• [Insight 2]
...
4. OVERALL SENTIMENT:
• [Positive/Negative/Neutral]

**ADDITIONAL NOTES:**
- Focus on the most important insights
- Highlight any contradictions or complementary information between articles if applicable


**READ MORE**
- If any article have URLs, add them to the "Read More" section at the end of the summary with the sources.
- NOTE: If the article does not have a URL, skip the "Read More" section.


Please provide the analysis:
"""
        return prompt
    
    def _create_combined_prompt(self, news_items: List[Dict[str, Any]]) -> str:
        """Create prompt for combined articles summarization"""
        
        # Prepare articles text
        articles_text = ""
        for i, article in enumerate(news_items, 1):
            articles_text += f"""
ARTICLE {i}:
Title: {article['title']}
Content: {article['summary']}
Source: {article['source']}
Keyword: {article['keyword']}
---
"""
        
        prompt = f"""
Please analyze the following {len(news_items)} news articles and provide a comprehensive combined summary organized into exactly 3 sections:

**ARTICLES TO ANALYZE:**
{articles_text}

**LINKS**
Articles with urls, if any, open the urls fetch the content of the page for more context.


**INSTRUCTIONS:**
Create a combined summary that synthesizes information from all articles into these 3 clearly separated sections:

1. **🔍 KEY FACTS:** Summarize the most important factual points, events, and developments across all articles. Group related information together.

2. **📈 MARKET IMPACTS:** Analyze the collective potential effects on markets, economy, industries, or financial implications from all the news.

3. **🏢 BUSINESS INSIGHTS:** Provide business-focused analysis of the overall trends, strategic implications, and what these developments mean for companies/sectors collectively.

**FORMAT REQUIREMENTS:**
- Use the exact section headers shown above with emojis
- Keep each section concise but comprehensive (3-6 bullet points each)
- Use bullet points (•) for clarity
- Identify patterns and connections between articles
- Be factual and avoid speculation
- If a section has limited relevant information, briefly state why

**ADDITIONAL NOTES:**
- Focus on the bigger picture and trends
- Highlight any contradictions or complementary information between articles
- Prioritize the most significant insights

**RESPONSE FORMAT**
Please provide the summary in the following format:
1. 🔍 KEY FACTS:
• [Fact 1]
• [Fact 2]
...
2. 📈 MARKET IMPACTS:
• [Impact 1]
• [Impact 2]
...
3. 🏢 BUSINESS INSIGHTS:
• [Insight 1]
• [Insight 2]
...
4. OVERALL SENTIMENT:
• [Positive/Negative/Neutral]

**ADDITIONAL NOTES:**
- Focus on the most important insights
- Highlight any contradictions or complementary information between articles if applicable

**READ MORE**
- If any article have URLs, add them to the "Read More" section at the end of the summary with the sources.
- NOTE: If the article does not have a URL, skip the "Read More" section.


Please provide the combined analysis:
"""
        return prompt
    
    def test_connection(self) -> bool:
        """Test if Gemini AI service is working"""
        try:
            response = self.model.generate_content("Hello, please respond with 'Connection successful'")
            return "successful" in response.text.lower()
        except Exception as e:
            logging.error(f"Gemini connection test failed: {str(e)}")
            return False