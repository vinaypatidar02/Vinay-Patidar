#!/usr/bin/env node
/**
 * gmail_auth.js — Gmail OAuth Setup for Claude Code
 * ==================================================
 * LEARNING NOTE — Why do we need this?
 *
 * Gmail MCP in Claude.ai works via the browser OAuth flow Anthropic
 * manages. But Claude Code runs locally in your terminal — it can't
 * do browser OAuth automatically. This script does it once, saves
 * the refresh token to .env, and then Claude Code can use Gmail
 * from that point forward without re-authenticating.
 *
 * You only need to run this ONCE. The refresh token doesn't expire
 * unless you revoke it from your Google account.
 *
 * Prerequisites:
 *   1. Go to https://console.cloud.google.com
 *   2. Create a project (or use existing)
 *   3. Enable Gmail API
 *   4. Create OAuth 2.0 credentials (Desktop app type)
 *   5. Copy Client ID and Client Secret to .env
 *
 * Then run:
 *   node scripts/gmail_auth.js
 *
 * It will open a browser URL. Paste the code back into the terminal.
 * Your .env will be updated with the refresh token automatically.
 *
 * SCOPES requested (read-only):
 *   gmail.readonly — read emails (for status updates)
 *   gmail.labels   — add "job-processed" label to handled emails
 */

const https = require('https');
const readline = require('readline');
const fs = require('fs');
const path = require('path');

// Load .env
const envPath = path.join(__dirname, '..', '.env');
if (!fs.existsSync(envPath)) {
  console.error('ERROR: .env file not found. Copy .env.example to .env first.');
  process.exit(1);
}

const env = {};
fs.readFileSync(envPath, 'utf8').split('\n').forEach(line => {
  const [k, ...v] = line.split('=');
  if (k && !k.startsWith('#')) env[k.trim()] = v.join('=').trim();
});

const CLIENT_ID     = env['GMAIL_CLIENT_ID'];
const CLIENT_SECRET = env['GMAIL_CLIENT_SECRET'];

if (!CLIENT_ID || !CLIENT_SECRET) {
  console.error(`
ERROR: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in .env

Steps to get them:
  1. Go to https://console.cloud.google.com
  2. Create project → APIs & Services → Enable Gmail API
  3. Credentials → Create OAuth 2.0 Client ID → Desktop app
  4. Copy Client ID and Client Secret into .env
  `);
  process.exit(1);
}

const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/gmail.labels',
  'https://www.googleapis.com/auth/gmail.modify',  // needed to add labels
].join(' ');

const REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob';  // copy-paste flow

const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
  `client_id=${encodeURIComponent(CLIENT_ID)}&` +
  `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
  `response_type=code&` +
  `scope=${encodeURIComponent(SCOPES)}&` +
  `access_type=offline&` +
  `prompt=consent`;

console.log('\n=== Gmail OAuth Setup ===\n');
console.log('1. Open this URL in your browser:\n');
console.log('   ' + authUrl);
console.log('\n2. Sign in with the Gmail account you want to monitor');
console.log('3. Click Allow');
console.log('4. Copy the authorisation code shown\n');

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
rl.question('Paste the authorisation code here: ', (code) => {
  rl.close();
  code = code.trim();

  // Exchange code for tokens
  const postData = new URLSearchParams({
    code,
    client_id:     CLIENT_ID,
    client_secret: CLIENT_SECRET,
    redirect_uri:  REDIRECT_URI,
    grant_type:    'authorization_code',
  }).toString();

  const req = https.request({
    hostname: 'oauth2.googleapis.com',
    path:     '/token',
    method:   'POST',
    headers: {
      'Content-Type':   'application/x-www-form-urlencoded',
      'Content-Length': Buffer.byteLength(postData),
    },
  }, (res) => {
    let body = '';
    res.on('data', chunk => body += chunk);
    res.on('end', () => {
      const tokens = JSON.parse(body);
      if (tokens.error) {
        console.error('\nERROR:', tokens.error, tokens.error_description);
        process.exit(1);
      }

      // Update .env with the refresh token
      let envContent = fs.readFileSync(envPath, 'utf8');
      envContent = envContent
        .replace(/^GMAIL_REFRESH_TOKEN=.*/m, `GMAIL_REFRESH_TOKEN=${tokens.refresh_token}`)
        .replace(/^GMAIL_ACCESS_TOKEN=.*/m,  `GMAIL_ACCESS_TOKEN=${tokens.access_token}`);

      fs.writeFileSync(envPath, envContent, 'utf8');

      console.log('\n✓ Success! Tokens saved to .env');
      console.log('  Refresh token (long-lived, saved): set');
      console.log('  Access token  (1hr, saved):        set');
      console.log('\nGmail auth is complete. Claude Code can now use Gmail MCP.');
      console.log('Run ./scripts/setup_stage2.sh to verify everything is working.\n');
    });
  });

  req.on('error', e => { console.error('Request error:', e); process.exit(1); });
  req.write(postData);
  req.end();
});
