# API Quota Management

## Google Gemini API Quota Issues

The Google Gemini API has strict rate limits and quotas, especially for the free tier:

### Free Tier Limits:
- **Requests per day**: Limited (varies by model)
- **Requests per minute**: Limited (varies by model)  
- **Input tokens per minute**: Limited (varies by model)

### Common Error Messages:
```
429 You exceeded your current quota, please check your plan and billing details
```

### Solutions Implemented:

1. **Disabled Warmup**: Server no longer makes test API calls during startup
2. **Disabled Validation**: API key validation no longer makes actual API calls
3. **Rate Limiting**: Added rate limiter (5 requests per minute per provider/model)
4. **Reduced Retries**: Reduced retry attempts from 3 to 2
5. **Caching**: Responses are cached for 30 minutes to reduce API calls

### Recommendations:

1. **Use gemini-1.5-flash**: This model has higher quotas than gemini-1.5-pro
2. **Monitor Usage**: Check your Google AI Studio dashboard for quota usage
3. **Upgrade Plan**: Consider upgrading to a paid plan for higher limits
4. **Implement Backoff**: The system now has exponential backoff for retries

### Testing:
- Server starts without making API calls
- Only makes API calls when user sends actual chat messages
- Rate limiting prevents excessive usage
- Caching reduces redundant API calls

### Emergency Fallback:
If quota is exceeded, the system will show a fallback message instead of crashing.
