/*
 * YARA Rule: Cryptocurrency Miner Detection
 * Detects crypto mining software and scripts
 */

rule XMRig_Miner {
    meta:
        description = "Detects XMRig cryptocurrency miner"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "crypto_miner"
    strings:
        $xmrig_stratum = "stratum+tcp://" nocase
        $xmrig_tls = "stratum+ssl://" nocase
        $xmrig_url = "xmrig.com" nocase
        $xmrig_pool = "pool.minexmr.com" nocase
        $xmrig_config = "\"algo\": \"rx/0\"" nocase
        $xmrig_donate = "donate-level" nocase
        $xmrig_user = "\"user\": \"" nocase
        $xmrig_pass = "\"pass\": \"" nocase
    condition:
        any of ($xmrig_stratum, $xmrig_tls) or
        ($xmrig_config and $xmrig_donate) or
        ($xmrig_url and $xmrig_pool)
}

rule Miner_Generic_Patterns {
    meta:
        description = "Detects generic cryptocurrency mining patterns"
        author = "Bionic Vuln Lab"
        severity = "high"
        category = "crypto_miner"
    strings:
        $stratum = "stratum+tcp://" nocase
        $stratum_ssl = "stratum+ssl://" nocase
        $mining_subscribe = "mining.subscribe" nocase
        $mining_authorize = "mining.authorize" nocase
        $mining_submit = "mining.submit" nocase
        $hash_rate = "hashrate" nocase
        $hash_rate2 = "hashes per second" nocase
        $crypto_wallet_btc = /[13][a-km-zA-HJ-NP-Z1-9]{25,34}/
        $crypto_wallet_eth = /0x[a-fA-F0-9]{40}/
        $crypto_wallet_xmr = /4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}/
        $pool_mining = "pool." nocase
        $worker_name = "worker" nocase
    condition:
        ($stratum and $mining_subscribe) or
        ($stratum_ssl and $mining_authorize) or
        ($mining_submit and $hash_rate) or
        ($pool_mining and $worker_name and $hash_rate) or
        (any of ($crypto_wallet_btc, $crypto_wallet_eth, $crypto_wallet_xmr) and $stratum)
}

rule Web_Based_Miner {
    meta:
        description = "Detects browser-based cryptocurrency miners"
        author = "Bionic Vuln Lab"
        severity = "medium"
        category = "crypto_miner"
    strings:
        $coin_imp = "coinimp.com" nocase
        $coin_hive = "coinhive.com" nocase
        $crypto_loot = "crypto-loot.com" nocase
        $mineralt = "mineralt" nocase
        $mineralt2 = "mineralt.com" nocase
        $wasm_miner = "wasmMiner" nocase
        $miner_script = "new Miner(" nocase
        $miner_anonymous = "Miner.Anonymous(" nocase
        $start_mining = "startMining" nocase
        $throttle = "throttleMiner" nocase
        $wasm_module = "application/wasm" nocase
    condition:
        any of ($coin_imp, $coin_hive, $crypto_loot, $mineralt, $mineralt2) or
        ($miner_script and $start_mining) or
        ($miner_anonymous and $throttle) or
        ($wasm_miner and $wasm_module)
}

rule Miner_Process_Indicators {
    meta:
        description = "Detects cryptocurrency mining process indicators"
        author = "Bionic Vuln Lab"
        severity = "medium"
        category = "crypto_miner"
    strings:
        $cpuminer = "cpuminer" nocase
        $ccminer = "ccminer" nocase
        $cgminer = "cgminer" nocase
        $bfgminer = "bfgminer" nocase
        $sgminer = "sgminer" nocase
        $ethminer = "ethminer" nocase
        $phoenixminer = "phoenixminer" nocase
        $lolminer = "lolminer" nocase
        $nbminer = "nbminer" nocase
        $t-rex = "t-rex" nocase
        $rigel = "rigel" nocase
        $pool_config = "--pool" nocase
        $wallet_flag = "--wallet" nocase
    condition:
        any of ($cpuminer, $ccminer, $cgminer, $bfgminer, $sgminer, $ethminer, $phoenixminer, $lolminer, $nbminer, $t-rex, $rigel) or
        ($pool_config and $wallet_flag)
}
