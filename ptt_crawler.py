import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime


class PTTCrawler:
    def __init__(self, board=None, keywords=None, max_pages=None, line_token=None, line_user_id=None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = 'https://www.ptt.cc'
        self.board = board
        self.keywords = keywords
        self.max_pages = max_pages
        self.output_dir = f"./ptt_{self.board}_data"
        self.cache_file = f"{self.output_dir}/article_cache.json"
        self.line_token = line_token
        self.line_user_id = line_user_id

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.article_cache = self.load_article_cache()

    def load_article_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_article_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.article_cache, f, ensure_ascii=False, indent=2)

    def is_new_article(self, article_url):
        article_id = article_url.split('/')[-1].strip()
        return article_id not in self.article_cache

    def mark_article_as_crawled(self, article_url):
        article_id = article_url.split('/')[-1].strip()
        self.article_cache[article_id] = {
            'crawled_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # LINE Messaging API 相關函數
    def send_line_notification(self, access_token, user_id, message):
        """
        Send notification using LINE Messaging API

        Parameters:
        access_token (str): Your Channel Access Token
        user_id (str): LINE user ID of the recipient
        message (str): Text message to be sent
        
        Returns:
        bool: Returns True if sending is successful, otherwise False
        """
        url = 'https://api.line.me/v2/bot/message/push'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        data = {
            'to': user_id,
            'messages': [
                {
                    'type': 'text',
                    'text': message
                }
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            print("LINE 通知發送成功！")
            return True
        else:
            print(f"LINE 通知發送失敗。狀態碼: {response.status_code}\n回應: {response.text}")
            return False

    def get_page_content(self, url):
        """Get page content"""
        try:
            response = requests.get(url, headers=self.headers, cookies={'over18': '1'})
            if response.status_code == 200:
                return response.text
            else:
                print(f"請求失敗。狀態碼: {response.status_code}\n回應: {response.text}")
                return None
        except Exception as e:
            print(f"發生錯誤: {str(e)}")
            return None

    def parse_article_list(self, content):
        """Parse article list, return article links and link to previous page"""
        soup = BeautifulSoup(content, 'html.parser')
        articles = []

        # Get all article links
        for div in soup.find_all('div', class_='r-ent'):
            title_div = div.find('div', class_='title')
            if title_div:
                link = title_div.find('a')
                if link:
                    title = link.text.strip()
                    url = self.base_url + link['href']

                    # Check if title contains all keywords
                    all_keywords_present = True

                    for keyword in self.keywords:
                        # Check keywords (case-insensitive for English)
                        if keyword.lower() not in title.lower():
                            all_keywords_present = False
                            break
                    
                    if all_keywords_present:
                        articles.append({
                            'title': title,
                            'url': url
                        })

        # Get link to previous page
        prev_page_link = soup.find('a', string='‹ 上頁')
        prev_page_url = self.base_url + prev_page_link['href'] if prev_page_link else None

        return articles, prev_page_url

    def parse_article_content(self, content):
        """Parse article content"""
        soup = BeautifulSoup(content, 'html.parser')
        article_data = {}

        # Get main content
        main_content = soup.find('div', id='main-content')
        if main_content:
            # Extract data like author, time
            metalines = main_content.find_all('div', class_='article-metaline')
            for meta in metalines:
                meta_name = meta.find('span', class_='article-meta-tag')
                meta_value = meta.find('span', class_='article-meta-value')
                if meta_name and meta_value:
                    key = meta_name.text.strip()
                    value = meta_value.text.strip()
                    if key != '標題': # Skip title field as we already have it
                        article_data[key] = value

        return article_data

    def crawl_articles(self):
        """Crawl articles until finding already pushed articles or reaching max pages, and filter titles containing keywords"""
        current_url = f"{self.base_url}/bbs/{self.board}/index.html"
        keyword_articles = []  # Store articles matching keywords
        new_articles_count = 0
        total_articles_checked = 0
        page_count = 0
        found_old_article = False

        while page_count < self.max_pages and not found_old_article:
            page_count += 1
            print(f"正在爬取第 {page_count} 頁...")
            content = self.get_page_content(current_url)
            if not content:
                break

            filtered_articles, prev_page_url = self.parse_article_list(content)

            # If no articles matching keywords on this page, continue to next page
            if not filtered_articles:
                if prev_page_url:
                    current_url = prev_page_url
                    time.sleep(2)
                    continue
                else:
                    break

            total_articles_checked += len(filtered_articles)

            for idx, article in enumerate(filtered_articles):
                # Check if this is a new article
                if self.is_new_article(article['url']):
                    print(f"  發現新文章 ({page_count}-{idx+1}): {article['title']}")
                    article_content = self.get_page_content(article['url'])

                    if article_content:
                        article_data = self.parse_article_content(article_content)
                        article.update(article_data)
                        keyword_articles.append(article)

                        self.mark_article_as_crawled(article['url'])

                        # Send LINE notification
                        message = f"\U0001F4E2 發現新文章\n"
                        message += f"\U0001F4DD 標題：{article['title']}\n\U0001F517 連結：{article['url']}"

                        if '時間' in article_data:
                            message += f"\n\U0001F552 發布時間：{article_data['時間']}"
                        if '作者' in article_data:
                            message += f"\n\U0000270D\U0000FE0F 作者：{article_data['作者']}"

                        self.send_line_notification(self.line_token, self.line_user_id, message)
                        new_articles_count += 1
                        
                    time.sleep(2)
                else:
                    print(f"  跳過已爬取的文章: {article['title']}")
                    found_old_article = True
                    break

            if found_old_article or not prev_page_url:
                break

            current_url = prev_page_url

            time.sleep(2)

        if not content:
            # Send LINE notification
            message = f"\U0001F6A8 爬蟲失敗"
            self.send_line_notification(self.line_token, self.line_user_id, message)
            return


        self.save_article_cache()

        if keyword_articles:
            # Same keyword set (different order) stored in the same JSON file
            sorted_keywords = sorted([k.lower() for k in self.keywords])
            keywords_filename = "_".join(sorted_keywords)
            timestamp = datetime.now().strftime("%Y%m")
            filename = f"{self.output_dir}/ptt_{self.board}_{keywords_filename}_{timestamp}.json"

            # Save results as JSON file
            data = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            data.extend(keyword_articles)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"結果已保存至 {filename}")

        print(f"\n爬蟲完成，共檢查了 {total_articles_checked} 篇文章，其中發現 {new_articles_count} 篇新文章。")
        print(f"爬取了 {page_count} 頁，{'找到舊文章而停止。' if found_old_article else '達到最大頁數或沒有更多頁面。'}")

        return keyword_articles

def main():
    # Set parameters
    board = 'Drama-Ticket'
    keywords = ['售票', 'gracie']
    max_pages = 30
    # Load environment variables from .env file
    load_dotenv()
    LINE_TOKEN = os.environ.get("LINE_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    
    # Check if environment variables are set
    if not LINE_TOKEN or not LINE_USER_ID:
        print("錯誤：未設定 LINE_TOKEN 或 LINE_USER_ID 環境變數")
        return 
    
    crawler = PTTCrawler(
        board=board,
        keywords=keywords,
        max_pages=max_pages,
        line_token=LINE_TOKEN,
        line_user_id=LINE_USER_ID
    )
    crawler.crawl_articles()

if __name__ == "__main__":
    main()
