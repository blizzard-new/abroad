# Step 2: create deploy\selfhost\.env with freshly generated secrets (random, made on this computer, never leave it).
# Safe to run again: existing secrets are kept; only the values you pass are changed.
#   powershell -ExecutionPolicy Bypass -File .\02-generate-secrets.ps1 -Domain app.example.com -AcmeEmail you@gmail.com `
#       -ContactEmail you@gmail.com -AdminEmails you@gmail.com
param(
    [Parameter(Mandatory = $true)][string]$Domain,
    [Parameter(Mandatory = $true)][string]$AcmeEmail,
    [string]$ContactEmail = '',
    [string]$AdminEmails = '',
    [switch]$AskGoogle,       # type the Google sign-in client ID and secret now (hidden input); otherwise edit .env later
    [switch]$UseExistingKeys  # type the document-encryption key from the old server (Render) instead of making a new one
)
. "$PSScriptRoot\lib.ps1"

if ($Domain -notmatch '^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$') { throw "Domain '$Domain' does not look like a host name (example: app.example.com)." }
if ($AcmeEmail -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') { throw "AcmeEmail '$AcmeEmail' does not look like an e-mail address." }

$e = Read-EnvFile
$fresh = ($e.Count -eq 0)

function Keep([string]$Key, [scriptblock]$Make) {
    if (-not $e.Contains($Key) -or -not $e[$Key]) { $e[$Key] = (& $Make) }
}

Write-Step 'Secrets'
$e['DOMAIN'] = $Domain
$e['ACME_EMAIL'] = $AcmeEmail
Keep 'DB_PASSWORD'  { New-RandomHex 24 }
Keep 'JWT_SECRET'   { New-RandomHex 32 }
# the two keys are signed with JWT_SECRET; regenerate them only if the secret changed (or they are missing)
$e['ANON_KEY']         = New-SupabaseJwt $e['JWT_SECRET'] 'anon'
$e['SERVICE_ROLE_KEY'] = New-SupabaseJwt $e['JWT_SECRET'] 'service_role'
Keep 'VAULT_MASTER_KEY'          { ConvertTo-Base64Url (New-RandomBytes 32) }
Keep 'EMAIL_VERIFICATION_SECRET' { ConvertTo-Base64Url (New-RandomBytes 32) }
if ($ContactEmail) { $e['CONTACT_EMAIL'] = $ContactEmail } elseif (-not $e.Contains('CONTACT_EMAIL')) { $e['CONTACT_EMAIL'] = '' }
if ($AdminEmails)  { $e['ADMIN_EMAILS']  = $AdminEmails }  elseif (-not $e.Contains('ADMIN_EMAILS'))  { $e['ADMIN_EMAILS'] = '' }
if (-not $e.Contains('GOOGLE_OAUTH_CLIENT_ID'))     { $e['GOOGLE_OAUTH_CLIENT_ID'] = '' }
if (-not $e.Contains('GOOGLE_OAUTH_CLIENT_SECRET')) { $e['GOOGLE_OAUTH_CLIENT_SECRET'] = '' }
if (-not $e.Contains('APP_WORKERS')) { $e['APP_WORKERS'] = '4' }
if (-not $e.Contains('APP_THREADS')) { $e['APP_THREADS'] = '16' }
if (-not $e.Contains('APP_CATALOGUE_CONCURRENCY')) { $e['APP_CATALOGUE_CONCURRENCY'] = '2' }

if ($UseExistingKeys) {
    # Saved form drafts and uploaded documents are encrypted with this key. If the old server already holds some,
    # only the same key can read them on the new one. (The old value is EXCHANGE_VAULT_MASTER_KEY in Render's Environment tab.)
    $secureKey = Read-Host 'EXCHANGE_VAULT_MASTER_KEY from the old server (hidden)' -AsSecureString
    $old = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)).Trim()
    if ($old.StartsWith('base64:')) { $old = $old.Substring(7) }
    $padded = $old.Replace('-', '+').Replace('_', '/'); while ($padded.Length % 4 -ne 0) { $padded += '=' }
    try { $raw = [Convert]::FromBase64String($padded) } catch { throw 'That is not a base64url value.' }
    if ($raw.Length -ne 32) { throw ('The key must decode to exactly 32 bytes (this one is {0}).' -f $raw.Length) }
    $e['VAULT_MASTER_KEY'] = $old
    Write-Ok 'using the existing document-encryption key'
}

if ($AskGoogle) {
    $e['GOOGLE_OAUTH_CLIENT_ID'] = (Read-Host 'Google OAuth client ID').Trim()
    $secure = Read-Host 'Google OAuth client secret (hidden)' -AsSecureString
    $e['GOOGLE_OAUTH_CLIENT_SECRET'] = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
}

Write-EnvFile $e
if ($fresh) { Write-Ok 'created deploy\selfhost\.env' } else { Write-Ok 'updated deploy\selfhost\.env (existing secrets kept)' }

Write-Step 'IMPORTANT: back up the secrets file'
Write-Host '  VAULT_MASTER_KEY encrypts every document users upload. If this file is lost, those documents can never be read again.'
Write-Host '  DB_PASSWORD / JWT_SECRET are baked into the database once it exists; do not regenerate them on a running system.'
Write-Host ("  Copy {0} into your password manager (as a secure note) now. Never e-mail it or paste it into chat." -f $script:EnvFile) -ForegroundColor Yellow
if (-not $e['GOOGLE_OAUTH_CLIENT_ID'] -or -not $e['GOOGLE_OAUTH_CLIENT_SECRET']) {
    Write-Warn 'Google sign-in is not configured yet (client ID / secret empty): the sign-in button stays grey. Re-run with -AskGoogle when you have them.'
}
if (-not $e['CONTACT_EMAIL']) { Write-Warn 'CONTACT_EMAIL is empty: /privacy and /terms will say no contact address is set.' }
