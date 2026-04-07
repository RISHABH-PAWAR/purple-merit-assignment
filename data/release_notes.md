# Release: Smart Checkout v2.1.0

**Release Date:** Day 7 of monitoring window  
**Teams:** Payments Engineering + Platform Engineering  
**Rollout:** 30% of users (feature flag: `smart_checkout_v2`)  

## What Changed

- Rebuilt entire checkout flow using React 18 components (replaced legacy jQuery 3.x UI)
- Added 3DS2 authentication for international card payments
- New payment retry logic: max 3 attempts with exponential backoff before fallback to legacy flow
- API gateway migrated from nginx 1.24 to Envoy 1.29 proxy
- New funnel step 3: ID verification widget (required for payments > $500)
- Mobile SDK updated: iOS 17.4 compatibility + Android 13 optimisations

## Success Criteria (defined pre-launch)

- Activation rate: maintain ≥ 60% (baseline 62%)
- Crash rate: stay below 1.0%
- API latency p95: stay below 500ms
- Payment success rate: stay above 98.5%
- Support ticket volume: increase < 30% from baseline
- Funnel completion: maintain ≥ 65%

## Known Risks at Launch

1. **3DS2 coverage gap:** Visa and Mastercard tested. American Express 3DS2 NOT tested on production card networks.
2. **Envoy load cap:** Envoy config load-tested to 500 RPS only. Production peak traffic is ~700 RPS during business hours.
3. **Android 11:** Android 12 and 13 compatibility confirmed. Android 11 was NOT re-tested after the mobile SDK update.
4. **Funnel step 3 UX:** The new ID verification step (step 3) was added without user testing. Only internal QA tested it.
5. **Idempotency:** Payment retry logic is new — idempotency keys for duplicate charge prevention are untested at scale.

## Rollback Plan

- Feature flag `smart_checkout_v2` can be set to 0% in under 5 minutes via the feature flag console
- Database migration v2.1.0 is fully backward-compatible — safe to rollback without data loss
- Previous nginx load balancer configuration is archived as `nginx-config-v2.0-backup` — estimated 20 min restore
- iOS/Android SDK rollback via forced app update — estimated 4–6 hours for user adoption

## Monitoring Contacts

- On-call Payments Eng: #payments-oncall Slack
- On-call Platform Eng: #platform-oncall Slack
- PM: #product-war-room Slack
