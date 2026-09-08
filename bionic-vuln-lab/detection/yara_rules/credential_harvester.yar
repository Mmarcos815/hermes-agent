/*
 * YARA Rule: Credential Harvester Detection
 * Detects credential stealing tools and patterns
 */

rule Keylogger_Detection {
    meta:
        description = "Detects keylogger patterns"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "credential_harvester"
    strings:
        $key_async = "GetAsyncKeyState" nocase
        $key_getkeystate = "GetKeyState" nocase
        $key_hook = "SetWindowsHookEx" nocase
        $key_hook_ll = "WH_KEYBOARD_LL" nocase
        $key_hook = "WH_KEYBOARD" nocase
        $key_log = "keylog" nocase
        $key_logger = "keylogger" nocase
        $key_hook_proc = "HookProc" nocase
        $key_hook_callback = "HookCallback" nocase
        $key_keys = "Keys." nocase
        $key_press = "KeyDown" nocase
        $key_press2 = "KeyPress" nocase
    condition:
        ($key_async and $key_log) or
        ($key_hook and $key_hook_ll) or
        ($key_hook and $key_hook_proc) or
        ($key_hook and $key_hook_callback) or
        ($key_logger and $key_press) or
        ($key_logger and $key_press2)
}

rule Credential_Dump_Tools {
    meta:
        description = "Detects credential dumping tools"
        author = "Bionic Vuln Lab"
        severity = "critical"
        category = "credential_harvester"
    strings:
        $mimikatz = "mimikatz" nocase
        $mimikatz_dll = "mimilib.dll" nocase
        $mimikatz_cmd = "mimikatz.exe" nocase
        $sekurlsa = "sekurlsa" nocase
        $lsadump = "lsadump" nocase
        $wdigest = "wdigest" nocase
        $kerberos = "kerberos" nocase
        $pypykatz = "pypykatz" nocase
        $procdump = "procdump" nocase
        $lsass = "lsass.exe" nocase
        $sam = "SAM" nocase
        $system = "SYSTEM" nocase
        $security = "SECURITY" nocase
    condition:
        $mimikatz or $mimikatz_dll or $mimikatz_cmd or
        ($sekurlsa and $lsadump) or
        ($pypykatz and $sekurlsa) or
        ($procdump and $lsass) or
        ($sam and $system and $security)
}

rule Browser_Credential_Stealer {
    meta:
        description = "Detects browser credential stealing patterns"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "credential_harvester"
    strings:
        $chrome_db = "Login Data" nocase
        $chrome_cookies = "Cookies" nocase
        $chrome_history = "History" nocase
        $chrome_webdata = "Web Data" nocase
        $firefox_logins = "logins.json" nocase
        $firefox_key4 = "key4.db" nocase
        $firefox_cookies = "cookies.sqlite" nocase
        $edge_db = "Microsoft Edge" nocase
        $sqlite = "sqlite3" nocase
        $decrypt = "CryptUnprotectData" nocase
        $nss = "NSS" nocase
        $pk11 = "PK11" nocase
    condition:
        ($chrome_db and $sqlite) or
        ($chrome_cookies and $sqlite) or
        ($firefox_logins and $firefox_key4) or
        ($edge_db and $sqlite) or
        ($decrypt and $chrome_db) or
        ($nss and $pk11)
}

rule Password_Stealer_Generic {
    meta:
        description = "Detects generic password stealing patterns"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "credential_harvester"
    strings:
        $password = "password" nocase
        $passwd = "passwd" nocase
        $credentials = "credentials" nocase
        $login = "login" nocase
        $username = "username" nocase
        $user = "user" nocase
        $email = "email" nocase
        $smtp = "smtp" nocase
        $ftp = "ftp" nocase
        $send_mail = "sendmail" nocase
        $smtp_send = "SMTP.send" nocase
        $mail_send = "mail(" nocase
        $exfil = "exfiltrate" nocase
        $exfiltration = "exfiltration" nocase
        $upload = "upload" nocase
        $post_data = "POST" nocase
        $http_post = "HttpWebRequest" nocase
    condition:
        ($password and $smtp and $send_mail) or
        ($credentials and $smtp_send) or
        ($password and $mail_send) or
        ($login and $exfil) or
        ($credentials and $exfiltration) or
        ($password and $upload and $post_data) or
        ($credentials and $http_post)
}

rule Token_Stealer {
    meta:
        description = "Detects token/session stealing patterns"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "credential_harvester"
    strings:
        $discord_token = "discord.com/api" nocase
        $discord_auth = "Authorization:" nocase
        $discord_bearer = "Bearer " nocase
        $telegram_token = "telegram.org" nocase
        $telegram_bot = "bot" nocase
        $session_token = "session_token" nocase
        $access_token = "access_token" nocase
        $refresh_token = "refresh_token" nocase
        $api_key = "api_key" nocase
        $secret_key = "secret_key" nocase
        $private_key = "private_key" nocase
        $aws_key = "AKIA" nocase
        $github_token = "ghp_" nocase
        $slack_token = "xoxb-" nocase
    condition:
        ($discord_token and $discord_auth) or
        ($discord_token and $discord_bearer) or
        ($telegram_token and $telegram_bot) or
        ($session_token and $access_token) or
        ($api_key and $secret_key) or
        ($aws_key) or
        ($github_token) or
        ($slack_token)
}
