import json
import requests
import yfinance as yf
from datetime import datetime
import wikipedia
from django.conf import settings


def fetch_wikipedia_summary(company_name: str) -> dict:
    """Fetch company summary from Wikipedia."""
    try:
        summary = wikipedia.summary(company_name, auto_suggest=True, sentences=5)
        return {'success': True, 'data': summary}
    except wikipedia.exceptions.DisambiguationError as e:
        return {'success': False, 'error': f'Disambiguation: {e.options[:3]}'}
    except wikipedia.exceptions.PageError:
        return {'success': False, 'error': 'Page not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def fetch_yfinance_data(company_name: str, ticker: str = None) -> dict:
    """Fetch financial data from Yahoo Finance."""
    try:
        # If ticker not provided, try common ones or search
        if not ticker:
            ticker_map = {
                'Tesla': 'TSLA',
                'Apple': 'AAPL',
                'Google': 'GOOGL',
                'Microsoft': 'MSFT',
                'Amazon': 'AMZN',
                'Meta': 'META',
                'OpenAI': 'N/A',  # OpenAI is private
            }
            ticker = ticker_map.get(company_name, company_name[:3].upper())
        
        if ticker == 'N/A':
            return {'success': False, 'error': f'{company_name} is a private company, no public ticker'}

        stock = yf.Ticker(ticker)
        info = stock.info

        financial_data = {
            'ticker': ticker,
            'current_price': info.get('currentPrice'),
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'avg_volume': info.get('averageVolume'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
        }
        return {'success': True, 'data': financial_data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def fetch_newsapi_data(company_name: str) -> dict:
    """Fetch news headlines from NewsAPI."""
    try:
        api_key = settings.NEWSAPI_KEY
        if not api_key:
            return {'success': False, 'error': 'NewsAPI key not configured'}

        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': company_name,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 5,
            'apiKey': api_key,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        articles = response.json().get('articles', [])
        news_data = [
            {
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'published_at': article['publishedAt'],
                'source': article['source']['name'],
            }
            for article in articles[:5]
        ]
        return {'success': True, 'data': news_data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def gather_research_context(company_name: str) -> dict:
    """Gather all research context from multiple sources."""
    context = {
        'company_name': company_name,
        'timestamp': datetime.utcnow().isoformat(),
        'wikipedia': fetch_wikipedia_summary(company_name),
        'financial': fetch_yfinance_data(company_name),
        'news': fetch_newsapi_data(company_name),
    }
    return context
