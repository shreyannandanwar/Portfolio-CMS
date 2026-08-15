# Deployment Fix: GitHub API Rate Limiting

## Problem
Your app is hitting GitHub API rate limits (60 requests/hour for unauthenticated requests), causing errors and health check failures.

## Solution
I've updated the code to support GitHub authentication, which increases the rate limit to 5,000 requests/hour.

## Steps to Fix on Render

### 1. Create a GitHub Personal Access Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `portfolio-app`
4. Select scopes:
   - ✅ `public_repo` (or just `repo` if you want private repos too)
   - ✅ `read:user`
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't see it again!)

### 2. Add Environment Variables to Render

1. Go to your Render dashboard: https://dashboard.render.com/
2. Select your web service
3. Go to **"Environment"** tab
4. Add these environment variables:

```
GITHUB_USERNAME=shreyannandanwar
GITHUB_TOKEN=ghp_your_token_here_paste_from_step_1
```

### 3. Redeploy

After adding the environment variables, Render will automatically redeploy. 

Alternatively, manually trigger a deploy from the **"Manual Deploy"** section.

## Verification

After deployment:

1. Check logs - you should see: `"Using cached GitHub data"` instead of API errors
2. Visit your site - it should load without errors
3. The health endpoint should return 200 OK

## Cache Behavior

- GitHub data is cached for **30 days**
- This minimizes API calls even with the higher rate limit
- You can manually refresh from the admin panel if needed

## Rate Limits Reference

| Authentication | Rate Limit |
|----------------|------------|
| None (before fix) | 60/hour |
| **Token (after fix)** | **5,000/hour** |

---

## Additional Improvements Made

I also improved error handling in the GitHub service to gracefully fall back to cached data when API calls fail.
