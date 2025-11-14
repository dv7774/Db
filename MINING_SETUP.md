# XYO Mining Automation Setup Guide

This guide will help you set up and configure the automated XYO mining workflow in your repository.

## Prerequisites

- GitHub repository with Actions enabled
- Etherscan API key
- XYO wallet address

## Step 1: Set Up Required Secrets

The mining automation requires two secrets to be configured in your repository:

1. Go to your repository on GitHub
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

### ETHERSCAN_API_KEY
- **Name:** `ETHERSCAN_API_KEY`
- **Value:** Your Etherscan API key
- **How to get it:**
  1. Visit [https://etherscan.io/apis](https://etherscan.io/apis)
  2. Sign up for a free account if you don't have one
  3. Navigate to "API Keys" in your account dashboard
  4. Create a new API key
  5. Copy the key and paste it as the secret value

### XYO_WALLET_ADDRESS
- **Name:** `XYO_WALLET_ADDRESS`
- **Value:** Your XYO wallet address (0x...)
- **Format:** Must be a valid Ethereum address starting with `0x`
- **Example:** `0x1234567890abcdef1234567890abcdef12345678`

## Step 2: Trigger the Workflow

Once secrets are configured, the workflow will automatically run on every push to the repository.

### Manual Trigger (Optional)
You can also trigger the workflow manually:
1. Go to **Actions** tab in your repository
2. Select "CI/CD Pipeline with Mining" workflow
3. Click **Run workflow**
4. Select the branch and click **Run workflow**

### Test the Setup
To verify your setup, make a small commit:
```bash
git commit --allow-empty -m "Test mining workflow"
git push
```

## Step 3: Monitor the Workflow

1. Navigate to the **Actions** tab in your repository
2. You should see a workflow run for "CI/CD Pipeline with Mining"
3. Click on the workflow run to see details
4. The workflow has three jobs that run in sequence:
   - **hello-world**: Verifies basic setup
   - **mining-test**: Runs the mining automation for 1 minute
   - **build**: Builds the Next.js application

### Job Status Indicators
- ✅ Green checkmark: Job completed successfully
- ❌ Red X: Job failed (check logs for details)
- 🟡 Yellow circle: Job is running
- ⚪ Gray circle: Job is queued or waiting

## Step 4: Review Mining Test Logs

To review the logs from the mining automation:

1. Click on the workflow run in the Actions tab
2. Click on the **mining-test** job
3. Expand the "Run mining automation test" step
4. You should see output like:

```
Starting XYO mining automation
Wallet Address: 0x12345678...12345678
Duration: 1 minute(s)
--------------------------------------------------
[HH:MM:SS] Mining iteration 1
  ⛏️  Processing block data...
  📊 Checking wallet balance via Etherscan API...
  ⏱️  Elapsed time: 0.0s / 60s
...
--------------------------------------------------
✅ Mining automation completed successfully
Total iterations: 6
Total time: 60.0s
```

### Interpreting the Logs

- **Wallet Address**: Shows partial wallet address for verification
- **Mining iterations**: Number of mining cycles completed
- **Elapsed time**: Progress through the test duration
- **Total time**: Actual time taken for the test

### Common Issues

#### ❌ Error: Missing required environment variables
**Solution**: Secrets are not configured correctly. Return to Step 1 and verify both secrets are set.

#### ❌ Build fails after mining test
**Solution**: This is expected if external resources (like Google Fonts) are blocked. The mining test itself is independent and should complete successfully.

#### ⚠️ Mining test takes longer than expected
**Solution**: The script runs for the specified duration (1 minute by default). If it takes significantly longer, check the logs for any delays or errors.

## Customizing the Mining Duration

To change the mining test duration, edit `.github/workflows/main.yml`:

```yaml
- name: Run mining automation test
  run: |
    python mining_automation.py --duration-minutes 5  # Change to desired duration
```

## Running the Script Locally

You can test the mining script locally before pushing:

```bash
# Set environment variables
export ETHERSCAN_API_KEY="your_api_key_here"
export XYO_WALLET_ADDRESS="0x1234567890abcdef1234567890abcdef12345678"

# Run the script
python mining_automation.py --duration-minutes 1
```

## Monitoring and Alerts

### Enable Email Notifications
1. Go to your GitHub profile → **Settings** → **Notifications**
2. Under "Actions", ensure "Send notifications for failed workflows only" is checked
3. You'll receive emails if the mining test or any job fails

### Workflow Status Badge
Add a status badge to your README to show the workflow status:

```markdown
![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/main.yml/badge.svg)
```

## Security Best Practices

✅ **DO:**
- Keep your API keys and wallet addresses secret
- Use GitHub Secrets for sensitive data
- Regularly rotate your API keys
- Monitor your wallet for unexpected activity

❌ **DON'T:**
- Commit API keys or wallet addresses to the repository
- Share your secrets with others
- Use production wallets for testing

## Troubleshooting

If you encounter issues:

1. **Check secrets are set correctly** in repository settings
2. **Review workflow logs** in the Actions tab
3. **Verify API key is valid** on Etherscan
4. **Ensure wallet address format** is correct (starts with 0x, 42 characters)

## Next Steps

- Monitor your first few workflow runs to ensure everything works correctly
- Adjust the mining duration as needed for your use case
- Consider adding branch filters to run only on specific branches
- Set up notifications for workflow failures

## Support

For issues related to:
- **GitHub Actions**: Check the Actions tab logs
- **Etherscan API**: Visit [Etherscan API documentation](https://docs.etherscan.io/)
- **XYO Network**: Visit [XYO Network documentation](https://docs.xyo.network/)
