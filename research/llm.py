import json
import anthropic
from django.conf import settings


def build_research_prompt(company_name: str, context: dict) -> str:
    """Build a detailed prompt for LLM research using gathered context."""
    wiki_data = context.get('wikipedia', {})
    financial_data = context.get('financial', {})
    news_data = context.get('news', {})

    wiki_summary = wiki_data.get('data', 'N/A') if wiki_data.get('success') else 'N/A'
    
    financial_info = ''
    if financial_data.get('success'):
        fd = financial_data['data']
        financial_info = f"""
Financial Data:
- Ticker: {fd.get('ticker')}
- Current Price: ${fd.get('current_price')}
- Market Cap: ${fd.get('market_cap')}
- P/E Ratio: {fd.get('pe_ratio')}
- 52-Week High/Low: ${fd.get('fifty_two_week_high')} / ${fd.get('fifty_two_week_low')}
- Sector: {fd.get('sector')}
- Industry: {fd.get('industry')}
"""
    
    news_info = ''
    if news_data.get('success'):
        news_list = news_data['data']
        news_info = 'Recent News Headlines:\n'
        for article in news_list:
            news_info += f"- {article['title']} ({article['source']})\n"

    prompt = f"""
You are a financial research analyst. Analyze the following information about {company_name} and provide a structured investment analysis report in JSON format.

Company Overview:
{wiki_summary}

{financial_info}

{news_info}

Based on this information, provide a detailed analysis in the following JSON format:
{{
    "company_overview": "2-3 sentence overview of the company",
    "market_position": "Analysis of market position and competitive advantages",
    "financial_health": "Assessment of financial health based on provided metrics",
    "recent_developments": "Summary of recent news and developments",
    "key_risks": "Identified risks and challenges",
    "opportunities": "Growth opportunities and potential catalysts",
    "overall_sentiment": "Overall sentiment score from 1-10 (1=very negative, 10=very positive)"
}}

Ensure the response is valid JSON that can be parsed.
"""
    return prompt


def generate_research_report(company_name: str, context: dict) -> dict:
    """Generate research report using Claude API."""
    try:
        api_key = settings.CLAUDE_API_KEY
        if not api_key:
            return {'success': False, 'error': 'Claude API key not configured'}

        client = anthropic.Anthropic(api_key=api_key)
        
        system_prompt = """You are an expert financial research analyst with deep knowledge of markets, 
        industries, and companies. Provide detailed, data-driven analysis in your responses."""
        
        user_prompt = build_research_prompt(company_name, context)

        message = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {'role': 'user', 'content': user_prompt}
            ]
        )

        response_text = message.content[0].text
        
        # Parse JSON from response
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                report_data = json.loads(json_str)
            else:
                report_data = json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return raw response
            report_data = {'raw_response': response_text}

        return {
            'success': True,
            'data': report_data,
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
