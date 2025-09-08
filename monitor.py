import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import config
from bot.telegram_bot import TelegramNewsBot

class UsageTracker:
    def __init__(self):
        self.data_file = 'bot_usage_data.json'
        self.developer_chat_id = config.DEVELOPER_CHAT_ID
        self.data = self._load_data()
        
    def _load_data(self) -> Dict[str, Any]:
        """Load usage data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Convert string dates back to datetime objects for comparison
                    if 'last_report_date' in data:
                        data['last_report_date'] = datetime.fromisoformat(data['last_report_date'])
                    return data
            else:
                # Initialize with default data
                return {
                    'users': set(),
                    'daily_stats': {},
                    'gemini_requests': {
                        'api_calls': 0,
                        'cli_calls': 0,
                        'tokens_used': 0,
                        'errors': 0
                    },
                    'last_report_date': datetime.now() - timedelta(days=1),
                    'total_news_requests': 0,
                    'total_ai_requests': 0,
                    'total_crypto_requests': 0
                }
        except Exception as e:
            logging.error(f"Error loading usage data: {str(e)}")
            return self._get_default_data()
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Get default data structure"""
        return {
            'users': set(),
            'daily_stats': {},
            'gemini_requests': {
                'api_calls': 0,
                'cli_calls': 0,
                'tokens_used': 0,
                'errors': 0
            },
            'last_report_date': datetime.now() - timedelta(days=1),
            'total_news_requests': 0,
            'total_ai_requests': 0,
            'total_crypto_requests': 0
        }
    
    def _save_data(self):
        """Save usage data to file"""
        try:
            # Convert datetime and set objects for JSON serialization
            data_to_save = self.data.copy()
            data_to_save['users'] = list(self.data['users'])
            data_to_save['last_report_date'] = self.data['last_report_date'].isoformat()
            
            with open(self.data_file, 'w') as f:
                json.dump(data_to_save, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Error saving usage data: {str(e)}")
    
    def get_all_user_chat_ids(self) -> list:
        """Get all user chat IDs for broadcasting"""
        try:
            user_ids = []
            if isinstance(self.data['users'], list):
                for user in self.data['users']:
                    if isinstance(user, dict):
                        user_ids.append(user['id'])
                    else:
                        user_ids.append(user)
            else:
                # Handle old set format
                user_ids = list(self.data['users'])
            return user_ids
        except Exception as e:
            logging.error(f"Error getting user chat IDs: {str(e)}")
            return []


    def track_user(self, user_id: int, username: str = None):
        """Track a user interaction"""
        try:
            user_info = {
                'id': user_id,
                'username': username or f"user_{user_id}",
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            }
            
            # Check if user already exists
            existing_user = None
            for user in self.data['users']:
                if isinstance(user, dict) and user.get('id') == user_id:
                    existing_user = user
                    break
                elif user == user_id:  # Handle old format
                    existing_user = user_id
                    break
            
            if existing_user:
                if isinstance(existing_user, dict):
                    existing_user['last_seen'] = datetime.now().isoformat()
                    if username:
                        existing_user['username'] = username
            else:
                # Ensure users is always a list
                if not isinstance(self.data['users'], list):
                    self.data['users'] = []
                self.data['users'].append(user_info)
                        
                self._save_data()
        except Exception as e:
            logging.error(f"Error tracking user: {str(e)}")
            
    def track_news_request(self, user_id: int, request_type: str = "regular"):
        """Track a news request"""
        try:
            self.data['total_news_requests'] += 1
            
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.data['daily_stats']:
                self.data['daily_stats'][today] = {
                    'news_requests': 0,
                    'ai_requests': 0,
                    'crypto_requests': 0,
                    'unique_users': set()
                }
            
            self.data['daily_stats'][today]['news_requests'] += 1
            self.data['daily_stats'][today]['unique_users'].append(user_id)
            
            # Convert set to list for JSON serialization
            self.data['daily_stats'][today]['unique_users'] = list(self.data['daily_stats'][today]['unique_users'])
            
            self._save_data()
        except Exception as e:
            logging.error(f"Error tracking news request: {str(e)}")
    
    def track_ai_request(self, user_id: int, request_type: str, success: bool = True):
        """Track an AI request"""
        try:
            self.data['total_ai_requests'] += 1
            
            if request_type.lower() == 'api':
                self.data['gemini_requests']['api_calls'] += 1
            
            if not success:
                self.data['gemini_requests']['errors'] += 1
            
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.data['daily_stats']:
                self.data['daily_stats'][today] = {
                    'news_requests': 0,
                    'ai_requests': 0,
                    'crypto_requests': 0,
                    'unique_users': set()
                }
            
            self.data['daily_stats'][today]['ai_requests'] += 1
            self.data['daily_stats'][today]['unique_users'].append(user_id)
            
            # Convert set to list for JSON serialization
            self.data['daily_stats'][today]['unique_users'] = list(self.data['daily_stats'][today]['unique_users'])
            
            self._save_data()
        except Exception as e:
            logging.error(f"Error tracking AI request: {str(e)}")
    
    def track_crypto_request(self, user_id: int):
        """Track a crypto request"""
        try:
            self.data['total_crypto_requests'] += 1
            
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.data['daily_stats']:
                self.data['daily_stats'][today] = {
                    'news_requests': 0,
                    'ai_requests': 0,
                    'crypto_requests': 0,
                    'unique_users': set()
                }
            
            self.data['daily_stats'][today]['crypto_requests'] += 1
            self.data['daily_stats'][today]['unique_users'].append(user_id)
            
            # Convert set to list for JSON serialization
            self.data['daily_stats'][today]['unique_users'] = list(self.data['daily_stats'][today]['unique_users'])
            
            self._save_data()
        except Exception as e:
            logging.error(f"Error tracking crypto request: {str(e)}")
    
    def estimate_token_usage(self, text_length: int, is_input: bool = True):
        """Estimate token usage (rough calculation)"""
        # Rough estimation: 1 token ≈ 4 characters for English text
        tokens = text_length // 4
        self.data['gemini_requests']['tokens_used'] += tokens
        self._save_data()
        return tokens
    
    def should_send_report(self) -> bool:
        """Check if it's time to send daily report"""
        try:
            now = datetime.now()
            last_report = self.data.get('last_report_date', now - timedelta(days=1))
            
            if isinstance(last_report, str):
                last_report = datetime.fromisoformat(last_report)
            
            return (now - last_report).total_seconds() >= 86400  # 24 hours
        except Exception as e:
            logging.error(f"Error checking report time: {str(e)}")
            return False
    
    async def send_daily_report(self):
        """Send daily usage report to developer"""
        try:
            if not self.should_send_report():
                return
            
            bot = TelegramNewsBot()
            
            # Calculate stats
            total_users = len(self.data['users']) if isinstance(self.data['users'], list) else len(self.data['users'])
            
            # Get yesterday's stats
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            yesterday_stats = self.data['daily_stats'].get(yesterday, {
                'news_requests': 0,
                'ai_requests': 0,
                'crypto_requests': 0,
                'unique_users': []
            })
            
            # Get last 7 days stats
            week_stats = self._get_week_stats()
            
            # Create report message
            report = f"📊 *Daily Bot Usage Report*\n\n"
            report += f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            
            # Overall stats
            report += f"👥 **Total Users:** {total_users}\n"
            report += f"📰 **Total News Requests:** {self.data['total_news_requests']}\n"
            report += f"🤖 **Total AI Requests:** {self.data['total_ai_requests']}\n"
            report += f"💰 **Total Crypto Requests:** {self.data['total_crypto_requests']}\n\n"
            
            # Yesterday's activity
            report += f"📊 **Yesterday's Activity:**\n"
            report += f"• News requests: {yesterday_stats['news_requests']}\n"
            report += f"• AI requests: {yesterday_stats['ai_requests']}\n"
            report += f"• Crypto requests: {yesterday_stats['crypto_requests']}\n"
            report += f"• Active users: {len(yesterday_stats['unique_users'])}\n\n"
            
            # Gemini API usage
            gemini = self.data['gemini_requests']
            report += f"🤖 **Gemini API Usage:**\n"
            report += f"• API calls: {gemini['api_calls']}\n"
            report += f"• Estimated tokens: {gemini['tokens_used']:,}\n"
            report += f"• Errors: {gemini['errors']}\n\n"
            
            # Weekly trend
            report += f"📈 **7-Day Trend:**\n"
            report += f"• Avg daily requests: {week_stats['avg_daily_requests']:.1f}\n"
            report += f"• Avg active users: {week_stats['avg_daily_users']:.1f}\n"
            report += f"• Most active day: {week_stats['most_active_day']}\n\n"
            
            # Recent active users (last 24h)
            recent_users = self._get_recent_active_users()
            if recent_users:
                report += f"👤 **Recent Active Users:** {recent_users}\n\n"
            
            report += f"🕒 **Report Time:** {datetime.now().strftime('%H:%M:%S')}"
            
            # Send to developer
            await bot.bot.send_message(
                chat_id=self.developer_chat_id,
                text=report,
                parse_mode='Markdown'
            )
            
            # Update last report date
            self.data['last_report_date'] = datetime.now()
            self._save_data()
            
            logging.info("Daily usage report sent to developer")
            
        except Exception as e:
            logging.error(f"Error sending daily report: {str(e)}")
    
    def _get_week_stats(self) -> Dict[str, Any]:
        """Get last 7 days statistics"""
        try:
            week_stats = {
                'avg_daily_requests': 0,
                'avg_daily_users': 0,
                'most_active_day': 'N/A',
                'total_requests': 0
            }
            
            days_data = []
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                day_stats = self.data['daily_stats'].get(date, {
                    'news_requests': 0,
                    'ai_requests': 0,
                    'crypto_requests': 0,
                    'unique_users': []
                })
                
                total_requests = (day_stats['news_requests'] + 
                                day_stats['ai_requests'] + 
                                day_stats['crypto_requests'])
                
                days_data.append({
                    'date': date,
                    'requests': total_requests,
                    'users': len(day_stats['unique_users'])
                })
            
            if days_data:
                week_stats['avg_daily_requests'] = sum(d['requests'] for d in days_data) / len(days_data)
                week_stats['avg_daily_users'] = sum(d['users'] for d in days_data) / len(days_data)
                
                most_active = max(days_data, key=lambda x: x['requests'])
                week_stats['most_active_day'] = f"{most_active['date']} ({most_active['requests']} req)"
                
            return week_stats
        except Exception as e:
            logging.error(f"Error calculating week stats: {str(e)}")
            return {'avg_daily_requests': 0, 'avg_daily_users': 0, 'most_active_day': 'N/A'}
    
    def _get_recent_active_users(self) -> str:
        """Get list of recently active users"""
        try:
            if not isinstance(self.data['users'], list):
                return "N/A"
            
            recent_users = []
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for user in self.data['users']:
                if isinstance(user, dict):
                    last_seen = datetime.fromisoformat(user['last_seen'])
                    if last_seen > cutoff_time:
                        username = user.get('username', f"user_{user['id']}")
                        recent_users.append(username)
            
            return ', '.join(recent_users[:5]) if recent_users else "None"
            
        except Exception as e:
            logging.error(f"Error getting recent users: {str(e)}")
            return "Error calculating"
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old daily stats data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            keys_to_remove = []
            for date_str in self.data['daily_stats'].keys():
                if date_str < cutoff_str:
                    keys_to_remove.append(date_str)
            
            for key in keys_to_remove:
                del self.data['daily_stats'][key]
            
            if keys_to_remove:
                logging.info(f"Cleaned up {len(keys_to_remove)} old daily stats entries")
                self._save_data()
                
        except Exception as e:
            logging.error(f"Error cleaning up old data: {str(e)}")
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        return {
            'total_users': len(self.data['users']) if isinstance(self.data['users'], list) else len(self.data['users']),
            'total_requests': (self.data['total_news_requests'] + 
                             self.data['total_ai_requests'] + 
                             self.data['total_crypto_requests']),
            'gemini_requests': self.data['gemini_requests'],
            'last_report': self.data['last_report_date']
        }