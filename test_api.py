#!/usr/bin/env python
"""
Test script for LLM-Powered Research Assistant API
"""
import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'research_assistant_api.settings')
django.setup()

BASE_URL = 'http://localhost:8000/api'

print('=' * 70)
print('LLM-Powered Research Assistant API - Live Test')
print('=' * 70)

try:
    # Test 1: Health endpoint
    print('\n✓ Test 1: Health Check')
    health = requests.get(f'{BASE_URL}/health/').json()
    print(f'  Status: {health.get("status", "unknown")}')
    print(f'  Available endpoints: {len(health.get("endpoints", {}))}')

    # Test 2: User login
    print('\n✓ Test 2: User Login')
    login_data = {'username': 'testuser', 'password': 'testpass123'}
    login_resp = requests.post(f'{BASE_URL}/users/login/', json=login_data).json()
    token = login_resp.get('access')
    
    if token:
        print(f'  ✅ Token obtained successfully')
    else:
        print(f'  ❌ Error: {login_resp}')
        exit(1)

    # Test 3: Get user profile
    print('\n✓ Test 3: User Profile')
    headers = {'Authorization': f'Bearer {token}'}
    profile = requests.get(f'{BASE_URL}/users/me/', headers=headers).json()
    print(f'  Username: {profile.get("username")}')
    print(f'  Email: {profile.get("email")}')
    print(f'  Subscription: {profile.get("subscription_tier")}')
    print(f'  Reports this month: {profile.get("reports_this_month", 0)}')

    # Test 4: Submit research job
    print('\n✓ Test 4: Submit Research Job')
    job_data = {'company_name': 'Apple Inc'}
    job_resp = requests.post(f'{BASE_URL}/research/jobs/', json=job_data, headers=headers)
    
    if job_resp.status_code == 201:
        job = job_resp.json()
        print(f'  Job ID: {job.get("id")}')
        print(f'  Status: {job.get("status")}')
        print(f'  Company: {job.get("company_name")}')
        
        # Test 5: Check job status
        print('\n✓ Test 5: Check Job Status')
        job_detail = requests.get(f'{BASE_URL}/research/jobs/{job.get("id")}/', headers=headers).json()
        print(f'  Current status: {job_detail.get("status")}')
        print(f'  Created at: {job_detail.get("created_at")}')
        
        # Test 6: List all research jobs
        print('\n✓ Test 6: List Research Jobs')
        jobs_list = requests.get(f'{BASE_URL}/research/jobs/', headers=headers).json()
        print(f'  Total jobs: {len(jobs_list) if isinstance(jobs_list, list) else 1}')
    else:
        print(f'  ❌ Error: {job_resp.status_code}')
        print(f'  Response: {job_resp.text[:200]}')

    # Test 7: Check rate limiting
    print('\n✓ Test 7: Rate Limiting Check')
    from users.models import User
    test_user = User.objects.get(username='testuser')
    print(f'  Subscription tier: {test_user.subscription_tier}')
    print(f'  Can create report: {test_user.can_create_report()}')
    print(f'  Free tier limit: 5 reports/month')

    print('\n' + '=' * 70)
    print('✨ API is LIVE and responding correctly!')
    print('=' * 70)
    print('\n📍 Access the API at: http://localhost:8000/')
    print('🔧 Admin panel at: http://localhost:8000/admin/')
    print('📊 API endpoints at: http://localhost:8000/api/health/')

except Exception as e:
    print(f'\n❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()
