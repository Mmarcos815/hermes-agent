# API ENDPOINTS - live intel 2026-09-16 - farm_3phones
## MintPull (com.garooms.tcgpackcash.gp v1.0.3, Arcane, mintpull.net)
- TOS/site: https://mintpull.net/tos (ToS v4.0 Sep 3 2026)
- KYC: https://api.sumsub.com (ID verify at cashout - SHIP ONLY rule)
- Anti-farm: https://api.fpjs.io + https://ap.api.fpjs.io (FingerprintJS - 1 acct/phone strict)
- Push: https://api.onesignal.com
- Game backend hint: https://app-card-l.luckfun.vip/ach_done.htm
## MintPull BACKEND CRACKED from Unity metadata (no cert needed)
- API: https://api.mintpull.net (CloudFront, live, returns build id)
- Game server: https://mintpull-gp.mintpull.net = AWS Ohio EC2 18.190.249.123 Columbus (same city as Rip Rush!) - Chinese admin portal 系统登录 Feishu login = Chinese white-label team (luckfun.vip)
- Assets: S3 df34.us-east-2 + CloudFront d1grpbmixgh84i
- Web: https://mintpull.net/rpp + /tos
## Outpost (com.cardoutpost.app v1.0.2, Vercel iad1, Expo RN)
- Web: https://www.cardoutpost.com (Next.js, /api/* = app shell, no public REST)
- Auth/backend: Supabase - aqvuvvvblfugjwoqhbje.supabase (cognito) + fakcdofjuaeweulzzuuf.supabase (rest) - anon key in JS bundle, enumerate next
- Staging seen: staging.cardoutpost (test env?)
- Pay: Stripe (b.stripecdn) + Apple Pay. Withdraw = KYC. Sell-back 100%-3% instant.
- Data: api.tcgdex.net referenced in-app
## Boxed (Loot Labs, CloudFront IAD + API Gateway api.boxed.gg)
- Web: https://boxed.gg/boxes /vending /battles /forge /rewards /missions /luckback /marketplace /exchange /leaderboard
- API: https://api.boxed.gg/ (gateway live, paths hidden - Frida target #1)
- CDN: https://cdn.boxed.gg + product-images.tcgplayer.com
- FREE: /rewards daily (level up = more), /missions gems (watch ads 1 gem, RevU installs), polls easy gems, luckback shards, affiliate
## Courtyard - OUT no SSN. Intel only: PullValue.io EV + Apify scrapers + public marketplace/leaderboard/blog
## TCGP (jp.pokemon.pokemontcgp v1.7.2) - closed DeNA. Data: https://api.tcgdex.net/v2/en/series/tcgp
## Rip Rush - PARKED age gate. com.emeraldmyth.riprush.and NOT installed. No bypass.
