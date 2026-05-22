import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import yfinance as yf
from django.conf import settings
from newsapi import NewsApiClient

from reports.models import ResearchReport
from reports.search import generate_embedding, serialize_embedding_for_pgvector
from usage.models import UsageLog


WIKIPEDIA_SUMMARY_URL = 'https://en.wikipedia.org/api/rest_v1/page/summary/{title}'
REQUIRED_REPORT_KEYS = {
    'company_overview',
    'market_position',
    'financial_health',
    'recent_developments',
    'key_risks',
    'opportunities',
    'overall_sentiment',
}


def _fetch_json(url, headers=None):
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=20) as response:
        payload = response.read().decode('utf-8')
    return json.loads(payload)


def fetch_wikipedia_summary(company_name):
    try:
        payload = _fetch_json(
            WIKIPEDIA_SUMMARY_URL.format(title=quote_plus(company_name))
        )
        return payload.get('extract') or 'No Wikipedia summary available.'
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return 'No Wikipedia summary available.'


def fetch_financial_data(company_name):
    defaults = {
        'symbol': '',
        'current_price': None,
        'market_cap': None,
        'forward_pe': None,
        'fifty_two_week_high': None,
        'fifty_two_week_low': None,
    }
    try:
        search_result = yf.Search(company_name, max_results=1)
        quotes = getattr(search_result, 'quotes', []) or []
        if not quotes:
            return defaults

        symbol = quotes[0].get('symbol')
        info = yf.Ticker(symbol).info
        return {
            'symbol': symbol,
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'market_cap': info.get('marketCap'),
            'forward_pe': info.get('forwardPE') or info.get('trailingPE'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        }
    except Exception:
        return defaults


def fetch_recent_news(company_name):
    if not settings.NEWSAPI_KEY:
        return []

    try:
        client = NewsApiClient(api_key=settings.NEWSAPI_KEY)
        response = client.get_everything(
            q=company_name,
            language='en',
            sort_by='publishedAt',
            page_size=5,
        )
        articles = response.get('articles', [])
        return [
            {
                'title': article.get('title', ''),
                'source': article.get('source', {}).get('name', ''),
                'published_at': article.get('publishedAt', ''),
                'url': article.get('url', ''),
            }
            for article in articles[:5]
        ]
    except Exception:
        return []


def build_research_context(company_name):
    return {
        'company_name': company_name,
        'wikipedia_summary': fetch_wikipedia_summary(company_name),
        'financial_data': fetch_financial_data(company_name),
        'recent_news': fetch_recent_news(company_name),
    }


def _extract_json_block(text):
    cleaned = text.strip()
    if cleaned.startswith('```'):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = '\n'.join(lines[1:-1]).strip()
    return json.loads(cleaned)


def validate_report_payload(report_json):
    missing_keys = REQUIRED_REPORT_KEYS.difference(report_json.keys())
    if missing_keys:
        missing = ', '.join(sorted(missing_keys))
        raise ValueError(f'Claude response is missing required keys: {missing}')

    sentiment = report_json.get('overall_sentiment')
    try:
        sentiment_value = int(sentiment)
    except (TypeError, ValueError) as exc:
        raise ValueError('overall_sentiment must be an integer from 1 to 10.') from exc

    if sentiment_value < 1 or sentiment_value > 10:
        raise ValueError('overall_sentiment must be an integer from 1 to 10.')

    for key in REQUIRED_REPORT_KEYS.difference({'overall_sentiment'}):
        if not str(report_json.get(key, '')).strip():
            raise ValueError(f'{key} must not be empty.')

    report_json['overall_sentiment'] = sentiment_value
    return report_json


def generate_report_with_claude(company_name, context):
    if not settings.CLAUDE_API_KEY:
        raise ValueError('CLAUDE_API_KEY is not configured.')

    system_prompt = (
        'You are a senior financial research analyst. '
        'Return only strict JSON with these keys: '
        'company_overview, market_position, financial_health, '
        'recent_developments, key_risks, opportunities, overall_sentiment. '
        'overall_sentiment must be an integer from 1 to 10.'
    )
    user_prompt = (
        f'Prepare an investment-style research report for {company_name}.\n'
        f'Context:\n{json.dumps(context, indent=2)}'
    )
    body = {
        'model': settings.CLAUDE_MODEL,
        'max_tokens': 1200,
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': user_prompt}],
    }
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': settings.CLAUDE_API_KEY,
        'anthropic-version': '2023-06-01',
    }
    request = Request(
        settings.ANTHROPIC_API_URL,
        data=json.dumps(body).encode('utf-8'),
        headers=headers,
        method='POST',
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        raise ValueError(f'Claude API request failed: {exc.reason}') from exc
    except URLError as exc:
        raise ValueError(f'Claude API request failed: {exc.reason}') from exc

    content_blocks = payload.get('content', [])
    if not content_blocks:
        raise ValueError('Claude API returned an empty response.')

    report_json = validate_report_payload(_extract_json_block(content_blocks[0].get('text', '{}')))
    usage = payload.get('usage', {})
    usage_counts = {
        'input_tokens': usage.get('input_tokens', 0),
        'output_tokens': usage.get('output_tokens', 0),
    }
    return report_json, usage_counts


def build_full_report_text(report_json):
    ordered_sections = [
        ('Company Overview', report_json['company_overview']),
        ('Market Position', report_json['market_position']),
        ('Financial Health', report_json['financial_health']),
        ('Recent Developments', report_json['recent_developments']),
        ('Key Risks', report_json['key_risks']),
        ('Opportunities', report_json['opportunities']),
        ('Overall Sentiment', str(report_json['overall_sentiment'])),
    ]
    return '\n\n'.join(f'{title}\n{body}' for title, body in ordered_sections)


def create_report_from_research(job, report_json, context, token_usage):
    full_text = build_full_report_text(report_json)
    embedding = generate_embedding(full_text)
    report = ResearchReport.objects.create(
        user=job.user,
        job=job,
        company_name=job.company_name,
        company_overview=report_json['company_overview'],
        market_position=report_json['market_position'],
        financial_health=report_json['financial_health'],
        recent_developments=report_json['recent_developments'],
        key_risks=report_json['key_risks'],
        opportunities=report_json['opportunities'],
        overall_sentiment=report_json['overall_sentiment'],
        full_report_text=full_text,
        embedding=embedding,
        embedding_vector=serialize_embedding_for_pgvector(embedding),
        source_payload=context,
    )
    UsageLog.objects.create(
        user=job.user,
        report=report,
        usage_type=UsageLog.TYPE_LLM_RESEARCH,
        endpoint='/api/research/jobs/',
        method='POST',
        status_code=200,
        llm_input_tokens=token_usage.get('input_tokens', 0),
        llm_output_tokens=token_usage.get('output_tokens', 0),
        metadata={'job_id': str(job.id), 'company_name': job.company_name},
    )
    return report
